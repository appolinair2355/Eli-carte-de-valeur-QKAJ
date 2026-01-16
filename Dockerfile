FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Exposer le port 10000
EXPOSE 10000

# Commande de démarrage
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "main:app"]
