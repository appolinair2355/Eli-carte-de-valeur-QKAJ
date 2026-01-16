# 🤖 GUIDE COMPLET BOT ENSEIGNE - DE A À Z

## 📋 TABLE DES MATIÈRES
1. [Configuration Initiale](#1-configuration-initiale)
2. [Déploiement](#2-déploiement)
3. [Utilisation Pas à Pas](#3-utilisation-pas-à-pas)
4. [Exemples Pratiques](#4-exemples-pratiques)
5. [Dépannage](#5-dépannage)

---

## 1️⃣ CONFIGURATION INITIALE

### Étape 1.1 : Obtenir le Token du Bot
```
1. Ouvrir Telegram
2. Chercher "@BotFather" 
3. Envoyer "/start"
4. Envoyer "/newbot"
5. Donner un nom : "Mon Bot Enseigne"
6. Donner un username unique : "monbot_enseigne_12345"
7. 🎉 Copier le TOKEN fourni (ex: 123456789:ABCdefGHIjklmnoPQRstuvWXYZabcdefgh)
```

### Étape 1.2 : Créer les Canaux
```
CANAL 1 - SOURCE (entrée)
├─ Nom: "Jeux Source"
├─ Type: Privé (confidentiel)
└─ But: Reçoit les jeux de l'API

CANAL 2 - PRÉDICTION (sortie)
├─ Nom: "Prédictions Bot"
├─ Type: Privé
└─ But: Le bot y envoie ses prédictions
```

### Étape 1.3 : Configurer les Variables d'Environnement (Replit)

**Sur Replit:**
```
1. Cliquer sur "Secrets" (clé 🔑) en bas à gauche
2. Ajouter :
   - BOT_TOKEN = 123456789:ABCdefGHIjklmnoPQRstuvWXYZabcdefgh
   - WEBHOOK_URL = https://MonProjet.username.repl.co (auto-généré)
```

**Sur Render.com:**
```
1. Dashboard → Environment
2. Ajouter:
   - BOT_TOKEN = votre_token
   - WEBHOOK_URL = https://monapp.onrender.com
```

---

## 2️⃣ DÉPLOIEMENT

### Option A : Sur Replit (RECOMMANDÉ)
```bash
# 1. Charger les fichiers
cd /home/runner/workspace
unzip yyuu.zip

# 2. Démarrer le bot
python main.py

# Le bot est actif sur: https://MonProjet.username.repl.co
```

### Option B : Sur Render.com
```bash
# 1. Créer nouveau service
# 2. Connecter GitHub (ou télécharger manuellement)
# 3. Ajouter les fichiers de yyuu.zip
# 4. Configuration Render:
#    - Build: pip install -r requirements.txt
#    - Start: gunicorn -w 4 -b 0.0.0.0:10000 main:app
# 5. Ajouter WEBHOOK_URL dans Environment
# 6. Déployer ✅
```

---

## 3️⃣ UTILISATION PAS À PAS

### Phase 1 : Configuration du Bot dans Telegram

**Étape 1: Ajouter le bot à vos canaux**
```
1. Aller dans "Jeux Source" (canal)
2. Ajouter le bot (@monbot_enseigne_12345)
3. Envoyer la commande: /config
4. Cliquer sur "Source" (ce canal reçoit les jeux)

5. Aller dans "Prédictions Bot" (canal)
6. Ajouter le bot
7. Envoyer: /config
8. Cliquer sur "Prediction" (ce canal reçoit les prédictions)
```

**Étape 2: Vérifier le statut**
```
Anywhere (chat privé avec le bot):
/stat

Réponse attendue:
📊 STATUS
Source (Input): -1002682552255
Prediction (Output): -1003329818758
Mode: Statique
```

---

## 4️⃣ EXEMPLES PRATIQUES

### EXEMPLE 1 : Mode Statique (Défaut)

**Scénario:** Les jeux arrivent du canal SOURCE

```
DANS LE CANAL SOURCE :
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#N123. (6♦️ 10♠️) #R
Cote: 1.5 @ 20:35

⬇️ LE BOT REÇOIT :
  - Jeu #123
  - Première carte: 6♦️
  - Vérifie règle statique: 6♦️ → ♣️

⬇️ LE BOT ENVOIE DANS CANAL PRÉDICTION :
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔵125🔵:♣️ statut :⏳
(Prédit ♣️ pour jeu #125 = #123+2)

⬇️ APRÈS VÉRIFICATION (30 secondes après) :
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#N125. (5♣️ 7♦️) ✅ (résultat finalisé)

⬇️ LE BOT ÉDITE SA PRÉDICTION :
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔵125🔵:♣️ statut :✅0️⃣ (GAGNÉ!)
```

### EXEMPLE 2 : Activation du Mode INTER (Intelligent)

**Étape 1: Collecter les données**
```
Jour 1-3: Laisser le bot prédire normalement
         (Collecte ~10-15 jeux)

Chat privé avec le bot:
/collect

Réponse:
🧠 ETAT DU MODE INTELLIGENT
Actif : ❌ NON
Données collectées : 12

📊 TOUS LES DÉCLENCHEURS COLLECTÉS:
Pour enseigne ♠️:
  • 6♦️ (3x)
  • 10♣️ (2x)
  • 5♠️ (1x)

Pour enseigne ♦️:
  • 8♠️ (4x)
  • A♣️ (2x)

[Bouton: ✅ Activer INTER]
```

**Étape 2: Activer INTER**
```
Chat privé avec le bot:
/inter activate

OU cliquer sur "✅ Activer INTER" depuis /collect

Réponse:
✅ MODE INTER ACTIVÉ
L'analyse Top 2 par enseigne est en cours...
```

**Étape 3: Vérifier les règles créées**
```
Chat privé avec le bot:
/inter status

Réponse:
🧠 MODE INTER - ✅ ACTIF

📊 8 règles créées (12 jeux analysés):

Pour prédire ♠️:
  • 6♦️ (3x)
  • 10♣️ (2x)

Pour prédire ♦️:
  • 8♠️ (4x)
  • A♣️ (2x)

Pour prédire ♣️:
  • 5♦️ (2x)

Pour prédire ♥️:
  • 7♠️ (3x)

[Bouton: 🔄 Relancer Analyse] [Bouton: ❌ Désactiver]
```

### EXEMPLE 3 : Cycle de Prédiction Complet (MODE INTER)

```
TIME: 08h30 (Session 05h-17h: ✅ ACTIF)

CANAL SOURCE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#N498. (8♠️ 3♣️) #R
Cote: 2.0 @ 08:30

⬇️ BOT ANALYZE:
  - Jeu #498
  - Première carte: 8♠️
  - Mode INTER: ✅ ACTIF
  - Pour ♦️: TOP2 = [8♠️ (4x), A♣️ (2x)]
  - ✅ 8♠️ est dans TOP2 pour ♦️
  - Prédiction: ♦️
  - Quarantaine: ❌ aucune
  - Émet prédiction

CANAL PRÉDICTION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔵500🔵:♦️ statut :⏳
(INTER TOP2, en attente)

⬇️ 30 SECONDES APRÈS...

CANAL SOURCE (ÉDITÉ):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#N500. (4♦️ 9♠️) ✅
Cote: 1.8 @ 08:30

⬇️ BOT VÉRIFIE:
  - Jeu #500 finalisé
  - Première carte: 4♦️
  - Costume ♦️ était prédit
  - Vérification: ✅ TROUVÉ DANS GROUPE!
  - Offset: 0 (jeu exact)

CANAL PRÉDICTION (ÉDITÉ):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔵500🔵:♦️ statut :✅0️⃣
(✅ VICTOIRE! Décalage 0)

📊 Bot stats:
✅ Wins: 45
❌ Losses: 12
📈 Win rate: 78.95%
```

### EXEMPLE 4 : Cas d'Échec + Quarantaine

```
PRÉDICTIONS ÉCHOUÉES CONSÉCUTIVES:

Prédiction #1 (8♠️ → ♦️): ❌ ÉCHEC
  Quarantaine activée: 8♠️_♦️

Prédiction #2 (8♠️ → ♦️ à nouveau): 🔒 BLOQUÉE
  Raison: En quarantaine pendant 30 min

AUTRE DÉCLENCHEUR UTILISÉ:
  Si A♣️ (2ème du TOP2) → ♦️
  Peut toujours prédire A♣️ → ♦️

APRÈS 30 MINUTES:
  Quarantaine levée ✅
  8♠️ peut être utilisé à nouveau
```

---

## 5️⃣ COMMANDES COMPLÈTES

### Commandes Utilisateur

| Commande | Usage | Résultat |
|----------|-------|----------|
| `/start` | Chat privé | Affiche l'aide complète |
| `/stat` | N'importe où | Statut du bot (canaux, mode) |
| `/inter status` | Chat privé | Voir les règles TOP2 par enseigne |
| `/inter activate` | Chat privé | Activer le mode intelligent |
| `/inter default` | Chat privé | Désactiver INTER → Statique |
| `/collect` | Chat privé | Voir toutes les données collectées |
| `/reset` | Chat privé | Réinitialiser prédictions automatiques |
| `/config` | N'importe où | Configurer ce canal (Source/Prédiction) |
| `/deploy` | Chat privé | Télécharger yyuu.zip |

### Flux Complet d'Utilisation

```
SEMAINE 1: APPRENTISSAGE
├─ /start (lire l'aide)
├─ /config dans Source → Cliquer "Source"
├─ /config dans Prédiction → Cliquer "Prediction"
├─ /stat (vérifier configuration)
├─ Laisser tourner 3-5 jours
└─ /collect (voir données collectées)

SEMAINE 2: ACTIVATION INTER
├─ /inter status (regarder données)
├─ /inter activate (activer mode intelligent)
├─ /inter status (voir règles créées)
└─ Laisser tourner 1-2 semaines

SEMAINE 3+: OPTIMISATION
├─ /inter status (vérifier TOP2)
├─ /collect (analyser les déclencheurs)
├─ Éditer INTER si mauvais résultats
└─ /reset (nettoyer si besoin)
```

---

## 🤖 PRÉDICTIONS AUTOMATIQUES (MODE INTER)

Le bot peut envoyer automatiquement des prédictions PENDANT les sessions de prédiction:

```
PENDANT SESSION (ex: 10h00 Bénin):
├─ BOT A SMART RULES (TOP2 par enseigne)
├─ BOT ENVOIE TOUS LES 20 MINUTES
├─ PRÉDICTION 1: 🥇 TOP1 pour ♠️
├─ PRÉDICTION 2: 🥇 TOP2 pour ♠️
├─ PRÉDICTION 3: 🥇 TOP1 pour ♥️
├─ PRÉDICTION 4: 🥇 TOP2 pour ♥️
└─ ... ET AINSI POUR TOUS LES COSTUMES

RÉSULTAT:
✅ Jusqu'à 8 prédictions auto (2 TOP × 4 costumes)
✅ Toutes les 20 minutes pendant la session
✅ Utilise les 2 MEILLEURS déclencheurs par costume
```

## 🔧 EXEMPLES DE FICHIERS DE CONFIGURATION

### Fichier: `smart_rules.json` (Créé automatiquement)
```json
[
  {
    "trigger": "6♦️",
    "predict": "♣️",
    "count": 3,
    "result_suit": "♣️"
  },
  {
    "trigger": "8♠️",
    "predict": "♦️",
    "count": 4,
    "result_suit": "♦️"
  },
  {
    "trigger": "10♣️",
    "predict": "♠️",
    "count": 2,
    "result_suit": "♠️"
  }
]
```

### Fichier: `inter_data.json` (Données collectées)
```json
[
  {
    "numero_resultat": 123,
    "declencheur": "6♦️",
    "numero_declencheur": 121,
    "result_suit": "♣️",
    "date": "2025-12-19T08:30:00"
  },
  {
    "numero_resultat": 125,
    "declencheur": "8♠️",
    "numero_declencheur": 123,
    "result_suit": "♦️",
    "date": "2025-12-19T08:35:00"
  }
]
```

---

## 📊 RÉSUMÉ SESSIONS HORAIRES

Le bot fonctionne UNIQUEMENT pendant:
```
SESSION 1: 01h00 - 06h00 (Bénin) ✅
SESSION 2: 09h00 - 12h00 (Bénin) ✅
SESSION 3: 15h00 - 18h00 (Bénin) ✅
SESSION 4: 21h00 - 00h00 (Bénin) ✅

HORS SESSIONS: 00h00 - 01h00, 06h00 - 09h00, 12h00 - 15h00, 18h00 - 21h00 ❌ PAS DE PRÉDICTIONS
```

---

## 🎯 CHECKLIST D'UTILISATION

- [ ] Créer le bot avec @BotFather
- [ ] Obtenir le TOKEN
- [ ] Configurer BOT_TOKEN et WEBHOOK_URL
- [ ] Créer les 2 canaux (Source + Prédiction)
- [ ] Ajouter le bot aux canaux
- [ ] Envoyer /config dans chaque canal
- [ ] Vérifier /stat
- [ ] Laisser collecter des données (3-5 jours)
- [ ] Envoyer /collect pour voir les données
- [ ] Envoyer /inter activate
- [ ] Vérifier /inter status
- [ ] Laisser le bot prédire
- [ ] Analyser les résultats
- [ ] Réajuster si besoin

---

## ❓ DÉPANNAGE RAPIDE

| Problème | Solution |
|----------|----------|
| Bot ne prédisait pas | Vérifier sessions horaires (2-5h, 5-17h, 17-22h) |
| Prédictions doubles | Vérifier si jeu déjà en attente (pending) |
| Quarantaine bloque tout | Attendre 30 min ou faire /inter default |
| Règles INTER invalides | Faire /collect → vérifier déclencheurs → /inter activate |
| Mode INTER ne s'active pas | Besoin de minimum 3 jeux collectés |
| Bot ne répond pas | Vérifier BOT_TOKEN et WEBHOOK_URL |

---

**🎉 VOUS ÊTES PRÊT À UTILISER LE BOT!**

Pour plus d'aide: `/start` directement dans le bot Telegram.

---

## 🚀 DÉPLOIEMENT RENDER.COM (PORT 10000)

### Configuration Rapide Render

**Étape 1:** Dashboard Render → Web Service
**Étape 2:** Variables d'environnement:
```
BOT_TOKEN = votre_token
WEBHOOK_URL = https://votre-app.onrender.com
```

**Étape 3:** Render détecte automatiquement `render.yaml`:
```
- Build: pip install -r requirements.txt
- Start: gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 main:app
- Port: 10000 (automatique)
```

**Vérification:** GET `https://votre-app.onrender.com/health`

### ✅ Le zip `yyuu.zip` contient TOUS les fichiers pour Render.com!

