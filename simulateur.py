"""
SIMULATEUR SPICE — simulateur.py
Génère la courbe I-V "vérité terrain" par résolution numérique de l'équation
implicite diode (Newton-Raphson via scipy.optimize.fsolve).
Sortie : V_sim, I_sim stockés dans SQLite.
"""

import json
import os
import sqlite3
import numpy as np
from scipy.optimize import fsolve

DB_PATH = os.path.join(os.path.dirname(__file__), "composants_db.sqlite")

# Tension thermique à 25°C
VT = 0.02585  # V


def _equation_diode(I, V_applied, IS, RS, N, BV, IBV):
    """
    Équation implicite de la diode avec résistance série.
    f(I) = 0 avec:
      I = IS*(exp((V_applied - I*RS)/(N*VT)) - 1)
    Zone inverse: I ≈ -IS
    Zone claquage: V_applied < -BV → I = -IBV
    """
    V_diode = V_applied - I * RS

    # Zone claquage
    if V_applied < -BV + 0.1:
        return I + IBV

    # Zone directe / inverse normale
    exp_arg = V_diode / (N * VT)
    # Clamp pour éviter overflow
    exp_arg = np.clip(exp_arg, -500, 500)
    I_model = IS * (np.exp(exp_arg) - 1.0)
    return I - I_model


def _simuler_diode(params: dict, V_sweep: np.ndarray) -> np.ndarray:
    """
    Résout l'équation implicite pour chaque tension du sweep.
    Retourne le tableau I_sim correspondant.
    """
    IS  = params["IS"]
    RS  = params["RS"]
    N   = params["N"]
    BV  = params["BV"]
    IBV = params["IBV"]

    I_result = np.zeros_like(V_sweep)
    I_guess  = 1e-12  # point de départ

    for k, V in enumerate(V_sweep):
        # Zone claquage
        if V < -BV + 0.1:
            I_result[k] = -IBV
            continue

        # Valeur initiale intelligente
        if V > 0:
            exp_arg = np.clip(V / (N * VT), -500, 500)
            I_guess = IS * (np.exp(exp_arg) - 1.0)
        else:
            I_guess = -IS

        sol, info, ier, _ = fsolve(
            _equation_diode, I_guess,
            args=(V, IS, RS, N, BV, IBV),
            full_output=True
        )
        I_result[k] = float(sol[0])

    return I_result


def _calculer_capacite(params: dict, V_sweep: np.ndarray) -> np.ndarray:
    """
    C = CJO / (1 - V/VJ)^M  pour V < FC*VJ (zone inverse / faible direct)
    Pour V > FC*VJ : formule linéarisée SPICE
    """
    CJO = params["CJO"]
    VJ  = params["VJ"]
    M   = params["M"]
    FC  = params["FC"]

    C = np.zeros_like(V_sweep)
    for k, V in enumerate(V_sweep):
        if V <= FC * VJ:
            denom = (1.0 - V / VJ)
            denom = max(denom, 1e-6)
            C[k] = CJO / (denom ** M)
        else:
            # Linearisation SPICE au-delà de FC*VJ
            F1 = (1.0 / (1.0 - FC)) ** (1.0 + M)
            C[k] = CJO * F1 * (1.0 + M * (V - FC * VJ) / (VJ * (1.0 - FC)))
    return C


def simuler(composant_nom: str,
            V_min: float = -5.0,
            V_max: float = 1.2,
            n_points: int = 2000,
            force: bool = False) -> tuple[np.ndarray, np.ndarray]:
    """
    Simule la courbe I-V du composant et la sauvegarde en base.

    Args:
        composant_nom: Nom du composant (ex: '1N4007')
        V_min:  Tension minimale du sweep
        V_max:  Tension maximale du sweep
        n_points: Nombre de points
        force:  Recalculer même si déjà en base

    Returns:
        (V_sim, I_sim) arrays numpy
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Récupérer le composant
    cursor.execute(
        "SELECT id, type, params_json FROM composants WHERE nom = ?",
        (composant_nom,)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Composant '{composant_nom}' introuvable en base. "
                         f"Lancez d'abord upload_spice.py.")

    comp_id, comp_type, params_json = row
    params = json.loads(params_json)

    # Vérifier si simulation déjà présente
    if not force:
        cursor.execute(
            "SELECT V_json, I_json FROM simulations WHERE composant_id = ? "
            "ORDER BY created_at DESC LIMIT 1",
            (comp_id,)
        )
        existing = cursor.fetchone()
        if existing:
            V_sim = np.array(json.loads(existing[0]))
            I_sim = np.array(json.loads(existing[1]))
            conn.close()
            print(f"[SIM] Simulation '{composant_nom}' chargée depuis la base "
                  f"({len(V_sim)} points).")
            return V_sim, I_sim

    # Générer le sweep de tension
    # Points plus denses autour du genou (0.4V–0.9V)
    V_dense = np.linspace(0.4, 0.9, n_points // 2)
    V_sparse_neg = np.linspace(V_min, 0.4, n_points // 4)
    V_sparse_pos = np.linspace(0.9, V_max, n_points // 4)
    V_sweep = np.unique(np.concatenate([V_sparse_neg, V_dense, V_sparse_pos]))

    print(f"[SIM] Simulation de {composant_nom} sur [{V_min}V, {V_max}V] "
          f"({len(V_sweep)} points)...")

    if comp_type == "diode":
        I_sim = _simuler_diode(params, V_sweep)
    else:
        raise NotImplementedError(f"Type de composant '{comp_type}' non supporté.")

    V_sim = V_sweep

    # Supprimer l'ancienne simulation
    cursor.execute(
        "DELETE FROM simulations WHERE composant_id = ?", (comp_id,)
    )

    # Sauvegarder
    cursor.execute("""
        INSERT INTO simulations (composant_id, V_json, I_json)
        VALUES (?, ?, ?)
    """, (comp_id, json.dumps(V_sim.tolist()), json.dumps(I_sim.tolist())))
    conn.commit()
    conn.close()

    print(f"[SIM] Simulation terminée. I_max={I_sim.max():.4f}A, "
          f"I_min={I_sim.min():.4e}A")
    return V_sim, I_sim


def charger_simulation(composant_nom: str) -> tuple[np.ndarray, np.ndarray] | None:
    """Charge la dernière simulation depuis la base."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM composants WHERE nom = ?", (composant_nom,)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    comp_id = row[0]
    cursor.execute(
        "SELECT V_json, I_json FROM simulations WHERE composant_id = ? "
        "ORDER BY created_at DESC LIMIT 1",
        (comp_id,)
    )
    sim = cursor.fetchone()
    conn.close()

    if not sim:
        return None

    return np.array(json.loads(sim[0])), np.array(json.loads(sim[1]))


if __name__ == "__main__":
    import sys
    nom = sys.argv[1] if len(sys.argv) > 1 else "1N4007"
    V, I = simuler(nom, force=True)
    print(f"\nRésultats pour {nom}:")
    print(f"  Points: {len(V)}")
    print(f"  V range: [{V.min():.3f}, {V.max():.3f}] V")
    print(f"  I à V=0.7V: {np.interp(0.7, V, I)*1000:.4f} mA")
    print(f"  I à V=1.0V: {np.interp(1.0, V, I)*1000:.4f} mA")
