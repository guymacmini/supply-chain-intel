"""Tests for the interactive chart generation functionality."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.utils.chart_generator import InteractiveChartGenerator, ChartData
from src.utils.research_analytics import ResearchMetrics
from src.utils.finnhub_client import FinnhubClient


@pytest.fixture
def temp_data_dir():
    """Create a temporary data directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_finnhub_client():
    """Create a mock Finnhub client for testing."""
    client = Mock(spec=FinnhubClient)
    client.get_quote.return_value = {
        'c': 150.00,  # Current price
        'pc': 145.00,  # Previous close
        'h': 152.00,   # High
        'l': 148.00,   # Low
        'o': 149.00,   # Open
        'volume': 1000000
    }
    return client


@pytest.fixture
def chart_generator(temp_data_dir, mock_finnhub_client):
    """Create a chart generator for testing."""
    return InteractiveChartGenerator(temp_data_dir, mock_finnhub_client)


@pytest.fixture
def sample_research_metrics():
    """Create sample research metrics for testing."""
    return [
        ResearchMetrics(
            filename='ai_revolution.md',
            theme='AI & Automation',
            generated_date='2024-02-01T10:00:00',
            word_count=8500,
            ticker_count=12,
            table_count=4,
            section_count=8,
            tldr_length=250,
            sources_count=15,
            thesis_count=3,
            confidence_keywords=8,
            sentiment_score=0.6,
            complexity_score=0.7,
            quality_score=0.85
        ),
        ResearchMetrics(
            filename='renewable_energy.md',
            theme='Clean Energy',
            generated_date='2024-02-02T14:30:00',
            word_count=7200,
            ticker_count=8,
            table_count=3,
            section_count=6,
            tldr_length=180,
            sources_count=12,
            thesis_count=2,
            confidence_keywords=6,
            sentiment_score=0.8,
            complexity_score=0.6,
            quality_score=0.78
        ),
        ResearchMetrics(
            filename='semiconductor_shortage.md',
            theme='Semiconductors',
            generated_date='2024-02-03T09:15:00',
            word_count=9100,
            ticker_count=15,
            table_count=5,
            section_count=10,
            tldr_length=300,
            sources_count=18,
            thesis_count=4,
            confidence_keywords=12,
            sentiment_score=0.2,
            complexity_score=0.8,
            quality_score=0.92
        )
    ]


class TestChartData:
    """Test ChartData functionality."""
    
    def test_chart_data_creation(self):
        """Test creating a ChartData object."""
        data = ChartData(
            chart_type='line',
            title='Test Chart',
            data={'labels': ['A', 'B'], 'datasets': []},
            options={'responsive': True},
            libraries=['chartjs']
        )
        
        assert data.chart_type == 'line'
        assert data.title == 'Test Chart'
        assert data.data['labels'] == ['A', 'B']
        assert data.options['responsive'] is True
        assert data.libraries == ['chartjs']
    
    def test_chart_data_serialization(self):
        """Test ChartData to_dict method."""
        data = ChartData(
            chart_type='bar',
            title='Bar Chart',
            data={'datasets': [{'data': [1, 2, 3]}]},
            options={'scales': {'y': {'beginAtZero': True}}},
            libraries=['chartjs']
        )
        
        result = data.to_dict()
        
        assert isinstance(result, dict)
        assert result['chart_type'] == 'bar'
        assert result['title'] == 'Bar Chart'
        assert result['data']['datasets'][0]['data'] == [1, 2, 3]
        assert result['options']['scales']['y']['beginAtZero'] is True


