# 📦 Instructions de Déploiement Render.com

## 🚀 Étapes de Déploiement

### 1. Créer un compte sur Render.com
- Allez sur https://render.com
- Créez un compte gratuit

### 2. Créer un nouveau Web Service
- Cliquez sur "New +" → "Web Service"
- Choisissez "Deploy from GitHub" (ou uploadez les fichiers manuellement)

### 3. Configuration du Service

#### Build & Deploy Settings:
- **Name**: joker-telegram-bot (ou votre nom préféré)
- **Environment**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 main:app`

#### Environment Variables (Variables d'environnement):
Ajoutez les variables suivantes dans les paramètres:

| Variable | Valeur | Description |
|----------|--------|-------------|
| `BOT_TOKEN` | Votre token Telegram | Token obtenu de BotFather |
| `WEBHOOK_URL` | https://VOTRE-APP.onrender.com | URL de votre app Render |
| `PORT` | 10000 | Port du serveur |
| `ADMIN_ID` | 1190237801 | Votre ID Telegram admin |
| `DEBUG` | false | Mode debug (false pour production) |

⚠️ **IMPORTANT**: Après le premier déploiement, vous aurez l'URL de votre app. 
Mettez à jour `WEBHOOK_URL` avec cette URL complète (ex: https://joker-bot-xyz.onrender.com)

### 4. Déployer
- Cliquez sur "Create Web Service"
- Attendez que le déploiement se termine (3-5 minutes)

### 5. Vérification
Une fois déployé:
1. Vérifiez que l'app est en ligne (status: "Live")
2. Testez votre bot sur Telegram avec `/start`
3. Vérifiez les logs sur Render pour voir si le webhook est bien configuré

## 📋 Fichiers Inclus dans le Package

- `main.py` - Point d'entrée de l'application Flask
- `bot.py` - Classe TelegramBot principale
- `handlers.py` - Gestionnaire de commandes et messages
- `card_predictor.py` - Moteur de prédiction intelligent
- `config.py` - Configuration (PORT configuré pour 10000)
- `requirements.txt` - Dépendances Python
- `render.yaml` - Configuration Render (optionnel, pour déploiement automatique)

## 🔧 Configuration PORT

Le port est configuré à **10000** pour Render.com.
- Development (Replit): PORT=5000
- Production (Render): PORT=10000

## ⚙️ Fonctionnalités du Bot

### Mode Intelligent (INTER)
- Collecte automatique des données de jeu
- Analyse Top 2 déclencheurs par enseigne
- Mise à jour automatique toutes les 30 minutes
- Activation via `/inter activate`

### Commandes Disponibles
- `/start` - Afficher le message de bienvenue
- `/stat` - Voir le statut du bot
- `/inter status` - Voir les règles du mode intelligent
- `/inter activate` - Activer le mode intelligent
- `/inter default` - Revenir aux règles statiques
- `/collect` - Voir les données collectées
- `/config` - Configurer les canaux

## 📞 Support

Pour toute question, contactez l'administrateur du bot.

---
**Date de création**: 25 Novembre 2025
**Version**: Production Ready pour Render.com
