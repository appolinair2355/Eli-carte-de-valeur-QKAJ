# main.py

"""
Main entry point for the Telegram bot deployment on render.com
"""
import os
import json
import logging
from flask import Flask, request, jsonify
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

# Importe la configuration et le bot
from config import Config
from bot import TelegramBot 

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize bot and config
try:
    config = Config()
except ValueError as e:
    logger.error(f"❌ Erreur d'initialisation de la configuration: {e}")
    exit(1) 

# 'bot' est l'instance de la classe TelegramBot
bot = TelegramBot(config.BOT_TOKEN) 

# Initialize Flask app
app = Flask(__name__)


# --- LOGIQUE WEBHOOK ---

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook from Telegram"""
    try:
        update = request.get_json(silent=True)
        if not update:
            return jsonify({'status': 'ok'}), 200

        # Délégation du traitement complet à bot.handle_update
        if update:
            bot.handle_update(update)
        
        return 'OK', 200
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return 'Error', 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for render.com"""
    return {'status': 'healthy', 'service': 'telegram-bot'}, 200

@app.route('/', methods=['GET'])
def home():
    """Root endpoint"""
    return {'message': 'Telegram Bot is running', 'status': 'active'}, 200

# --- CONFIGURATION WEBHOOK ---

def setup_webhook():
    """Set up webhook on startup"""
    try:
        full_webhook_url = config.get_webhook_url()
        
        # Log de diagnostic
        logger.info(f"🔍 Environnement détecté:")
        logger.info(f"  - PORT: {config.PORT}")
        logger.info(f"  - WEBHOOK_URL (env): {os.getenv('WEBHOOK_URL', 'NON DÉFINI')}")
        logger.info(f"  - RENDER: {os.getenv('RENDER', 'false')}")
        logger.info(f"  - REPLIT_DOMAINS: {os.getenv('REPLIT_DOMAINS', 'NON DÉFINI')}")
        
        if full_webhook_url and not config.WEBHOOK_URL.startswith('https://.repl.co'):
            logger.info(f"🔗 Tentative de configuration webhook: {full_webhook_url}")

            success = bot.set_webhook(full_webhook_url)
            
            if success:
                logger.info(f"✅ Webhook configuré avec succès.")
                logger.info(f"🎯 Bot prêt pour prédictions automatiques et vérifications via webhook")
            else:
                logger.error("❌ Échec configuration webhook.")
                logger.error("💡 Vérifiez que WEBHOOK_URL est correctement défini dans les variables d'environnement Render")
        else:
            logger.warning("⚠️ WEBHOOK_URL non configurée ou non valide. Le webhook ne sera PAS configuré.")
            if os.getenv('RENDER'):
                logger.error("🚨 SUR RENDER.COM : Vous DEVEZ définir WEBHOOK_URL dans les variables d'environnement !")
    except Exception as e:
        logger.error(f"❌ Erreur critique lors du setup du webhook: {e}")

# --- RÉINITIALISATION PROGRAMMÉE DES PRÉDICTIONS ---

def reset_every_2_hours():
    """
    Réinitialisation toutes les 2 heures:
    - Efface les collectes, les règles INTER et les prédictions automatiques
    - Ne touche pas aux bilans et aux canaux configurés
    """
    try:
        if bot.handlers.card_predictor:
            predictor = bot.handlers.card_predictor
            predictor.reset_all_data(full=True)
            logger.info("🔄 RESET COMPLET EFFECTUÉ (Collectes, Règles, Prédictions effacées toutes les 2h)")
    except Exception as e:
        logger.error(f"❌ Erreur lors du reset 2h: {e}")

def reset_non_inter_predictions():
    """
    Reset complet à 00h59 heure du Bénin:
    - EFFACE TOUT (prédictions, INTER, smart rules, collecte, etc.)
    - GARDE SEULEMENT les IDs canaux
    - RÉACTIVE le mode INTER automatiquement
    - RÉINITIALISE la collecte à zéro
    """
    try:
        # Fichiers à EFFACER COMPLÈTEMENT
        files_to_clear = [
            'predictions.json',
            'inter_data.json',
            'smart_rules.json',
            'collected_games.json',
            'sequential_history.json',
            'pending_edits.json',
            'quarantined_rules.json',
            'last_prediction_time.json',
            'last_predicted_game_number.json',
            'consecutive_fails.json',
            'single_trigger_until.json',
            'inter_mode_status.json',
            'last_analysis_time.json',
            'last_inter_update.json',
            'last_report_sent.json',
            'wait_until_next_update.json'
        ]
        
        # Effacer tous les fichiers
        for file in files_to_clear:
            if os.path.exists(file):
                os.remove(file)
                logger.info(f"🗑️ Supprimé: {file}")
        
        # Recharger le bot predictor pour réinitialiser TOUTES les données
        if bot.handlers.card_predictor:
            predictor = bot.handlers.card_predictor
            
            # Forcer la réinitialisation complète
            predictor.predictions = {}
            predictor.inter_data = []
            predictor.smart_rules = []
            predictor.collected_games = set()
            predictor.sequential_history = {}
            predictor.pending_edits = {}
            predictor.quarantined_rules = {}
            predictor.last_prediction_time = 0
            predictor.last_predicted_game_number = 0
            predictor.consecutive_fails = 0
            predictor.single_trigger_until = 0
            predictor.last_analysis_time = 0
            predictor.last_inter_update_time = 0
            predictor.last_report_sent = {}
            predictor.wait_until_next_update = 0
            
            # ✅ RÉACTIVER le mode INTER automatiquement
            predictor.is_inter_mode_active = True
            predictor._save_all_data()
            
            logger.info("🔄 RESET COMPLET EFFECTUÉ À 00h59 (BÉNIN):")
            logger.info("   ✅ TOUT EFFACÉ (prédictions, INTER, smart rules, collecte, etc.)")
            logger.info("   ✅ CONSERVÉ: IDs canaux (channels_config.json)")
            logger.info("   ✅ MODE INTER: RÉACTIVÉ automatiquement")
            logger.info("   ✅ COLLECTE: Réinitialisée à zéro")
        else:
            logger.error("❌ card_predictor non initialisé")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du reset complet: {e}")

