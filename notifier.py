import requests
import json
import logging
import time
from typing import Dict, Any, Optional
import config  # Import config here to avoid circular import issues if possible

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Notifier")

def send_telegram(chat_id: str, message: str, bot_token: str = None) -> bool:
    """
    Send Telegram message to a specific user.
    Uses default bot token if no custom token provided.
    """
    token = bot_token if bot_token else config.TELEGRAM_BOT_TOKEN
    
    if not token or not chat_id:
        return False
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    
    try:
        resp = requests.post(url, json=payload, timeout=5)
        return resp.status_code == 200
    except Exception as e:
        logger.error(f"Telegram Fail: {e}")
        return False

def send_discord(webhook_url: str, message: str) -> bool:
    if not webhook_url: return False
    try:
        requests.post(webhook_url, json={"content": message}, timeout=5)
        return True
    except Exception as e:
        logger.error(f"Discord Fail: {e}")
        return False

def send_webhook(url: str, event_data: Dict[str, Any]) -> bool:
    """
    SaaS Feature: Send raw JSON payload to user's system.
    """
    if not url: return False
    try:
        # Add server timestamp for synchronization
        event_data["server_timestamp"] = int(time.time())
        requests.post(url, json=event_data, timeout=3, headers={"Content-Type": "application/json"})
        return True
    except Exception as e:
        logger.error(f"Webhook Fail: {e}")
        return False

def dispatch_alert(user_settings: dict, message: str, event_data: Dict[str, Any]) -> None:
    """
    The Router: Decides where to send the alert based on user settings.
    """
    if not user_settings:
        return

    # 1. Telegram Channel
    tg_settings = user_settings.get("telegram")
    if tg_settings and isinstance(tg_settings, dict):
        chat_id = tg_settings.get("chat_id")
        custom_token = tg_settings.get("bot_token") 
        if chat_id:
            send_telegram(chat_id, message, custom_token)

    # 2. Discord Webhook
    discord_url = user_settings.get("discord_webhook")
    if discord_url:
        send_discord(discord_url, message)

    # 3. Custom Webhook (Algo-Trading Ready)
    webhook_url = user_settings.get("webhook_url")
    if webhook_url:
        send_webhook(webhook_url, event_data)