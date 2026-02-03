"""Enhanced webhook integrations for Slack, Discord, and other platforms."""

import json
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum


class WebhookPlatform(Enum):
    """Supported webhook platforms."""
    SLACK = "slack"
    DISCORD = "discord"
    GENERIC = "generic"
    TEAMS = "teams"


@dataclass
class WebhookMessage:
    """Structured webhook message."""
    title: str
    content: str
    platform: WebhookPlatform
    color: Optional[str] = None
    fields: Optional[List[Dict[str, str]]] = None
    timestamp: Optional[str] = None
    footer: Optional[str] = None
    thumbnail_url: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class WebhookIntegrations:
    """Enhanced webhook integration manager."""
    
    # Color scheme for different message types
    COLORS = {
        'success': '#10B981',   # Green
        'warning': '#F59E0B',   # Yellow  
        'error': '#EF4444',     # Red
        'info': '#3B82F6',      # Blue
        'research': '#8B5CF6',  # Purple
        'alert': '#F59E0B'      # Orange
    }
    
    def __init__(self, default_timeout: int = 30):
        """Initialize webhook integrations.
        
        Args:
            default_timeout: Default request timeout in seconds
        """
        self.default_timeout = default_timeout
    
    def detect_platform(self, webhook_url: str) -> WebhookPlatform:
        """Detect platform from webhook URL.
        
        Args:
            webhook_url: The webhook URL
            
        Returns:
            Detected platform type
        """
        if 'hooks.slack.com' in webhook_url:
            return WebhookPlatform.SLACK
        elif 'discord.com/api/webhooks' in webhook_url:
            return WebhookPlatform.DISCORD
        elif 'outlook.office.com' in webhook_url:
            return WebhookPlatform.TEAMS
        else:
            return WebhookPlatform.GENERIC
    
    def send_message(self, webhook_url: str, message: WebhookMessage, timeout: Optional[int] = None) -> bool:
        """Send message to webhook.
        
        Args:
            webhook_url: Target webhook URL
            message: Message to send
            timeout: Request timeout (uses default if None)
            
        Returns:
            True if message sent successfully
        """
        if not webhook_url:
            return False
            
        timeout = timeout or self.default_timeout
        
        # Auto-detect platform if not specified
        if message.platform == WebhookPlatform.GENERIC:
            message.platform = self.detect_platform(webhook_url)
        
        try:
            payload = self._build_payload(message)
            
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            response.raise_for_status()
            return True
            
        except Exception as e:
            print(f"Failed to send webhook message: {e}")
            return False
    
    def _build_payload(self, message: WebhookMessage) -> Dict[str, Any]:
        """Build platform-specific payload.
        
        Args:
            message: Message to format
            
        Returns:
            Platform-specific payload
        """
        if message.platform == WebhookPlatform.SLACK:
            return self._build_slack_payload(message)
        elif message.platform == WebhookPlatform.DISCORD:
            return self._build_discord_payload(message)
        elif message.platform == WebhookPlatform.TEAMS:
            return self._build_teams_payload(message)
        else:
            return self._build_generic_payload(message)
    
    def _build_slack_payload(self, message: WebhookMessage) -> Dict[str, Any]:
        """Build Slack-specific payload."""
        payload = {
            "text": message.title,
            "attachments": [
                {
                    "color": message.color or self.COLORS['info'],
                    "text": message.content,
                    "ts": int(datetime.fromisoformat(message.timestamp).timestamp()) if message.timestamp else None
                }
            ]
        }
        
        # Add fields if provided
        if message.fields:
            payload["attachments"][0]["fields"] = [
                {
                    "title": field["name"],
                    "value": field["value"],
                    "short": field.get("inline", False)
                }
                for field in message.fields
            ]
        
        # Add footer
        if message.footer:
            payload["attachments"][0]["footer"] = message.footer
        
        # Add thumbnail
        if message.thumbnail_url:
            payload["attachments"][0]["thumb_url"] = message.thumbnail_url
        
        return payload
    
    def _build_discord_payload(self, message: WebhookMessage) -> Dict[str, Any]:
        """Build Discord-specific payload."""
        embed = {
            "title": message.title,
            "description": message.content,
            "color": int(message.color.replace('#', ''), 16) if message.color else int(self.COLORS['info'].replace('#', ''), 16),
            "timestamp": message.timestamp
        }
        
        # Add fields if provided
        if message.fields:
            embed["fields"] = [
                {
                    "name": field["name"],
                    "value": field["value"],
                    "inline": field.get("inline", False)
                }
                for field in message.fields
            ]
        
        # Add footer
        if message.footer:
            embed["footer"] = {"text": message.footer}
        
        # Add thumbnail
        if message.thumbnail_url:
            embed["thumbnail"] = {"url": message.thumbnail_url}
        
        return {"embeds": [embed]}
    
    def _build_teams_payload(self, message: WebhookMessage) -> Dict[str, Any]:
        """Build Microsoft Teams-specific payload."""
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": message.color or self.COLORS['info'],
            "summary": message.title,
            "sections": [
                {
                    "activityTitle": message.title,
                    "activityText": message.content,
                    "markdown": True
                }
            ]
        }
        
        # Add fields as facts
        if message.fields:
            payload["sections"][0]["facts"] = [
                {
                    "name": field["name"],
                    "value": field["value"]
                }
                for field in message.fields
            ]
        
        return payload
    
    def _build_generic_payload(self, message: WebhookMessage) -> Dict[str, Any]:
        """Build generic JSON payload."""
        return {
            "title": message.title,
            "content": message.content,
            "timestamp": message.timestamp,
            "color": message.color,
            "fields": message.fields,
            "footer": message.footer,
            "thumbnail_url": message.thumbnail_url
        }
    
    # Convenience methods for different message types
    
    def send_research_notification(self, webhook_url: str, research_title: str, 
                                   tickers: List[str], filename: str, summary: str = None) -> bool:
        """Send research completion notification.
        
        Args:
            webhook_url: Target webhook URL
            research_title: Title of the research
            tickers: List of tickers analyzed
            filename: Research filename
            summary: Optional summary
            
        Returns:
            True if sent successfully
        """
        fields = [
            {"name": "📊 Tickers", "value": ", ".join(tickers), "inline": True},
            {"name": "📄 File", "value": filename, "inline": True}
        ]
        
        if summary:
            fields.append({"name": "📝 Summary", "value": summary, "inline": False})
        
        message = WebhookMessage(
            title=f"🔍 New Research: {research_title}",
            content="Fresh research analysis completed!",
            platform=WebhookPlatform.GENERIC,
            color=self.COLORS['research'],
            fields=fields,
            footer="Supply Chain Intel"
        )
        
        return self.send_message(webhook_url, message)
    
    def send_price_alert(self, webhook_url: str, ticker: str, current_price: float,
                        alert_price: float, change_percent: float) -> bool:
        """Send price alert notification.
        
        Args:
            webhook_url: Target webhook URL
            ticker: Stock ticker
            current_price: Current stock price
            alert_price: Alert trigger price
            change_percent: Price change percentage
            
        Returns:
            True if sent successfully
        """
        direction = "📈" if change_percent > 0 else "📉"
        color = self.COLORS['success'] if change_percent > 0 else self.COLORS['error']
        
        fields = [
            {"name": "💰 Current Price", "value": f"${current_price:.2f}", "inline": True},
            {"name": "🎯 Alert Price", "value": f"${alert_price:.2f}", "inline": True},
            {"name": "📊 Change", "value": f"{change_percent:+.2f}%", "inline": True}
        ]
        
        message = WebhookMessage(
            title=f"{direction} Price Alert: {ticker}",
            content=f"Price alert triggered for {ticker}",
            platform=WebhookPlatform.GENERIC,
            color=color,
            fields=fields,
            footer="Supply Chain Intel Alerts"
        )
        
        return self.send_message(webhook_url, message)
    
    def send_watchlist_update(self, webhook_url: str, added_tickers: List[str] = None,
                             removed_tickers: List[str] = None, notes: str = None) -> bool:
        """Send watchlist update notification.
        
        Args:
            webhook_url: Target webhook URL
            added_tickers: List of added tickers
            removed_tickers: List of removed tickers
            notes: Optional update notes
            
        Returns:
            True if sent successfully
        """
        content_parts = []
        fields = []
        
        if added_tickers:
            content_parts.append(f"Added: {', '.join(added_tickers)}")
            fields.append({"name": "➕ Added", "value": ", ".join(added_tickers), "inline": True})
        
        if removed_tickers:
            content_parts.append(f"Removed: {', '.join(removed_tickers)}")
            fields.append({"name": "➖ Removed", "value": ", ".join(removed_tickers), "inline": True})
        
        if notes:
            fields.append({"name": "📝 Notes", "value": notes, "inline": False})
        
        content = " | ".join(content_parts) if content_parts else "Watchlist updated"
        
        message = WebhookMessage(
            title="📋 Watchlist Update",
            content=content,
            platform=WebhookPlatform.GENERIC,
            color=self.COLORS['info'],
            fields=fields,
            footer="Supply Chain Intel"
        )
        
        return self.send_message(webhook_url, message)
    
    def send_error_notification(self, webhook_url: str, error_title: str, 
                               error_message: str, context: Dict[str, str] = None) -> bool:
        """Send error notification.
        
        Args:
            webhook_url: Target webhook URL
            error_title: Error title
            error_message: Error message
            context: Optional context information
            
        Returns:
            True if sent successfully
        """
        fields = [{"name": "⚠️ Error", "value": error_message, "inline": False}]
        
        if context:
            for key, value in context.items():
                fields.append({"name": key, "value": str(value), "inline": True})
        
        message = WebhookMessage(
            title=f"🚨 Error: {error_title}",
            content="An error occurred in Supply Chain Intel",
            platform=WebhookPlatform.GENERIC,
            color=self.COLORS['error'],
            fields=fields,
            footer="Supply Chain Intel Error Monitor"
        )
        
        return self.send_message(webhook_url, message)
    
    def send_daily_digest(self, webhook_url: str, stats: Dict[str, Any]) -> bool:
        """Send daily digest notification.
        
        Args:
            webhook_url: Target webhook URL
            stats: Daily statistics
            
        Returns:
            True if sent successfully
        """
        fields = []
        
        if 'research_count' in stats:
            fields.append({"name": "📄 Research Documents", "value": str(stats['research_count']), "inline": True})
        
        if 'watchlist_changes' in stats:
            fields.append({"name": "📋 Watchlist Changes", "value": str(stats['watchlist_changes']), "inline": True})
        
        if 'price_alerts' in stats:
            fields.append({"name": "🚨 Price Alerts", "value": str(stats['price_alerts']), "inline": True})
        
        if 'top_themes' in stats and stats['top_themes']:
            top_themes = ", ".join(stats['top_themes'][:3])
            fields.append({"name": "🎯 Top Themes", "value": top_themes, "inline": False})
        
        message = WebhookMessage(
            title="📊 Daily Supply Chain Intel Digest",
            content=f"Daily activity summary for {datetime.now().strftime('%Y-%m-%d')}",
            platform=WebhookPlatform.GENERIC,
            color=self.COLORS['info'],
            fields=fields,
            footer="Supply Chain Intel Daily Digest"
        )
        
        return self.send_message(webhook_url, message)
    
    def test_webhook(self, webhook_url: str) -> Dict[str, Any]:
        """Test webhook connectivity.
        
        Args:
            webhook_url: Webhook URL to test
            
        Returns:
            Test result information
        """
        platform = self.detect_platform(webhook_url)
        
        message = WebhookMessage(
            title="🔧 Webhook Test",
            content="This is a test message from Supply Chain Intel",
            platform=platform,
            color=self.COLORS['success'],
            fields=[
                {"name": "Platform", "value": platform.value.title(), "inline": True},
                {"name": "Status", "value": "Connected ✅", "inline": True}
            ],
            footer="Supply Chain Intel Test"
        )
        
        success = self.send_message(webhook_url, message)
        
        return {
            'success': success,
            'platform': platform.value,
            'timestamp': datetime.now().isoformat(),
            'url': webhook_url[:50] + '...' if len(webhook_url) > 50 else webhook_url
        }