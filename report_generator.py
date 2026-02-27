"""
GÉNÉRATEUR DE RAPPORTS PDF — report_generator.py
Génère un rapport de validation complet en PDF avec FPDF2.
Contenu : header, courbes, tableau métriques, histogramme, verdict PASS/FAIL.
"""

import os
import json
import sqlite3
import tempfile
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime

DB_PATH     = os.path.join(os.path.dirname(__file__), "composants_db.sqlite")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


def _sauvegarder_figure_temp(fig: plt.Figure, suffix: str = "") -> str:
    """Sauvegarde une figure matplotlib dans un fichier temp et retourne le chemin."""
    tmp = tempfile.NamedTemporaryFile(suffix=f"_{suffix}.png", delete=False)
    fig.savefig(tmp.name, dpi=120, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return tmp.name


def generer_rapport(composant_nom: str, quant_type: str = "int8") -> str:
    """
    Génère le rapport PDF de validation pour un composant.
    Retourne le chemin vers le fichier PDF généré.
    """
    try:
        from fpdf import FPDF
    except ImportError:
        raise ImportError("fpdf2 requis : pip install fpdf2")

    from metriques import toutes_metriques, verdict_pass_fail

    # Charger les données
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, type, params_json FROM composants WHERE nom = ?",
                   (composant_nom,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Composant '{composant_nom}' introuvable.")

    comp_id, comp_type, params_json = row
    params = json.loads(params_json)

    # Simulation
    cursor.execute(
        "SELECT V_json, I_json FROM simulations WHERE composant_id = ? "
        "ORDER BY created_at DESC LIMIT 1", (comp_id,)
    )
    sim = cursor.fetchone()

    # IA
    cursor.execute(
        "SELECT V_pred_json, I_pred_json, mae, rmse, erreur_max, erreur_rel "
        "FROM modeles_ia WHERE composant_id = ? ORDER BY created_at DESC LIMIT 1",
        (comp_id,)
    )
    ia = cursor.fetchone()

    # HLS
    cursor.execute(
        "SELECT V_hls_json, I_hls_json, mae, rmse, erreur_max, erreur_rel "
        "FROM modeles_hls WHERE composant_id = ? AND quant_type = ? "
        "ORDER BY created_at DESC LIMIT 1",
        (comp_id, quant_type)
    )
    hls = cursor.fetchone()
    conn.close()

    if not sim:
        raise ValueError(f"Aucune simulation pour '{composant_nom}'.")

    V_sim = np.array(json.loads(sim[0]))
    I_sim = np.array(json.loads(sim[1]))
    has_ia  = ia  is not None
    has_hls = hls is not None

    # ── Générer les figures temporaires ──────────────────────────────────
    from visualiseur_validation import (courbe_unique, validation_ia,
                                        validation_hls, validation_complete,
                                        COULEURS, STYLE)

    tmp_files = []

    # Figure 1 : courbe simulée
    fig1 = courbe_unique(composant_nom)
    tmp1 = _sauvegarder_figure_temp(fig1, "sim")
    tmp_files.append(tmp1)

    # Figure 2 : validation IA (si disponible)
    tmp2 = None
    if has_ia:
        fig2 = validation_ia(composant_nom)
        tmp2 = _sauvegarder_figure_temp(fig2, "ia")
        tmp_files.append(tmp2)

    # Figure 3 : validation HLS (si disponible)
    tmp3 = None
    if has_hls:
        fig3 = validation_hls(composant_nom)
        tmp3 = _sauvegarder_figure_temp(fig3, "hls")
        tmp_files.append(tmp3)

    # Figure 4 : histogramme erreurs
    tmp4 = None
    if has_ia or has_hls:
        fig4, ax = plt.subplots(figsize=(10, 4))
        fig4.patch.set_facecolor("white")
        if has_ia:
            I_pred = np.array(json.loads(ia[1]))
            err_ia = np.abs(I_sim - np.interp(V_sim, np.array(json.loads(ia[0])), I_pred))
            ax.hist(err_ia, bins=60, alpha=0.65, color=COULEURS["ia"],
                    label="Erreur IA", density=True)
        if has_hls:
            I_hls = np.array(json.loads(hls[1]))
            err_hls = np.abs(I_sim - np.interp(V_sim, np.array(json.loads(hls[0])), I_hls))
            ax.hist(err_hls, bins=60, alpha=0.65, color=COULEURS["hls"],
                    label="Erreur HLS int8", density=True)
        ax.set_xlabel("Erreur absolue (A)")
        ax.set_ylabel("Densité")
        ax.set_title("Distribution des erreurs")
        ax.set_xscale("log")
        ax.grid(True, alpha=0.3)
        ax.legend()
        fig4.tight_layout()
        tmp4 = _sauvegarder_figure_temp(fig4, "hist")
        tmp_files.append(tmp4)

    # ── Construire le PDF ─────────────────────────────────────────────────
    class PDF(FPDF):
        def header(self):
            self.set_font("Helvetica", "B", 13)
            self.set_fill_color(44, 62, 80)
            self.set_text_color(255, 255, 255)
            self.cell(0, 12, f"Rapport de Validation — {composant_nom}",
                      align="C", fill=True)
            self.ln(4)
            self.set_text_color(0, 0, 0)

        def footer(self):
            self.set_y(-12)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 8,
                      f"Généré le {datetime.now().strftime('%Y-%m-%d %H:%M')} "
                      f"| Plateforme Validation SPICE",
                      align="C")

    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Titre et infos générales
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_fill_color(236, 240, 241)
    pdf.cell(0, 8, "1. Informations Composant", fill=True)
    pdf.ln(3)
    pdf.set_font("Helvetica", size=10)

    infos = [
        ("Nom", composant_nom),
        ("Type", comp_type),
        ("Date rapport", datetime.now().strftime("%Y-%m-%d %H:%M")),
    ]
    for key, val in infos:
        pdf.cell(50, 7, f"{key}:", border=0)
        pdf.cell(0, 7, str(val))
        pdf.ln()

    # Paramètres SPICE (tableau)
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_fill_color(236, 240, 241)
    pdf.cell(0, 8, "2. Paramètres SPICE", fill=True)
    pdf.ln(3)
    pdf.set_font("Helvetica", size=9)

    col_w = [45, 60, 85]
    headers = ["Paramètre", "Valeur", "Description"]
    descriptions = {
        "IS": "Courant de saturation (A)", "RS": "Résistance série (Ω)",
        "N": "Facteur d'idéalité", "BV": "Tension de claquage (V)",
        "IBV": "Courant de claquage (A)", "CJO": "Capacité jonction (F)",
        "VJ": "Potentiel jonction (V)", "M": "Coefficient gradation",
        "FC": "Coefficient direct", "TT": "Temps transit (s)",
        "EG": "Bande interdite (eV)", "XTI": "Coeff température",
        "KF": "Facteur bruit", "AF": "Exposant bruit",
    }

    pdf.set_fill_color(44, 62, 80)
    pdf.set_text_color(255, 255, 255)
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 7, h, border=1, fill=True, align="C")
    pdf.ln()
    pdf.set_fill_color(255, 255, 255)
    pdf.set_text_color(0, 0, 0)

    fill = False
    for pname, pval in params.items():
        pdf.set_fill_color(245, 245, 245) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.cell(col_w[0], 6, pname, border=1, fill=True)
        pdf.cell(col_w[1], 6, f"{pval:.6g}" if isinstance(pval, float) else str(pval),
                 border=1, fill=True)
        pdf.cell(col_w[2], 6, descriptions.get(pname, ""), border=1, fill=True)
        pdf.ln()
        fill = not fill

    # Courbe simulée
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_fill_color(236, 240, 241)
    pdf.cell(0, 8, "3. Courbe I-V Simulée (Vérité Terrain)", fill=True)
    pdf.ln(4)
    pdf.image(tmp1, x=10, w=190)
    pdf.ln(3)

    # Métriques IA
    if has_ia and tmp2:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_fill_color(236, 240, 241)
        pdf.cell(0, 8, "4. Validation IA (MLP Keras)", fill=True)
        pdf.ln(4)
        pdf.image(tmp2, x=10, w=190)
        pdf.ln(3)

        m_ia = toutes_metriques(I_sim,
                                np.interp(V_sim, np.array(json.loads(ia[0])),
                                          np.array(json.loads(ia[1]))))
        verdict_ia = verdict_pass_fail(m_ia["E_rel_%"], "ia")

        pdf.set_font("Helvetica", size=10)
        pdf.cell(0, 7,
                 f"MAE={m_ia['MAE']:.3e}A | RMSE={m_ia['RMSE']:.3e}A | "
                 f"E_rel={m_ia['E_rel_%']:.2f}% | R²={m_ia['R2']:.4f}")
        pdf.ln()
        _ecrire_verdict(pdf, verdict_ia, "IA")

    # Métriques HLS
    if has_hls and tmp3:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_fill_color(236, 240, 241)
        pdf.cell(0, 8, f"5. Validation HLS ({quant_type})", fill=True)
        pdf.ln(4)
        pdf.image(tmp3, x=10, w=190)
        pdf.ln(3)

        m_hls = toutes_metriques(I_sim,
                                 np.interp(V_sim, np.array(json.loads(hls[0])),
                                           np.array(json.loads(hls[1]))))
        verdict_hls = verdict_pass_fail(m_hls["E_rel_%"], "hls")

        pdf.set_font("Helvetica", size=10)
        pdf.cell(0, 7,
                 f"MAE={m_hls['MAE']:.3e}A | RMSE={m_hls['RMSE']:.3e}A | "
                 f"E_rel={m_hls['E_rel_%']:.2f}% | R²={m_hls['R2']:.4f}")
        pdf.ln()
        _ecrire_verdict(pdf, verdict_hls, "HLS")

    # Histogramme
    if tmp4:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_fill_color(236, 240, 241)
        pdf.cell(0, 8, "6. Distribution des Erreurs", fill=True)
        pdf.ln(4)
        pdf.image(tmp4, x=10, w=190)

    # Sauvegarder
    pdf_path = os.path.join(REPORTS_DIR, f"{composant_nom}_validation.pdf")
    pdf.output(pdf_path)

    # Nettoyer les fichiers temp
    for f in tmp_files:
        try:
            os.unlink(f)
        except Exception:
            pass

    print(f"[RAPPORT] PDF généré: {pdf_path}")
    return pdf_path


def _ecrire_verdict(pdf, verdict: str, mode: str):
    """Écrit le verdict PASS/FAIL dans le PDF avec couleur."""
    pdf.set_font("Helvetica", "B", 13)
    if verdict == "PASS":
        pdf.set_text_color(39, 174, 96)
        pdf.cell(0, 10, f"VERDICT {mode}: ✓ PASS", align="C")
    else:
        pdf.set_text_color(192, 57, 43)
        pdf.cell(0, 10, f"VERDICT {mode}: ✗ FAIL", align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)


if __name__ == "__main__":
    import sys
    nom = sys.argv[1] if len(sys.argv) > 1 else "1N4007"
    path = generer_rapport(nom)
    print(f"Rapport disponible: {path}")
