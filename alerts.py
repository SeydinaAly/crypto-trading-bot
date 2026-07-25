import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import (
    ALERT_TYPE, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    DISCORD_WEBHOOK, EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENT
)
from logger import logger
from datetime import datetime

class AlertManager:
    """Manage alerts across multiple platforms"""
    
    def __init__(self):
        self.alert_type = ALERT_TYPE
        self.sent_alerts = []
    
    def send_alert(self, title, message, alert_type="info"):
        """
        Send alert to configured channels
        
        alert_type: 'info', 'warning', 'error', 'trade'
        """
        formatted_message = self._format_message(title, message, alert_type)
        
        if self.alert_type in ["telegram", "all"]:
            self._send_telegram(formatted_message)
        
        if self.alert_type in ["discord", "all"]:
            self._send_discord(formatted_message, alert_type)
        
        if self.alert_type in ["email", "all"]:
            self._send_email(title, formatted_message)
        
        self.sent_alerts.append({
            "timestamp": datetime.now(),
            "title": title,
            "message": message,
            "type": alert_type
        })
        
        logger.info(f"📢 Alert sent: {title}")
    
    def _format_message(self, title, message, alert_type):
        """Format message with emoji based on type"""
        emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "trade": "💰"
        }.get(alert_type, "📢")
        
        return f"{emoji} **{title}**\n{message}\n\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    def _send_telegram(self, message):
        """Send alert via Telegram"""
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            logger.warning("Telegram config missing")
            return
        
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "Markdown"
            }
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code == 200:
                logger.debug("✅ Telegram alert sent")
            else:
                logger.error(f"Telegram error: {response.text}")
        except Exception as e:
            logger.error(f"Telegram failed: {str(e)}")
    
    def _send_discord(self, message, alert_type="info"):
        """Send alert via Discord"""
        if not DISCORD_WEBHOOK:
            logger.warning("Discord config missing")
            return
        
        try:
            colors = {
                "info": 3447003,      # Blue
                "warning": 16776960,  # Yellow
                "error": 15158332,    # Red
                "trade": 65280        # Green
            }
            
            payload = {
                "embeds": [{
                    "title": message.split('\n')[0],
                    "description": '\n'.join(message.split('\n')[1:]),
                    "color": colors.get(alert_type, 3447003)
                }]
            }
            response = requests.post(DISCORD_WEBHOOK, json=payload, timeout=5)
            if response.status_code == 204:
                logger.debug("✅ Discord alert sent")
            else:
                logger.error(f"Discord error: {response.text}")
        except Exception as e:
            logger.error(f"Discord failed: {str(e)}")
    
    def _send_email(self, title, message):
        """Send alert via Email"""
        if not EMAIL_SENDER or not EMAIL_PASSWORD or not EMAIL_RECIPIENT:
            logger.warning("Email config missing")
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = EMAIL_SENDER
            msg['To'] = EMAIL_RECIPIENT
            msg['Subject'] = f"🤖 Crypto Bot: {title}"
            
            body = message.replace('**', '')
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            logger.debug("✅ Email alert sent")
        except Exception as e:
            logger.error(f"Email failed: {str(e)}")
    
    def get_alert_history(self, limit=10):
        """Get recent alert history"""
        return self.sent_alerts[-limit:]

# Global alert manager instance
alert_manager = AlertManager()

if __name__ == "__main__":
    manager = AlertManager()
    manager.send_alert("Test Alert", "This is a test message", "info")
    manager.send_alert("Trade Alert", "Bought 1 ETH @ $2000", "trade")
    manager.send_alert("Warning", "Price dropped 5%", "warning")
