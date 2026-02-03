"""REST API routes for programmatic access to research data."""

import json
import re
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app
from typing import Dict, List, Any, Optional

from .api_auth import require_api_key
from ..utils import (
    MarkdownGenerator, WatchlistManager, HistoricalTracker, 
    MultiThemeCorrelationAnalyzer, SectorAnalysisCache, SavedResearchStore
)
from ..agents import ExploreAgent
from ..models import WatchlistEntity, SavedResearch, SavedResearchStatus


def create_api_blueprint(data_dir: Path, api_key_manager) -> Blueprint:
    """Create API blueprint with all REST endpoints.
    
    Args:
        data_dir: Data directory path
        api_key_manager: APIKeyManager instance
        
    Returns:
        Flask Blueprint with API routes
    """
    api = Blueprint('api', __name__, url_prefix='/api/v1')
    
    # Initialize managers
    markdown_generator = MarkdownGenerator(output_dir=data_dir)
    watchlist_manager = WatchlistManager(data_dir=data_dir)
    historical_tracker = HistoricalTracker(data_dir=data_dir)
    correlation_analyzer = MultiThemeCorrelationAnalyzer(data_dir=data_dir)
    sector_cache = SectorAnalysisCache(cache_dir=data_dir / 'cache')
    saved_research_store = SavedResearchStore(data_dir=data_dir)
    
    # Authentication decorator with manager
    auth_required = require_api_key(api_key_manager)
    
    # ============================================================================
    # RESEARCH ENDPOINTS
    # ============================================================================
    
    @api.route('/research', methods=['GET'])
    @auth_required
    def list_research():
        """List all research documents with metadata."""
        try:
            research_files = markdown_generator.list_research()
            research_list = []
            
            for research_path in research_files:
                try:
                    # Read file to extract metadata
                    with open(research_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Extract YAML frontmatter
                    metadata = {}
                    if content.startswith('---'):
                        end_marker = content.find('---', 3)
                        if end_marker != -1:
                            frontmatter = content[3:end_marker]
                            for line in frontmatter.split('\n'):
                                if ':' in line:
                                    key, value = line.split(':', 1)
                                    metadata[key.strip()] = value.strip().strip("'\"")
                    
                    # Extract TLDR
                    tldr = None
                    tldr_match = re.search(r'\*\*TLDR:\*\*\s*([^*]+)', content)
                    if tldr_match:
                        tldr = tldr_match.group(1).strip()
                    
                    research_list.append({
                        'id': research_path.stem,
                        'filename': research_path.name,
                        'title': metadata.get('theme', research_path.stem),
                        'generated': metadata.get('generated'),
                        'model': metadata.get('model'),
                        'depth': metadata.get('depth'),
                        'tickers_found': metadata.get('tickers_found'),
                        'tool_calls': metadata.get('tool_calls'),
                        'type': metadata.get('type', 'research'),
                        'tldr': tldr,
                        'size_bytes': research_path.stat().st_size,
                        'created_at': datetime.fromtimestamp(research_path.stat().st_ctime).isoformat()
                    })
                    
                except Exception as e:
                    # Skip files that can't be processed
                    continue
            
            # Sort by creation date, newest first
            research_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            return jsonify({
                'success': True,
                'total': len(research_list),
                'research': research_list
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @api.route('/research/<research_id>', methods=['GET'])
    @auth_required
    def get_research(research_id: str):
        """Get a specific research document by ID."""
        try:
            research_files = markdown_generator.list_research()
            
            # Find matching research file
            research_path = None
            for path in research_files:
                if path.stem == research_id or path.name == research_id:
                    research_path = path
                    break
            
            if not research_path:
                return jsonify({
                    'success': False,
                    'error': 'Research document not found'
                }), 404
            
            # Read and parse the document
            with open(research_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata
            metadata = {}
            if content.startswith('---'):
                end_marker = content.find('---', 3)
                if end_marker != -1:
                    frontmatter = content[3:end_marker]
                    for line in frontmatter.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            metadata[key.strip()] = value.strip().strip("'\"")
            
            # Return structured data
            response_data = {
                'success': True,
                'research': {
                    'id': research_path.stem,
                    'filename': research_path.name,
                    'content': content,
                    'metadata': metadata,
                    'size_bytes': len(content),
                    'created_at': datetime.fromtimestamp(research_path.stat().st_ctime).isoformat(),
                    'modified_at': datetime.fromtimestamp(research_path.stat().st_mtime).isoformat()
                }
            }
            
            # Optionally include parsed sections
            if request.args.get('include_parsed') == 'true':
                response_data['research']['parsed_sections'] = _parse_research_sections(content)
            
            return jsonify(response_data)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @api.route('/research', methods=['POST'])
    @auth_required
    def create_research():
        """Trigger new research generation."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'JSON payload required'
                }), 400
            
            query = data.get('query')
            if not query:
                return jsonify({
                    'success': False,
                    'error': 'Query parameter required'
                }), 400
            
            depth = data.get('depth', 2)
            
            # Initialize explore agent
            explore_agent = ExploreAgent()
            
            # Generate research
            output_path = explore_agent.run(query, depth=depth)
            
            # Read the generated content
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return jsonify({
                'success': True,
                'research': {
                    'id': output_path.stem,
                    'filename': output_path.name,
                    'query': query,
                    'depth': depth,
                    'path': str(output_path),
                    'size_bytes': len(content),
                    'created_at': datetime.now().isoformat()
                },
                'message': 'Research generated successfully'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # ============================================================================
    # WATCHLIST ENDPOINTS
    # ============================================================================
    
    @api.route('/watchlist', methods=['GET'])
    @auth_required
    def get_watchlist():
        """Get all watchlist entities."""
        try:
            entities = watchlist_manager.get_all()
            
            return jsonify({
                'success': True,
                'total': len(entities),
                'watchlist': [entity.to_dict() for entity in entities]
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @api.route('/watchlist', methods=['POST'])
    @auth_required
    def add_to_watchlist():
        """Add entity to watchlist."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'JSON payload required'
                }), 400
            
            ticker = data.get('ticker')
            if not ticker:
                return jsonify({
                    'success': False,
                    'error': 'Ticker parameter required'
                }), 400
            
            entity = WatchlistEntity(
                ticker=ticker.upper(),
                name=data.get('name', ''),
                themes=data.get('themes', []),
                added_date=datetime.now().strftime('%Y-%m-%d'),
                source_research=data.get('source_research')
            )
            
            if watchlist_manager.add(entity):
                return jsonify({
                    'success': True,
                    'entity': entity.to_dict(),
                    'message': f'Added {ticker} to watchlist'
                }), 201
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to add entity (may already exist)'
                }), 409
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @api.route('/watchlist/<ticker>', methods=['DELETE'])
    @auth_required
    def remove_from_watchlist(ticker: str):
        """Remove entity from watchlist."""
        try:
            if watchlist_manager.remove(ticker.upper()):
                return jsonify({
                    'success': True,
                    'message': f'Removed {ticker} from watchlist'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'Entity {ticker} not found in watchlist'
                }), 404
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # ============================================================================
    # HISTORICAL TRACKING ENDPOINTS
    # ============================================================================
    
    @api.route('/performance/stats', methods=['GET'])
    @auth_required
    def get_performance_stats():
        """Get historical performance statistics."""
        try:
            stats = historical_tracker.get_hit_rate_stats()
            return jsonify(stats)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @api.route('/performance/theses', methods=['GET'])
    @auth_required
    def get_investment_theses():
        """Get all investment theses with performance data."""
        try:
            theses_data = []
            
            for thesis_id, thesis in historical_tracker.theses.items():
                perf = historical_tracker.performance.get(thesis_id)
                
                theses_data.append({
                    'thesis': thesis.to_dict(),
                    'performance': perf.to_dict() if perf else None
                })
            
            # Sort by created date
            theses_data.sort(
                key=lambda x: x['thesis'].get('created_date', ''), 
                reverse=True
            )
            
            return jsonify({
                'success': True,
                'total': len(theses_data),
                'theses': theses_data
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @api.route('/performance/update', methods=['POST'])
    @auth_required
    def update_performance():
        """Update thesis performance data."""
        try:
            data = request.get_json() or {}
            thesis_id = data.get('thesis_id')
            
            success = historical_tracker.update_performance(thesis_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Performance updated successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to update performance - data unavailable'
                }), 400
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # ============================================================================
    # CORRELATION ANALYSIS ENDPOINTS
    # ============================================================================
    
    @api.route('/correlations', methods=['GET'])
    @auth_required
    def get_correlations():
        """Get theme correlation analysis."""
        try:
            themes = request.args.getlist('themes')
            
            if themes:
                overlaps = correlation_analyzer.analyze_theme_correlations(themes)
            else:
                overlaps = correlation_analyzer.analyze_theme_correlations()
            
            opportunities = correlation_analyzer.identify_cross_theme_opportunities()
            
            return jsonify({
                'success': True,
                'theme_overlaps': [overlap.to_dict() for overlap in overlaps],
                'cross_theme_opportunities': [opp.to_dict() for opp in opportunities],
                'themes_analyzed': correlation_analyzer._get_available_themes()
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # ============================================================================
    # CACHE MANAGEMENT ENDPOINTS
    # ============================================================================
    
    @api.route('/cache/stats', methods=['GET'])
    @auth_required
    def get_cache_stats():
        """Get cache performance statistics."""
        try:
            stats = sector_cache.get_cache_stats()
            return jsonify(stats)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @api.route('/cache/cleanup', methods=['POST'])
    @auth_required
    def cleanup_cache():
        """Cleanup expired cache entries."""
        try:
            cleaned = sector_cache.cleanup_expired_entries()
            return jsonify({
                'success': True,
                'entries_cleaned': cleaned,
                'message': f'Cleaned up {cleaned} expired cache entries'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # ============================================================================
    # SAVED RESEARCH ENDPOINTS
    # ============================================================================
    
    @api.route('/saved-research', methods=['GET'])
    @auth_required
    def get_saved_research():
        """Get all saved research items."""
        try:
            items = saved_research_store.list_all()
            
            # Apply filters
            status = request.args.get('status')
            if status:
                items = [item for item in items if item.status.value == status]
            
            tags = request.args.getlist('tags')
            if tags:
                items = [item for item in items if any(tag in item.tags for tag in tags)]
            
            return jsonify({
                'success': True,
                'total': len(items),
                'saved_research': [item.to_dict() for item in items]
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @api.route('/saved-research', methods=['POST'])
    @auth_required
    def save_research():
        """Save a research document to saved research."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'JSON payload required'
                }), 400
            
            filename = data.get('filename')
            if not filename:
                return jsonify({
                    'success': False,
                    'error': 'Filename parameter required'
                }), 400
            
            # Create SavedResearch object
            saved_research = SavedResearch(
                filename=filename,
                title=data.get('title', filename),
                status=SavedResearchStatus(data.get('status', 'interested')),
                saved_date=datetime.now().strftime('%Y-%m-%d'),
                notes=data.get('notes', ''),
                tags=data.get('tags', []),
                rating=data.get('rating')
            )
            
            if saved_research_store.save(saved_research):
                return jsonify({
                    'success': True,
                    'saved_research': saved_research.to_dict(),
                    'message': 'Research saved successfully'
                }), 201
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to save research (may already exist)'
                }), 409
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # ============================================================================
    # HELPER FUNCTIONS
    # ============================================================================
    
    def _parse_research_sections(content: str) -> Dict[str, Any]:
        """Parse research content into structured sections."""
        sections = {}
        
        # Extract TLDR
        tldr_match = re.search(r'\*\*TLDR:\*\*\s*([^*]+)', content)
        if tldr_match:
            sections['tldr'] = tldr_match.group(1).strip()
        
        # Extract executive summary
        exec_summary_match = re.search(r'## Executive Summary\n(.*?)\n##', content, re.DOTALL)
        if exec_summary_match:
            sections['executive_summary'] = exec_summary_match.group(1).strip()
        
        # Extract tickers from tables
        ticker_pattern = r'\|\s*([A-Z]{1,5})\s*\|'
        tickers = list(set(re.findall(ticker_pattern, content)))
        sections['tickers'] = [t for t in tickers if len(t) >= 2]
        
        # Extract key insights
        insights = re.findall(r'^[-*]\s+(.+)$', content, re.MULTILINE)
        sections['key_insights'] = insights[:10]  # Top 10 insights
        
        return sections
    
    # ============================================================================
    # ALERT SYSTEM ENDPOINTS  
    # ============================================================================
    
    # Import here to avoid circular imports
    from ..utils.alert_system import AlertManager, AlertType, AlertTrigger
    alert_manager = AlertManager(data_dir)
    
    @api.route('/alerts/rules', methods=['GET'])
    @auth_required
    def list_alert_rules():
        """List all alert rules."""
        try:
            enabled_only = request.args.get('enabled_only', 'true').lower() == 'true'
            rules = alert_manager.get_alert_rules(enabled_only=enabled_only)
            
            return jsonify({
                'status': 'success',
                'data': {
                    'rules': [rule.to_dict() for rule in rules],
                    'total': len(rules)
                }
            })
            
        except Exception as e:
            return jsonify({'status': 'error', 'error': str(e)}), 500
    
    @api.route('/alerts/rules', methods=['POST'])
    @auth_required  
    def create_alert_rule():
        """Create a new alert rule."""
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['name', 'alert_type', 'trigger', 'condition_value']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'status': 'error', 
                        'error': f'Missing required field: {field}'
                    }), 400
            
            # Convert string enums to enum objects
            alert_type = AlertType(data['alert_type'])
            trigger = AlertTrigger(data['trigger'])
            
            rule = alert_manager.create_alert_rule(
                name=data['name'],
                alert_type=alert_type,
                trigger=trigger,
                condition_value=float(data['condition_value']),
                ticker=data.get('ticker'),
                theme=data.get('theme'),
                email_recipients=data.get('email_recipients', []),
                webhook_url=data.get('webhook_url')
            )
            
            return jsonify({
                'status': 'success',
                'data': {'rule': rule.to_dict()}
            }), 201
            
        except ValueError as e:
            return jsonify({'status': 'error', 'error': f'Invalid value: {str(e)}'}), 400
        except Exception as e:
            return jsonify({'status': 'error', 'error': str(e)}), 500
    
    @api.route('/alerts/rules/<rule_id>', methods=['PUT'])
    @auth_required
    def update_alert_rule(rule_id: str):
        """Update an existing alert rule.""" 
        try:
            data = request.get_json()
            
            # Convert enum fields if provided
            if 'alert_type' in data:
                data['alert_type'] = AlertType(data['alert_type'])
            if 'trigger' in data:
                data['trigger'] = AlertTrigger(data['trigger'])
            
            success = alert_manager.update_alert_rule(rule_id, **data)
            
            if success:
                updated_rule = alert_manager.alert_rules.get(rule_id)
                return jsonify({
                    'status': 'success',
                    'data': {'rule': updated_rule.to_dict()}
                })
            else:
                return jsonify({'status': 'error', 'error': 'Rule not found'}), 404
                
        except ValueError as e:
            return jsonify({'status': 'error', 'error': f'Invalid value: {str(e)}'}), 400
        except Exception as e:
            return jsonify({'status': 'error', 'error': str(e)}), 500
    
    @api.route('/alerts/rules/<rule_id>', methods=['DELETE'])
    @auth_required
    def delete_alert_rule(rule_id: str):
        """Delete an alert rule."""
        try:
            success = alert_manager.delete_alert_rule(rule_id)
            
            if success:
                return jsonify({'status': 'success'})
            else:
                return jsonify({'status': 'error', 'error': 'Rule not found'}), 404
                
        except Exception as e:
            return jsonify({'status': 'error', 'error': str(e)}), 500
    
    @api.route('/alerts/rules/<rule_id>/events', methods=['GET'])
    @auth_required
    def get_alert_events(rule_id: str):
        """Get events for a specific alert rule."""
        try:
            limit = int(request.args.get('limit', 50))
            events = alert_manager.get_alert_events(rule_id=rule_id, limit=limit)
            
            return jsonify({
                'status': 'success',
                'data': {
                    'events': [event.to_dict() for event in events],
                    'total': len(events)
                }
            })
            
        except Exception as e:
            return jsonify({'status': 'error', 'error': str(e)}), 500
    
    @api.route('/alerts/events', methods=['GET'])
    @auth_required
    def list_alert_events():
        """List all recent alert events."""
        try:
            limit = int(request.args.get('limit', 100))
            events = alert_manager.get_alert_events(limit=limit)
            
            return jsonify({
                'status': 'success',
                'data': {
                    'events': [event.to_dict() for event in events],
                    'total': len(events)
                }
            })
            
        except Exception as e:
            return jsonify({'status': 'error', 'error': str(e)}), 500
    
    @api.route('/alerts/check', methods=['POST'])
    @auth_required
    def check_alerts():
        """Manually trigger alert checks."""
        try:
            triggered_events = alert_manager.check_all_alerts()
            
            return jsonify({
                'status': 'success',
                'data': {
                    'triggered_events': [event.to_dict() for event in triggered_events],
                    'count': len(triggered_events)
                }
            })
            
        except Exception as e:
            return jsonify({'status': 'error', 'error': str(e)}), 500
    
    @api.route('/alerts/stats', methods=['GET'])
    @auth_required
    def get_alert_statistics():
        """Get alert system statistics."""
        try:
            stats = alert_manager.get_alert_statistics()
            
            return jsonify({
                'status': 'success',
                'data': stats
            })
            
        except Exception as e:
            return jsonify({'status': 'error', 'error': str(e)}), 500
    
    @api.route('/alerts/config/email', methods=['POST'])
    @auth_required
    def configure_alert_email():
        """Configure email settings for alerts."""
        try:
            data = request.get_json()
            
            required_fields = ['smtp_server', 'smtp_port', 'username', 'password']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'status': 'error',
                        'error': f'Missing required field: {field}'
                    }), 400
            
            success = alert_manager.configure_email(
                smtp_server=data['smtp_server'],
                smtp_port=int(data['smtp_port']),
                username=data['username'],
                password=data['password'],
                use_tls=data.get('use_tls', True)
            )
            
            if success:
                return jsonify({'status': 'success'})
            else:
                return jsonify({'status': 'error', 'error': 'Configuration failed'}), 500
                
        except Exception as e:
            return jsonify({'status': 'error', 'error': str(e)}), 500
    
    # Convenience endpoints for common alert types
    @api.route('/alerts/price-alert', methods=['POST'])
    @auth_required
    def create_price_alert():
        """Create a price alert (convenience endpoint)."""
        try:
            data = request.get_json()
            
            required_fields = ['ticker', 'trigger', 'price']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'status': 'error',
                        'error': f'Missing required field: {field}'
                    }), 400
            
            trigger = AlertTrigger(data['trigger'])
            rule = alert_manager.create_price_alert(
                ticker=data['ticker'],
                trigger=trigger,
                price=float(data['price']),
                emails=data.get('emails', [])
            )
            
            return jsonify({
                'status': 'success',
                'data': {'rule': rule.to_dict()}
            }), 201
            
        except ValueError as e:
            return jsonify({'status': 'error', 'error': f'Invalid value: {str(e)}'}), 400
        except Exception as e:
            return jsonify({'status': 'error', 'error': str(e)}), 500
    
    @api.route('/alerts/daily-digest', methods=['POST'])
    @auth_required
    def create_daily_digest():
        """Create a daily digest alert (convenience endpoint)."""
        try:
            data = request.get_json()
            
            if 'emails' not in data:
                return jsonify({
                    'status': 'error',
                    'error': 'Missing required field: emails'
                }), 400
            
            rule = alert_manager.create_daily_digest(
                emails=data['emails'],
                delivery_time=data.get('delivery_time', '09:00')
            )
            
            return jsonify({
                'status': 'success',
                'data': {'rule': rule.to_dict()}
            }), 201
            
        except Exception as e:
            return jsonify({'status': 'error', 'error': str(e)}), 500
    
    # ============================================================================
    # CHARTS ENDPOINTS  
    # ============================================================================
    
    # Import chart generator
    from ..utils.chart_generator import InteractiveChartGenerator
    chart_generator = InteractiveChartGenerator(data_dir)
    
    @api.route('/charts/<chart_type>', methods=['GET'])
    @auth_required
    def get_chart_data(chart_type: str):
        """Get chart data for a specific chart type."""
        try:
            # Parse query parameters
            ticker = request.args.get('ticker', 'AAPL')
            days = int(request.args.get('days', 90))
            
            chart_data = None
            
            if chart_type == 'sector_distribution':
                chart_data = chart_generator.generate_sector_distribution_chart()
            elif chart_type == 'quality_trends':
                chart_data = chart_generator.generate_quality_trends_chart(days=days)
            elif chart_type == 'research_volume':
                chart_data = chart_generator.generate_research_volume_chart()
            elif chart_type == 'price_chart':
                chart_data = chart_generator.generate_price_chart(ticker=ticker, period_days=days)
            elif chart_type == 'ticker_comparison':
                tickers = request.args.get('tickers', 'AAPL,MSFT,GOOGL').split(',')
                chart_data = chart_generator.generate_multi_ticker_comparison(tickers[:5])  # Limit to 5
            elif chart_type == 'correlation_heatmap':
                tickers = request.args.get('tickers', 'AAPL,MSFT,GOOGL,AMZN,TSLA').split(',')
                chart_data = chart_generator.generate_ticker_correlation_heatmap(tickers[:5])
            elif chart_type == 'performance_scatter':
                chart_data = chart_generator.generate_performance_scatter_plot()
            else:
                return jsonify({
                    'status': 'error',
                    'error': f'Unknown chart type: {chart_type}'
                }), 400
            
            if chart_data:
                return jsonify({
                    'status': 'success',
                    'data': chart_data.to_dict()
                })
            else:
                return jsonify({
                    'status': 'error',
                    'error': 'Failed to generate chart data'
                }), 500
                
        except Exception as e:
            return jsonify({'status': 'error', 'error': str(e)}), 500
    
    @api.route('/charts/dashboard', methods=['GET'])
    @auth_required
    def get_dashboard_charts():
        """Get all dashboard charts at once."""
        try:
            charts = chart_generator.generate_dashboard_charts()
            
            # Convert ChartData objects to dictionaries
            charts_data = {name: chart.to_dict() for name, chart in charts.items()}
            
            return jsonify({
                'status': 'success',
                'data': charts_data
            })
            
        except Exception as e:
            return jsonify({'status': 'error', 'error': str(e)}), 500
    
    @api.route('/charts/export', methods=['POST'])
    @auth_required
    def export_chart_data():
        """Export all chart data to file."""
        try:
            data = request.get_json() or {}
            format_type = data.get('format', 'json')
            
            # Generate all charts
            charts = chart_generator.generate_dashboard_charts()
            
            if format_type == 'json':
                # Export as JSON
                charts_data = {name: chart.to_dict() for name, chart in charts.items()}
                
                # Create response
                from flask import make_response
                response = make_response(json.dumps(charts_data, indent=2))
                response.headers['Content-Type'] = 'application/json'
                response.headers['Content-Disposition'] = f'attachment; filename=charts-{datetime.now().strftime("%Y%m%d")}.json'
                
                return response
            else:
                return jsonify({
                    'status': 'error',
                    'error': 'Only JSON format is currently supported'
                }), 400
                
        except Exception as e:
            return jsonify({'status': 'error', 'error': str(e)}), 500
    
    @api.route('/charts/custom', methods=['POST'])
    @auth_required
    def create_custom_chart():
        """Create a custom chart with user-specified parameters."""
        try:
            data = request.get_json()
            chart_type = data.get('chart_type', 'line')
            
            if chart_type == 'price':
                ticker = data.get('ticker', 'AAPL')
                days = data.get('days', 90)
                chart_data = chart_generator.generate_price_chart(ticker=ticker, period_days=days)
            elif chart_type == 'correlation':
                tickers = data.get('tickers', ['AAPL', 'MSFT'])
                chart_data = chart_generator.generate_ticker_correlation_heatmap(tickers)
            elif chart_type == 'comparison':
                tickers = data.get('tickers', ['AAPL', 'MSFT'])
                metrics = data.get('metrics', ['price', 'market_cap'])
                chart_data = chart_generator.generate_multi_ticker_comparison(tickers, metrics)
            else:
                return jsonify({
                    'status': 'error',
                    'error': f'Unsupported chart type: {chart_type}'
                }), 400
            
            return jsonify({
                'status': 'success',
                'data': chart_data.to_dict()
            })
            
        except Exception as e:
            return jsonify({'status': 'error', 'error': str(e)}), 500
    
    return api