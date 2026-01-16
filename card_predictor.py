# card_predictor.py

import re
import logging
import time
import os
import json
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Any
from collections import defaultdict
import pytz

logger = logging.getLogger(__name__)
# Mis à jour à DEBUG pour vous aider à tracer la collecte.
logger.setLevel(logging.DEBUG) 

# ================== CONFIG ==================
BENIN_TZ = pytz.timezone("Africa/Porto-Novo")

# --- 1. RÈGLES STATIQUES (Supprimées pour Mode INTER exclusif) ---
STATIC_RULES = {}

# Correspondance des costumes vers les cartes de valeur
SUIT_TO_VALUE_MAP = {
    "♠️": "Q",
    "♦️": "K",
    "♣️": "J",
    "❤️": "A",
    "♥️": "A"
}

# Symboles pour les status de vérification
SYMBOL_MAP = {0: '✅0️⃣', 1: '✅1️⃣', 2: '✅2️⃣', 'lost': '❌'}

# Sessions de prédictions (heure_début, heure_fin)
# 1h-6h, 9h-12h, 15h-18h, 21h-00h (00h = 24)
PREDICTION_SESSIONS = [
    (1, 6),
    (9, 12),
    (15, 18),
    (21, 24)
]

class CardPredictor:
    """Gère la logique de prédiction d'ENSEIGNE (Couleur) et la vérification."""

    def __init__(self, telegram_message_sender=None):
        
        # <<<<<<<<<<<<<<<< ZONE CRITIQUE À MODIFIER PAR L'UTILISATEUR >>>>>>>>>>>>>>>>
        # ⚠️ IDs DE CANAUX CONFIGURÉS
        self.HARDCODED_SOURCE_ID = -1003424179389  # <--- ID du canal SOURCE/DÉCLENCHEUR
        self.HARDCODED_PREDICTION_ID = -1003362820311 # <--- ID du canal PRÉDICTION/RÉSULTAT
        # <<<<<<<<<<<<<<<< FIN ZONE CRITIQUE >>>>>>>>>>>>>>>>
        
        # Stockage temporaire du rule_index et trigger pour passer à make_prediction
        self._last_rule_index = 0
        self._last_trigger_used = None

        # --- A. Chargement des Données ---
        self.predictions = self._load_data('predictions.json') 
        self.processed_messages = self._load_data('processed.json', is_set=True) 
        self.last_prediction_time = self._load_data('last_prediction_time.json', is_scalar=True) or 0
        self.last_predicted_game_number = self._load_data('last_predicted_game_number.json', is_scalar=True) or 0
        self.consecutive_fails = self._load_data('consecutive_fails.json', is_scalar=True) or 0
        self.pending_edits: Dict[int, Dict] = self._load_data('pending_edits.json')
        
        # --- B. Configuration Canaux (AVEC FALLBACK SÉCURISÉ) ---
        raw_config = self._load_data('channels_config.json')
        self.config_data = raw_config if isinstance(raw_config, dict) else {}
        
        self.target_channel_id = self.config_data.get('target_channel_id')
        if not self.target_channel_id and self.HARDCODED_SOURCE_ID != 0:
            self.target_channel_id = self.HARDCODED_SOURCE_ID
            logger.info(f"✅ Canal SOURCE (codé en dur): {self.target_channel_id}")
            
        self.prediction_channel_id = self.config_data.get('prediction_channel_id')
        if not self.prediction_channel_id and self.HARDCODED_PREDICTION_ID != 0:
            self.prediction_channel_id = self.HARDCODED_PREDICTION_ID
            logger.info(f"✅ Canal PRÉDICTION (codé en dur): {self.prediction_channel_id}")
        
        # --- C. Logique INTER (Intelligente) ---
        self.telegram_message_sender = telegram_message_sender
        self.active_admin_chat_id = self._load_data('active_admin_chat_id.json', is_scalar=True)
        
        self.sequential_history: Dict[int, Dict] = self._load_data('sequential_history.json') 
        self.inter_data: List[Dict] = self._load_data('inter_data.json') 
        self.is_inter_mode_active = self._load_data('inter_mode_status.json', is_scalar=True)
        self.smart_rules = self._load_data('smart_rules.json')
        self.last_analysis_time = self._load_data('last_analysis_time.json', is_scalar=True) or 0
        self.collected_games = self._load_data('collected_games.json', is_set=True)
        
        self.single_trigger_until = self._load_data('single_trigger_until.json', is_scalar=True) or 0
        
        # Nouvelles données: quarantaine intelligente et rapports
        self.quarantined_rules = self._load_data('quarantined_rules.json')
        if not isinstance(self.quarantined_rules, dict):
            self.quarantined_rules = {}
        self.wait_until_next_update = self._load_data('wait_until_next_update.json', is_scalar=True) or 0
        self.last_inter_update_time = self._load_data('last_inter_update.json', is_scalar=True) or 0
        self.last_report_sent = self._load_data('last_report_sent.json')
        
        if self.is_inter_mode_active is None:
            self.is_inter_mode_active = True
        
        self.prediction_cooldown = 30 
        
        if self.inter_data and not self.is_inter_mode_active and not self.smart_rules:
             self.analyze_and_set_smart_rules(initial_load=True)

    # --- Persistance ---
    def _load_data(self, filename: str, is_set: bool = False, is_scalar: bool = False) -> Any:
        try:
            is_dict = filename in ['channels_config.json', 'predictions.json', 'sequential_history.json', 'smart_rules.json', 'pending_edits.json']
            
            if not os.path.exists(filename):
                return set() if is_set else (None if is_scalar else ({} if is_dict else []))
            with open(filename, 'r') as f:
                content = f.read().strip()
                if not content: return set() if is_set else (None if is_scalar else ({} if is_dict else []))
                data = json.loads(content)
                if is_set: return set(data)
                if filename in ['sequential_history.json', 'predictions.json', 'pending_edits.json'] and isinstance(data, dict): 
                    return {int(k): v for k, v in data.items()}
                return data
        except Exception as e:
            logger.error(f"⚠️ Erreur chargement {filename}: {e}")
            is_dict = filename in ['channels_config.json', 'predictions.json', 'sequential_history.json', 'smart_rules.json', 'pending_edits.json']
            return set() if is_set else (None if is_scalar else ({} if is_dict else []))

    def _save_data(self, data: Any, filename: str):
        try:
            if isinstance(data, set): data = list(data)
            if filename == 'channels_config.json' and isinstance(data, dict):
                if 'target_channel_id' in data and data['target_channel_id'] is not None:
                    data['target_channel_id'] = int(data['target_channel_id'])
                if 'prediction_channel_id' in data and data['prediction_channel_id'] is not None:
                    data['prediction_channel_id'] = int(data['prediction_channel_id'])
            
            with open(filename, 'w') as f: json.dump(data, f, indent=4)
        except Exception as e: logger.error(f"❌ Erreur sauvegarde {filename}: {e}")

    def _save_all_data(self):
        self._save_data(self.predictions, 'predictions.json')
        self._save_data(self.processed_messages, 'processed.json')
        self._save_data(self.last_prediction_time, 'last_prediction_time.json')
        self._save_data(self.last_predicted_game_number, 'last_predicted_game_number.json')
        self._save_data(self.consecutive_fails, 'consecutive_fails.json')
        self._save_data(self.inter_data, 'inter_data.json')
        self._save_data(self.sequential_history, 'sequential_history.json')
        self._save_data(self.is_inter_mode_active, 'inter_mode_status.json')
        self._save_data(self.smart_rules, 'smart_rules.json')
        self._save_data(self.active_admin_chat_id, 'active_admin_chat_id.json')
        self._save_data(self.last_analysis_time, 'last_analysis_time.json')
        self._save_data(self.pending_edits, 'pending_edits.json')
        self._save_data(self.collected_games, 'collected_games.json')
        self._save_data(self.single_trigger_until, 'single_trigger_until.json')
        self._save_data(self.quarantined_rules, 'quarantined_rules.json')
        self._save_data(self.wait_until_next_update, 'wait_until_next_update.json')
        self._save_data(self.last_inter_update_time, 'last_inter_update.json')
        self._save_data(self.last_report_sent, 'last_report_sent.json')

    # ======== TEMPS & SESSIONS ========
    def now(self):
        return datetime.now(BENIN_TZ)
    
    def is_in_session(self):
        """Le bot doit prédire 24h/24 sans interruption."""
        return True
    
    def current_session_label(self):
        h = self.now().hour
        return f"Service 24h/24 (Actuel: {h:02d}h)"
    
    # ======== RAPPORTS ========
    def check_and_send_reports(self):
        """Envoie les rapports de fin de session (appelé régulièrement)."""
        if not self.telegram_message_sender or not self.prediction_channel_id:
            logger.debug("⚠️ Pas de sender ou prediction_channel_id")
            return
        
        now = self.now()
        key_date = now.strftime("%Y-%m-%d")
        
        # Heures de fin de session : 6h, 12h, 18h, 00h (minuit)
        report_hours = {6: ("01h00", "06h00"), 12: ("09h00", "12h00"), 18: ("15h00", "18h00"), 0: ("21h00", "00h00")}
        
        # Vérifier si c'est une heure de rapport
        if now.hour not in report_hours:
            return
        
        key = f"{key_date}_{now.hour}"
        
        # Éviter d'envoyer deux fois
        if self.last_report_sent.get(key):
            return
        
        logger.info(f"📊 Envoi rapport de session à {now.hour}h...")
        
        start, end = report_hours[now.hour]
        
        # Compter les prédictions complétées (won ou lost)
        session_predictions = {}
        for game_num, pred in self.predictions.items():
            status = pred.get('status')
            if status in ['won', 'lost']:
                session_predictions[game_num] = pred
        
        total = len(session_predictions)
        wins = sum(1 for p in session_predictions.values() if p.get("status") == 'won')
        fails = sum(1 for p in session_predictions.values() if p.get("status") == 'lost')
        win_rate = (wins / total * 100) if total > 0 else 0
        fail_rate = (fails / total * 100) if total > 0 else 0
        
        # Construire le message
        msg = (f"🎬 **BILAN DE SESSION**\n\n"
               f"⏰ Heure de Bénin : {now.strftime('%H:%M:%S - %d/%m/%Y')}\n"
               f"📅 Session : {start} – {end}\n"
               f"🧠 Mode : {'✅ INTER ACTIF' if self.is_inter_mode_active else '❌ STATIQUE'}\n"
               f"🔄 Règles : {self.get_inter_version()}\n\n"
               f"📊 **RÉSULTATS**\n"
               f"📈 Total : {total}\n"
               f"✅ Succès : {wins} ({win_rate:.1f}%)\n"
               f"❌ Échecs : {fails} ({fail_rate:.1f}%)\n\n"
               f"💖 Merci à tous sur le code promo !\n\n"
               f"👨‍💻 Dev : Sossou Kouamé\n"
               f"🎟️ Code : Koua229")
        
        try:
            self.telegram_message_sender(self.prediction_channel_id, msg)
            self.last_report_sent[key] = True
            self._save_all_data()
            logger.info(f"✅ Rapport {start}-{end} envoyé: {total} prédictions, {wins} succès")
        except Exception as e:
            logger.error(f"❌ Erreur envoi rapport: {e}")
    
    def get_inter_version(self):
        if not self.last_inter_update_time:
            return "Base neuve"
        return datetime.fromtimestamp(self.last_inter_update_time, BENIN_TZ).strftime("%Y-%m-%d | %Hh%M")
    
    def _get_last_update_display(self):
        """Retourne la date et heure de la dernière mise à jour INTER ou un message par défaut."""
        if not self.last_inter_update_time:
            return "Pas encore de mise à jour"
        return datetime.fromtimestamp(self.last_inter_update_time, BENIN_TZ).strftime("%d/%m/%Y à %H:%M:%S")
    
    def get_session_report_preview(self):
        """Retourne un aperçu du rapport de fin de session avec le temps restant."""
        now = self.now()
        report_hours = {6: ("01h00", "06h00"), 12: ("09h00", "12h00"), 18: ("15h00", "18h00"), 0: ("21h00", "00h00")}
        
        # Trouver la prochaine heure de rapport
        next_report_hour = None
        for h in sorted(report_hours.keys()):
            if h > now.hour:
                next_report_hour = h
                break
        if next_report_hour is None:
            next_report_hour = min(report_hours.keys())
        
        # Temps restant
        minutes_until = ((next_report_hour - now.hour) * 60 - now.minute) % (24 * 60)
        hours = minutes_until // 60
        mins = minutes_until % 60
        
        # Stats de prédictions
        session_predictions = {k: v for k, v in self.predictions.items() if v.get('status') in ['won', 'lost', 'pending']}
        total = len(session_predictions)
        wins = sum(1 for p in session_predictions.values() if str(p.get("status", "")).startswith("✅") or p.get("status") == 'won')
        fails = sum(1 for p in session_predictions.values() if p.get("status") in ["❌", "lost"])
        win_rate = (wins / total * 100) if total else 0
        fail_rate = (fails / total * 100) if total else 0
        
        start, end = report_hours[next_report_hour]
        
        msg = (f"📋 **APERÇU DU BILAN**\n\n"
               f"⏰ Heure de Bénin : {now.strftime('%H:%M:%S - %d/%m/%Y')}\n"
               f"🎯 Prochain bilan : {start} – {end}\n"
               f"⏳ Temps restant : {hours}h{mins:02d}\n\n"
               f"🧠 Mode Intelligent : {'✅ ACTIF' if self.is_inter_mode_active else '❌ INACTIF'}\n"
               f"🔄 Dernière mise à jour IA : {self._get_last_update_display()}\n\n"
               f"📊 **STATISTIQUES ACTUELLES**\n"
               f"📈 Prédictions : {total}\n"
               f"✅ Réussites : {wins} ({win_rate:.1f}%)\n"
               f"❌ Échecs : {fails} ({fail_rate:.1f}%)\n\n"
               f"👨‍💻 **Développeur** : Sossou Kouamé\n"
               f"🎟️ **Code Promo** : Koua229")
        
        return msg
    
    def set_channel_id(self, channel_id: int, channel_type: str):
        if not isinstance(self.config_data, dict): self.config_data = {}
        if channel_type == 'source':
            self.target_channel_id = channel_id
            self.config_data['target_channel_id'] = channel_id
        elif channel_type == 'prediction':
            self.prediction_channel_id = channel_id
            self.config_data['prediction_channel_id'] = channel_id
        self._save_data(self.config_data, 'channels_config.json')
        return True

    # --- Outils d'Extraction/Comptage ---
    
    def _extract_parentheses_content(self, text: str) -> List[str]:
        """Extrait le contenu de toutes les sections de parenthèses (non incluses)."""
        pattern = r'\(([^)]+)\)'
        return re.findall(pattern, text)

    def _count_cards_in_content(self, content: str) -> int:
        """Compte les symboles de cartes (♠️, ♥️, ♦️, ♣️) dans une chaîne, en normalisant ❤️ vers ♥️."""
        normalized_content = content.replace("❤️", "♥️")
        return len(re.findall(r'(\d+|[AKQJ])(♠️|♥️|♦️|♣️)', normalized_content, re.IGNORECASE))
        
    def has_pending_indicators(self, text: str) -> bool:
        """Vérifie si le message contient des indicateurs suggérant qu'il sera édité (temporaire)."""
        indicators = ['⏰', '▶', '🕐', '➡️']
        return any(indicator in text for indicator in indicators)

    def has_completion_indicators(self, text: str) -> bool:
        """Vérifie si le message contient des indicateurs de complétion après édition (✅ ou 🔰)."""
        completion_indicators = ['✅', '🔰']
        return any(indicator in text for indicator in completion_indicators)
        
    def is_final_result_structurally_valid(self, text: str) -> bool:
        """
        Vérifie si le message contient un numéro de jeu et des parenthèses.
        Rendu plus flexible pour ne pas bloquer la vérification.
        """
        if not (self.extract_game_number(text) or '#N' in text or '🔵' in text):
            return False
            
        # Si on a un numéro de jeu, on considère que c'est un message valide à vérifier
        # même si les parenthèses sont absentes (cas rares de formats simplifiés)
        return True
        
    # --- Outils d'Extraction (Continuation) ---
    def extract_game_number(self, message: str) -> Optional[int]:
        # Formats: #N1249. , №1249, 🔵1249🔵
        match = re.search(r'#N(\d+)', message, re.IGNORECASE) 
        if not match: match = re.search(r'№(\d+)', message)
        if not match: match = re.search(r'🔵(\d+)🔵', message)
        num = int(match.group(1)) if match else None
        if num:
            logger.debug(f"🎮 Numéro du jeu extrait: {num}")
        return num

    def is_message_finalized(self, text: str) -> bool:
        """Vérifie si le message ne contient plus d'indicateurs de message non finalisé."""
        pending_indicators = ['⏰', '⏱️', '▶', '🕐', '➡️']
        # Si le message contient un indicateur de temps, il n'est pas finalisé
        if any(indicator in text for indicator in pending_indicators):
            return False
        # Si le message contient un tiret et deux groupes de parenthèses (ex: 21(...) - 22(...)), il est finalisé
        if '-' in text and text.count('(') >= 2:
            return True
        return True # Par défaut, on considère finalisé s'il n'y a pas d'indicateur

    def extract_card_details(self, content: str) -> List[Tuple[str, str]]:
        # Normalise ♥️ en ❤️
        normalized_content = content.replace("♥️", "❤️")
        # Cherche Valeur + Enseigne (ex: 10♦️, A♠️, Q♥️)
        # Supporte aussi les formats collés comme J♦️Q♦️9♠️7♣️
        return re.findall(r'(\d+|[AKQJ])(♠️|❤️|♦️|♣️)', normalized_content, re.IGNORECASE)

    def get_first_two_cards_info(self, message: str) -> List[str]:
        """
        Retourne les DEUX PREMIÈRES cartes du PREMIER groupe.
        Supporte les formats (cards) et NUM(cards).
        """
        # Cherche le premier bloc entre parenthèses, potentiellement précédé de chiffres
        match = re.search(r'(?:\d+)?\(([^)]*)\)', message)
        if not match: return []
        
        details = self.extract_card_details(match.group(1))
        cards = []
        for i in range(min(len(details), 2)):
            v, c = details[i]
            normalized_c = "♥️" if c == "❤️" else c
            cards.append(f"{v.upper()}{normalized_c}")
        return cards
    
    def get_all_cards_in_first_group(self, message: str) -> List[str]:
        """
        Retourne TOUTES les cartes du PREMIER groupe.
        """
        match = re.search(r'(?:\d+)?\(([^)]*)\)', message)
        if not match: return []
        
        details = self.extract_card_details(match.group(1))
        cards = []
        for v, c in details:
            normalized_c = "♥️" if c == "❤️" else c
            cards.append(f"{v.upper()}{normalized_c}")
        return cards
        
    # --- Logique INTER (Collecte et Analyse) ---
    def collect_inter_data(self, game_number: int, message: str):
        """Collecte les données (N-2 -> N) même si le message est en cours."""
        # On normalise pour les cœurs
        message = message.replace("❤️", "♥️")
        
        # Pour la collecte, on regarde uniquement la PREMIÈRE carte comme déclencheur potentiel
        trigger_cards = self.get_first_two_cards_info(message)
        if not trigger_cards: return
        
        # Pour le résultat du jeu actuel N (pour la vérification/apprentissage)
        # On regarde la première carte du premier groupe
        first_card_full = trigger_cards[0]
        match_suit = re.search(r'(♠️|♥️|♦️|♣️)', first_card_full)
        if not match_suit: return
        suit = match_suit.group(1)
        
        # Remplacement du costume par la carte de valeur
        result_value = SUIT_TO_VALUE_MAP.get(suit, suit)
        
        # Vérifier si déjà dans collected_games
        if game_number in self.collected_games:
            return

        # On stocke uniquement la PREMIÈRE carte comme déclencheur pour ce jeu N
        # (Conformément à l'instruction : la collecte enregistre la première carte)
        self.sequential_history[game_number] = {
            'carte': first_card_full, 
            'date': datetime.now().isoformat()
        }
        self.collected_games.add(game_number)
        
        n_minus_2 = game_number - 2
        trigger_entry = self.sequential_history.get(n_minus_2)
        
        if trigger_entry:
            trigger_card = trigger_entry.get('carte')
            if trigger_card:
                self.inter_data.append({
                    'numero_resultat': game_number,
                    'declencheur': trigger_card, 
                    'numero_declencheur': n_minus_2,
                    'result_suit': result_value, 
                    'date': datetime.now().isoformat()
                })
                logger.info(f"🧠 Jeu {game_number} collecté pour INTER: {trigger_card} -> {result_value}")

        limit = game_number - 50
        self.sequential_history = {k:v for k,v in self.sequential_history.items() if k >= limit}
        self.collected_games = {g for g in self.collected_games if g >= limit}
        
        self._save_all_data()

    
    def reset_all_data(self):
        """Réinitialisation complète toutes les 2 heures"""
        logger.info("🧹 Réinitialisation complète (collecte, règles inter, prédictions)")
        self.collected_games = set()
        self.smart_rules = []
        self.predictions = {}
        self.last_predicted_game_number = 0
        self.wait_until_next_update = 0
        self.inter_data = []
        self.sequential_history = {}
        self.pending_edits = {}
        self.quarantined_rules = {}
        self.last_prediction_time = 0
        self.consecutive_fails = 0
        self.single_trigger_until = 0
        self.last_analysis_time = 0
        self.last_inter_update_time = 0
        
        # Sauvegarde des fichiers vides
        self._save_all_data()
        
        # Ré-activer le mode INTER automatiquement
        self.is_inter_mode_active = True
        self._save_data(self.is_inter_mode_active, 'inter_mode_status.json')
        logger.info("✅ Mode INTER ré-activé automatiquement")

    def check_and_update_rules_periodic(self, force=False):
        """Met à jour les règles INTER si nécessaire (toutes les 15 min)."""
        now = time.time()
        if force or now - self.last_inter_update_time >= 900: # 15 min
            logger.info("🕒 Mise à jour automatique des règles INTER (15 min)")
            self.analyze_and_set_smart_rules(force_activate=True)

    def analyze_and_set_smart_rules(self, chat_id: Optional[int] = None, initial_load: bool = False, force_activate: bool = False):
        """
        Analyse les données pour trouver les Top 5 déclencheurs par ENSEIGNE DE RÉSULTAT.
        """
        self.last_inter_update_time = time.time() # Marquer la mise à jour
        # Toujours recharger les dernières données avant l'analyse
        self.inter_data = self._load_data('inter_data.json')
        
        # Grouper par enseigne de RÉSULTAT (A, K, Q, J)
        result_suit_groups = defaultdict(lambda: defaultdict(int))
        
        for entry in self.inter_data:
            trigger_card = entry['declencheur']
            result_val = entry['result_suit']
            
            # NE JAMAIS utiliser un déclencheur qui contient A, K, Q, J
            if any(val in trigger_card for val in ['A', 'K', 'Q', 'J']):
                continue
                
            # Compter combien de fois ce déclencheur mène à cette carte de valeur
            result_suit_groups[result_val][trigger_card] += 1
        
        self.smart_rules = []
        seen_triggers = set()
        
        # Pour chaque carte de valeur cible (Q, K, J, A)
        for result_val in ["Q", "K", "J", "A"]:
            triggers_for_this_val = result_suit_groups.get(result_val, {})
            
            if not triggers_for_this_val:
                continue
            
            # Trier par fréquence et prendre jusqu'à 5 meilleurs
            # On s'assure qu'ils sont uniques globalement dans les tops si possible
            # Mais ici le user demande "pas de top identiques"
            top_triggers = sorted(
                triggers_for_this_val.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            count_added = 0
            for trigger_card, count in top_triggers:
                if count_added >= 5:
                    break
                if trigger_card in seen_triggers:
                    continue
                    
                self.smart_rules.append({
                    'trigger': trigger_card,
                    'predict': result_val,
                    'count': count,
                    'result_suit': result_val
                })
                seen_triggers.add(trigger_card)
                count_added += 1

        # MODE INTER : ACTIVÉ AUTOMATIQUEMENT
        self.is_inter_mode_active = True
            
        self.last_analysis_time = time.time()
        self._save_all_data()

        logger.info(f"🧠 Analyse terminée. Règles trouvées: {len(self.smart_rules)}. Mode actif: {self.is_inter_mode_active}")
        
        # Notification si demandée
        if chat_id is not None and self.telegram_message_sender:
            if self.smart_rules:
                msg = f"✅ **Analyse terminée !**\n\n{len(self.smart_rules)} règles créées à partir de {len(self.inter_data)} jeux collectés.\n\n🧠 **Mode INTER activé automatiquement**"
            else:
                msg = f"⚠️ **Pas assez de données**\n\n{len(self.inter_data)} jeux collectés. Continuez à jouer pour créer des règles."
            self.telegram_message_sender(chat_id, msg)
        
        # SYSTÈME DE QUARANTAINE SUPPRIMÉ
        self.quarantined_rules = {}

    def check_and_update_rules(self):
        """Vérification périodique (15 minutes)."""
        if time.time() - self.last_inter_update_time >= 900:
            logger.info("🕒 Mise à jour automatique des règles INTER (15 min)")
            self.analyze_and_set_smart_rules(force_activate=True)

    def check_and_send_automatic_predictions(self):
        """DÉSACTIVÉ - Les prédictions sont basées sur les messages du canal source uniquement."""
        pass

    def get_bot_status(self):
        total = len(self.predictions)
        wins = sum(1 for p in self.predictions.values() if str(p.get("status", "")).startswith("✅"))
        fails = sum(1 for p in self.predictions.values() if p.get("status") == "❌")
        
        return (f"📊 **STATUT DU BOT**\n\n"
                f"🧠 Mode intelligent : {'ACTIF' if self.is_inter_mode_active else 'INACTIF'}\n"
                f"🎯 Session : {self.current_session_label()}\n"
                f"📈 Prédictions : {total}\n"
                f"✅ Réussites : {wins}\n"
                f"❌ Échecs : {fails}\n\n"
                f"🔖 Version IA : {self.get_inter_version()}")
    
    def get_inter_status(self) -> Tuple[str, Dict]:
        """Retourne le statut du mode INTER avec message et clavier."""
        data_count = len(self.inter_data)
        
        if not self.smart_rules:
            message = f"🧠 **MODE INTER - {'✅ ACTIF' if self.is_inter_mode_active else '❌ INACTIF'}**\n\n"
            message += f"📊 **{data_count} jeux collectés**\n"
            message += "⚠️ Pas encore assez de règles créées.\n\n"
            message += "**Cliquez sur 'Analyser' pour générer les règles !**"
            
            keyboard_buttons = [
                [{'text': '🔄 Analyser et Activer', 'callback_data': 'inter_apply'}]
            ]
            
            if self.is_inter_mode_active:
                keyboard_buttons.append([{'text': '❌ Désactiver', 'callback_data': 'inter_default'}])
            
            keyboard = {'inline_keyboard': keyboard_buttons}
        else:
            rules_by_result = defaultdict(list)
            for rule in self.smart_rules:
                rules_by_result[rule['result_suit']].append(rule)
            
            message = f"🧠 **MODE INTER - {'✅ ACTIF' if self.is_inter_mode_active else '❌ INACTIF'}**\n\n"
            message += f"📊 **{len(self.smart_rules)} règles** créées ({data_count} jeux analysés):\n\n"
            
            for suit in ['Q', 'K', 'J', 'A']:
                if suit in rules_by_result:
                    message += f"**Pour prédire {suit}:**\n"
                    for rule in rules_by_result[suit]:
                        message += f"  • {rule['trigger']} ({rule['count']}x)\n"
                    message += "\n"
            
            if self.is_inter_mode_active:
                keyboard = {
                    'inline_keyboard': [
                        [{'text': '🔄 Relancer Analyse', 'callback_data': 'inter_apply'}],
                        [{'text': '❌ Désactiver', 'callback_data': 'inter_default'}]
                    ]
                }
            else:
                keyboard = {
                    'inline_keyboard': [
                        [{'text': '🚀 Activer INTER', 'callback_data': 'inter_apply'}]
                    ]
                }
        
        return message, keyboard
    
    def _apply_quarantine(self, prediction):
        """Applique la quarantaine intelligente après un échec - mise en quarantaine 1h."""
        trigger_used = prediction.get('predicted_from_trigger')
        predicted_suit = prediction.get('predicted_costume')
        
        if not trigger_used or not predicted_suit:
            return
        
        key = f"{trigger_used}_{predicted_suit}"
        
        for rule in self.smart_rules:
            if rule.get('trigger') == trigger_used and rule.get('predict') == predicted_suit:
                # Enregistrer le TOP en quarantaine avec timestamp expiration
                self.quarantined_rules[key] = {
                    'count': rule.get('count', 1),
                    'timestamp': time.time(),
                    'expires_at': time.time() + 3600  # Expiration après 1 heure
                }
                logger.info(f"🔒 Quarantaine appliquée: {key} (expire dans 1h)")
                break
        
        self.wait_until_next_update = time.time() + 1800
        self._save_all_data()


    # --- CŒUR DU SYSTÈME : PRÉDICTION ---
    
    def should_wait_for_edit(self, text: str, message_id: int) -> bool:
        if self.has_pending_indicators(text):
            game_number = self.extract_game_number(text)
            if message_id not in self.pending_edits:
                self.pending_edits[message_id] = {
                    'game_number': game_number,
                    'original_text': text,
                    'timestamp': datetime.now().isoformat()
                }
                self._save_data(self.pending_edits, 'pending_edits.json')
            return True
        return False

    def should_predict(self, message: str) -> Tuple[bool, Optional[int], Optional[str], Optional[bool]]:
        self.check_and_send_reports()
        self.check_and_update_rules_periodic()

        # Le bot doit prédire 24h/24 sans interruption
        game_number = self.extract_game_number(message)
        if not game_number:
            logger.debug("❌ Aucun numéro de jeu trouvé")
            return False, None, None, None

        # Le jeu qu'on va prédire est N + 2
        predicted_game_target = game_number + 2

        # ✅ ÉCART DE 4 JEUX : On vérifie par rapport au DERNIER JEU PRÉDIT (target)
        if self.last_predicted_game_number > 0:
            last_target = self.last_predicted_game_number + 2
            diff = predicted_game_target - last_target
            if diff < 4:
                logger.debug(f"⏳ Écart insuffisant ({predicted_game_target} - {last_target} < 4). Prédiction ignorée.")
                return False, None, None, None

        # On permet de re-prédire pour le même jeu source si c'est un message édité avec de nouvelles cartes
        if game_number in self.predictions and self.predictions[game_number].get('status') == 'pending':
             return False, None, None, None

        # ✅ RÉCUPÉRER LA DERNIÈRE VALEUR PRÉDITE POUR ÉVITER LES DOUBLONS CONSÉCUTIFS
        last_predicted_value = None
        if self.predictions:
            sorted_preds = sorted(self.predictions.values(), key=lambda x: x.get('timestamp', 0), reverse=True)
            if sorted_preds:
                last_pred_suit = sorted_preds[0].get('predicted_costume')
                last_predicted_value = SUIT_TO_VALUE_MAP.get(last_pred_suit, last_pred_suit)

        # 🔍 Vérifier les DEUX premières cartes du 1er groupe pour prédire
        prediction_trigger_cards = self.get_first_two_cards_info(message)
        if not prediction_trigger_cards:
            logger.debug("❌ Aucune carte trouvée pour le déclenchement dans le 1er groupe")
            return False, None, None, None

        logger.info(f"🎮 Jeu source: {game_number} → Cartes déclencheur (2 premières): {prediction_trigger_cards}")

        predicted_suit = None
        trigger_used = None
        is_inter_prediction = False
        rule_index = 0

        # ======= MODE INTER : PRIORITÉ ABSOLUE (TOP 5 UNIQUEMENT) =======
        if self.is_inter_mode_active and self.smart_rules:
            rules_by_value = defaultdict(list)
            for rule in self.smart_rules:
                val = rule.get('predict', rule.get('result_suit'))
                rules_by_value[val].append(rule)
            
            if not self.smart_rules:
                logger.debug("⏳ Mode INTER actif mais aucune règle générée. En attente de collecte.")
                return False, None, None, None

            for val_target in ["A", "K", "Q", "J"]:
                # ✅ RÈGLE : Pas deux valeurs identiques consécutives
                if val_target == last_predicted_value:
                    logger.debug(f"🚫 Valeur {val_target} identique à la précédente. Passage à la suivante.")
                    continue

                val_rules = rules_by_value.get(val_target, [])[:5]
                for idx, rule in enumerate(val_rules):
                    if rule['trigger'] in prediction_trigger_cards:
                        key = f"{rule['trigger']}_{rule['predict']}"
                        if key in self.quarantined_rules:
                            qua_data = self.quarantined_rules[key]
                            if isinstance(qua_data, dict) and time.time() < qua_data.get('expires_at', 0):
                                continue
                            elif not isinstance(qua_data, dict) and qua_data >= rule.get("count", 1):
                                continue

                        already_predicted = False
                        target_game_internal = game_number + 2
                        if target_game_internal in self.predictions:
                            prev_pred = self.predictions[target_game_internal]
                            if prev_pred.get('predicted_from') == game_number and \
                               prev_pred.get('predicted_from_trigger') == rule['trigger'] and \
                               prev_pred.get('status') == 'pending':
                                already_predicted = True
                        
                        if already_predicted: continue

                        predicted_suit = rule['predict']
                        trigger_used = rule['trigger']
                        is_inter_prediction = True
                        rule_index = idx + 1
                        logger.info(f"🔮 INTER (TOP{rule_index}) pour {val_target}: {trigger_used} → {predicted_suit}")
                        break
                if predicted_suit: break
            
            if not predicted_suit:
                logger.debug("⚠️ MODE INTER actif mais aucune règle TOP5 éligible (valeur différente attendue).")
                return False, None, None, None
        
        # ======= MODE STATIQUE : UTILISÉ UNIQUEMENT SI INTER INACTIF =======
        else:
            # On vérifie les DEUX premières cartes contre les règles statiques
            for card_in_trigger in prediction_trigger_cards:
                if card_in_trigger in STATIC_RULES:
                    predicted_suit = STATIC_RULES[card_in_trigger]
                    trigger_used = card_in_trigger
                    is_inter_prediction = False
                    rule_index = 0
                    logger.info(f"🔮 STATIQUE: {trigger_used} → {predicted_suit}")
                    break
            
            if not predicted_suit:
                logger.debug(f"⚠️ Aucune règle statique ne match pour les cartes {prediction_trigger_cards}")
                return False, None, None, None

        # ✅ Si une prédiction est trouvée (INTER ou STATIQUE), vérifier cooldown et lancer
        if predicted_suit:
            if self.last_prediction_time and time.time() < self.last_prediction_time + self.prediction_cooldown:
                logger.debug("⏸️ Cooldown prédiction actif")
                return False, None, None, None

            self._last_rule_index = rule_index
            self._last_trigger_used = trigger_used
            return True, game_number, predicted_suit, is_inter_prediction

        return False, None, None, None

    def prepare_prediction_text(self, game_number_source: int, predicted_costume: str) -> str:
        target_game = game_number_source + 2
        # Remplacement du costume par la carte de valeur dans le message de prédiction (A, K, Q, J)
        predicted_value = SUIT_TO_VALUE_MAP.get(predicted_costume, predicted_costume)
        text = f"🔵{target_game}🔵:{predicted_value} statut :⏳"
        logger.info(f"📝 Prédiction formatée: Jeu {game_number_source} → {target_game}, Valeur: {predicted_value} (Déclencheur: {self._last_trigger_used})")
        return text


    def make_prediction(self, game_number_source: int, suit: str, message_id_bot: int, is_inter: bool = False, trigger_used: Optional[str] = None):
        target = game_number_source + 2
        txt = self.prepare_prediction_text(game_number_source, suit)
        
        # Obtenir le déclencheur utilisé (priorité au paramètre, puis au stockage, puis par défaut '?')
        if not trigger_used:
            trigger_used = self._last_trigger_used or '?'
        
        self.predictions[target] = {
            'predicted_costume': suit, 
            'status': 'pending', 
            'predicted_from': game_number_source, 
            'predicted_from_trigger': trigger_used,
            'message_text': txt, 
            'message_id': message_id_bot, 
            'is_inter': is_inter,
            'rule_index': self._last_rule_index,
            'timestamp': time.time()
        }
        
        self.last_prediction_time = time.time()
        self.last_predicted_game_number = game_number_source
        self.consecutive_fails = 0
        self._save_all_data()

    # --- VERIFICATION LOGIQUE ---

    def verify_prediction(self, message: str) -> Optional[Dict]:
        """Vérifie une prédiction (message normal). Attend la fin du chrono."""
        if '⏰' in message or '⏱️' in message:
            logger.debug("⏳ Vérification ignorée car message en cours (indicateur de temps)")
            return None
        return self._verify_prediction_common(message, is_edited=False)

    def verify_prediction_from_edit(self, message: str) -> Optional[Dict]:
        """Vérifie une prédiction (message édité). Attend la fin du chrono."""
        if '⏰' in message or '⏱️' in message:
            logger.debug("⏳ Vérification ignorée car message édité en cours (indicateur de temps)")
            return None
        return self._verify_prediction_common(message, is_edited=True)

    def check_value_in_first_parentheses(self, message: str, predicted_value: str) -> bool:
        """Vérifie si la valeur prédite (A, K, Q, J) est présente dans le PREMIER groupe."""
        # On normalise le message
        normalized_message = message.replace("❤️", "♥️")
        
        # Extraction du premier groupe entre parenthèses (avec ou sans préfixe numérique)
        match = re.search(r'(?:\d+)?\(([^)]*)\)', normalized_message)
        if not match:
            return False
        
        first_group = match.group(1).upper()
        logger.debug(f"🔍 Recherche de la VALEUR '{predicted_value}' dans le premier groupe : {first_group}")
        
        # On cherche la valeur exacte
        if predicted_value in first_group:
            logger.info(f"✅ SUCCÈS: Valeur {predicted_value} trouvée dans le premier groupe")
            return True
            
        return False

    def _verify_prediction_common(self, message: str, is_edited: bool = False) -> Optional[Dict]:
        """Logique de vérification commune - UNIQUEMENT pour messages finalisés."""
        self.check_and_send_reports()
        
        # NORMALISATION : Convertir ❤️ en ♥️ pour la comparaison
        message = message.replace("❤️", "♥️")
        
        game_num = self.extract_game_number(message)
        if not game_num:
            return None

        # Collecte de données pour INTER (même si on n'a pas prédit ce jeu spécifiquement)
        # On ne collecte QUE si le message est finalisé
        if self.is_message_finalized(message):
            self.collect_inter_data(game_num, message)

        if not self.predictions:
            return None
            
        # --- VÉRIFICATION SÉQUENTIELLE (N, N+1, N+2) ---
        # On trie pour traiter les plus anciennes d'abord
        for predicted_game in sorted(self.predictions.keys()):
            prediction = self.predictions[predicted_game]
            if prediction.get('status') != 'pending':
                continue

            predicted_suit = prediction.get('predicted_costume')
            predicted_val = SUIT_TO_VALUE_MAP.get(predicted_suit, predicted_suit)
            
            found = False
            status_symbol = None
            
            # Vérifier si le jeu actuel correspond à une prédiction (N, N+1, N+2)
            for offset in [0, 1, 2]:
                check_game_num = predicted_game + offset
                if game_num == check_game_num:
                    # ✅ RÈGLE : Le message du jeu actuel DOIT être finalisé avant de vérifier
                    if not self.is_message_finalized(message):
                        logger.debug(f"⏳ Jeu {game_num} match prédiction {predicted_game}+{offset} mais message non finalisé. Report.")
                        return None

                    value_found = self.check_value_in_first_parentheses(message, predicted_val)
                    if value_found:
                        prediction['status'] = 'won'
                        status_symbol = SYMBOL_MAP.get(offset, f'✅{offset}')
                        found = True
                        logger.info(f"✅ Prédiction GAGNÉE à {offset} (Jeu source: {game_num})")
                    elif offset == 2: # Échec final au 3ème jeu (N+2)
                        prediction['status'] = 'lost'
                        status_symbol = SYMBOL_MAP.get('lost', '❌')
                        found = True
                        logger.info(f"❌ Prédiction PERDUE définitivement (Jeu source: {game_num})")
                    break

            # Sécurité : si on a dépassé le numéro attendu
            if not found and game_num > predicted_game + 2:
                # On vérifie quand même si le message qui dépasse est finalisé pour être sûr du "lost"
                if self.is_message_finalized(message):
                    prediction['status'] = 'lost'
                    status_symbol = SYMBOL_MAP.get('lost', '❌')
                    found = True

            if found:
                # Format du message final avec le bon statut (✅0️⃣, ✅1️⃣, ✅2️⃣ ou ❌)
                prediction['message_text'] = f"🔵{predicted_game}🔵:{predicted_val} statut :{status_symbol}"
                
                if prediction['status'] == 'won':
                    self.consecutive_fails = 0
                else:
                    self.consecutive_fails += 1
                    # Appliquer la quarantaine si c'est une prédiction INTER
                    if prediction.get('is_inter'):
                        self._apply_quarantine(prediction)

                self._save_all_data()
                return {
                    'type': 'edit_message',
                    'message_id_to_edit': prediction.get('message_id'),
                    'new_text': prediction['message_text']
                }

        return None


    def reset_automatic_predictions(self) -> Dict[str, int]:
        """
        Réinitialise les prédictions automatiques (non-INTER) sans toucher aux données Collect ni INTER.
        Retourne le nombre de prédictions supprimées.
        """
        inter_predictions = {}
        non_inter_count = 0
        
        inter_game_numbers = set()
        for game_num, prediction in self.predictions.items():
            if prediction.get('is_inter', False):
                inter_predictions[game_num] = prediction
                inter_game_numbers.add(game_num)
            else:
                non_inter_count += 1
        
        self.predictions = inter_predictions
        
        inter_message_ids = {pred.get('message_id') for pred in inter_predictions.values() if pred.get('message_id')}
        new_pending_edits = {}
        removed_pending = 0
        for msg_id, edit_data in self.pending_edits.items():
            game_num = edit_data.get('game_number')
            if game_num in inter_game_numbers or msg_id in inter_message_ids:
                new_pending_edits[msg_id] = edit_data
            else:
                removed_pending += 1
        self.pending_edits = new_pending_edits
        
        self.last_prediction_time = 0
        self.last_predicted_game_number = 0
        self.consecutive_fails = 0
        self.single_trigger_until = 0
        
        self._save_all_data()
        
        logger.info(f"🔄 Reset manuel: {non_inter_count} prédictions auto supprimées, {len(inter_predictions)} INTER conservées")
        
        return {
            'removed': non_inter_count,
            'kept_inter': len(inter_predictions),
            'removed_pending': removed_pending
        }

# Global instance
card_predictor = CardPredictor()
