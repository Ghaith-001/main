"""
Service numérique: conversion d'un modèle IA vers projet HLS.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
import importlib
from datetime import datetime
from typing import Any

import numpy as np

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "composants_db.sqlite")
HLS_ROOT = os.path.join(BASE_DIR, "hls_projects", "digital")
UPLOADS_ROOT = os.path.join(BASE_DIR, "models", "digital_uploads")

os.makedirs(HLS_ROOT, exist_ok=True)
os.makedirs(UPLOADS_ROOT, exist_ok=True)


def _safe_name(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_-]+", "_", value.strip())
    return value.strip("_") or "model"


def _ensure_digital_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS digital_hls_jobs (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name         TEXT NOT NULL,
            input_model_path   TEXT NOT NULL,
            output_project_dir TEXT,
            output_zip_path    TEXT,
            backend            TEXT NOT NULL DEFAULT 'hls4ml',
            precision          TEXT NOT NULL DEFAULT 'ap_fixed<16,6>',
            target_part        TEXT NOT NULL DEFAULT 'xc7a35tcpg236-1',
            clock_period       REAL NOT NULL DEFAULT 10.0,
            io_type            TEXT NOT NULL DEFAULT 'io_parallel',
            status             TEXT NOT NULL DEFAULT 'created',
            resources_json     TEXT,
            latency_json       TEXT,
            error_message      TEXT,
            created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()


def _insert_job(
    conn: sqlite3.Connection,
    model_name: str,
    input_model_path: str,
    backend: str,
    precision: str,
    target_part: str,
    clock_period: float,
    io_type: str,
) -> int:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO digital_hls_jobs
            (model_name, input_model_path, backend, precision, target_part, clock_period, io_type, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (model_name, input_model_path, backend, precision, target_part, float(clock_period), io_type, "running"),
    )
    conn.commit()
    return int(cur.lastrowid)


def _update_job_success(
    conn: sqlite3.Connection,
    job_id: int,
    output_project_dir: str,
    output_zip_path: str,
    resources: dict[str, Any],
    latency: dict[str, Any],
) -> None:
    conn.execute(
        """
        UPDATE digital_hls_jobs
        SET status = ?,
            output_project_dir = ?,
            output_zip_path = ?,
            resources_json = ?,
            latency_json = ?
        WHERE id = ?
        """,
        (
            "done",
            output_project_dir,
            output_zip_path,
            json.dumps(resources),
            json.dumps(latency),
            job_id,
        ),
    )
    conn.commit()


def _update_job_error(conn: sqlite3.Connection, job_id: int, error_message: str) -> None:
    conn.execute(
        "UPDATE digital_hls_jobs SET status = ?, error_message = ? WHERE id = ?",
        ("error", error_message[:1000], job_id),
    )
    conn.commit()


def _estimate_resources_and_latency(model, precision: str, clock_period: float, reuse_factor: int = 1) -> tuple[dict[str, Any], dict[str, Any]]:
    bits = 16
    m_bits = re.search(r"<(\d+)", precision)
    if m_bits:
        bits = int(m_bits.group(1))

    dense_layers = [layer for layer in model.layers if layer.get_weights()]
    macs = 0
    total_weights = 0
    layer_sizes: list[dict[str, int]] = []

    for layer in dense_layers:
        weights = layer.get_weights()
        if not weights:
            continue
        weight_matrix = weights[0]
        bias_vector = weights[1] if len(weights) > 1 else np.array([])
        in_dim, out_dim = int(weight_matrix.shape[0]), int(weight_matrix.shape[1])
        layer_sizes.append({"in": in_dim, "out": out_dim})
        macs += in_dim * out_dim
        total_weights += int(weight_matrix.size + bias_vector.size)

    dsp_est = max(1, int(np.ceil(macs / max(1, reuse_factor)))) if macs > 0 else 0
    bram18_est = int(np.ceil((total_weights * bits) / (18 * 1024))) if total_weights > 0 else 0
    latency_cycles = int(np.ceil(macs / max(1, reuse_factor)) + sum(layer["out"] for layer in layer_sizes))
    latency_ns = round(latency_cycles * float(clock_period), 2)
    throughput_msps = round(1000.0 / float(clock_period), 2)

    resources = {
        "params_total": int(model.count_params()),
        "weights_total": int(total_weights),
        "mac_operations": int(macs),
        "estimated_dsp": int(dsp_est),
        "estimated_bram18": int(bram18_est),
        "precision": precision,
    }

    latency = {
        "estimated_cycles": int(latency_cycles),
        "clock_period_ns": float(clock_period),
        "estimated_latency_ns": latency_ns,
        "estimated_latency_us": round(latency_ns / 1000.0, 3),
        "estimated_throughput_msps": throughput_msps,
    }

    return resources, latency


def _write_stub_hls_project(model, project_dir: str, model_name: str, precision: str, target_part: str, clock_period: float) -> None:
    firmware_dir = os.path.join(project_dir, "firmware")
    weights_dir = os.path.join(firmware_dir, "weights")
    os.makedirs(weights_dir, exist_ok=True)

    dense_layers = [layer for layer in model.layers if layer.get_weights()]

    with open(os.path.join(firmware_dir, "parameters.h"), "w", encoding="utf-8") as f:
        lines = [
            "#ifndef PARAMETERS_H_",
            "#define PARAMETERS_H_",
            "#include \"ap_fixed.h\"",
            "#include \"ap_int.h\"",
            f"typedef {precision} data_t;",
            f"typedef {precision} weight_t;",
            "typedef ap_fixed<24,10> accum_t;",
            "typedef ap_fixed<24,10> result_t;",
            f"#define N_LAYERS {len(dense_layers)}",
        ]
        for idx, layer in enumerate(dense_layers, start=1):
            w = layer.get_weights()[0]
            lines.append(f"#define N_LAYER_{idx}_IN {w.shape[0]}")
            lines.append(f"#define N_LAYER_{idx}_OUT {w.shape[1]}")
        lines.append("#endif")
        f.write("\n".join(lines))

    with open(os.path.join(firmware_dir, "myproject.h"), "w", encoding="utf-8") as f:
        f.write(
            "#ifndef MYPROJECT_H_\n"
            "#define MYPROJECT_H_\n"
            "#include \"parameters.h\"\n"
            "void myproject(data_t input[1], result_t output[1]);\n"
            "#endif\n"
        )

    cpp_lines = [
        '#include "myproject.h"',
        '#include "weights/weights.h"',
        "",
        "void myproject(data_t input[1], result_t output[1]) {",
        "#pragma HLS PIPELINE II=1",
    ]

    for idx, layer in enumerate(dense_layers, start=1):
        w = layer.get_weights()[0]
        in_dim, out_dim = int(w.shape[0]), int(w.shape[1])
        source = "input" if idx == 1 else f"layer{idx-1}_out"
        cpp_lines.extend(
            [
                f"  data_t layer{idx}_out[{out_dim}];",
                f"  for (int j = 0; j < {out_dim}; j++) {{",
                f"    accum_t acc = bias{idx}[j];",
                f"    for (int i = 0; i < {in_dim}; i++) acc += weight{idx}[i][j] * {source}[i];",
                f"    layer{idx}_out[j] = {'acc > 0 ? acc : (accum_t)0' if idx < len(dense_layers) else 'acc'};",
                "  }",
            ]
        )

    if dense_layers:
        cpp_lines.append(f"  output[0] = layer{len(dense_layers)}_out[0];")
    else:
        cpp_lines.append("  output[0] = input[0];")
    cpp_lines.append("}")

    with open(os.path.join(firmware_dir, "myproject.cpp"), "w", encoding="utf-8") as f:
        f.write("\n".join(cpp_lines))

    weight_lines = ["#ifndef WEIGHTS_H_", "#define WEIGHTS_H_", '#include "../parameters.h"', ""]
    for idx, layer in enumerate(dense_layers, start=1):
        weights = layer.get_weights()
        W = weights[0]
        b = weights[1] if len(weights) > 1 else np.zeros((W.shape[1],), dtype=np.float32)

        np.savetxt(os.path.join(weights_dir, f"w{idx}.dat"), W, fmt="%.8e")
        np.savetxt(os.path.join(weights_dir, f"b{idx}.dat"), b, fmt="%.8e")

        rows, cols = W.shape
        weight_lines.append(f"static weight_t weight{idx}[{rows}][{cols}] = {{")
        for r in range(rows):
            row_data = ", ".join(f"{float(x):.8e}" for x in W[r])
            weight_lines.append(f"  {{{row_data}}},")
        weight_lines.append("};")
        bias_data = ", ".join(f"{float(x):.8e}" for x in b)
        weight_lines.append(f"static weight_t bias{idx}[{len(b)}] = {{{bias_data}}};")
        weight_lines.append("")

    weight_lines.append("#endif")
    with open(os.path.join(weights_dir, "weights.h"), "w", encoding="utf-8") as f:
        f.write("\n".join(weight_lines))

    with open(os.path.join(project_dir, "build_prj.tcl"), "w", encoding="utf-8") as f:
        f.write(
            f"open_project {model_name}_prj\n"
            "set_top myproject\n"
            "add_files firmware/myproject.cpp\n"
            "add_files firmware/myproject.h\n"
            "add_files firmware/parameters.h\n"
            "open_solution solution1\n"
            f"set_part {{{target_part}}}\n"
            f"create_clock -period {clock_period} -name default\n"
            "csynth_design\n"
            "export_design -format ip_catalog\n"
            "exit\n"
        )


def save_uploaded_model(uploaded_file, model_basename: str | None = None) -> tuple[str, str]:
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in {".keras", ".h5"}:
        raise ValueError("Formats acceptés: .keras ou .h5")

    base_name = _safe_name(model_basename or os.path.splitext(uploaded_file.name)[0])
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{base_name}_{ts}{ext}"
    model_path = os.path.join(UPLOADS_ROOT, filename)

    with open(model_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return model_path, base_name


def generate_hls_project_from_model(
    model_path: str,
    model_name: str,
    target_part: str = "xc7a35tcpg236-1",
    clock_period: float = 10.0,
    precision: str = "ap_fixed<16,6>",
    io_type: str = "io_parallel",
    backend: str = "Vivado",
) -> dict[str, Any]:
    import tensorflow as tf

    safe_model_name = _safe_name(model_name)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_name = f"{safe_model_name}_{ts}"
    project_dir = os.path.join(HLS_ROOT, project_name)
    os.makedirs(project_dir, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    _ensure_digital_table(conn)
    job_id = _insert_job(
        conn,
        model_name=safe_model_name,
        input_model_path=model_path,
        backend="hls4ml",
        precision=precision,
        target_part=target_part,
        clock_period=clock_period,
        io_type=io_type,
    )

    try:
        model = tf.keras.models.load_model(model_path)
        resources, latency = _estimate_resources_and_latency(model, precision=precision, clock_period=clock_period)

        engine = "hls4ml"
        try:
            hls4ml = importlib.import_module("hls4ml")

            hls_config = hls4ml.utils.config_from_keras_model(model, granularity="name")
            hls_config["Model"]["Precision"] = precision
            hls_config["Model"]["ReuseFactor"] = 1
            hls_config["Model"]["Strategy"] = "Latency"

            hls_model = hls4ml.converters.convert_from_keras_model(
                model,
                hls_config=hls_config,
                output_dir=project_dir,
                backend=backend,
                project_name="myproject",
                part=target_part,
                clock_period=float(clock_period),
                io_type=io_type,
            )
            hls_model.compile()

            with open(os.path.join(project_dir, "hls4ml_config.json"), "w", encoding="utf-8") as f:
                json.dump(hls_config, f, indent=2)

        except Exception:
            engine = "stub"
            _write_stub_hls_project(
                model=model,
                project_dir=project_dir,
                model_name=safe_model_name,
                precision=precision,
                target_part=target_part,
                clock_period=float(clock_period),
            )

        report_payload = {
            "engine": engine,
            "model_name": safe_model_name,
            "target_part": target_part,
            "clock_period_ns": float(clock_period),
            "precision": precision,
            "io_type": io_type,
            "resources": resources,
            "latency": latency,
        }
        with open(os.path.join(project_dir, "digital_report.json"), "w", encoding="utf-8") as f:
            json.dump(report_payload, f, indent=2)

        zip_path = shutil.make_archive(project_dir, "zip", project_dir)
        _update_job_success(
            conn,
            job_id=job_id,
            output_project_dir=project_dir,
            output_zip_path=zip_path,
            resources=resources,
            latency=latency,
        )

        return {
            "job_id": job_id,
            "project_dir": project_dir,
            "zip_path": zip_path,
            "resources": resources,
            "latency": latency,
            "engine": engine,
            "target_part": target_part,
            "clock_period": float(clock_period),
            "precision": precision,
            "io_type": io_type,
        }
    except Exception as exc:
        _update_job_error(conn, job_id=job_id, error_message=str(exc))
        raise
    finally:
        conn.close()
