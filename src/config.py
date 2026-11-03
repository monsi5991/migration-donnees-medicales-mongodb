"""Configuration de la migration, lue depuis les variables d'environnement.

Les valeurs sont fournies par docker-compose (fichier .env). Aucune valeur
sensible (mot de passe) n'est écrite en dur dans le code.
"""
import os

# Connexion MongoDB
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", "27017"))
MONGO_DB = os.getenv("MONGO_DB", "healthcare")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "admissions")
MONGO_USER = os.getenv("MONGO_MIGRATION_USER", "")
MONGO_PASSWORD = os.getenv("MONGO_MIGRATION_PASSWORD", "")

# Fichiers
CSV_PATH = os.getenv("CSV_PATH", "data/healthcare_dataset.csv")
EXPORT_PATH = os.getenv("EXPORT_PATH", "data/export/admissions_export.json")

# Taille des lots envoyés à MongoDB (insert_many)
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "5000"))


def mongo_uri():
    """Construit l'URI de connexion (avec authentification si un utilisateur est défini)."""
    if MONGO_USER:
        return (f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/"
                f"{MONGO_DB}?authSource={MONGO_DB}")
    return f"mongodb://{MONGO_HOST}:{MONGO_PORT}/"
