"""
Chemins de stockage persistants (local + déploiement Render/Azure).
"""

import os


def get_data_dir() -> str:
    project_root = os.path.dirname(os.path.dirname(__file__))
    configured_dir = os.getenv("APP_DATA_DIR", "").strip()

    candidates = []
    if configured_dir:
        candidates.append(configured_dir)
    candidates.extend([
        os.path.join("/tmp", "analoglab_data"),
        project_root,
    ])

    for candidate in candidates:
        try:
            os.makedirs(candidate, exist_ok=True)
            test_file = os.path.join(candidate, ".write_test")
            with open(test_file, "w", encoding="utf-8") as handle:
                handle.write("ok")
            os.remove(test_file)
            return candidate
        except OSError:
            continue

    raise PermissionError("Aucun dossier d'écriture disponible pour les bases SQLite.")


def get_contact_db_path() -> str:
    return os.path.join(get_data_dir(), "contact_messages.db")


def get_recommendations_db_path() -> str:
    return os.path.join(get_data_dir(), "recommendations.db")
