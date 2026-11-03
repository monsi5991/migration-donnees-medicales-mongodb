"""Tests unitaires du nettoyage et de la transformation (sans MongoDB)."""
import datetime
import io

import pandas as pd
import pytest

from transform import EXPECTED_COLUMNS, check_columns, clean, integrity_report, row_to_document

CSV = """Name,Age,Gender,Blood Type,Medical Condition,Date of Admission,Doctor,Hospital,Insurance Provider,Billing Amount,Room Number,Admission Type,Discharge Date,Medication,Test Results
Bobby JacksOn,30,Male,B-,Cancer,2024-01-31,Matthew Smith,Sons and Miller,Blue Cross,18856.281305978155,328,Urgent,2024-02-02,Paracetamol,Normal
LesLie TErRy,62,Male,A+,Obesity,2019-08-20,Samantha Davies,Kim Inc,Medicare,33643.327286577885,265,Emergency,2019-08-26,Ibuprofen,Inconclusive
LesLie TErRy,62,Male,A+,Obesity,2019-08-20,Samantha Davies,Kim Inc,Medicare,33643.327286577885,265,Emergency,2019-08-26,Ibuprofen,Inconclusive
"""


@pytest.fixture
def raw_df():
    return pd.read_csv(io.StringIO(CSV), dtype=str)


def test_colonnes_presentes(raw_df):
    check_columns(raw_df)  # ne lève pas d'erreur
    assert set(raw_df.columns) == set(EXPECTED_COLUMNS)


def test_colonne_manquante(raw_df):
    with pytest.raises(ValueError):
        check_columns(raw_df.drop(columns=["Age"]))


def test_rapport_integrite_detecte_doublons(raw_df):
    report = integrity_report(raw_df)
    assert report["lignes"] == 3
    assert report["doublons"] == 1
    assert report["valeurs_manquantes"] == {}


def test_nettoyage_supprime_doublons_et_type(raw_df):
    df = clean(raw_df)
    assert len(df) == 2
    assert df["Age"].dtype == "int64"
    assert df["Room Number"].dtype == "int64"
    assert df["Billing Amount"].iloc[0] == 18856.28
    assert pd.api.types.is_datetime64_any_dtype(df["Date of Admission"])


def test_noms_normalises(raw_df):
    df = clean(raw_df)
    assert df["Name"].tolist() == ["Bobby Jackson", "Leslie Terry"]


def test_document_mongodb(raw_df):
    doc = row_to_document(clean(raw_df).iloc[0])
    assert doc["patient"] == {"name": "Bobby Jackson", "age": 30, "gender": "Male", "blood_type": "B-"}
    assert doc["admission"]["date"] == datetime.datetime(2024, 1, 31)
    assert isinstance(doc["billing"]["amount"], float)
    assert doc["admission"]["room_number"] == 328
