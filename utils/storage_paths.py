"""
Chemins de stockage persistants (local + déploiement Render/Azure).
"""

import os


def get_data_dir() -> str:
    project_root = os.path.dirname(os.path.dirname(__file__))
    data_dir = os.getenv("APP_DATA_DIR", project_root)
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def get_contact_db_path() -> str:
    return os.path.join(get_data_dir(), "contact_messages.db")


def get_recommendations_db_path() -> str:
    return os.path.join(get_data_dir(), "recommendations.db")
