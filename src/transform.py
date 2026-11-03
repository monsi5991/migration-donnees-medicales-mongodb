"""Lecture, contrôle et transformation du CSV (aucune dépendance à MongoDB).

Ces fonctions sont testées par tests/test_transform.py.
"""
import pandas as pd

# Colonnes attendues dans le CSV et type cible de chacune
EXPECTED_COLUMNS = {
    "Name": "string",
    "Age": "int",
    "Gender": "string",
    "Blood Type": "string",
    "Medical Condition": "string",
    "Date of Admission": "date",
    "Doctor": "string",
    "Hospital": "string",
    "Insurance Provider": "string",
    "Billing Amount": "float",
    "Room Number": "int",
    "Admission Type": "string",
    "Discharge Date": "date",
    "Medication": "string",
    "Test Results": "string",
}


def read_csv(path):
    """Lit le CSV en texte brut (les types sont appliqués ensuite, de façon contrôlée)."""
    return pd.read_csv(path, dtype=str)


def check_columns(df):
    """Vérifie que toutes les colonnes attendues sont présentes. Lève une erreur sinon."""
    missing = set(EXPECTED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes dans le CSV : {sorted(missing)}")


def integrity_report(df):
    """Retourne un petit rapport d'intégrité : lignes, colonnes, manquants, doublons, types."""
    return {
        "lignes": len(df),
        "colonnes": list(df.columns),
        "valeurs_manquantes": {c: int(n) for c, n in df.isna().sum().items() if n > 0},
        "doublons": int(df.duplicated().sum()),
        "types": {c: str(t) for c, t in df.dtypes.items()},
    }


def clean(df):
    """Nettoie et type les données.

    - supprime les espaces en trop ;
    - met les noms de patients au format « Prénom Nom » (le CSV mélange majuscules/minuscules) ;
    - convertit Age et Room Number en entiers, Billing Amount en décimal arrondi à 2 chiffres,
      les dates en datetime ;
    - supprime les doublons exacts (même séjour enregistré deux fois).
    """
    df = df.copy()
    for col in df.columns:
        df[col] = df[col].str.strip()
    df["Name"] = df["Name"].str.title()
    df["Hospital"] = df["Hospital"].str.rstrip(",").str.strip()

    df["Age"] = pd.to_numeric(df["Age"], errors="raise").astype("int64")
    df["Room Number"] = pd.to_numeric(df["Room Number"], errors="raise").astype("int64")
    df["Billing Amount"] = pd.to_numeric(df["Billing Amount"], errors="raise").round(2)
    df["Date of Admission"] = pd.to_datetime(df["Date of Admission"], format="%Y-%m-%d")
    df["Discharge Date"] = pd.to_datetime(df["Discharge Date"], format="%Y-%m-%d")

    df = df.drop_duplicates().reset_index(drop=True)
    return df


def row_to_document(row):
    """Transforme une ligne du CSV en document MongoDB (schéma décrit dans le README)."""
    return {
        "patient": {
            "name": row["Name"],
            "age": int(row["Age"]),
            "gender": row["Gender"],
            "blood_type": row["Blood Type"],
        },
        "medical_condition": row["Medical Condition"],
        "admission": {
            "date": row["Date of Admission"].to_pydatetime(),
            "type": row["Admission Type"],
            "discharge_date": row["Discharge Date"].to_pydatetime(),
            "room_number": int(row["Room Number"]),
            "doctor": row["Doctor"],
            "hospital": row["Hospital"],
        },
        "billing": {
            "amount": float(row["Billing Amount"]),
            "insurance_provider": row["Insurance Provider"],
        },
        "medication": row["Medication"],
        "test_results": row["Test Results"],
    }


def to_documents(df):
    """Transforme tout le DataFrame en liste de documents."""
    return [row_to_document(row) for _, row in df.iterrows()]
