"""
MÉTRIQUES — metriques.py
Fonctions de calcul des métriques d'erreur entre simulation et prédiction.
Critères PASS/FAIL:
  - IA   : PASS si erreur_rel < 2%
  - HLS  : PASS si erreur_rel < 5%
"""

import numpy as np

# Seuils PASS/FAIL
SEUIL_IA_PASS  = 2.0   # % erreur relative
SEUIL_HLS_PASS = 5.0   # % erreur relative


def calcul_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Mean Absolute Error (MAE).
    MAE = mean(|y_true - y_pred|)
    """
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)
    return float(np.mean(np.abs(y_true - y_pred)))


def calcul_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Root Mean Squared Error (RMSE).
    RMSE = sqrt(mean((y_true - y_pred)^2))
    """
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def calcul_erreur_max(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Erreur maximale absolue.
    E_max = max(|y_true - y_pred|)
    """
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)
    return float(np.max(np.abs(y_true - y_pred)))


def calcul_erreur_rel(y_true: np.ndarray, y_pred: np.ndarray,
                      epsilon: float = 1e-15) -> float:
    """
    Erreur relative moyenne en pourcentage.
    E_rel = mean(|y_true - y_pred| / (|y_true| + epsilon)) * 100
    """
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)
    rel = np.abs(y_true - y_pred) / (np.abs(y_true) + epsilon)
    return float(np.mean(rel) * 100.0)


def calcul_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Coefficient de détermination R².
    R² = 1 - SS_res / SS_tot
    """
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return 1.0
    return float(1.0 - ss_res / ss_tot)


def toutes_metriques(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """
    Calcule toutes les métriques en une seule fois.
    Retourne un dict avec MAE, RMSE, E_max, E_rel, R2.
    """
    return {
        "MAE":       calcul_mae(y_true, y_pred),
        "RMSE":      calcul_rmse(y_true, y_pred),
        "E_max":     calcul_erreur_max(y_true, y_pred),
        "E_rel_%":   calcul_erreur_rel(y_true, y_pred),
        "R2":        calcul_r2(y_true, y_pred),
    }


def verdict_pass_fail(erreur_rel: float, mode: str = "ia") -> str:
    """
    Retourne 'PASS' ou 'FAIL' selon le seuil du mode.
    mode: 'ia' (seuil 2%) ou 'hls' (seuil 5%)
    """
    seuil = SEUIL_IA_PASS if mode == "ia" else SEUIL_HLS_PASS
    return "PASS" if erreur_rel < seuil else "FAIL"


def rapport_metriques(y_true: np.ndarray, y_pred: np.ndarray,
                      mode: str = "ia", composant: str = "") -> str:
    """
    Génère un rapport textuel des métriques.
    """
    m = toutes_metriques(y_true, y_pred)
    verdict = verdict_pass_fail(m["E_rel_%"], mode)
    seuil   = SEUIL_IA_PASS if mode == "ia" else SEUIL_HLS_PASS

    lines = [
        f"\n{'='*45}",
        f"  RAPPORT MÉTRIQUES — {composant} [{mode.upper()}]",
        f"{'='*45}",
        f"  MAE           : {m['MAE']:.6e} A",
        f"  RMSE          : {m['RMSE']:.6e} A",
        f"  Erreur max    : {m['E_max']:.6e} A",
        f"  Erreur rel.   : {m['E_rel_%']:.4f} %  (seuil: {seuil}%)",
        f"  R²            : {m['R2']:.6f}",
        f"{'='*45}",
        f"  VERDICT       : {'✅ ' if verdict == 'PASS' else '❌ '}{verdict}",
        f"{'='*45}\n",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    # Test rapide
    y_true = np.array([1e-10, 1e-8, 1e-5, 1e-3, 0.01, 0.1, 0.5, 1.0])
    y_pred = y_true * (1 + np.random.normal(0, 0.01, len(y_true)))
    print(rapport_metriques(y_true, y_pred, mode="ia", composant="TEST"))
