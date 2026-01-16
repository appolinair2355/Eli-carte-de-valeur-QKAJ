# config.py

"""
Configuration settings for the Telegram bot
"""
import os
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- IDS DE CANAUX PAR DÉFAUT (Supprimés, les vrais IDs sont maintenant dans config.json) ---
DEFAULT_TARGET_CHANNEL_ID = None 
DEFAULT_PREDICTION_CHANNEL_ID = None 

# --- CONSTANTES POUR LES CALLBACKS DE CONFIGURATION ---
CALLBACK_SOURCE = "config_source"
CALLBACK_PREDICTION = "config_prediction"
CALLBACK_CANCEL = "config_cancel"

class Config:
    """Configuration class for bot settings"""
    
    def __init__(self):
        # BOT_TOKEN - OBLIGATOIRE
        self.BOT_TOKEN = self._get_bot_token()
        
        # Détermination de l'URL du Webhook
        self.WEBHOOK_URL = self._determine_webhook_url()
        logger.info(f"🔗 Webhook URL configuré: {self.WEBHOOK_URL}")

        # Port pour le serveur (utilise PORT env ou 5000 par défaut pour Replit)
        self.PORT = int(os.getenv('PORT') or 5000)
        
        # Canaux (Les vraies valeurs sont gérées par CardPredictor)
        self.TARGET_CHANNEL_ID = DEFAULT_TARGET_CHANNEL_ID
        self.PREDICTION_CHANNEL_ID = DEFAULT_PREDICTION_CHANNEL_ID
        
        # Mode Debug
        self.DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
        
        # Validation finale
        self._validate_config()
    
    def _get_bot_token(self) -> str:
        """Récupère et valide le token du bot depuis les fichiers ou variables d'environnement."""
        token = None
        
        # Priorité 1: Fichier secrets_config.json
        try:
            if os.path.exists('secrets_config.json'):
                with open('secrets_config.json', 'r') as f:
                    import json
                    secrets = json.load(f)
                    token = secrets.get('BOT_TOKEN')
                    if token:
                        logger.info("✅ BOT_TOKEN chargé depuis secrets_config.json")
        except Exception as e:
            logger.debug(f"⚠️ Impossible de lire secrets_config.json: {e}")
        
        # Priorité 2: Variables d'environnement
        if not token:
            token = os.getenv('BOT_TOKEN')
            if token:
                logger.info("✅ BOT_TOKEN chargé depuis variables d'environnement")
        
        if not token:
            raise ValueError("BOT_TOKEN not found in secrets_config.json or environment variables.")
        if ':' not in token or not token.split(':')[0].isdigit():
            raise ValueError("Invalid bot token format")

        logger.info(f"✅ BOT_TOKEN configuré: {token[:10]}...")
        return token
    
    def _determine_webhook_url(self) -> str:
        """Détermine l'URL du webhook avec priorité à l'ENV."""
        webhook_url = os.getenv('WEBHOOK_URL')
        
        # Logique d'auto-génération (adaptée à Replit)
        if not webhook_url:
            # Détection Replit
            if os.getenv('REPLIT_DOMAINS'):
                webhook_url = f"https://{os.getenv('REPLIT_DOMAINS')}"
            elif os.getenv('REPL_SLUG'):
                webhook_url = f'https://{os.getenv("REPL_SLUG", "")}.{os.getenv("REPL_OWNER", "")}.repl.co'
            # Sur Render, WEBHOOK_URL DOIT être défini manuellement
            elif os.getenv('RENDER'):
                logger.warning("⚠️ Sur Render.com, WEBHOOK_URL doit être défini manuellement dans les variables d'environnement")
        
        return webhook_url or ""
    
    def _validate_config(self) -> None:
        """Valide les paramètres de configuration."""
        if self.WEBHOOK_URL and not self.WEBHOOK_URL.startswith('https://'):
            logger.warning("⚠️ L'URL du webhook devrait utiliser HTTPS pour la production.")
        
        logger.info("✅ Configuration validée avec succès.")
    
    def get_webhook_url(self) -> str:
        """Renvoie l'URL complète du webhook (y compris /webhook)."""
        if self.WEBHOOK_URL:
            return f"{self.WEBHOOK_URL}/webhook"
        return ""
    
    def __str__(self) -> str:
        """Représentation textuelle de la configuration (sans données sensibles)."""
        return (
            f"Config(\n"
            f"  WEBHOOK_URL: {self.WEBHOOK_URL},\n"
            f"  PORT: {self.PORT},\n"
            f"  TARGET_CHANNEL_ID: {self.TARGET_CHANNEL_ID},\n"
            f"  PREDICTION_CHANNEL_ID: {self.PREDICTION_CHANNEL_ID},\n"
            f"  DEBUG: {self.DEBUG}\n"
            f")"
)
        