class TestInteractiveChartGenerator:
    """Test chart generation functionality."""
    
    def test_generator_initialization(self, temp_data_dir, mock_finnhub_client):
        """Test chart generator initialization."""
        generator = InteractiveChartGenerator(temp_data_dir, mock_finnhub_client)
        
        assert generator.data_dir == temp_data_dir
        assert generator.research_dir == temp_data_dir / 'research'
        assert generator.charts_dir == temp_data_dir / 'charts'
        assert generator.finnhub_client == mock_finnhub_client
        
        # Check directories are created
        assert generator.charts_dir.exists()
    
    def test_price_chart_generation(self, chart_generator):
        """Test generating a price chart."""
        chart_data = chart_generator.generate_price_chart('AAPL', period_days=30)
        
        assert isinstance(chart_data, ChartData)
        assert chart_data.chart_type == 'line'
        assert 'AAPL' in chart_data.title
        assert 'chartjs' in chart_data.libraries
        
        # Check data structure
        assert 'labels' in chart_data.data
        assert 'datasets' in chart_data.data
        assert len(chart_data.data['datasets']) > 0
        
        # Check options
        assert 'responsive' in chart_data.options
        assert chart_data.options['responsive'] is True
        assert 'plugins' in chart_data.options
        assert 'scales' in chart_data.options
    
    def test_sector_distribution_chart(self, chart_generator, sample_research_metrics):
        """Test generating sector distribution chart."""
        with patch.object(chart_generator.analytics_engine, 'analyze_all_documents', 
                         return_value=sample_research_metrics):
            
            chart_data = chart_generator.generate_sector_distribution_chart()
            
            assert isinstance(chart_data, ChartData)
            assert chart_data.chart_type == 'doughnut'
            assert 'Research Distribution' in chart_data.title
            
            # Check data contains the themes from sample metrics
            labels = chart_data.data['labels']
            assert 'AI & Automation' in labels
            assert 'Clean Energy' in labels
            assert 'Semiconductors' in labels
            
            # Check dataset structure
            datasets = chart_data.data['datasets']
            assert len(datasets) == 1
            assert 'data' in datasets[0]
            assert 'backgroundColor' in datasets[0]
    
    def test_empty_sector_distribution(self, chart_generator):
        """Test sector distribution chart with no data."""
        with patch.object(chart_generator.analytics_engine, 'analyze_all_documents', 
                         return_value=[]):
            
            chart_data = chart_generator.generate_sector_distribution_chart()
            
            assert isinstance(chart_data, ChartData)
            assert 'No research data available' in chart_data.title
            assert chart_data.data['labels'] == ['No Data']
    
    def test_quality_trends_chart(self, chart_generator):
        """Test generating quality trends chart."""
        # Mock the quality trends data
        mock_trends = {
            'dates': ['2024-02-01', '2024-02-02', '2024-02-03'],
            'quality_scores': [0.85, 0.78, 0.92],
            'word_counts': [8500, 7200, 9100],
            'ticker_counts': [12, 8, 15],
            'sources_counts': [15, 12, 18]
        }
        
        with patch.object(chart_generator.analytics_engine, 'get_quality_trends', 
                         return_value=mock_trends):
            
            chart_data = chart_generator.generate_quality_trends_chart(days=30)
            
            assert isinstance(chart_data, ChartData)
            assert chart_data.chart_type == 'line'
            assert '30 Days' in chart_data.title
            
            # Check data structure
            assert chart_data.data['labels'] == mock_trends['dates']
            datasets = chart_data.data['datasets']
            assert len(datasets) == 2  # Quality score and word count
            
            # Check quality score dataset
            quality_dataset = datasets[0]
            assert 'Quality Score' in quality_dataset['label']
            assert quality_dataset['data'] == mock_trends['quality_scores']
    
    def test_research_volume_chart(self, chart_generator, sample_research_metrics):
        """Test generating research volume chart."""
        with patch.object(chart_generator.analytics_engine, 'analyze_all_documents', 
                         return_value=sample_research_metrics):
            
            chart_data = chart_generator.generate_research_volume_chart()
            
            assert isinstance(chart_data, ChartData)
            assert chart_data.chart_type == 'bar'
            assert 'Research Volume' in chart_data.title
            
            # Should have monthly data
            assert 'labels' in chart_data.data
            assert len(chart_data.data['labels']) > 0
            
            # Check dataset
            datasets = chart_data.data['datasets']
            assert len(datasets) == 1
            assert 'Research Documents' in datasets[0]['label']
    
    def test_ticker_correlation_heatmap(self, chart_generator):
        """Test generating correlation heatmap."""
        tickers = ['AAPL', 'MSFT', 'GOOGL']
        chart_data = chart_generator.generate_ticker_correlation_heatmap(tickers)
        
        assert isinstance(chart_data, ChartData)
        assert chart_data.chart_type == 'heatmap'
        assert 'Correlation Heatmap' in chart_data.title
        assert 'plotly' in chart_data.libraries
        
        # Check Plotly data structure
        plotly_data = chart_data.data['data'][0]
        assert plotly_data['type'] == 'heatmap'
        assert plotly_data['x'] == tickers
        assert plotly_data['y'] == tickers
        assert len(plotly_data['z']) == len(tickers)  # Square matrix
        assert len(plotly_data['z'][0]) == len(tickers)
    
    def test_correlation_heatmap_insufficient_tickers(self, chart_generator):
        """Test correlation heatmap with insufficient tickers."""
        chart_data = chart_generator.generate_ticker_correlation_heatmap(['AAPL'])
        
        assert isinstance(chart_data, ChartData)
        assert 'Need at least 2 tickers' in chart_data.title
    
    def test_performance_scatter_plot(self, chart_generator):
        """Test generating performance scatter plot."""
        # Provide custom performance data
        performance_data = [
            {'confidence': 0.8, 'return_pct': 15.5, 'ticker': 'AAPL'},
            {'confidence': 0.6, 'return_pct': -5.2, 'ticker': 'MSFT'},
            {'confidence': 0.9, 'return_pct': 25.1, 'ticker': 'GOOGL'}
        ]
        
        chart_data = chart_generator.generate_performance_scatter_plot(performance_data)
        
        assert isinstance(chart_data, ChartData)
        assert chart_data.chart_type == 'scatter'
        assert 'Performance vs Confidence' in chart_data.title
        
        # Check data structure
        datasets = chart_data.data['datasets']
        assert len(datasets) == 1
        
        dataset = datasets[0]
        assert len(dataset['data']) == 3
        
        # Check data points
        point1 = dataset['data'][0]
        assert point1['x'] == 80.0  # 0.8 * 100
        assert point1['y'] == 15.5
        assert point1['label'] == 'AAPL'
    
    def test_multi_ticker_comparison(self, chart_generator):
        """Test generating multi-ticker comparison chart."""
        tickers = ['AAPL', 'MSFT', 'GOOGL']
        metrics = ['price', 'market_cap', 'pe_ratio']
        
        chart_data = chart_generator.generate_multi_ticker_comparison(tickers, metrics)
        
        assert isinstance(chart_data, ChartData)
        assert chart_data.chart_type == 'bar'
        assert 'Multi-Ticker Comparison' in chart_data.title
        
        # Check data structure
        assert chart_data.data['labels'] == tickers
        datasets = chart_data.data['datasets']
        assert len(datasets) == len(metrics)
        
        # Check each metric has a dataset
        metric_labels = [dataset['label'] for dataset in datasets]
        assert any('Price' in label for label in metric_labels)
        assert any('Market Cap' in label for label in metric_labels)
        assert any('Pe Ratio' in label for label in metric_labels)
        
        # Check scales configuration
        scales = chart_data.options['scales']
        assert 'y' in scales
        assert 'y2' in scales  # Multiple y-axes
        assert 'y3' in scales
    
    def test_empty_ticker_comparison(self, chart_generator):
        """Test multi-ticker comparison with empty ticker list."""
        chart_data = chart_generator.generate_multi_ticker_comparison([])
        
        assert isinstance(chart_data, ChartData)
        assert 'No tickers provided' in chart_data.title
    
    def test_dashboard_charts_generation(self, chart_generator, sample_research_metrics):
        """Test generating complete dashboard charts."""
        with patch.object(chart_generator.analytics_engine, 'analyze_all_documents', 
                         return_value=sample_research_metrics):
            with patch.object(chart_generator.analytics_engine, 'get_quality_trends',
                             return_value={'dates': [], 'quality_scores': [], 'word_counts': [], 
                                         'ticker_counts': [], 'sources_counts': []}):
                
                charts = chart_generator.generate_dashboard_charts()
                
                assert isinstance(charts, dict)
                assert len(charts) > 0
                
                # Check that key charts are included
                expected_charts = ['sector_distribution', 'quality_trends', 'research_volume']
                for chart_name in expected_charts:
                    assert chart_name in charts
                    assert isinstance(charts[chart_name], ChartData)
    
    def test_chart_export(self, chart_generator):
        """Test exporting chart data to file."""
        chart_data = chart_generator.generate_price_chart('AAPL')
        
        # Export the chart
        output_path = chart_generator.export_chart_data(chart_data, 'test_chart')
        
        assert output_path.exists()
        assert output_path.suffix == '.json'
        
        # Verify exported content
        with open(output_path, 'r') as f:
            exported_data = json.load(f)
        
        assert exported_data['chart_type'] == chart_data.chart_type
        assert exported_data['title'] == chart_data.title
        assert 'data' in exported_data
        assert 'options' in exported_data
    
    def test_error_handling_in_chart_generation(self, chart_generator):
        """Test error handling when chart generation fails."""
        # Mock analytics engine to raise exception
        with patch.object(chart_generator.analytics_engine, 'analyze_all_documents',
                         side_effect=Exception("Test error")):
            
            chart_data = chart_generator.generate_sector_distribution_chart()
            
            # Should return error chart instead of crashing
            assert isinstance(chart_data, ChartData)
            assert 'Error:' in chart_data.title
    
    def test_create_empty_chart(self, chart_generator):
        """Test creating empty chart with message."""
        message = "No data available for analysis"
        chart_data = chart_generator._create_empty_chart(message)
        
        assert isinstance(chart_data, ChartData)
        assert chart_data.title == message
        assert chart_data.chart_type == 'bar'
        assert chart_data.data['labels'] == ['No Data']
        assert chart_data.data['datasets'][0]['data'] == [0]
    
    def test_create_error_chart(self, chart_generator):
        """Test creating error chart."""
        error_message = "API connection failed"
        chart_data = chart_generator._create_error_chart(error_message)
        
        assert isinstance(chart_data, ChartData)
        assert f"Error: {error_message}" == chart_data.title
        assert chart_data.chart_type == 'bar'


