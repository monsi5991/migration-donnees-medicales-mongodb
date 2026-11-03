# Image de la migration : Python + dépendances + scripts
FROM python:3.12-slim

WORKDIR /app

# Installation des dépendances en premier (mise en cache de cette couche)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code et des tests
COPY src/ src/
COPY tests/ tests/

# Par défaut : tests unitaires puis migration
CMD ["sh", "-c", "pytest -q tests/test_transform.py && python src/migrate.py"]
