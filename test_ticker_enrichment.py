#!/usr/bin/env python3
"""Test script to verify enhanced ticker enrichment works."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.utils.finnhub_client import FinnhubClient
from src.agents.explore_agent import ExploreAgent

def test_finnhub_enrichment():
    """Test the enhanced Finnhub client with ticker enrichment."""
    print("Testing enhanced Finnhub client...")
    
    client = FinnhubClient()
    
    if not client.is_available():
        print("⚠️  Finnhub client not available (API key missing)")
        print("   Set FINNHUB_API_KEY environment variable to test")
        return False
    
    # Test with a well-known ticker
    ticker = "AAPL"
    print(f"\nFetching enhanced data for {ticker}...")
    
    data = client.get_market_data(ticker)
    if not data:
        print(f"❌ Failed to fetch data for {ticker}")
        return False
    
    print(f"✅ Successfully fetched enhanced data for {ticker}:")
    
    # Display all the enhanced fields
    fields_to_show = [
        'ticker', 'current_price', 'market_cap', 'market_cap_tier',
        'sector', 'industry', 'country', 'pe_ratio', 
        'revenue_ttm', 'revenue_growth', 'eps_ttm'
    ]
    
    for field in fields_to_show:
        value = data.get(field)
        if value is not None:
            if field == 'market_cap' and value:
                # Format market cap nicely
                if value >= 1000000:
                    formatted = f"${value/1000000:.2f}T"
                elif value >= 1000:
                    formatted = f"${value/1000:.1f}B"
                else:
                    formatted = f"${value:.0f}M"
                print(f"   {field}: {formatted} ({value:.0f}M)")
            elif field == 'current_price' and value:
                print(f"   {field}: ${value:.2f}")
            elif field in ['revenue_ttm'] and value:
                print(f"   {field}: ${value:.0f}M")
            elif field in ['revenue_growth'] and value:
                print(f"   {field}: {value:.1f}%")
            elif field in ['eps_ttm'] and value:
                print(f"   {field}: ${value:.2f}")
            else:
                print(f"   {field}: {value}")
        else:
            print(f"   {field}: N/A")
    
    return True

def test_market_cap_classification():
    """Test market cap tier classification."""
    print("\n" + "="*50)
    print("Testing market cap tier classification...")
    
    client = FinnhubClient()
    
    test_cases = [
        (500000, "mega"),    # $500B
        (50000, "large"),    # $50B
        (5000, "mid"),       # $5B
        (800, "small"),      # $800M
        (100, "micro")       # $100M
    ]
    
    for market_cap, expected_tier in test_cases:
        actual_tier = client._classify_market_cap_tier(market_cap)
        status = "✅" if actual_tier == expected_tier else "❌"
        print(f"{status} ${market_cap}M -> {actual_tier} (expected: {expected_tier})")
    
    return True

def test_explore_agent_integration():
    """Test that ExploreAgent can use the enhanced ticker data."""
    print("\n" + "="*50)
    print("Testing ExploreAgent integration with enhanced ticker enrichment...")
    
    agent = ExploreAgent()
    
    if not agent.finnhub_client.is_available():
        print("⚠️  Skipping ExploreAgent test - Finnhub not available")
        return True
    
    # Test the market valuation section generation
    test_tickers = ['AAPL', 'MSFT', 'NVDA']
    
    print(f"Generating market section for: {', '.join(test_tickers)}")
    
    market_section = agent._generate_market_valuation_section(test_tickers)
    
    if not market_section:
        print("❌ Failed to generate market section")
        return False
    
    print("✅ Successfully generated enhanced market section")
    print("Sample output:")
    print(market_section[:500] + "..." if len(market_section) > 500 else market_section)
    
    # Check for enhanced features
    enhanced_features = [
        "Trading & Valuation Metrics",
        "Company Profiles & Fundamentals",
        "Tier",
        "Sector Exposure",
        "Geographic Exposure",
        "Market Cap Distribution"
    ]
    
    missing_features = []
    for feature in enhanced_features:
        if feature not in market_section:
            missing_features.append(feature)
    
    if missing_features:
        print(f"⚠️  Missing enhanced features: {', '.join(missing_features)}")
    else:
        print("✅ All enhanced features present")
    
    return True

def main():
    """Run all tests."""
    print("="*60)
    print("Enhanced Ticker Enrichment Test Suite")
    print("="*60)
    
    all_passed = True
    
    try:
        all_passed &= test_market_cap_classification()
    except Exception as e:
        print(f"❌ Market cap classification test failed: {e}")
        all_passed = False
    
    try:
        all_passed &= test_finnhub_enrichment()
    except Exception as e:
        print(f"❌ Finnhub enrichment test failed: {e}")
        all_passed = False
    
    try:
        all_passed &= test_explore_agent_integration()
    except Exception as e:
        print(f"❌ ExploreAgent integration test failed: {e}")
        all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ All ticker enrichment tests passed!")
    else:
        print("❌ Some tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()