class TestChartIntegration:
    """Integration tests for chart generation."""
    
    def test_end_to_end_chart_generation(self, temp_data_dir):
        """Test complete chart generation workflow."""
        # Create some research files to work with
        research_dir = temp_data_dir / 'research'
        research_dir.mkdir(parents=True)
        
        # Create sample research file
        sample_research = research_dir / 'test_research.md'
        sample_research.write_text("""
        # Investment Research: AI Revolution
        
        **TLDR:** AI companies show strong growth potential despite recent volatility.
        
        ## Analysis
        
        | Company | Ticker | Market Cap | P/E Ratio |
        |---------|--------|------------|-----------|
        | NVIDIA  | NVDA   | $1.5T     | 65        |
        | Microsoft | MSFT | $2.8T     | 28        |
        
        ## Sources
        1. Company earnings reports
        2. Industry analysis from Goldman Sachs
        3. Market data from Yahoo Finance
        """)
        
        # Mock Finnhub client
        mock_client = Mock(spec=FinnhubClient)
        mock_client.get_quote.return_value = {
            'c': 450.00, 'pc': 440.00, 'h': 455.00, 'l': 445.00, 'volume': 2000000
        }
        
        # Create generator and generate charts
        generator = InteractiveChartGenerator(temp_data_dir, mock_client)
        
        # Generate various charts
        price_chart = generator.generate_price_chart('NVDA', 90)
        sector_chart = generator.generate_sector_distribution_chart()
        volume_chart = generator.generate_research_volume_chart()
        
        # Verify all charts were generated successfully
        assert isinstance(price_chart, ChartData)
        assert isinstance(sector_chart, ChartData)
        assert isinstance(volume_chart, ChartData)
        
        # Verify chart data is properly structured
        assert price_chart.chart_type == 'line'
        assert 'NVDA' in price_chart.title
        assert len(price_chart.data['datasets']) > 0
        
        # Test export functionality
        export_path = generator.export_chart_data(price_chart, 'integration_test')
        assert export_path.exists()
        
        # Verify exported file content
        with open(export_path, 'r') as f:
            exported = json.load(f)
            assert exported['chart_type'] == price_chart.chart_type
    
    def test_chart_generation_with_real_analytics(self, temp_data_dir):
        """Test chart generation with real analytics engine."""
        # Create research directory and sample files
        research_dir = temp_data_dir / 'research'
        research_dir.mkdir(parents=True)
        
        # Create multiple research files with different themes
        files = [
            ('ai_research.md', 'AI & Machine Learning'),
            ('energy_research.md', 'Clean Energy'),
            ('semiconductor_research.md', 'Semiconductors')
        ]
        
        for filename, theme in files:
            research_file = research_dir / filename
            research_file.write_text(f"""
            # Investment Research: {theme}
            
            **TLDR:** Analysis of {theme.lower()} sector opportunities.
            
            ## Market Analysis
            
            This research covers the {theme.lower()} market trends and investment opportunities.
            
            | Metric | Value |
            |--------|-------|
            | Market Size | $100B |
            | Growth Rate | 15% |
            
            ## Investment Thesis
            
            Strong growth potential in {theme.lower()} sector.
            
            ## Sources
            1. Industry reports
            2. Company filings
            3. Market analysis
            """)
        
        # Create generator with real analytics
        mock_client = Mock(spec=FinnhubClient)
        generator = InteractiveChartGenerator(temp_data_dir, mock_client)
        
        # Generate dashboard charts
        dashboard_charts = generator.generate_dashboard_charts()
        
        # Verify charts were generated
        assert isinstance(dashboard_charts, dict)
        assert len(dashboard_charts) > 0
        
        # Check specific charts
        if 'sector_distribution' in dashboard_charts:
            sector_chart = dashboard_charts['sector_distribution']
            # Should have detected the different themes
            themes_found = sector_chart.data.get('labels', [])
            assert len(themes_found) > 0
        
        if 'research_volume' in dashboard_charts:
            volume_chart = dashboard_charts['research_volume']
            assert volume_chart.chart_type == 'bar'
    
    def test_performance_with_large_dataset(self, temp_data_dir):
        """Test chart generation performance with larger dataset."""
        # Create larger sample dataset
        performance_data = []
        for i in range(1000):
            performance_data.append({
                'confidence': 0.3 + (i % 70) / 100.0,  # 0.3 to 1.0
                'return_pct': -30 + (i % 81),  # -30% to +50%
                'ticker': f'STOCK{i:04d}',
                'thesis': f'Investment thesis {i}'
            })
        
        mock_client = Mock(spec=FinnhubClient)
        generator = InteractiveChartGenerator(temp_data_dir, mock_client)
        
        # Generate scatter plot with large dataset
        chart_data = generator.generate_performance_scatter_plot(performance_data)
        
        # Should complete without errors
        assert isinstance(chart_data, ChartData)
        assert chart_data.chart_type == 'scatter'
        assert len(chart_data.data['datasets'][0]['data']) == 1000
        
        # Verify data structure is correct
        data_points = chart_data.data['datasets'][0]['data']
        assert all('x' in point and 'y' in point and 'label' in point for point in data_points)
    
    def test_multiple_chart_export(self, temp_data_dir):
        """Test exporting multiple charts."""
        mock_client = Mock(spec=FinnhubClient)
        generator = InteractiveChartGenerator(temp_data_dir, mock_client)
        
        # Generate multiple charts
        charts = {
            'price_chart': generator.generate_price_chart('AAPL'),
            'sector_chart': generator.generate_sector_distribution_chart(),
            'performance_chart': generator.generate_performance_scatter_plot()
        }
        
        # Export each chart
        exported_files = []
        for name, chart_data in charts.items():
            export_path = generator.export_chart_data(chart_data, f'multi_export_{name}')
            exported_files.append(export_path)
            assert export_path.exists()
        
        # Verify all files were created and contain valid JSON
        for file_path in exported_files:
            with open(file_path, 'r') as f:
                data = json.load(f)
                assert 'chart_type' in data
                assert 'title' in data
                assert 'data' in data
                assert 'options' in data