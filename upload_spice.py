"""
MODULE ADMIN — upload_spice.py
Charge les paramètres SPICE depuis un fichier JSON vers la base SQLite.
Usage: python upload_spice.py --file data/1N4007_params.json
"""

import argparse
import json
import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), "composants_db.sqlite")


def init_db(conn: sqlite3.Connection):
    """Crée les tables si elles n'existent pas."""
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS composants (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nom       TEXT UNIQUE NOT NULL,
            type      TEXT NOT NULL,
            params_json TEXT NOT NULL,
            description TEXT DEFAULT ''
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS simulations (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            composant_id INTEGER NOT NULL,
            V_json       TEXT NOT NULL,
            I_json       TEXT NOT NULL,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (composant_id) REFERENCES composants(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS modeles_ia (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            composant_id INTEGER NOT NULL,
            model_path   TEXT NOT NULL,
            V_pred_json  TEXT NOT NULL,
            I_pred_json  TEXT NOT NULL,
            mae          REAL,
            rmse         REAL,
            erreur_max   REAL,
            erreur_rel   REAL,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (composant_id) REFERENCES composants(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS modeles_hls (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            composant_id INTEGER NOT NULL,
            quant_type   TEXT NOT NULL DEFAULT 'int8',
            V_hls_json   TEXT NOT NULL,
            I_hls_json   TEXT NOT NULL,
            mae          REAL,
            rmse         REAL,
            erreur_max   REAL,
            erreur_rel   REAL,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (composant_id) REFERENCES composants(id)
        )
    """)

    cursor.execute("""
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
    """)

    conn.commit()
    print("[DB] Tables initialisées.")


def upload_composant(json_path: str) -> bool:
    """Charge un composant depuis un JSON et l'insère dans la DB."""
    if not os.path.exists(json_path):
        print(f"[ERREUR] Fichier introuvable: {json_path}")
        return False

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    nom = data.get("nom")
    type_ = data.get("type")
    params = data.get("parametres", {})
    description = data.get("description", "")

    if not nom or not type_:
        print("[ERREUR] Le JSON doit contenir 'nom' et 'type'.")
        return False

    conn = sqlite3.connect(DB_PATH)
    init_db(conn)
    cursor = conn.cursor()

    # Vérification doublon
    cursor.execute("SELECT id FROM composants WHERE nom = ?", (nom,))
    existing = cursor.fetchone()

    if existing:
        # Mise à jour
        cursor.execute("""
            UPDATE composants SET type=?, params_json=?, description=?
            WHERE nom=?
        """, (type_, json.dumps(params), description, nom))
        print(f"[UPLOAD] Composant '{nom}' mis à jour (id={existing[0]}).")
    else:
        cursor.execute("""
            INSERT INTO composants (nom, type, params_json, description)
            VALUES (?, ?, ?, ?)
        """, (nom, type_, json.dumps(params), description))
        print(f"[UPLOAD] Composant '{nom}' inséré (id={cursor.lastrowid}).")

    conn.commit()
    conn.close()
    return True


def list_composants():
    """Affiche tous les composants en base."""
    if not os.path.exists(DB_PATH):
        print("[INFO] Base de données vide — aucun composant chargé.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nom, type, description FROM composants")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("[INFO] Aucun composant en base.")
        return

    print("\n=== COMPOSANTS EN BASE ===")
    print(f"{'ID':<5} {'NOM':<12} {'TYPE':<20} {'DESCRIPTION'}")
    print("-" * 60)
    for row in rows:
        print(f"{row[0]:<5} {row[1]:<12} {row[2]:<20} {row[3]}")
    print()


def get_composant(nom: str) -> dict | None:
    """Retourne les infos d'un composant par son nom."""
    if not os.path.exists(DB_PATH):
        return None

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nom, type, params_json, description FROM composants WHERE nom = ?",
        (nom,)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "nom": row[1],
        "type": row[2],
        "parametres": json.loads(row[3]),
        "description": row[4]
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Module Admin — Upload paramètres SPICE vers SQLite"
    )
    parser.add_argument(
        "--file", type=str, help="Chemin vers le fichier JSON de paramètres"
    )
    parser.add_argument(
        "--list", action="store_true", help="Lister les composants en base"
    )
    parser.add_argument(
        "--init", action="store_true", help="Initialiser la base de données"
    )

    args = parser.parse_args()

    if args.init:
        conn = sqlite3.connect(DB_PATH)
        init_db(conn)
        conn.close()

    if args.file:
        success = upload_composant(args.file)
        sys.exit(0 if success else 1)

    if args.list:
        list_composants()

    if not args.file and not args.list and not args.init:
        # Charger tous les fichiers data/ par défaut
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        if os.path.exists(data_dir):
            for fname in os.listdir(data_dir):
                if fname.endswith("_params.json"):
                    path = os.path.join(data_dir, fname)
                    upload_composant(path)
        list_composants()
