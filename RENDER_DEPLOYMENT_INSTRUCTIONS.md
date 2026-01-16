# 🚀 Instructions de Déploiement sur Render.com

## 1️⃣ Préparation
- Extraire le fichier ZIP dans un dossier
- Vérifier que tous les fichiers sont présents :
  - `bot.py`, `card_predictor.py`, `config.py`, `handlers.py`, `main.py`
  - `requirements.txt`, `render.yaml`

## 2️⃣ Créer un Service sur Render.com
1. Aller sur https://render.com
2. Cliquer sur "New +" > "Web Service"
3. Connecter votre repo GitHub (ou charger les fichiers)
4. Configuration :
   - **Name** : `telegram-bot-predictor`
   - **Runtime** : `Python 3.11`
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `gunicorn main:app --bind 0.0.0.0:10000`

## 3️⃣ Variables d'Environnement
Ajouter dans les "Environment Variables" :
- `BOT_TOKEN` : Votre token Telegram
- `WEBHOOK_URL` : L'URL fournie par Render (ex: `https://votre-app.onrender.com`)

## 4️⃣ Déployer
Cliquer sur "Create Web Service" et attendre le déploiement.

## 5️⃣ Vérifier le Webhook
Après le déploiement, le bot configurera automatiquement le webhook avec Telegram.
Vous verrez dans les logs : "✅ Webhook configuré avec succès."

---

**Port** : 10000 (Render) - Auto-détecté dans le code
**Timezone** : Africa/Porto-Novo (Bénin)
