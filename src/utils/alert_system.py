"""Advanced alert system for price monitoring, thesis changes, and research notifications."""

import json
import smtplib
import requests
from datetime import datetime, timedelta, time
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field, asdict
try:
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
    from email.mime.base import MimeBase
    from email import encoders
except ImportError:
    # Python 3.14+ compatibility - class names are MIME* (uppercase)
    from email.mime.text import MIMEText as MimeText
    from email.mime.multipart import MIMEMultipart as MimeMultipart
    from email.mime.base import MIMEBase as MimeBase
    from email import encoders
import threading
import time as time_module

# Import enhanced webhook integrations
from .webhook_integrations import WebhookIntegrations, WebhookMessage, WebhookPlatform
from enum import Enum

from .finnhub_client import FinnhubClient
from .saved_research_store import SavedResearchStore
from .historical_tracker import HistoricalTracker


class AlertType(Enum):
    """Types of alerts supported by the system."""
    PRICE_ALERT = "price_alert"
    THESIS_CHANGE = "thesis_change"  
    DAILY_DIGEST = "daily_digest"
    RESEARCH_UPDATE = "research_update"
    PERFORMANCE_ALERT = "performance_alert"


class AlertTrigger(Enum):
    """Alert trigger conditions."""
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    PRICE_CHANGE_PCT = "price_change_pct"
    VOLUME_SPIKE = "volume_spike"
    THESIS_DOWNGRADE = "thesis_downgrade"
    THESIS_UPGRADE = "thesis_upgrade"
    NEW_RESEARCH = "new_research"
    DAILY_SUMMARY = "daily_summary"


@dataclass
class AlertRule:
    """Configuration for a specific alert rule."""
    id: str
    name: str
    alert_type: AlertType
    trigger: AlertTrigger
    condition_value: float
    ticker: Optional[str] = None
    theme: Optional[str] = None
    enabled: bool = True
    email_recipients: List[str] = field(default_factory=list)
    webhook_url: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_triggered: Optional[str] = None
    trigger_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            'alert_type': self.alert_type.value if isinstance(self.alert_type, AlertType) else self.alert_type,
            'trigger': self.trigger.value if isinstance(self.trigger, AlertTrigger) else self.trigger
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AlertRule':
        """Create AlertRule from dictionary data."""
        # Convert enum strings back to enums
        if 'alert_type' in data and isinstance(data['alert_type'], str):
            data['alert_type'] = AlertType(data['alert_type'])
        if 'trigger' in data and isinstance(data['trigger'], str):
            data['trigger'] = AlertTrigger(data['trigger'])
        
        return cls(**data)


@dataclass
class AlertEvent:
    """Record of a triggered alert."""
    alert_rule_id: str
    timestamp: str
    trigger_reason: str
    current_value: float
    threshold_value: float
    ticker: Optional[str] = None
    additional_data: Dict = field(default_factory=dict)
    delivered: bool = False
    delivery_methods: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AlertEvent':
        return cls(**data)


@dataclass
class EmailConfig:
    """Email configuration for alert delivery."""
    smtp_server: str
    smtp_port: int
    username: str
    password: str
    use_tls: bool = True
    sender_name: str = "Supply Chain Intel"
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EmailConfig':
        return cls(**data)


