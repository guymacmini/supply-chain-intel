#!/usr/bin/env python3
"""End-to-End tests for Flask web application."""

import pytest
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.web.app import app
from src.utils.watchlist_manager import WatchlistManager
from src.models import WatchlistEntity


class TestFlaskApp:
    """End-to-End tests for the Flask application."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        with app.test_client() as client:
            with app.app_context():
                yield client
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create temporary data directory with sample research file."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create data directory structure
        research_dir = temp_dir / 'research'
        research_dir.mkdir(parents=True)
        
        # Create sample research file
        sample_research = """---
depth: 2
generated: '2026-02-02T13:39:22.134101'
model: claude-opus-4-5-20251101
query: Test Query
theme: Test Theme
tickers_found: 5
tool_calls: 10
type: research
---

# Test Research Report
**Generated**: 2026-02-02 13:35
**Depth**: 2-level analysis

## 📌 TLDR
This is a test research report for end-to-end testing.

## Analysis
Sample analysis content with some data.

### Key Companies
- AAPL (Apple Inc.)
- MSFT (Microsoft)

| Ticker | Company | P/E Ratio |
|--------|---------|-----------|
| AAPL   | Apple   | 28.5      |
| MSFT   | Microsoft | 32.1    |

## Conclusion
Test conclusion.
"""
        
        sample_file = research_dir / 'test_research_20260202_133922.md'
        sample_file.write_text(sample_research)
        
        # Mock the DATA_DIR in the app module and create fresh watchlist manager
        with patch('src.web.app.DATA_DIR', temp_dir):
            with patch('src.web.app.watchlist_manager', WatchlistManager(data_dir=temp_dir)):
                yield temp_dir
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
    
    def test_index_route(self, client, temp_data_dir):
        """Test the main index route returns 200."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Supply Chain Intel' in response.data
        assert b'Dashboard' in response.data or b'research' in response.data.lower()
    
    def test_explore_page(self, client, temp_data_dir):
        """Test explore page loads correctly."""
        response = client.get('/explore')
        assert response.status_code == 200
        assert b'explore' in response.data.lower() or b'research' in response.data.lower()
    
    def test_thesis_page(self, client, temp_data_dir):
        """Test thesis page loads correctly.""" 
        response = client.get('/thesis')
        assert response.status_code == 200
        assert b'thesis' in response.data.lower()
    
    def test_monitor_page(self, client, temp_data_dir):
        """Test monitor page loads correctly."""
        response = client.get('/monitor')
        assert response.status_code == 200
        assert b'monitor' in response.data.lower() or b'digest' in response.data.lower()
    
    def test_watchlist_page(self, client, temp_data_dir):
        """Test watchlist page loads correctly."""
        response = client.get('/watchlist')
        assert response.status_code == 200
        assert b'watchlist' in response.data.lower()
    
    def test_history_page(self, client, temp_data_dir):
        """Test history page loads correctly."""
        response = client.get('/history')
        assert response.status_code == 200
        assert b'history' in response.data.lower() or b'documents' in response.data.lower()
    
    def test_view_research_existing_file(self, client, temp_data_dir):
        """Test viewing an existing research file."""
        response = client.get('/research/test_research_20260202_133922.md')
        assert response.status_code == 200
        assert b'Test Research Report' in response.data
        assert b'Export PDF' in response.data
        assert b'TLDR' in response.data
    
    def test_view_research_nonexistent_file(self, client, temp_data_dir):
        """Test viewing a nonexistent research file returns 404."""
        response = client.get('/research/nonexistent_file.md')
        assert response.status_code == 404
        assert b'not found' in response.data.lower()
    
    def test_pdf_export_existing_file(self, client, temp_data_dir):
        """Test PDF export for existing research file."""
        response = client.get('/export/test_research_20260202_133922.md/pdf')
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/pdf'
        assert 'attachment' in response.headers['Content-Disposition']
        assert 'test_research_20260202_133922.pdf' in response.headers['Content-Disposition']
        
        # Check that actual PDF content is returned
        assert response.data.startswith(b'%PDF-')  # PDF file signature
        assert len(response.data) > 1000  # Should be substantial content
    
    def test_pdf_export_nonexistent_file(self, client, temp_data_dir):
        """Test PDF export for nonexistent file returns 404."""
        response = client.get('/export/nonexistent_file.md/pdf')
        assert response.status_code == 404
        assert b'not found' in response.data.lower()
    
    def test_api_get_watchlist(self, client, temp_data_dir):
        """Test getting watchlist via API."""
        response = client.get('/api/watchlist')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
    
    def test_api_add_to_watchlist(self, client, temp_data_dir):
        """Test adding entity to watchlist."""
        payload = {
            'ticker': 'AAPL',
            'name': 'Apple Inc.',
            'themes': ['Consumer Electronics', 'Tech']
        }
        response = client.post('/api/watchlist', 
                             json=payload,
                             content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'AAPL' in data['message']
    
    def test_api_add_to_watchlist_missing_ticker(self, client, temp_data_dir):
        """Test adding to watchlist without ticker returns error."""
        payload = {'name': 'Test Company'}
        response = client.post('/api/watchlist',
                             json=payload,
                             content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'ticker' in data['error'].lower()
    
    def test_api_remove_from_watchlist(self, client, temp_data_dir):
        """Test removing entity from watchlist."""
        # First add an entity
        payload = {'ticker': 'MSFT', 'name': 'Microsoft'}
        client.post('/api/watchlist', json=payload, content_type='application/json')
        
        # Then remove it
        response = client.delete('/api/watchlist/MSFT')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'MSFT' in data['message']


class TestFlaskAppExploreAPI:
    """Test explore API endpoints with mocked agents."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        with app.test_client() as client:
            with app.app_context():
                yield client
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create temporary data directory."""
        temp_dir = Path(tempfile.mkdtemp())
        research_dir = temp_dir / 'research'
        research_dir.mkdir(parents=True)
        
        with patch('src.web.app.DATA_DIR', temp_dir):
            yield temp_dir
        
        import shutil
        shutil.rmtree(temp_dir)
    
    @patch('src.web.app.ExploreAgent')
    def test_api_explore_success(self, mock_agent_class, client, temp_data_dir):
        """Test successful explore API call."""
        # Mock the agent
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        # Create a mock output file
        output_file = temp_data_dir / 'research' / 'mock_output_20260202_133922.md'
        output_file.write_text("# Mock Research Output\nThis is mock research content.")
        mock_agent.run.return_value = output_file
        
        payload = {
            'query': 'artificial intelligence companies',
            'depth': 2
        }
        
        response = client.post('/api/explore',
                             json=payload,
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'content' in data
        assert 'Mock Research Output' in data['content']
        
        # Verify agent was called correctly
        mock_agent.run.assert_called_once_with('artificial intelligence companies', depth=2)
    
    def test_api_explore_missing_query(self, client, temp_data_dir):
        """Test explore API with missing query."""
        payload = {'depth': 2}
        
        response = client.post('/api/explore',
                             json=payload,
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'query' in data['error'].lower()
    
    @patch('src.web.app.ExploreAgent')
    def test_api_explore_agent_error(self, mock_agent_class, client, temp_data_dir):
        """Test explore API when agent raises exception."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.run.side_effect = Exception("Mock agent error")
        
        payload = {
            'query': 'test query',
            'depth': 1
        }
        
        response = client.post('/api/explore',
                             json=payload,
                             content_type='application/json')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Mock agent error' in data['error']


class TestFlaskAppMonitorAPI:
    """Test monitor API endpoints with mocked agents."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        with app.test_client() as client:
            with app.app_context():
                yield client
    
    @pytest.fixture 
    def temp_data_dir(self):
        """Create temporary data directory."""
        temp_dir = Path(tempfile.mkdtemp())
        digests_dir = temp_dir / 'digests'
        digests_dir.mkdir(parents=True)
        
        with patch('src.web.app.DATA_DIR', temp_dir):
            yield temp_dir
        
        import shutil
        shutil.rmtree(temp_dir)
    
    @patch('src.web.app.MonitorAgent')
    def test_api_monitor_success(self, mock_agent_class, client, temp_data_dir):
        """Test successful monitor API call."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        # Create a mock digest file
        digest_file = temp_data_dir / 'digests' / 'digest_20260202_133922.md'
        digest_file.write_text("# Mock Digest\nMock digest content.")
        mock_agent.run.return_value = digest_file
        
        response = client.post('/api/monitor')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'content' in data
        assert 'Mock Digest' in data['content']
        
        mock_agent.run.assert_called_once()


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])