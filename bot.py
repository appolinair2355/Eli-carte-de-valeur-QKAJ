# bot.py

"""
Telegram Bot implementation with advanced features and deployment capabilities
"""
import os
import logging
import requests
import json
from typing import Dict, Any, Optional

# Importation des classes de logique métier
from handlers import TelegramHandlers
from card_predictor import CardPredictor 

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class TelegramBot:
    """
    Classe de haut niveau pour gérer les interactions avec l'API Telegram
    et déléguer le traitement des mises à jour aux handlers.
    """

    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.deployment_file_path = "deployment.zip" 
        
        # Initialize advanced handlers
        self.handlers = TelegramHandlers(token)
        
        if not self.handlers.card_predictor:
            logger.error("🚨 Le moteur de prédiction n'a pas pu être initialisé.")


    def handle_update(self, update: Dict[str, Any]) -> None:
        """Handle incoming Telegram update with advanced features for webhook mode"""
        try:
            # Log de haut niveau pour les différents types d'updates
            if 'message' in update or 'channel_post' in update:
                logger.info(f"🔄 Bot traite message normal/post canal via webhook")
            elif 'edited_message' in update or 'edited_channel_post' in update:
                logger.info(f"🔄 Bot traite message édité/post édité via webhook")
            elif 'my_chat_member' in update:
                 logger.info(f"🔄 Bot traite événement d'adhésion au chat (my_chat_member)")
            elif 'callback_query' in update:
                 logger.info(f"🔄 Bot traite clic de bouton (callback_query)")

            logger.debug(f"Received update: {json.dumps(update, indent=2)}")

            # Délégation du traitement complet aux handlers
            self.handlers.handle_update(update)
            
            logger.info(f"✅ Update traité avec succès via webhook")

        except Exception as e:
            logger.error(f"❌ Error handling update via webhook: {e}")

    # --- Méthodes API Directes (Pour setWebhook et autres) ---

    def send_message(self, chat_id: int, text: str, parse_mode: str = 'Markdown') -> bool:
        """Send text message to user (méthode de secours/utilitaire)"""
        # Utilisation de la méthode du handler pour la cohérence
        return self.handlers.send_message(chat_id, text, parse_mode) is not None

    def send_document(self, chat_id: int, file_path: str) -> bool:
        """Send document file to user (Méthode incluse pour respecter le schéma)"""
        try:
            url = f"{self.base_url}/sendDocument"

            if not os.path.exists(file_path):
                logger.error(f"File not found for sending: {file_path}")
                return False

            with open(file_path, 'rb') as file:
                files = {
                    'document': (os.path.basename(file_path), file, 'application/zip')
                }
                data = {
                    'chat_id': chat_id,
                    'caption': '📦 Deployment Package for render.com'
                }

                response = requests.post(url, data=data, files=files, timeout=60)
                return response.json().get('ok', False)
        except Exception as e:
            logger.error(f"Error sending document: {e}")
            return False

    def set_webhook(self, webhook_url: str) -> bool:
        """Set webhook URL for the bot"""
        try:
            url = f"{self.base_url}/setWebhook"
            # MISE À JOUR CRITIQUE: Inclure 'callback_query' et 'my_chat_member'
            data = {
                'url': webhook_url,
                'allowed_updates': ['message', 'edited_message', 'channel_post', 'edited_channel_post', 'callback_query', 'my_chat_member']
            }

            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            if result.get('ok'):
                logger.info(f"Webhook set successfully: {webhook_url}")
                return True
            else:
                logger.error(f"Failed to set webhook: {result}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error setting webhook: {e}")
            return False
        except Exception as e:
            logger.error(f"Error setting webhook: {e}")
            return False

    def get_bot_info(self) -> Dict[str, Any]:
        """Get bot information"""
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=30)
            result = response.json()
            return result.get('result', {}) if result.get('ok') else {}
        except Exception as e:
            logger.error(f"Error getting bot info: {e}")
            return {}
            
