"""
MOTEUR DE VISUALISATION — visualiseur_validation.py
Génère des figures Matplotlib pour la validation des composants.

Fonctions:
  - courbe_unique(composant)         : courbe I-V simulée
  - validation_ia(composant)         : SIMULATION vs IA
  - validation_hls(composant)        : SIMULATION vs HLS
  - validation_complete(composant)   : SIMULATION + IA + HLS + tableau
"""

import os
import sqlite3
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Backend non-interactif pour Streamlit
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch

DB_PATH = os.path.join(os.path.dirname(__file__), "composants_db.sqlite")

# Palette de couleurs
COULEURS = {
    "simulation": "#1f77b4",  # bleu
    "ia":         "#2ca02c",  # vert
    "hls":        "#ff7f0e",  # orange
    "erreur":     "#d62728",  # rouge
    "fond":       "#f8f9fa",
}

STYLE = {
    "simulation": {"color": COULEURS["simulation"], "lw": 2.0, "ls": "-",  "label": "Simulation SPICE"},
    "ia":         {"color": COULEURS["ia"],         "lw": 1.8, "ls": "--", "label": "Prédiction IA (MLP)"},
    "hls":        {"color": COULEURS["hls"],        "lw": 1.8, "ls": "-.", "label": "HLS int8 (quantifié)"},
}