def send_startup_message():
    """Envoie un message de démarrage de session avec la dernière mise à jour INTER."""
    try:
        if bot.handlers.card_predictor:
            predictor = bot.handlers.card_predictor
            if not predictor.telegram_message_sender or not predictor.prediction_channel_id:
                return
            
            now = predictor.now()
            last_update = predictor.get_inter_version()
            session_label = predictor.current_session_label()
            inter_active = "✅ ACTIF" if predictor.is_inter_mode_active else "❌ INACTIF"
            
            msg = (f"🎬 **LES PRÉDICTIONS REPRENNENT !**\n\n"
                   f"⏰ Heure de Bénin : {now.strftime('%H:%M:%S - %d/%m/%Y')}\n"
                   f"📅 Session : {session_label}\n"
                   f"🧠 Mode Intelligent : {inter_active}\n"
                   f"🔄 Mise à jour des règles : {last_update}\n\n"
                   f"👨‍💻 **Développeur** : Sossou Kouamé\n"
                   f"🎟️ **Code Promo** : Koua229")
            
            predictor.telegram_message_sender(predictor.prediction_channel_id, msg)
            logger.info("📢 Message de démarrage de session envoyé")
    except Exception as e:
        logger.error(f"❌ Erreur envoi message démarrage: {e}")

def send_session_reports():
    """Envoie les rapports de session à 5h, 17h, 22h (heure du Bénin)."""
    try:
        if bot.handlers.card_predictor:
            bot.handlers.card_predictor.check_and_send_reports()
    except Exception as e:
        logger.error(f"❌ Erreur envoi rapport: {e}")

def setup_scheduler():
    """Configure le planificateur pour la réinitialisation quotidienne et les rapports."""
    try:
        scheduler = BackgroundScheduler()
        benin_tz = pytz.timezone('Africa/Porto-Novo')
        
        # Réinitialisation toutes les 2 heures
        trigger_reset_2h = CronTrigger(hour='*/2', minute=0, timezone=benin_tz)
        scheduler.add_job(
            reset_every_2_hours,
            trigger=trigger_reset_2h,
            id='two_hourly_reset',
            name='Réinitialisation toutes les 2 heures',
            replace_existing=True
        )

        # Réinitialisation complète à 00h59
        trigger_reset_full = CronTrigger(hour=0, minute=59, timezone=benin_tz)
        scheduler.add_job(
            reset_non_inter_predictions,
            trigger=trigger_reset_full,
            id='daily_full_reset',
            name='Réinitialisation complète à 00h59',
            replace_existing=True
        )
        
        # Message de redémarrage à 1h, 9h, 15h, 21h
        for hour in [1, 9, 15, 21]:
            trigger_startup = CronTrigger(hour=hour, minute=0, timezone=benin_tz)
            scheduler.add_job(
                send_startup_message,
                trigger=trigger_startup,
                id=f'startup_message_{hour}h',
                name=f'Message redémarrage à {hour}h00',
                replace_existing=True
            )
        
        # Rapports automatiques à 6h, 12h, 18h, 00h
        for hour in [6, 12, 18, 0]:
            trigger_report = CronTrigger(hour=hour, minute=0, timezone=benin_tz)
            scheduler.add_job(
                send_session_reports,
                trigger=trigger_report,
                id=f'session_report_{hour}h',
                name=f'Rapport de session à {hour}h00',
                replace_existing=True
            )
        
        # Réinitialisation toutes les 15 minutes des règles inter
        trigger_inter_update = CronTrigger(minute='*/15', timezone=benin_tz)
        scheduler.add_job(
            bot.handlers.card_predictor.analyze_and_set_smart_rules,
            trigger=trigger_inter_update,
            id='inter_rules_update',
            name='Mise à jour des règles INTER toutes les 15 minutes',
            replace_existing=True,
            kwargs={'force_activate': True}
        )
        
        scheduler.start()
        logger.info("⏰ Planificateur configuré:")
        logger.info("   - Réinitialisation à 00h59 (heure du Bénin)")
        logger.info("   - Rapports à 5h00, 17h00, 22h00 (heure du Bénin)")
        
        return scheduler
    except Exception as e:
        logger.error(f"❌ Erreur configuration planificateur: {e}")
        return None

# Configure webhook au démarrage (fonctionne avec Gunicorn)
setup_webhook()

scheduler = setup_scheduler()

if __name__ == '__main__':
    # Get port from environment (10000 pour Render.com, 5000 pour Replit)
    port = int(os.getenv('PORT', 10000))
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=config.DEBUG)
