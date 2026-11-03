"""Tests d'intégration : vérifient la base APRÈS migration.

Ils sont lancés par le service « tests » du docker-compose, avec l'utilisateur
en lecture seule (analyst_user). Ils sont ignorés si MongoDB n'est pas joignable.
"""
import os

import pytest
from pymongo import MongoClient
from pymongo.errors import OperationFailure, ServerSelectionTimeoutError

import config
from transform import clean, read_csv


def _uri(user, password):
    return (f"mongodb://{user}:{password}@{config.MONGO_HOST}:{config.MONGO_PORT}/"
            f"{config.MONGO_DB}?authSource={config.MONGO_DB}")


@pytest.fixture(scope="module")
def collection():
    user = os.getenv("MONGO_ANALYST_USER", "")
    client = MongoClient(_uri(user, os.getenv("MONGO_ANALYST_PASSWORD", "")),
                         serverSelectionTimeoutMS=3000)
    try:
        client.admin.command("ping")
    except ServerSelectionTimeoutError:
        pytest.skip("MongoDB non joignable")
    yield client[config.MONGO_DB][config.MONGO_COLLECTION]
    client.close()


def test_nombre_de_documents(collection):
    expected = len(clean(read_csv(config.CSV_PATH)))
    assert collection.count_documents({}) == expected


def test_pas_de_doublons(collection):
    pipeline = [{"$group": {"_id": {"p": "$patient", "a": "$admission", "b": "$billing",
                                    "m": "$medication", "t": "$test_results",
                                    "c": "$medical_condition"}, "n": {"$sum": 1}}},
                {"$match": {"n": {"$gt": 1}}}, {"$count": "doublons"}]
    assert list(collection.aggregate(pipeline)) == []


def test_types(collection):
    assert collection.count_documents({"patient.age": {"$not": {"$type": "int"}}}) == 0
    assert collection.count_documents({"billing.amount": {"$not": {"$type": "double"}}}) == 0
    assert collection.count_documents({"admission.date": {"$not": {"$type": "date"}}}) == 0


def test_index_crees(collection):
    names = set(collection.index_information())
    assert {"idx_patient_name", "idx_medical_condition", "idx_admission_date", "idx_hospital"} <= names


def test_lecture_seule(collection):
    """Le rôle analyste ne doit PAS pouvoir écrire."""
    with pytest.raises(OperationFailure):
        collection.insert_one({"test": "interdit"})
