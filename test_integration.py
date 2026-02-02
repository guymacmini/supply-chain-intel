#!/usr/bin/env python3
"""Test script to verify the analyzer integration works."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all imports work."""
    print("Testing imports...")
    from src.agents.explore_agent import ExploreAgent
    from src.analysis.shortage_analyzer import ShortageAnalyzer, analyze_bottlenecks
    from src.analysis.valuation_checker import ValuationChecker, check_valuations
    from src.analysis.demand_analyzer import DemandAnalyzer, analyze_demand
    print("✅ All imports successful")
    return True

def test_analyzers_standalone():
    """Test analyzers work standalone."""
    print("\nTesting standalone analyzers...")
    
    # Test bottleneck analyzer
    from src.analysis.shortage_analyzer import analyze_bottlenecks
    result = analyze_bottlenecks([
        {"component": "HBM3 Memory", "lead_time_months": 9, "source_concentration": "dual-source"},
        {"component": "CoWoS Packaging", "capacity_utilization": 95, "geographic_risk": "Taiwan"}
    ])
    assert "Supply Chain Bottleneck" in result
    print("✅ Bottleneck analyzer works")
    
    # Test valuation checker
    from src.analysis.valuation_checker import check_valuations
    result = check_valuations([
        {"ticker": "NVDA", "company": "NVIDIA", "current_pe": 55, "pe_5y_avg": 40, "pe_sector_avg": 25},
        {"ticker": "INTC", "company": "Intel", "current_pe": 12, "pe_5y_avg": 15, "pe_sector_avg": 25}
    ])
    assert "Valuation Reality Check" in result
    print("✅ Valuation checker works")
    
    # Test demand analyzer
    from src.analysis.demand_analyzer import analyze_demand
    result = analyze_demand([
        {
            "tier_name": "CoWoS Advanced Packaging",
            "tier_level": 1,
            "demand_multiplier": 2.0,
            "scale_lead_time_months": 24,
            "current_utilization": 95,
            "pricing_power": "high"
        }
    ])
    assert "Demand Acceleration" in result
    print("✅ Demand analyzer works")
    
    return True

def test_explore_agent_initialization():
    """Test ExploreAgent can be instantiated."""
    print("\nTesting ExploreAgent initialization...")
    from src.agents.explore_agent import ExploreAgent
    
    agent = ExploreAgent()
    
    # Check that the new methods exist
    assert hasattr(agent, '_generate_tldr')
    assert hasattr(agent, '_generate_contrarian_analysis')
    assert hasattr(agent, '_extract_and_analyze_bottlenecks')
    assert hasattr(agent, '_extract_and_analyze_demand')
    assert hasattr(agent, '_extract_and_check_valuations')
    
    print("✅ ExploreAgent has all new methods")
    return True

def main():
    print("=" * 60)
    print("Integration Test: ExploreAgent + Analyzers")
    print("=" * 60)
    
    all_passed = True
    
    try:
        test_imports()
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        all_passed = False
    
    try:
        test_analyzers_standalone()
    except Exception as e:
        print(f"❌ Standalone analyzer test failed: {e}")
        all_passed = False
    
    try:
        test_explore_agent_initialization()
    except Exception as e:
        print(f"❌ ExploreAgent initialization test failed: {e}")
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All integration tests passed!")
    else:
        print("❌ Some tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
