"""Démonstration des opérations CRUD avec pymongo sur la collection migrée.

Usage : python src/crud.py
"""
from datetime import datetime

from pymongo import MongoClient

import config


def get_collection():
    """Retourne la collection des admissions."""
    client = MongoClient(config.mongo_uri())
    return client[config.MONGO_DB][config.MONGO_COLLECTION]


def create(collection):
    """CREATE : ajoute un séjour de test."""
    doc = {
        "patient": {"name": "Test Patient", "age": 40, "gender": "Female", "blood_type": "O+"},
        "medical_condition": "Asthma",
        "admission": {"date": datetime(2024, 1, 10), "type": "Urgent",
                      "discharge_date": datetime(2024, 1, 15), "room_number": 101,
                      "doctor": "Test Doctor", "hospital": "Test Hospital"},
        "billing": {"amount": 1500.0, "insurance_provider": "Medicare"},
        "medication": "Ibuprofen",
        "test_results": "Normal",
    }
    return collection.insert_one(doc).inserted_id


def read(collection):
    """READ : quelques recherches."""
    print("Patient de test :", collection.find_one({"patient.name": "Test Patient"}, {"_id": 0}))
    print("Séjours pour diabète :", collection.count_documents({"medical_condition": "Diabetes"}))
    pipeline = [{"$group": {"_id": "$medical_condition", "facture_moyenne": {"$avg": "$billing.amount"}}},
                {"$sort": {"facture_moyenne": -1}}]
    for row in collection.aggregate(pipeline):
        print(f"  {row['_id']:<15} {row['facture_moyenne']:>10.2f}")


def update(collection):
    """UPDATE : modifie le résultat de test du patient de test."""
    result = collection.update_one({"patient.name": "Test Patient"},
                                   {"$set": {"test_results": "Abnormal"}})
    return result.modified_count


def delete(collection):
    """DELETE : supprime le patient de test."""
    return collection.delete_many({"patient.name": "Test Patient"}).deleted_count


if __name__ == "__main__":
    col = get_collection()
    print("CREATE  ->", create(col))
    read(col)
    print("UPDATE  -> documents modifiés :", update(col))
    print("DELETE  -> documents supprimés :", delete(col))
