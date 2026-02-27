"""
ENTRAÎNEMENT IA — trainer.py
MLP Keras pour approximer la courbe I-V d'un composant.
Architecture : Dense(64,relu) → Dense(128,relu) → Dense(64,relu) → Dense(1,linear)
Sortie : V_pred, I_pred, modèle sauvegardé en .keras
"""

import json
import os
import sqlite3
import numpy as np
import joblib

DB_PATH    = os.path.join(os.path.dirname(__file__), "composants_db.sqlite")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODELS_DIR, exist_ok=True)


def _build_model():
    """Construit le MLP Keras."""
    import tensorflow as tf
    from tensorflow import keras

    model = keras.Sequential([
        keras.layers.Input(shape=(1,)),
        keras.layers.Dense(64,  activation="relu"),
        keras.layers.Dense(128, activation="relu"),
        keras.layers.Dense(128, activation="relu"),
        keras.layers.Dense(64,  activation="relu"),
        keras.layers.Dense(32,  activation="relu"),
        keras.layers.Dense(1,   activation="linear"),
    ], name="IV_approximator")

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=1e-3),
        loss="mse",
        metrics=["mae"]
    )
    return model


def entrainer(composant_nom: str, epochs: int = 400,
              force: bool = False) -> tuple[np.ndarray, np.ndarray]:
    """
    Entraîne le MLP sur la simulation I-V du composant.

    Args:
        composant_nom: Nom du composant (ex: '1N4007')
        epochs:       Nombre max d'époques (EarlyStopping actif)
        force:        Ré-entraîner même si un modèle existe

    Returns:
        (V_pred, I_pred) sur les mêmes points que V_sim
    """
    import tensorflow as tf
    from tensorflow import keras
    from sklearn.preprocessing import MinMaxScaler

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Récupérer l'id du composant
    cursor.execute("SELECT id FROM composants WHERE nom = ?", (composant_nom,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Composant '{composant_nom}' introuvable.")
    comp_id = row[0]

    # Vérifier si modèle déjà présent
    model_path = os.path.join(MODELS_DIR, f"{composant_nom}_model.keras")
    if not force and os.path.exists(model_path):
        cursor.execute(
            "SELECT V_pred_json, I_pred_json FROM modeles_ia "
            "WHERE composant_id = ? ORDER BY created_at DESC LIMIT 1",
            (comp_id,)
        )
        existing = cursor.fetchone()
        if existing:
            V_pred = np.array(json.loads(existing[0]))
            I_pred = np.array(json.loads(existing[1]))
            conn.close()
            print(f"[IA] Modèle '{composant_nom}' chargé depuis la base.")
            return V_pred, I_pred

    # Charger la simulation
    cursor.execute(
        "SELECT V_json, I_json FROM simulations WHERE composant_id = ? "
        "ORDER BY created_at DESC LIMIT 1",
        (comp_id,)
    )
    sim = cursor.fetchone()
    conn.close()

    if not sim:
        raise ValueError(f"Aucune simulation pour '{composant_nom}'. "
                         f"Lancez simulateur.py d'abord.")

    V_sim = np.array(json.loads(sim[0]))
    I_sim = np.array(json.loads(sim[1]))

    print(f"[IA] Entraînement sur {len(V_sim)} points pour '{composant_nom}'...")

    # Normalisation
    scaler_V = MinMaxScaler(feature_range=(0, 1))
    scaler_I = MinMaxScaler(feature_range=(0, 1))

    V_scaled = scaler_V.fit_transform(V_sim.reshape(-1, 1))
    I_scaled = scaler_I.fit_transform(I_sim.reshape(-1, 1))

    # Sauvegarde des scalers
    scaler_path_V = os.path.join(MODELS_DIR, f"{composant_nom}_scaler_V.pkl")
    scaler_path_I = os.path.join(MODELS_DIR, f"{composant_nom}_scaler_I.pkl")
    joblib.dump(scaler_V, scaler_path_V)
    joblib.dump(scaler_I, scaler_path_I)

    # Construction et entraînement
    model = _build_model()

    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=30,
            restore_best_weights=True, verbose=0
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5,
            patience=15, min_lr=1e-6, verbose=0
        ),
    ]

    history = model.fit(
        V_scaled, I_scaled,
        epochs=epochs,
        batch_size=64,
        validation_split=0.1,
        callbacks=callbacks,
        verbose=1
    )

    # Prédiction sur tous les points
    I_pred_scaled = model.predict(V_scaled, verbose=0)
    I_pred = scaler_I.inverse_transform(I_pred_scaled).flatten()
    V_pred = V_sim.copy()

    # Sauvegarde modèle
    model.save(model_path)
    print(f"[IA] Modèle sauvegardé: {model_path}")

    # Métriques
    from metriques import toutes_metriques
    m = toutes_metriques(I_sim, I_pred)
    print(f"[IA] MAE={m['MAE']:.4e} | RMSE={m['RMSE']:.4e} | "
          f"E_rel={m['E_rel_%']:.2f}% | R²={m['R2']:.6f}")

    # Sauvegarde en base
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM modeles_ia WHERE composant_id = ?", (comp_id,)
    )
    cursor.execute("""
        INSERT INTO modeles_ia
            (composant_id, model_path, V_pred_json, I_pred_json,
             mae, rmse, erreur_max, erreur_rel)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        comp_id, model_path,
        json.dumps(V_pred.tolist()), json.dumps(I_pred.tolist()),
        m["MAE"], m["RMSE"], m["E_max"], m["E_rel_%"]
    ))
    conn.commit()
    conn.close()

    return V_pred, I_pred


def charger_prediction_ia(composant_nom: str) -> tuple[np.ndarray, np.ndarray] | None:
    """Charge la dernière prédiction IA depuis la base."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM composants WHERE nom = ?", (composant_nom,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    cursor.execute(
        "SELECT V_pred_json, I_pred_json FROM modeles_ia "
        "WHERE composant_id = ? ORDER BY created_at DESC LIMIT 1",
        (row[0],)
    )
    pred = cursor.fetchone()
    conn.close()
    if not pred:
        return None
    return np.array(json.loads(pred[0])), np.array(json.loads(pred[1]))


if __name__ == "__main__":
    import sys
    nom = sys.argv[1] if len(sys.argv) > 1 else "1N4007"
    V, I = entrainer(nom, force=True)
    print(f"\nPrédiction IA pour {nom}: {len(V)} points")
    print(f"  I à V=0.7V (prédit): {np.interp(0.7, V, I)*1000:.4f} mA")
