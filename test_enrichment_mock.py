#!/usr/bin/env python3
"""Test enhanced ticker enrichment with mock data."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.agents.explore_agent import ExploreAgent
from unittest.mock import Mock

def test_enhanced_market_section_with_mock():
    """Test the enhanced market section with mock data."""
    print("Testing enhanced market section with mock data...")
    
    agent = ExploreAgent()
    
    # Mock the Finnhub client
    mock_client = Mock()
    mock_client.is_available.return_value = True
    
    # Create mock enhanced data
    mock_data = {
        'AAPL': {
            'ticker': 'AAPL',
            'current_price': 185.50,
            '52_week_high': 198.23,
            '52_week_low': 164.08,
            'pe_ratio': 28.5,
            'market_cap': 2850000,  # $2.85T in millions
            'market_cap_tier': 'mega',
            'sector': 'Technology Hardware & Equipment',
            'industry': 'Technology Hardware, Storage & Peripherals',
            'country': 'US',
            'revenue_ttm': 391000,  # $391B in millions
            'revenue_growth': 8.2,
            'eps_ttm': 6.43
        },
        'NVDA': {
            'ticker': 'NVDA', 
            'current_price': 875.30,
            '52_week_high': 890.45,
            '52_week_low': 390.25,
            'pe_ratio': 55.2,
            'market_cap': 2200000,  # $2.2T in millions
            'market_cap_tier': 'mega',
            'sector': 'Semiconductors & Semiconductor Equipment',
            'industry': 'Semiconductors',
            'country': 'US',
            'revenue_ttm': 95000,  # $95B in millions
            'revenue_growth': 122.4,
            'eps_ttm': 15.25
        },
        'TSLA': {
            'ticker': 'TSLA',
            'current_price': 208.50,
            '52_week_high': 271.20,
            '52_week_low': 152.37,
            'pe_ratio': 42.8,
            'market_cap': 665000,  # $665B in millions
            'market_cap_tier': 'mega',
            'sector': 'Automobiles & Components',
            'industry': 'Automobiles',
            'country': 'US',
            'revenue_ttm': 98000,  # $98B in millions
            'revenue_growth': 19.3,
            'eps_ttm': 4.87
        }
    }
    
    mock_client.get_market_data_for_tickers.return_value = mock_data
    agent.finnhub_client = mock_client
    
    # Test the enhanced market section
    tickers = ['AAPL', 'NVDA', 'TSLA']
    market_section = agent._generate_market_valuation_section(tickers)
    
    if not market_section:
        print("❌ Failed to generate market section")
        return False
    
    print("✅ Successfully generated enhanced market section")
    
    # Check for enhanced features
    enhanced_features = [
        "Enhanced Market Data & Company Profiles",
        "Trading & Valuation Metrics",
        "Company Profiles & Fundamentals", 
        "Tier",
        "Sector Exposure",
        "Geographic Exposure",
        "Market Cap Distribution"
    ]
    
    print("\nChecking for enhanced features:")
    all_present = True
    for feature in enhanced_features:
        if feature in market_section:
            print(f"   ✅ {feature}")
        else:
            print(f"   ❌ {feature} - MISSING")
            all_present = False
    
    # Print sample output
    print("\n" + "="*50)
    print("SAMPLE OUTPUT:")
    print("="*50)
    print(market_section)
    
    return all_present

def main():
    """Run the mock test."""
    print("Enhanced Ticker Enrichment Mock Test")
    print("="*50)
    
    try:
        success = test_enhanced_market_section_with_mock()
        if success:
            print("\n✅ Enhanced ticker enrichment implementation verified!")
        else:
            print("\n❌ Some features missing in implementation")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()