class AlertNotificationEngine:
    """Handles delivery of alerts via email, webhooks, etc."""
    
    def __init__(self, email_config: Optional[EmailConfig] = None):
        """Initialize notification engine.
        
        Args:
            email_config: Email configuration for email alerts
        """
        self.email_config = email_config
        self.webhook_integrations = WebhookIntegrations()
    
    def send_email_alert(self, alert_rule: AlertRule, alert_event: AlertEvent, 
                        custom_message: str = None) -> bool:
        """Send alert via email.
        
        Args:
            alert_rule: The alert rule that triggered
            alert_event: The alert event details
            custom_message: Optional custom message content
            
        Returns:
            True if email sent successfully
        """
        if not self.email_config or not alert_rule.email_recipients:
            return False
        
        try:
            # Create message
            msg = MimeMultipart()
            msg['From'] = f"{self.email_config.sender_name} <{self.email_config.username}>"
            msg['To'] = ", ".join(alert_rule.email_recipients)
            
            # Create subject based on alert type
            if alert_rule.ticker:
                subject = f"Supply Chain Alert: {alert_rule.ticker} - {alert_rule.name}"
            else:
                subject = f"Supply Chain Alert: {alert_rule.name}"
            msg['Subject'] = subject
            
            # Create email body
            if custom_message:
                body = custom_message
            else:
                body = self._generate_alert_email_body(alert_rule, alert_event)
            
            msg.attach(MimeText(body, 'html'))
            
            # Send email
            server = smtplib.SMTP(self.email_config.smtp_server, self.email_config.smtp_port)
            if self.email_config.use_tls:
                server.starttls()
            server.login(self.email_config.username, self.email_config.password)
            
            text = msg.as_string()
            server.sendmail(self.email_config.username, alert_rule.email_recipients, text)
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"Failed to send email alert: {e}")
            return False
    
    def send_webhook_alert(self, alert_rule: AlertRule, alert_event: AlertEvent) -> bool:
        """Send alert via enhanced webhook integrations.
        
        Args:
            alert_rule: The alert rule that triggered
            alert_event: The alert event details
            
        Returns:
            True if webhook sent successfully
        """
        if not alert_rule.webhook_url:
            return False
        
        try:
            # Use enhanced webhook integrations for better formatting
            if alert_rule.alert_type == AlertType.PRICE and alert_event.ticker:
                # Price alert - use specialized price alert method
                return self.webhook_integrations.send_price_alert(
                    webhook_url=alert_rule.webhook_url,
                    ticker=alert_event.ticker,
                    current_price=alert_event.current_value,
                    alert_price=alert_event.threshold_value,
                    change_percent=((alert_event.current_value - alert_event.threshold_value) / alert_event.threshold_value) * 100
                )
            else:
                # Generic alert - use structured message
                message = WebhookMessage(
                    title=f"🚨 Alert: {alert_rule.name}",
                    content=alert_event.trigger_reason,
                    platform=WebhookPlatform.GENERIC,
                    color=self.webhook_integrations.COLORS['alert'],
                    fields=[
                        {"name": "Type", "value": alert_rule.alert_type.value.title(), "inline": True},
                        {"name": "Trigger", "value": alert_rule.trigger.value.title(), "inline": True},
                        {"name": "Current Value", "value": str(alert_event.current_value), "inline": True},
                        {"name": "Threshold", "value": str(alert_event.threshold_value), "inline": True}
                    ] + ([{"name": "Ticker", "value": alert_event.ticker, "inline": True}] if alert_event.ticker else []),
                    footer="Supply Chain Intel Alerts"
                )
                
                return self.webhook_integrations.send_message(alert_rule.webhook_url, message)
            
        except Exception as e:
            print(f"Failed to send enhanced webhook alert: {e}")
            # Fallback to basic webhook
            return self._send_basic_webhook_alert(alert_rule, alert_event)
    
    def _send_basic_webhook_alert(self, alert_rule: AlertRule, alert_event: AlertEvent) -> bool:
        """Fallback basic webhook alert method."""
        try:
            payload = {
                'alert_rule': {
                    'id': alert_rule.id,
                    'name': alert_rule.name,
                    'type': alert_rule.alert_type.value,
                    'trigger': alert_rule.trigger.value,
                    'ticker': alert_rule.ticker,
                    'theme': alert_rule.theme
                },
                'event': alert_event.to_dict(),
                'timestamp': datetime.now().isoformat()
            }
            
            response = requests.post(
                alert_rule.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Failed to send basic webhook alert: {e}")
            return False
    
    def _generate_alert_email_body(self, alert_rule: AlertRule, alert_event: AlertEvent) -> str:
        """Generate HTML email body for alert."""
        
        # Color coding based on alert type
        color_map = {
            AlertType.PRICE_ALERT: "#FF6B35",
            AlertType.THESIS_CHANGE: "#4ECDC4", 
            AlertType.DAILY_DIGEST: "#45B7D1",
            AlertType.RESEARCH_UPDATE: "#96CEB4",
            AlertType.PERFORMANCE_ALERT: "#FECA57"
        }
        
        color = color_map.get(alert_rule.alert_type, "#555555")
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                
                <!-- Header -->
                <div style="background-color: {color}; color: white; padding: 20px; text-align: center;">
                    <h1 style="margin: 0; font-size: 24px;">Supply Chain Intel Alert</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">{alert_rule.name}</p>
                </div>
                
                <!-- Alert Details -->
                <div style="padding: 30px;">
                    <h2 style="color: #333; margin-top: 0;">Alert Triggered</h2>
                    
                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                        <tr style="border-bottom: 1px solid #eee;">
                            <td style="padding: 12px; font-weight: bold; color: #666;">Ticker:</td>
                            <td style="padding: 12px; color: #333;">{alert_event.ticker or 'N/A'}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #eee;">
                            <td style="padding: 12px; font-weight: bold; color: #666;">Trigger:</td>
                            <td style="padding: 12px; color: #333;">{alert_event.trigger_reason}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #eee;">
                            <td style="padding: 12px; font-weight: bold; color: #666;">Current Value:</td>
                            <td style="padding: 12px; color: #333; font-weight: bold;">{alert_event.current_value}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #eee;">
                            <td style="padding: 12px; font-weight: bold; color: #666;">Threshold:</td>
                            <td style="padding: 12px; color: #333;">{alert_event.threshold_value}</td>
                        </tr>
                        <tr>
                            <td style="padding: 12px; font-weight: bold; color: #666;">Time:</td>
                            <td style="padding: 12px; color: #333;">{alert_event.timestamp}</td>
                        </tr>
                    </table>
                    
                    {self._generate_additional_context(alert_rule, alert_event)}
                </div>
                
                <!-- Footer -->
                <div style="background-color: #f8f9fa; padding: 20px; text-align: center; border-top: 1px solid #eee;">
                    <p style="margin: 0; color: #666; font-size: 14px;">
                        Supply Chain Intelligence Platform<br>
                        <small>Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_additional_context(self, alert_rule: AlertRule, alert_event: AlertEvent) -> str:
        """Generate additional context based on alert type."""
        if alert_rule.alert_type == AlertType.DAILY_DIGEST:
            return self._generate_daily_digest_context(alert_event)
        elif alert_rule.alert_type == AlertType.THESIS_CHANGE:
            return self._generate_thesis_change_context(alert_event)
        else:
            return ""
    
    def _generate_daily_digest_context(self, alert_event: AlertEvent) -> str:
        """Generate context for daily digest alerts."""
        data = alert_event.additional_data
        
        html = """
        <div style="margin-top: 20px; padding: 20px; background-color: #f8f9fa; border-radius: 6px;">
            <h3 style="margin-top: 0; color: #333;">Daily Summary</h3>
        """
        
        if 'watchlist_updates' in data:
            html += f"<p><strong>Watchlist Updates:</strong> {data['watchlist_updates']}</p>"
        
        if 'new_research' in data:
            html += f"<p><strong>New Research:</strong> {data['new_research']}</p>"
        
        if 'price_changes' in data:
            html += f"<p><strong>Significant Price Changes:</strong> {data['price_changes']}</p>"
        
        html += "</div>"
        return html
    
    def _generate_thesis_change_context(self, alert_event: AlertEvent) -> str:
        """Generate context for thesis change alerts."""
        data = alert_event.additional_data
        
        html = """
        <div style="margin-top: 20px; padding: 20px; background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 6px;">
            <h3 style="margin-top: 0; color: #856404;">Investment Thesis Update</h3>
        """
        
        if 'old_rating' in data and 'new_rating' in data:
            html += f"<p><strong>Rating Change:</strong> {data['old_rating']} → {data['new_rating']}</p>"
        
        if 'confidence_change' in data:
            html += f"<p><strong>Confidence Level:</strong> {data['confidence_change']}</p>"
        
        if 'analysis' in data:
            html += f"<p><strong>Analysis:</strong> {data['analysis']}</p>"
        
        html += "</div>"
        return html


class AlertManager:
    """Main alert management system."""
    
    def __init__(self, data_dir: Path, finnhub_client: FinnhubClient = None):
        """Initialize alert manager.
        
        Args:
            data_dir: Directory for storing alert data
            finnhub_client: Finnhub client for price data
        """
        self.data_dir = data_dir
        self.alerts_dir = data_dir / 'alerts'
        self.alerts_dir.mkdir(parents=True, exist_ok=True)
        
        self.rules_file = self.alerts_dir / 'alert_rules.json'
        self.events_file = self.alerts_dir / 'alert_events.json'
        self.config_file = self.alerts_dir / 'config.json'
        
        self.finnhub_client = finnhub_client or FinnhubClient()
        self.saved_research_store = SavedResearchStore(data_dir)
        self.historical_tracker = HistoricalTracker(data_dir)
        
        # Load configuration and rules
        self.email_config = self._load_email_config()
        self.notification_engine = AlertNotificationEngine(self.email_config)
        self.alert_rules: Dict[str, AlertRule] = self._load_alert_rules()
        self.alert_events: List[AlertEvent] = self._load_alert_events()
        
        # Background monitoring
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        
    def create_alert_rule(self, name: str, alert_type: AlertType, trigger: AlertTrigger,
                         condition_value: float, ticker: str = None, theme: str = None,
                         email_recipients: List[str] = None, webhook_url: str = None) -> AlertRule:
        """Create a new alert rule.
        
        Args:
            name: Human-readable name for the alert
            alert_type: Type of alert (price, thesis, etc.)
            trigger: Trigger condition 
            condition_value: Threshold value for trigger
            ticker: Optional ticker symbol to monitor
            theme: Optional theme to monitor
            email_recipients: Email addresses for notifications
            webhook_url: Webhook URL for notifications
            
        Returns:
            Created AlertRule object
        """
        rule_id = f"{alert_type.value}_{trigger.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        rule = AlertRule(
            id=rule_id,
            name=name,
            alert_type=alert_type,
            trigger=trigger,
            condition_value=condition_value,
            ticker=ticker,
            theme=theme,
            email_recipients=email_recipients or [],
            webhook_url=webhook_url
        )
        
        self.alert_rules[rule_id] = rule
        self._save_alert_rules()
        
        return rule
    
    def create_price_alert(self, ticker: str, trigger: AlertTrigger, 
                          price: float, emails: List[str] = None) -> AlertRule:
        """Convenience method to create price alerts.
        
        Args:
            ticker: Stock ticker to monitor
            trigger: Price trigger condition
            price: Target price
            emails: Email recipients
            
        Returns:
            Created AlertRule object
        """
        name = f"{ticker} {trigger.value.replace('_', ' ').title()} ${price:.2f}"
        
        return self.create_alert_rule(
            name=name,
            alert_type=AlertType.PRICE_ALERT,
            trigger=trigger,
            condition_value=price,
            ticker=ticker,
            email_recipients=emails
        )
    
    def create_daily_digest(self, emails: List[str], delivery_time: str = "09:00") -> AlertRule:
        """Create daily digest alert.
        
        Args:
            emails: Email recipients
            delivery_time: Time to send digest (HH:MM format)
            
        Returns:
            Created AlertRule object
        """
        return self.create_alert_rule(
            name=f"Daily Digest - {delivery_time}",
            alert_type=AlertType.DAILY_DIGEST,
            trigger=AlertTrigger.DAILY_SUMMARY,
            condition_value=float(delivery_time.replace(':', '')),  # Convert to numeric
            email_recipients=emails
        )
    
    def update_alert_rule(self, rule_id: str, **updates) -> bool:
        """Update an existing alert rule.
        
        Args:
            rule_id: ID of rule to update
            **updates: Fields to update
            
        Returns:
            True if updated successfully
        """
        if rule_id not in self.alert_rules:
            return False
        
        rule = self.alert_rules[rule_id]
        
        for key, value in updates.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
        
        self._save_alert_rules()
        return True
    
    def delete_alert_rule(self, rule_id: str) -> bool:
        """Delete an alert rule.
        
        Args:
            rule_id: ID of rule to delete
            
        Returns:
            True if deleted successfully
        """
        if rule_id in self.alert_rules:
            del self.alert_rules[rule_id]
            self._save_alert_rules()
            return True
        return False
    
    def get_alert_rules(self, enabled_only: bool = True) -> List[AlertRule]:
        """Get all alert rules.
        
        Args:
            enabled_only: Whether to return only enabled rules
            
        Returns:
            List of AlertRule objects
        """
        rules = list(self.alert_rules.values())
        
        if enabled_only:
            rules = [r for r in rules if r.enabled]
        
        return sorted(rules, key=lambda r: r.created_at, reverse=True)
    
    def start_monitoring(self, check_interval: int = 300) -> None:
        """Start background monitoring for alerts.
        
        Args:
            check_interval: Check interval in seconds (default 5 minutes)
        """
        if self._monitoring:
            return
        
        self._monitoring = True
        
        def monitor_loop():
            while self._monitoring:
                try:
                    self.check_all_alerts()
                    time_module.sleep(check_interval)
                except Exception as e:
                    print(f"Alert monitoring error: {e}")
                    time_module.sleep(60)  # Sleep 1 minute on error
        
        self._monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def stop_monitoring(self) -> None:
        """Stop background monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
    
    def check_all_alerts(self) -> List[AlertEvent]:
        """Check all enabled alert rules and trigger any that match.
        
        Returns:
            List of triggered AlertEvent objects
        """
        triggered_events = []
        
        for rule in self.get_alert_rules(enabled_only=True):
            try:
                events = self._check_alert_rule(rule)
                triggered_events.extend(events)
            except Exception as e:
                print(f"Error checking alert rule {rule.id}: {e}")
        
        if triggered_events:
            self._save_alert_events()
        
        return triggered_events
    
    def _check_alert_rule(self, rule: AlertRule) -> List[AlertEvent]:
        """Check a single alert rule and trigger if conditions are met.
        
        Args:
            rule: AlertRule to check
            
        Returns:
            List of triggered AlertEvent objects
        """
        events = []
        
        if rule.alert_type == AlertType.PRICE_ALERT:
            events = self._check_price_alert(rule)
        elif rule.alert_type == AlertType.DAILY_DIGEST:
            events = self._check_daily_digest(rule)
        elif rule.alert_type == AlertType.THESIS_CHANGE:
            events = self._check_thesis_change_alert(rule)
        elif rule.alert_type == AlertType.RESEARCH_UPDATE:
            events = self._check_research_update_alert(rule)
        elif rule.alert_type == AlertType.PERFORMANCE_ALERT:
            events = self._check_performance_alert(rule)
        
        # Process triggered events
        for event in events:
            self._process_alert_event(rule, event)
            self.alert_events.append(event)
        
        return events
    
    def _check_price_alert(self, rule: AlertRule) -> List[AlertEvent]:
        """Check price-based alert conditions."""
        if not rule.ticker:
            return []
        
        try:
            quote = self.finnhub_client.get_quote(rule.ticker)
            current_price = quote['c']  # Current price
            
            triggered = False
            reason = ""
            
            if rule.trigger == AlertTrigger.PRICE_ABOVE and current_price > rule.condition_value:
                triggered = True
                reason = f"Price rose above ${rule.condition_value:.2f}"
            elif rule.trigger == AlertTrigger.PRICE_BELOW and current_price < rule.condition_value:
                triggered = True
                reason = f"Price dropped below ${rule.condition_value:.2f}"
            elif rule.trigger == AlertTrigger.PRICE_CHANGE_PCT:
                # Calculate daily change percentage
                prev_close = quote['pc']  # Previous close
                change_pct = ((current_price - prev_close) / prev_close) * 100
                
                if abs(change_pct) > rule.condition_value:
                    triggered = True
                    direction = "rose" if change_pct > 0 else "fell"
                    reason = f"Price {direction} {abs(change_pct):.1f}% (threshold: {rule.condition_value:.1f}%)"
            elif rule.trigger == AlertTrigger.VOLUME_SPIKE:
                # Check if volume is significantly above average
                volume = quote.get('volume', 0)
                # Simplified volume spike detection (would need historical data for proper implementation)
                if volume > rule.condition_value:
                    triggered = True
                    reason = f"Volume spike: {volume:,} shares"
            
            if triggered:
                return [AlertEvent(
                    alert_rule_id=rule.id,
                    timestamp=datetime.now().isoformat(),
                    trigger_reason=reason,
                    current_value=current_price,
                    threshold_value=rule.condition_value,
                    ticker=rule.ticker,
                    additional_data=quote
                )]
            
        except Exception as e:
            print(f"Error checking price for {rule.ticker}: {e}")
        
        return []
    
    def _check_daily_digest(self, rule: AlertRule) -> List[AlertEvent]:
        """Check if it's time to send daily digest."""
        now = datetime.now()
        target_time = int(rule.condition_value)  # Stored as HHMM (e.g., 900 for 09:00)
        target_hour = target_time // 100
        target_minute = target_time % 100
        
        # Check if it's the right time (within 5-minute window) and not already sent today
        current_time = now.hour * 100 + now.minute
        time_match = abs(current_time - target_time) <= 5
        
        if not time_match:
            return []
        
        # Check if already sent today
        today_str = now.strftime('%Y-%m-%d')
        recent_events = [e for e in self.alert_events 
                        if e.alert_rule_id == rule.id and 
                        e.timestamp.startswith(today_str)]
        
        if recent_events:
            return []  # Already sent today
        
        # Generate digest content
        digest_data = self._generate_daily_digest_data()
        
        return [AlertEvent(
            alert_rule_id=rule.id,
            timestamp=now.isoformat(),
            trigger_reason="Daily digest scheduled delivery",
            current_value=float(now.hour * 100 + now.minute),
            threshold_value=rule.condition_value,
            additional_data=digest_data
        )]
    
    def _check_thesis_change_alert(self, rule: AlertRule) -> List[AlertEvent]:
        """Check for significant thesis changes."""
        # This would integrate with the historical tracker to detect thesis changes
        # Implementation would check for rating downgrades/upgrades
        return []  # Placeholder for now
    
    def _check_research_update_alert(self, rule: AlertRule) -> List[AlertEvent]:
        """Check for new research updates."""
        # This would check for new research documents matching criteria
        return []  # Placeholder for now
    
    def _check_performance_alert(self, rule: AlertRule) -> List[AlertEvent]:
        """Check for significant performance changes."""
        # This would integrate with performance tracking
        return []  # Placeholder for now
    
    def _generate_daily_digest_data(self) -> Dict:
        """Generate data for daily digest."""
        # Get watchlist updates
        saved_research = self.saved_research_store.get_all_research()
        watchlist_count = len(saved_research)
        
        # Get recent price movements for watched tickers
        tickers = set()
        for research in saved_research:
            if research.tickers:
                tickers.update(research.tickers)
        
        price_changes = []
        for ticker in list(tickers)[:10]:  # Limit to 10 tickers for performance
            try:
                quote = self.finnhub_client.get_quote(ticker)
                change_pct = ((quote['c'] - quote['pc']) / quote['pc']) * 100
                if abs(change_pct) > 5:  # Significant moves only
                    price_changes.append(f"{ticker}: {change_pct:+.1f}%")
            except:
                continue
        
        return {
            'watchlist_updates': f"{watchlist_count} items tracked",
            'price_changes': ", ".join(price_changes) if price_changes else "No significant moves",
            'new_research': "Check platform for latest analysis"
        }
    
    def _process_alert_event(self, rule: AlertRule, event: AlertEvent) -> None:
        """Process a triggered alert event by sending notifications.
        
        Args:
            rule: AlertRule that triggered
            event: AlertEvent with trigger details
        """
        delivery_success = []
        
        # Send email notification
        if rule.email_recipients:
            if self.notification_engine.send_email_alert(rule, event):
                delivery_success.append('email')
        
        # Send webhook notification  
        if rule.webhook_url:
            if self.notification_engine.send_webhook_alert(rule, event):
                delivery_success.append('webhook')
        
        # Update event with delivery status
        event.delivered = len(delivery_success) > 0
        event.delivery_methods = delivery_success
        
        # Update rule statistics
        rule.last_triggered = event.timestamp
        rule.trigger_count += 1
        self._save_alert_rules()
    
    def get_alert_events(self, rule_id: str = None, limit: int = 100) -> List[AlertEvent]:
        """Get alert events, optionally filtered by rule.
        
        Args:
            rule_id: Optional rule ID to filter by
            limit: Maximum number of events to return
            
        Returns:
            List of AlertEvent objects
        """
        events = self.alert_events
        
        if rule_id:
            events = [e for e in events if e.alert_rule_id == rule_id]
        
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)
        return events[:limit]
    
    def get_alert_statistics(self) -> Dict:
        """Get alert system statistics.
        
        Returns:
            Dictionary with alert statistics
        """
        total_rules = len(self.alert_rules)
        enabled_rules = len([r for r in self.alert_rules.values() if r.enabled])
        total_events = len(self.alert_events)
        
        # Events by type in last 30 days
        cutoff = datetime.now() - timedelta(days=30)
        recent_events = [e for e in self.alert_events 
                        if datetime.fromisoformat(e.timestamp) > cutoff]
        
        events_by_type = {}
        for event in recent_events:
            rule = self.alert_rules.get(event.alert_rule_id)
            if rule:
                event_type = rule.alert_type.value
                events_by_type[event_type] = events_by_type.get(event_type, 0) + 1
        
        return {
            'total_rules': total_rules,
            'enabled_rules': enabled_rules,
            'total_events': total_events,
            'events_last_30_days': len(recent_events),
            'events_by_type': events_by_type,
            'monitoring_active': self._monitoring
        }
    
    def _load_email_config(self) -> Optional[EmailConfig]:
        """Load email configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    if 'email' in config_data:
                        return EmailConfig.from_dict(config_data['email'])
        except Exception as e:
            print(f"Error loading email config: {e}")
        
        return None
    
    def _load_alert_rules(self) -> Dict[str, AlertRule]:
        """Load alert rules from storage."""
        try:
            if self.rules_file.exists():
                with open(self.rules_file, 'r') as f:
                    rules_data = json.load(f)
                    return {rule_id: AlertRule.from_dict(data) 
                           for rule_id, data in rules_data.items()}
        except Exception as e:
            print(f"Error loading alert rules: {e}")
        
        return {}
    
    def _save_alert_rules(self) -> None:
        """Save alert rules to storage."""
        try:
            rules_data = {rule_id: rule.to_dict() 
                         for rule_id, rule in self.alert_rules.items()}
            
            with open(self.rules_file, 'w') as f:
                json.dump(rules_data, f, indent=2)
        except Exception as e:
            print(f"Error saving alert rules: {e}")
    
    def _load_alert_events(self) -> List[AlertEvent]:
        """Load alert events from storage."""
        try:
            if self.events_file.exists():
                with open(self.events_file, 'r') as f:
                    events_data = json.load(f)
                    return [AlertEvent.from_dict(data) for data in events_data]
        except Exception as e:
            print(f"Error loading alert events: {e}")
        
        return []
    
    def _save_alert_events(self) -> None:
        """Save alert events to storage."""
        try:
            # Keep only last 1000 events to prevent file from growing too large
            events_to_save = sorted(self.alert_events, 
                                  key=lambda e: e.timestamp, 
                                  reverse=True)[:1000]
            
            events_data = [event.to_dict() for event in events_to_save]
            
            with open(self.events_file, 'w') as f:
                json.dump(events_data, f, indent=2)
                
            self.alert_events = events_to_save
        except Exception as e:
            print(f"Error saving alert events: {e}")
    
    def configure_email(self, smtp_server: str, smtp_port: int, 
                       username: str, password: str, use_tls: bool = True) -> bool:
        """Configure email settings for alerts.
        
        Args:
            smtp_server: SMTP server hostname
            smtp_port: SMTP port number
            username: Email username
            password: Email password
            use_tls: Whether to use TLS encryption
            
        Returns:
            True if configuration saved successfully
        """
        try:
            email_config = EmailConfig(
                smtp_server=smtp_server,
                smtp_port=smtp_port,
                username=username,
                password=password,
                use_tls=use_tls
            )
            
            # Save configuration
            config_data = {}
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
            
            config_data['email'] = email_config.to_dict()
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.email_config = email_config
            self.notification_engine = AlertNotificationEngine(email_config)
            
            return True
            
        except Exception as e:
            print(f"Error configuring email: {e}")
            return False