def _charger_donnees(composant_nom: str) -> dict:
    """Charge toutes les données disponibles pour un composant."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, type FROM composants WHERE nom = ?", (composant_nom,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Composant '{composant_nom}' introuvable.")
    comp_id, comp_type = row

    data = {"nom": composant_nom, "type": comp_type}

    # Simulation
    cursor.execute(
        "SELECT V_json, I_json FROM simulations WHERE composant_id = ? "
        "ORDER BY created_at DESC LIMIT 1", (comp_id,)
    )
    sim = cursor.fetchone()
    if sim:
        data["V_sim"] = np.array(json.loads(sim[0]))
        data["I_sim"] = np.array(json.loads(sim[1]))

    # Modèle IA
    cursor.execute(
        "SELECT V_pred_json, I_pred_json, mae, rmse, erreur_max, erreur_rel "
        "FROM modeles_ia WHERE composant_id = ? ORDER BY created_at DESC LIMIT 1",
        (comp_id,)
    )
    ia = cursor.fetchone()
    if ia:
        data["V_pred"] = np.array(json.loads(ia[0]))
        data["I_pred"] = np.array(json.loads(ia[1]))
        data["m_ia"] = {"MAE": ia[2], "RMSE": ia[3], "E_max": ia[4], "E_rel_%": ia[5]}

    # Modèle HLS
    cursor.execute(
        "SELECT V_hls_json, I_hls_json, mae, rmse, erreur_max, erreur_rel "
        "FROM modeles_hls WHERE composant_id = ? ORDER BY created_at DESC LIMIT 1",
        (comp_id,)
    )
    hls = cursor.fetchone()
    if hls:
        data["V_hls"] = np.array(json.loads(hls[0]))
        data["I_hls"] = np.array(json.loads(hls[1]))
        data["m_hls"] = {"MAE": hls[2], "RMSE": hls[3], "E_max": hls[4], "E_rel_%": hls[5]}

    conn.close()
    return data


def _configurer_axe_iv(ax, titre: str = ""):
    """Configure les axes pour une courbe I-V diode standard."""
    ax.set_xlabel("Tension V (V)", fontsize=11)
    ax.set_ylabel("Courant I (A)", fontsize=11)
    if titre:
        ax.set_title(titre, fontsize=12, fontweight="bold")
    ax.set_yscale("symlog", linthresh=1e-9)
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.legend(fontsize=10, loc="upper left")
    ax.set_facecolor(COULEURS["fond"])
    ax.axhline(0, color="black", lw=0.5, alpha=0.5)
    ax.axvline(0, color="black", lw=0.5, alpha=0.5)


def courbe_unique(composant_nom: str,
                  type_courbe: str = "simulation") -> plt.Figure:
    """
    Affiche uniquement la courbe simulée du composant.
    Annote le seuil de conduction et le genou de la courbe.
    """
    data = _charger_donnees(composant_nom)

    if "V_sim" not in data:
        raise ValueError(f"Aucune simulation disponible pour '{composant_nom}'.")

    V, I = data["V_sim"], data["I_sim"]

    fig, ax = plt.subplots(figsize=(9, 6))
    fig.patch.set_facecolor("white")

    ax.plot(V, I, **STYLE["simulation"])

    # Annotation genou : point où dI/dV est max (zone directe)
    mask_pos = V > 0.1
    if mask_pos.sum() > 10:
        V_pos, I_pos = V[mask_pos], I[mask_pos]
        dIdV = np.gradient(I_pos, V_pos)
        idx_genou = np.argmax(dIdV)
        if 0 < idx_genou < len(V_pos) - 1:
            ax.annotate(
                f"Genou\n({V_pos[idx_genou]:.2f}V, {I_pos[idx_genou]*1000:.2f}mA)",
                xy=(V_pos[idx_genou], I_pos[idx_genou]),
                xytext=(V_pos[idx_genou] - 0.4, I_pos[idx_genou] * 10),
                arrowprops=dict(arrowstyle="->", color="gray"),
                fontsize=9, color="gray"
            )

    # Annotation seuil 1mA
    I_threshold = 1e-3
    if I.max() > I_threshold:
        idx_th = np.argmin(np.abs(I - I_threshold))
        ax.axvline(V[idx_th], color="red", ls=":", alpha=0.6, lw=1.2,
                   label=f"V(1mA) = {V[idx_th]:.3f}V")

    _configurer_axe_iv(ax, f"Courbe I-V — {composant_nom} (Simulation SPICE)")

    # Info parameters
    textstr = f"{composant_nom}\nType: {data['type']}"
    ax.text(0.98, 0.05, textstr, transform=ax.transAxes, fontsize=9,
            ha="right", va="bottom",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.4))

    fig.tight_layout()
    return fig


def validation_ia(composant_nom: str) -> plt.Figure:
    """
    Superposition SIMULATION vs PRÉDICTION IA.
    2 subplots : courbes superposées + erreur absolue.
    """
    data = _charger_donnees(composant_nom)

    if "V_sim" not in data:
        raise ValueError(f"Aucune simulation pour '{composant_nom}'.")
    if "V_pred" not in data:
        raise ValueError(f"Aucune prédiction IA pour '{composant_nom}'. "
                         f"Entraînez d'abord le modèle.")

    V_sim, I_sim   = data["V_sim"], data["I_sim"]
    V_pred, I_pred = data["V_pred"], data["I_pred"]
    m = data.get("m_ia", {})

    from metriques import verdict_pass_fail, calcul_erreur_rel
    err_rel  = m.get("E_rel_%", calcul_erreur_rel(I_sim, I_pred))
    verdict  = verdict_pass_fail(err_rel, mode="ia")
    couleur_verdict = "#2ca02c" if verdict == "PASS" else "#d62728"

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 9),
                                   gridspec_kw={"height_ratios": [3, 1.2]})
    fig.patch.set_facecolor("white")

    # Subplot 1 : courbes superposées
    ax1.plot(V_sim, I_sim,   **STYLE["simulation"])
    ax1.plot(V_pred, I_pred, **STYLE["ia"])

    label_m = (f"MAE={m.get('MAE', 0):.3e}A | RMSE={m.get('RMSE', 0):.3e}A | "
               f"E_rel={err_rel:.2f}%")
    ax1.text(0.02, 0.97, label_m, transform=ax1.transAxes, fontsize=9,
             va="top", bbox=dict(boxstyle="round", facecolor="lightgreen", alpha=0.5))

    verdict_txt = f"VERDICT IA: {verdict}"
    ax1.text(0.98, 0.05, verdict_txt, transform=ax1.transAxes, fontsize=11,
             fontweight="bold", ha="right", va="bottom",
             color=couleur_verdict,
             bbox=dict(boxstyle="round", facecolor=couleur_verdict, alpha=0.15))

    _configurer_axe_iv(ax1, f"Validation IA — {composant_nom}")

    # Subplot 2 : erreur absolue
    erreur_abs = np.abs(I_sim - np.interp(V_sim, V_pred, I_pred))
    ax2.fill_between(V_sim, erreur_abs, alpha=0.4, color=COULEURS["erreur"])
    ax2.plot(V_sim, erreur_abs, color=COULEURS["erreur"], lw=1.2,
             label=f"Erreur abs (max={m.get('E_max', erreur_abs.max()):.3e}A)")
    ax2.set_xlabel("Tension V (V)", fontsize=10)
    ax2.set_ylabel("|Erreur| (A)", fontsize=10)
    ax2.set_title("Erreur absolue point par point", fontsize=10)
    ax2.set_yscale("log")
    ax2.grid(True, alpha=0.3, linestyle="--")
    ax2.legend(fontsize=9)
    ax2.set_facecolor(COULEURS["fond"])

    fig.tight_layout(pad=2.0)
    return fig


def validation_hls(composant_nom: str) -> plt.Figure:
    """
    Superposition SIMULATION vs HLS (quantifié int8).
    2 subplots : courbes + erreur de quantification.
    """
    data = _charger_donnees(composant_nom)

    if "V_sim" not in data:
        raise ValueError(f"Aucune simulation pour '{composant_nom}'.")
    if "V_hls" not in data:
        raise ValueError(f"Aucun modèle HLS pour '{composant_nom}'. "
                         f"Lancez d'abord hls_converter.py.")

    V_sim, I_sim = data["V_sim"], data["I_sim"]
    V_hls, I_hls = data["V_hls"], data["I_hls"]
    m = data.get("m_hls", {})

    from metriques import verdict_pass_fail, calcul_erreur_rel
    err_rel = m.get("E_rel_%", calcul_erreur_rel(I_sim, I_hls))
    verdict = verdict_pass_fail(err_rel, mode="hls")
    couleur_verdict = "#2ca02c" if verdict == "PASS" else "#d62728"

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 9),
                                   gridspec_kw={"height_ratios": [3, 1.2]})
    fig.patch.set_facecolor("white")

    ax1.plot(V_sim, I_sim,  **STYLE["simulation"])
    ax1.plot(V_hls, I_hls,  **STYLE["hls"])

    label_m = (f"MAE={m.get('MAE', 0):.3e}A | E_rel={err_rel:.2f}% "
               f"(erreur quantification int8)")
    ax1.text(0.02, 0.97, label_m, transform=ax1.transAxes, fontsize=9,
             va="top", bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.7))

    ax1.text(0.98, 0.05, f"VERDICT HLS: {verdict}", transform=ax1.transAxes,
             fontsize=11, fontweight="bold", ha="right", va="bottom",
             color=couleur_verdict,
             bbox=dict(boxstyle="round", facecolor=couleur_verdict, alpha=0.15))

    _configurer_axe_iv(ax1, f"Validation HLS (int8) — {composant_nom}")

    # Erreur quantification
    erreur_quant = np.abs(I_sim - np.interp(V_sim, V_hls, I_hls))
    ax2.fill_between(V_sim, erreur_quant, alpha=0.4, color=COULEURS["hls"])
    ax2.plot(V_sim, erreur_quant, color=COULEURS["hls"], lw=1.2,
             label=f"Erreur quantification (max={erreur_quant.max():.3e}A)")
    ax2.set_xlabel("Tension V (V)", fontsize=10)
    ax2.set_ylabel("|Erreur quant.| (A)", fontsize=10)
    ax2.set_title("Erreur de quantification int8", fontsize=10)
    ax2.set_yscale("log")
    ax2.grid(True, alpha=0.3, linestyle="--")
    ax2.legend(fontsize=9)
    ax2.set_facecolor(COULEURS["fond"])

    fig.tight_layout(pad=2.0)
    return fig


def validation_complete(composant_nom: str,
                        exporter_pdf: bool = True) -> plt.Figure:
    """
    Superposition SIMULATION + IA + HLS.
    Layout:
      - [haut] 3 courbes superposées
      - [milieu-gauche] zoom genou (0.4V–0.9V)
      - [milieu-droite] tableau métriques comparatif
      - [bas] histogramme erreurs
    """
    data = _charger_donnees(composant_nom)

    if "V_sim" not in data:
        raise ValueError(f"Aucune simulation pour '{composant_nom}'.")

    V_sim, I_sim = data["V_sim"], data["I_sim"]
    has_ia  = "V_pred" in data
    has_hls = "V_hls"  in data

    from metriques import toutes_metriques, verdict_pass_fail

    fig = plt.figure(figsize=(14, 14))
    fig.patch.set_facecolor("white")
    fig.suptitle(f"Validation Complète — {composant_nom}",
                 fontsize=15, fontweight="bold", y=0.98)

    gs = gridspec.GridSpec(3, 2, figure=fig,
                           height_ratios=[2.5, 2, 1.5],
                           hspace=0.4, wspace=0.35)

    # ── Subplot 1 : courbes superposées (toute la largeur) ──────────────
    ax_main = fig.add_subplot(gs[0, :])
    ax_main.plot(V_sim, I_sim, **STYLE["simulation"], zorder=3)

    if has_ia:
        ax_main.plot(data["V_pred"], data["I_pred"], **STYLE["ia"], zorder=2)
    if has_hls:
        ax_main.plot(data["V_hls"],  data["I_hls"],  **STYLE["hls"], zorder=1)

    _configurer_axe_iv(ax_main, f"Courbes I-V superposées — {composant_nom}")

    # ── Subplot 2 : zoom genou ───────────────────────────────────────────
    ax_zoom = fig.add_subplot(gs[1, 0])
    mask_genou = (V_sim >= 0.4) & (V_sim <= 0.95)
    V_g, I_g = V_sim[mask_genou], I_sim[mask_genou]

    ax_zoom.plot(V_g, I_g, **STYLE["simulation"])
    if has_ia:
        mask_ia = (data["V_pred"] >= 0.4) & (data["V_pred"] <= 0.95)
        ax_zoom.plot(data["V_pred"][mask_ia], data["I_pred"][mask_ia], **STYLE["ia"])
    if has_hls:
        mask_hls = (data["V_hls"] >= 0.4) & (data["V_hls"] <= 0.95)
        ax_zoom.plot(data["V_hls"][mask_hls], data["I_hls"][mask_hls], **STYLE["hls"])

    ax_zoom.set_xlabel("Tension V (V)", fontsize=10)
    ax_zoom.set_ylabel("Courant I (A)", fontsize=10)
    ax_zoom.set_title("Zoom — Zone critique (genou)", fontsize=11, fontweight="bold")
    ax_zoom.set_yscale("log")
    ax_zoom.grid(True, alpha=0.3)
    ax_zoom.legend(fontsize=9)
    ax_zoom.set_facecolor(COULEURS["fond"])

    # ── Subplot 3 : tableau métriques ───────────────────────────────────
    ax_tab = fig.add_subplot(gs[1, 1])
    ax_tab.axis("off")

    col_labels = ["Métrique", "IA (MLP)", "HLS (int8)", "Seuil PASS"]
    rows_data  = []

    metriques_noms = ["MAE (A)", "RMSE (A)", "E_max (A)", "E_rel (%)"]

    m_ia  = data.get("m_ia",  {})
    m_hls = data.get("m_hls", {})

    if has_ia and has_hls:
        im = toutes_metriques(I_sim, np.interp(V_sim, data["V_pred"], data["I_pred"]))
        hm = toutes_metriques(I_sim, np.interp(V_sim, data["V_hls"],  data["I_hls"]))

        rows_data = [
            [metriques_noms[0], f"{im['MAE']:.3e}",    f"{hm['MAE']:.3e}",    "—"],
            [metriques_noms[1], f"{im['RMSE']:.3e}",   f"{hm['RMSE']:.3e}",   "—"],
            [metriques_noms[2], f"{im['E_max']:.3e}",  f"{hm['E_max']:.3e}",  "—"],
            [metriques_noms[3], f"{im['E_rel_%']:.2f}", f"{hm['E_rel_%']:.2f}", "<2% / <5%"],
        ]
        verdict_ia  = verdict_pass_fail(im["E_rel_%"], "ia")
        verdict_hls = verdict_pass_fail(hm["E_rel_%"], "hls")
        rows_data.append(["VERDICT",
                          f"{'✅' if verdict_ia=='PASS' else '❌'} {verdict_ia}",
                          f"{'✅' if verdict_hls=='PASS' else '❌'} {verdict_hls}",
                          ""])
    elif has_ia:
        im = toutes_metriques(I_sim, np.interp(V_sim, data["V_pred"], data["I_pred"]))
        rows_data = [
            [metriques_noms[0], f"{im['MAE']:.3e}",    "N/A", "—"],
            [metriques_noms[1], f"{im['RMSE']:.3e}",   "N/A", "—"],
            [metriques_noms[2], f"{im['E_max']:.3e}",  "N/A", "—"],
            [metriques_noms[3], f"{im['E_rel_%']:.2f}", "N/A", "<2%"],
        ]
        rows_data.append(["VERDICT",
                          f"{'✅' if verdict_pass_fail(im['E_rel_%'],'ia')=='PASS' else '❌'} "
                          f"{verdict_pass_fail(im['E_rel_%'],'ia')}",
                          "N/A", ""])
    else:
        rows_data = [[m, "N/A", "N/A", "—"] for m in metriques_noms]
        rows_data.append(["VERDICT", "N/A", "N/A", ""])

    table = ax_tab.table(
        cellText=rows_data,
        colLabels=col_labels,
        loc="center",
        cellLoc="center"
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.1, 1.8)

    # Colorer l'en-tête
    for j in range(len(col_labels)):
        table[0, j].set_facecolor("#2c3e50")
        table[0, j].set_text_props(color="white", fontweight="bold")

    # Colorer ligne VERDICT
    n_rows = len(rows_data)
    for j in range(len(col_labels)):
        table[n_rows, j].set_facecolor("#ecf0f1")

    ax_tab.set_title("Tableau Comparatif des Métriques",
                     fontsize=11, fontweight="bold", pad=10)

    # ── Subplot 4 : histogramme erreurs ─────────────────────────────────
    ax_hist = fig.add_subplot(gs[2, :])

    if has_ia:
        err_ia = np.abs(I_sim - np.interp(V_sim, data["V_pred"], data["I_pred"]))
        ax_hist.hist(err_ia, bins=60, alpha=0.6, color=COULEURS["ia"],
                     label="Erreur IA", density=True)
    if has_hls:
        err_hls = np.abs(I_sim - np.interp(V_sim, data["V_hls"], data["I_hls"]))
        ax_hist.hist(err_hls, bins=60, alpha=0.6, color=COULEURS["hls"],
                     label="Erreur HLS int8", density=True)

    ax_hist.set_xlabel("Erreur absolue (A)", fontsize=10)
    ax_hist.set_ylabel("Densité", fontsize=10)
    ax_hist.set_title("Distribution des erreurs", fontsize=11, fontweight="bold")
    ax_hist.set_xscale("log")
    ax_hist.grid(True, alpha=0.3)
    ax_hist.legend(fontsize=9)
    ax_hist.set_facecolor(COULEURS["fond"])

    # Export PDF
    if exporter_pdf:
        try:
            from report_generator import generer_rapport
            generer_rapport(composant_nom)
        except Exception as e:
            print(f"[RAPPORT] Avertissement export PDF: {e}")

    return fig


if __name__ == "__main__":
    import sys
    nom = sys.argv[1] if len(sys.argv) > 1 else "1N4007"
    fig = courbe_unique(nom)
    fig.savefig(f"{nom}_courbe.png", dpi=150, bbox_inches="tight")
    print(f"Courbe sauvegardée: {nom}_courbe.png")
