# Verwenden Sie ein offizielles Python-Runtime-Image als Basis
FROM python:3.8-slim-buster

# Setzen Sie das Arbeitsverzeichnis im Container
WORKDIR /app

# Kopieren Sie die aktuellen Verzeichnisinhalte in das Arbeitsverzeichnis im Container
COPY ../scripts/matrix-b0t.py /app/matrix-b0t.py

# Installieren Sie alle benötigten Pakete
RUN pip install --no-cache-dir requests matrix_client configparser matrix-nio

# Führen Sie das Skript aus, wenn der Container gestartet wird
CMD ["python", "./matrix-b0t.py"]