"""Interactive chart generation for research data visualization."""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
import statistics

from .finnhub_client import FinnhubClient
from .research_analytics import ResearchAnalyticsEngine


@dataclass
class ChartData:
    """Data structure for chart configuration and data."""
    chart_type: str  # 'line', 'bar', 'pie', 'scatter', etc.
    title: str
    data: Dict[str, Any]
    options: Dict[str, Any]
    libraries: List[str]  # ['chartjs', 'plotly', etc.]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'chart_type': self.chart_type,
            'title': self.title,
            'data': self.data,
            'options': self.options,
            'libraries': self.libraries
        }


class InteractiveChartGenerator:
    """Generates interactive charts for research data using Chart.js and Plotly."""
    
    def __init__(self, data_dir: Path, finnhub_client: FinnhubClient = None):
        """Initialize chart generator.
        
        Args:
            data_dir: Directory containing research data
            finnhub_client: Finnhub client for market data
        """
        self.data_dir = data_dir
        self.research_dir = data_dir / 'research'
        self.charts_dir = data_dir / 'charts'
        self.charts_dir.mkdir(parents=True, exist_ok=True)
        
        self.finnhub_client = finnhub_client or FinnhubClient()
        self.analytics_engine = ResearchAnalyticsEngine(data_dir)
    
    def generate_price_chart(self, ticker: str, period_days: int = 90) -> ChartData:
        """Generate price chart for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            period_days: Number of days of price history
            
        Returns:
            ChartData object with price chart configuration
        """
        try:
            # Get historical data (this is a simplified version)
            # In production, you'd use the Finnhub historical data API
            
            # For now, simulate some price data
            import random
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)
            
            dates = []
            prices = []
            volumes = []
            
            # Generate sample data (replace with actual Finnhub historical data)
            base_price = 100 + random.uniform(-50, 50)
            current_date = start_date
            
            while current_date <= end_date:
                dates.append(current_date.strftime('%Y-%m-%d'))
                # Simple random walk for price
                base_price += random.uniform(-5, 5)
                base_price = max(base_price, 10)  # Keep price positive
                prices.append(round(base_price, 2))
                volumes.append(random.randint(100000, 5000000))
                current_date += timedelta(days=1)
            
            chart_data = {
                'labels': dates,
                'datasets': [
                    {
                        'label': f'{ticker} Price',
                        'data': prices,
                        'borderColor': '#3b82f6',
                        'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                        'borderWidth': 2,
                        'fill': True,
                        'tension': 0.1
                    }
                ]
            }
            
            chart_options = {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': f'{ticker} Price Chart ({period_days} Days)',
                        'font': {'size': 16, 'weight': 'bold'}
                    },
                    'legend': {'display': False},
                    'tooltip': {
                        'mode': 'index',
                        'intersect': False,
                        'callbacks': {
                            'label': 'function(context) { return "$" + context.parsed.y.toFixed(2); }'
                        }
                    }
                },
                'scales': {
                    'x': {
                        'display': True,
                        'title': {'display': True, 'text': 'Date'},
                        'grid': {'display': False}
                    },
                    'y': {
                        'display': True,
                        'title': {'display': True, 'text': 'Price ($)'},
                        'beginAtZero': False
                    }
                },
                'interaction': {
                    'mode': 'nearest',
                    'axis': 'x',
                    'intersect': False
                }
            }
            
            return ChartData(
                chart_type='line',
                title=f'{ticker} Price Chart',
                data=chart_data,
                options=chart_options,
                libraries=['chartjs']
            )
            
        except Exception as e:
            # Return empty chart on error
            return self._create_error_chart(f"Failed to generate price chart for {ticker}: {str(e)}")
    
    def generate_sector_distribution_chart(self, research_metrics: List = None) -> ChartData:
        """Generate pie chart showing sector distribution in research.
        
        Args:
            research_metrics: Optional list of research metrics
            
        Returns:
            ChartData object with sector distribution chart
        """
        try:
            if research_metrics is None:
                research_metrics = self.analytics_engine.analyze_all_documents()
            
            # Count research by sector/theme
            theme_counts = {}
            for metrics in research_metrics:
                theme = metrics.theme or 'Unknown'
                theme_counts[theme] = theme_counts.get(theme, 0) + 1
            
            # Sort by count and take top 10
            sorted_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            if not sorted_themes:
                return self._create_empty_chart("No research data available")
            
            labels = [theme for theme, count in sorted_themes]
            data = [count for theme, count in sorted_themes]
            
            # Generate colors for each sector
            colors = [
                '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
                '#06b6d4', '#84cc16', '#f97316', '#ec4899', '#6366f1'
            ]
            
            chart_data = {
                'labels': labels,
                'datasets': [{
                    'data': data,
                    'backgroundColor': colors[:len(data)],
                    'borderColor': '#ffffff',
                    'borderWidth': 2
                }]
            }
            
            chart_options = {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': 'Research Distribution by Sector/Theme',
                        'font': {'size': 16, 'weight': 'bold'}
                    },
                    'legend': {
                        'position': 'right',
                        'labels': {'padding': 20, 'usePointStyle': True}
                    },
                    'tooltip': {
                        'callbacks': {
                            'label': 'function(context) { return context.label + ": " + context.parsed + " documents (" + Math.round(context.parsed/context.dataset.data.reduce((a,b)=>a+b)*100) + "%)"; }'
                        }
                    }
                }
            }
            
            return ChartData(
                chart_type='doughnut',
                title='Research Sector Distribution',
                data=chart_data,
                options=chart_options,
                libraries=['chartjs']
            )
            
        except Exception as e:
            return self._create_error_chart(f"Failed to generate sector chart: {str(e)}")
    
    def generate_quality_trends_chart(self, days: int = 30) -> ChartData:
        """Generate line chart showing research quality trends over time.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            ChartData object with quality trends chart
        """
        try:
            trends = self.analytics_engine.get_quality_trends(days=days)
            
            if not trends['dates']:
                return self._create_empty_chart("No research quality data available")
            
            chart_data = {
                'labels': trends['dates'],
                'datasets': [
                    {
                        'label': 'Quality Score',
                        'data': trends['quality_scores'],
                        'borderColor': '#10b981',
                        'backgroundColor': 'rgba(16, 185, 129, 0.1)',
                        'borderWidth': 3,
                        'fill': True,
                        'tension': 0.3
                    },
                    {
                        'label': 'Avg Word Count (scaled)',
                        'data': [count / 100 for count in trends['word_counts']],  # Scale down for visibility
                        'borderColor': '#3b82f6',
                        'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                        'borderWidth': 2,
                        'fill': False,
                        'tension': 0.3,
                        'yAxisID': 'y1'
                    }
                ]
            }
            
            chart_options = {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': f'Research Quality Trends ({days} Days)',
                        'font': {'size': 16, 'weight': 'bold'}
                    },
                    'legend': {'display': True, 'position': 'top'},
                    'tooltip': {
                        'mode': 'index',
                        'intersect': False
                    }
                },
                'scales': {
                    'x': {
                        'display': True,
                        'title': {'display': True, 'text': 'Date'}
                    },
                    'y': {
                        'type': 'linear',
                        'display': True,
                        'position': 'left',
                        'title': {'display': True, 'text': 'Quality Score'},
                        'min': 0,
                        'max': 1
                    },
                    'y1': {
                        'type': 'linear',
                        'display': True,
                        'position': 'right',
                        'title': {'display': True, 'text': 'Word Count (x100)'},
                        'grid': {'drawOnChartArea': False},
                        'min': 0
                    }
                },
                'interaction': {
                    'mode': 'nearest',
                    'axis': 'x',
                    'intersect': False
                }
            }
            
            return ChartData(
                chart_type='line',
                title='Research Quality Trends',
                data=chart_data,
                options=chart_options,
                libraries=['chartjs']
            )
            
        except Exception as e:
            return self._create_error_chart(f"Failed to generate quality trends chart: {str(e)}")
    
    def generate_ticker_correlation_heatmap(self, tickers: List[str]) -> ChartData:
        """Generate correlation heatmap for a list of tickers.
        
        Args:
            tickers: List of ticker symbols
            
        Returns:
            ChartData object with correlation heatmap
        """
        try:
            if len(tickers) < 2:
                return self._create_empty_chart("Need at least 2 tickers for correlation analysis")
            
            # Generate sample correlation data (replace with actual analysis)
            import random
            correlation_matrix = []
            
            for i, ticker1 in enumerate(tickers):
                row = []
                for j, ticker2 in enumerate(tickers):
                    if i == j:
                        correlation = 1.0  # Perfect correlation with self
                    else:
                        # Generate realistic correlation values
                        correlation = random.uniform(-0.8, 0.9)
                        if abs(correlation) < 0.1:
                            correlation = random.uniform(-0.3, 0.3)  # Many stocks have low correlation
                    row.append(round(correlation, 2))
                correlation_matrix.append(row)
            
            # Prepare data for Plotly heatmap
            plotly_data = {
                'z': correlation_matrix,
                'x': tickers,
                'y': tickers,
                'type': 'heatmap',
                'colorscale': [
                    [0, '#ef4444'],      # Red for negative correlation
                    [0.5, '#ffffff'],    # White for no correlation
                    [1, '#10b981']       # Green for positive correlation
                ],
                'zmid': 0,
                'zmin': -1,
                'zmax': 1,
                'text': [[f'{val:.2f}' for val in row] for row in correlation_matrix],
                'texttemplate': '%{text}',
                'textfont': {'size': 12},
                'showscale': True,
                'colorbar': {
                    'title': 'Correlation',
                    'titlefont': {'size': 14}
                }
            }
            
            plotly_layout = {
                'title': {
                    'text': 'Ticker Correlation Heatmap',
                    'x': 0.5,
                    'font': {'size': 18}
                },
                'xaxis': {
                    'title': 'Tickers',
                    'side': 'bottom'
                },
                'yaxis': {
                    'title': 'Tickers'
                },
                'width': 600,
                'height': 600,
                'margin': {'l': 80, 'r': 80, 't': 80, 'b': 80}
            }
            
            return ChartData(
                chart_type='heatmap',
                title='Ticker Correlation Heatmap',
                data={'data': [plotly_data], 'layout': plotly_layout},
                options={},
                libraries=['plotly']
            )
            
        except Exception as e:
            return self._create_error_chart(f"Failed to generate correlation heatmap: {str(e)}")
    
    def generate_research_volume_chart(self) -> ChartData:
        """Generate bar chart showing research volume over time.
        
        Returns:
            ChartData object with research volume chart
        """
        try:
            # Get all research metrics
            all_metrics = self.analytics_engine.analyze_all_documents()
            
            if not all_metrics:
                return self._create_empty_chart("No research documents found")
            
            # Group by month
            monthly_counts = {}
            for metrics in all_metrics:
                if metrics.generated_date:
                    try:
                        date = datetime.fromisoformat(metrics.generated_date[:19])
                        month_key = date.strftime('%Y-%m')
                        monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1
                    except:
                        continue  # Skip invalid dates
            
            # Sort by date
            sorted_months = sorted(monthly_counts.items())
            
            if not sorted_months:
                return self._create_empty_chart("No valid research dates found")
            
            labels = [month for month, count in sorted_months]
            data = [count for month, count in sorted_months]
            
            chart_data = {
                'labels': labels,
                'datasets': [{
                    'label': 'Research Documents',
                    'data': data,
                    'backgroundColor': '#3b82f6',
                    'borderColor': '#1d4ed8',
                    'borderWidth': 1
                }]
            }
            
            chart_options = {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': 'Research Volume by Month',
                        'font': {'size': 16, 'weight': 'bold'}
                    },
                    'legend': {'display': False}
                },
                'scales': {
                    'x': {
                        'display': True,
                        'title': {'display': True, 'text': 'Month'}
                    },
                    'y': {
                        'display': True,
                        'title': {'display': True, 'text': 'Number of Documents'},
                        'beginAtZero': True
                    }
                }
            }
            
            return ChartData(
                chart_type='bar',
                title='Research Volume',
                data=chart_data,
                options=chart_options,
                libraries=['chartjs']
            )
            
        except Exception as e:
            return self._create_error_chart(f"Failed to generate research volume chart: {str(e)}")
    
    def generate_performance_scatter_plot(self, performance_data: List[Dict] = None) -> ChartData:
        """Generate scatter plot of thesis performance vs confidence.
        
        Args:
            performance_data: Optional list of performance data
            
        Returns:
            ChartData object with performance scatter plot
        """
        try:
            # Generate sample performance data if none provided
            if performance_data is None:
                import random
                performance_data = []
                
                for i in range(50):  # 50 sample data points
                    performance_data.append({
                        'confidence': random.uniform(0.3, 0.95),
                        'return_pct': random.uniform(-30, 50),
                        'ticker': f'TICK{i:02d}',
                        'thesis': f'Investment thesis {i}'
                    })
            
            # Prepare data for scatter plot
            chart_data = {
                'datasets': [{
                    'label': 'Thesis Performance',
                    'data': [
                        {
                            'x': item['confidence'] * 100,  # Convert to percentage
                            'y': item['return_pct'],
                            'label': item.get('ticker', f'Point {i}')
                        }
                        for i, item in enumerate(performance_data)
                    ],
                    'backgroundColor': 'rgba(59, 130, 246, 0.6)',
                    'borderColor': '#3b82f6',
                    'borderWidth': 1,
                    'pointRadius': 6,
                    'pointHoverRadius': 8
                }]
            }
            
            chart_options = {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': 'Investment Thesis Performance vs Confidence',
                        'font': {'size': 16, 'weight': 'bold'}
                    },
                    'legend': {'display': False},
                    'tooltip': {
                        'callbacks': {
                            'title': 'function(context) { return context[0].raw.label; }',
                            'label': 'function(context) { return "Confidence: " + context.parsed.x.toFixed(1) + "%, Return: " + context.parsed.y.toFixed(1) + "%"; }'
                        }
                    }
                },
                'scales': {
                    'x': {
                        'display': True,
                        'title': {'display': True, 'text': 'Confidence Level (%)'},
                        'min': 0,
                        'max': 100
                    },
                    'y': {
                        'display': True,
                        'title': {'display': True, 'text': 'Return (%)'},
                        'grid': {
                            'drawBorder': False,
                            'color': function(context) {
                                if (context.tick.value === 0) {
                                    return '#374151';  # Darker line for zero line
                                }
                                return '#e5e7eb';  # Light gray for other lines
                            }
                        }
                    }
                }
            }
            
            return ChartData(
                chart_type='scatter',
                title='Performance vs Confidence',
                data=chart_data,
                options=chart_options,
                libraries=['chartjs']
            )
            
        except Exception as e:
            return self._create_error_chart(f"Failed to generate performance scatter plot: {str(e)}")
    
    def generate_multi_ticker_comparison(self, tickers: List[str], metrics: List[str] = None) -> ChartData:
        """Generate multi-axis comparison chart for multiple tickers.
        
        Args:
            tickers: List of ticker symbols
            metrics: List of metrics to compare (e.g., ['price', 'volume', 'market_cap'])
            
        Returns:
            ChartData object with multi-ticker comparison
        """
        try:
            if not tickers:
                return self._create_empty_chart("No tickers provided for comparison")
            
            if metrics is None:
                metrics = ['price', 'market_cap', 'pe_ratio']
            
            # Generate sample data for each ticker and metric
            import random
            
            chart_data = {
                'labels': tickers,
                'datasets': []
            }
            
            colors = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6']
            
            for i, metric in enumerate(metrics):
                # Generate realistic sample data based on metric
                if metric == 'price':
                    data = [round(random.uniform(50, 500), 2) for _ in tickers]
                    unit = '$'
                elif metric == 'market_cap':
                    data = [round(random.uniform(10, 500), 1) for _ in tickers]  # Billions
                    unit = 'B'
                elif metric == 'pe_ratio':
                    data = [round(random.uniform(8, 40), 1) for _ in tickers]
                    unit = 'x'
                elif metric == 'volume':
                    data = [random.randint(100000, 10000000) for _ in tickers]
                    unit = ''
                else:
                    data = [round(random.uniform(1, 100), 2) for _ in tickers]
                    unit = ''
                
                dataset = {
                    'label': f'{metric.replace("_", " ").title()} ({unit})',
                    'data': data,
                    'backgroundColor': colors[i % len(colors)],
                    'borderColor': colors[i % len(colors)],
                    'borderWidth': 2,
                    'yAxisID': f'y{i+1}' if i > 0 else 'y'
                }
                
                chart_data['datasets'].append(dataset)
            
            # Create scale configurations for multiple y-axes
            y_axes = {
                'y': {
                    'type': 'linear',
                    'display': True,
                    'position': 'left',
                    'title': {'display': True, 'text': metrics[0].replace('_', ' ').title()}
                }
            }
            
            # Add additional y-axes for other metrics
            for i in range(1, len(metrics)):
                y_axes[f'y{i+1}'] = {
                    'type': 'linear',
                    'display': True,
                    'position': 'right',
                    'title': {'display': True, 'text': metrics[i].replace('_', ' ').title()},
                    'grid': {'drawOnChartArea': False}
                }
            
            chart_options = {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': 'Multi-Ticker Metrics Comparison',
                        'font': {'size': 16, 'weight': 'bold'}
                    },
                    'legend': {'display': True, 'position': 'top'}
                },
                'scales': {
                    'x': {
                        'display': True,
                        'title': {'display': True, 'text': 'Tickers'}
                    },
                    **y_axes
                }
            }
            
            return ChartData(
                chart_type='bar',
                title='Multi-Ticker Comparison',
                data=chart_data,
                options=chart_options,
                libraries=['chartjs']
            )
            
        except Exception as e:
            return self._create_error_chart(f"Failed to generate multi-ticker comparison: {str(e)}")
    
    def _create_empty_chart(self, message: str) -> ChartData:
        """Create an empty chart with a message.
        
        Args:
            message: Message to display
            
        Returns:
            ChartData object with empty chart
        """
        chart_data = {
            'labels': ['No Data'],
            'datasets': [{
                'label': 'No Data',
                'data': [0],
                'backgroundColor': '#d1d5db',
                'borderColor': '#9ca3af',
                'borderWidth': 1
            }]
        }
        
        chart_options = {
            'responsive': True,
            'maintainAspectRatio': False,
            'plugins': {
                'title': {
                    'display': True,
                    'text': message,
                    'font': {'size': 16, 'weight': 'bold'}
                },
                'legend': {'display': False}
            },
            'scales': {
                'y': {'display': False},
                'x': {'display': False}
            }
        }
        
        return ChartData(
            chart_type='bar',
            title='No Data Available',
            data=chart_data,
            options=chart_options,
            libraries=['chartjs']
        )
    
    def _create_error_chart(self, error_message: str) -> ChartData:
        """Create an error chart.
        
        Args:
            error_message: Error message to display
            
        Returns:
            ChartData object with error chart
        """
        return self._create_empty_chart(f"Error: {error_message}")
    
    def generate_dashboard_charts(self) -> Dict[str, ChartData]:
        """Generate a complete set of charts for the dashboard.
        
        Returns:
            Dictionary of chart names to ChartData objects
        """
        charts = {}
        
        try:
            # Load research metrics once for efficiency
            research_metrics = self.analytics_engine.analyze_all_documents()
            
            # Generate various charts
            charts['sector_distribution'] = self.generate_sector_distribution_chart(research_metrics)
            charts['quality_trends'] = self.generate_quality_trends_chart(days=30)
            charts['research_volume'] = self.generate_research_volume_chart()
            charts['performance_scatter'] = self.generate_performance_scatter_plot()
            
            # Add sample ticker charts
            sample_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'][:3]  # Limit for performance
            if sample_tickers:
                charts['price_chart'] = self.generate_price_chart(sample_tickers[0])
                charts['ticker_comparison'] = self.generate_multi_ticker_comparison(sample_tickers)
                
                if len(sample_tickers) >= 2:
                    charts['correlation_heatmap'] = self.generate_ticker_correlation_heatmap(sample_tickers)
            
        except Exception as e:
            print(f"Error generating dashboard charts: {e}")
            # Return at least one error chart
            charts['error'] = self._create_error_chart("Failed to generate dashboard charts")
        
        return charts
    
    def export_chart_data(self, chart_data: ChartData, filename: str) -> Path:
        """Export chart data to JSON file.
        
        Args:
            chart_data: ChartData object to export
            filename: Output filename (without extension)
            
        Returns:
            Path to exported file
        """
        output_path = self.charts_dir / f"{filename}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chart_data.to_dict(), f, indent=2, ensure_ascii=False)
        
        return output_path