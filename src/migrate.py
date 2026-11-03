"""Script principal : migre le CSV des données médicales vers MongoDB.

Étapes :
  1. lecture du CSV et contrôle d'intégrité AVANT migration ;
  2. nettoyage / typage des données ;
  3. insertion par lots dans MongoDB (la collection est vidée avant : script rejouable) ;
  4. création des index ;
  5. contrôle d'intégrité APRÈS migration (nombre de documents, types, champs) ;
  6. export de la collection en JSON (sauvegarde).

Usage : python src/migrate.py
"""
import json
import logging
import os
import sys
import time

from pymongo import ASCENDING, MongoClient
from pymongo.errors import ServerSelectionTimeoutError

import config
from transform import check_columns, clean, integrity_report, read_csv, to_documents

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("migration")


def connect(retries=10, delay=3):
    """Se connecte à MongoDB en réessayant (le conteneur peut mettre quelques secondes à démarrer)."""
    for attempt in range(1, retries + 1):
        try:
            client = MongoClient(config.mongo_uri(), serverSelectionTimeoutMS=3000)
            client.admin.command("ping")
            log.info("Connecté à MongoDB (%s:%s)", config.MONGO_HOST, config.MONGO_PORT)
            return client
        except ServerSelectionTimeoutError:
            log.warning("MongoDB indisponible (tentative %s/%s)...", attempt, retries)
            time.sleep(delay)
    raise RuntimeError("Impossible de se connecter à MongoDB")


def insert_documents(collection, documents, batch_size):
    """Vide la collection puis insère les documents par lots. Retourne le nombre inséré."""
    collection.delete_many({})
    inserted = 0
    for start in range(0, len(documents), batch_size):
        batch = documents[start:start + batch_size]
        inserted += len(collection.insert_many(batch).inserted_ids)
        log.info("  %s / %s documents insérés", inserted, len(documents))
    return inserted


def create_indexes(collection):
    """Crée les index utiles aux recherches les plus fréquentes."""
    collection.create_index([("patient.name", ASCENDING)], name="idx_patient_name")
    collection.create_index([("medical_condition", ASCENDING)], name="idx_medical_condition")
    collection.create_index([("admission.date", ASCENDING)], name="idx_admission_date")
    collection.create_index([("admission.hospital", ASCENDING)], name="idx_hospital")
    return collection.index_information()


def check_after_migration(collection, expected_count):
    """Vérifie la base après migration. Lève une erreur si un contrôle échoue."""
    count = collection.count_documents({})
    if count != expected_count:
        raise AssertionError(f"{count} documents en base, {expected_count} attendus")

    # Champs obligatoires : aucun document ne doit en manquer
    required = ["patient.name", "patient.age", "medical_condition", "admission.date",
                "admission.discharge_date", "billing.amount", "test_results"]
    for field in required:
        missing = collection.count_documents({field: {"$exists": False}})
        if missing:
            raise AssertionError(f"{missing} documents sans le champ {field}")

    # Typage : $type vérifie le type BSON stocké
    checks = {"patient.age": "int", "admission.room_number": "int",
              "billing.amount": "double", "admission.date": "date"}
    for field, bson_type in checks.items():
        wrong = collection.count_documents({field: {"$not": {"$type": bson_type}}})
        if wrong:
            raise AssertionError(f"{wrong} documents avec {field} d'un type autre que {bson_type}")
    log.info("Contrôles après migration OK : %s documents, champs et types conformes", count)


def export_collection(collection, path):
    """Exporte la collection en JSON (une sauvegarde lisible des données migrées)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    docs = list(collection.find({}, {"_id": 0}))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, default=str)
    log.info("Export JSON : %s documents -> %s", len(docs), path)


def main():
    log.info("1. Lecture du CSV : %s", config.CSV_PATH)
    df = read_csv(config.CSV_PATH)
    check_columns(df)
    before = integrity_report(df)
    log.info("   Avant migration : %s lignes, %s doublons, manquants : %s",
             before["lignes"], before["doublons"], before["valeurs_manquantes"] or "aucun")

    log.info("2. Nettoyage et typage")
    df = clean(df)
    log.info("   %s lignes après suppression des doublons", len(df))
    documents = to_documents(df)

    log.info("3. Insertion dans %s.%s", config.MONGO_DB, config.MONGO_COLLECTION)
    client = connect()
    collection = client[config.MONGO_DB][config.MONGO_COLLECTION]
    insert_documents(collection, documents, config.BATCH_SIZE)

    log.info("4. Création des index")
    log.info("   Index : %s", list(create_indexes(collection)))

    log.info("5. Contrôles après migration")
    check_after_migration(collection, len(documents))

    log.info("6. Export")
    export_collection(collection, config.EXPORT_PATH)

    client.close()
    log.info("Migration terminée avec succès")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # message clair et code retour non nul en cas d'échec
        log.error("Échec de la migration : %s", exc)
        sys.exit(1)
