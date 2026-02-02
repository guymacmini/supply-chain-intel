#!/usr/bin/env python3
"""Test script for research comparison functionality."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.utils.research_comparator import ResearchComparator

def test_research_listing():
    """Test listing available research reports."""
    print("Testing research report listing...")
    
    data_dir = Path(__file__).parent / 'data'
    comparator = ResearchComparator(data_dir)
    
    reports = comparator.list_available_research()
    
    if not reports:
        print("⚠️  No research reports found in data/research/")
        return False
    
    print(f"✅ Found {len(reports)} research reports:")
    for i, report in enumerate(reports, 1):
        print(f"   {i}. {report['theme']} ({report['filename']})")
        print(f"      - {report['tickers_found']} tickers, {report['size_kb']}KB")
        if report['generated']:
            print(f"      - Generated: {report['generated'][:10]}")
        print()
    
    return True

def test_research_parsing():
    """Test parsing individual research reports."""
    print("Testing research report parsing...")
    
    data_dir = Path(__file__).parent / 'data'
    comparator = ResearchComparator(data_dir)
    
    # Get first available report
    reports = comparator.list_available_research()
    if not reports:
        print("❌ No reports available for parsing test")
        return False
    
    filename = reports[0]['filename']
    print(f"Parsing: {filename}")
    
    parsed = comparator.parse_research_content(filename)
    
    if not parsed:
        print(f"❌ Failed to parse {filename}")
        return False
    
    if 'error' in parsed:
        print(f"❌ Error parsing {filename}: {parsed['error']}")
        return False
    
    print("✅ Successfully parsed research report:")
    print(f"   Theme: {parsed['theme']}")
    print(f"   Generated: {parsed['generated'][:10] if parsed['generated'] else 'Unknown'}")
    print(f"   Tickers Found: {parsed['tickers_found']}")
    print(f"   TLDR: {parsed['tldr'][:100]}...")
    print(f"   Key Companies: {len(parsed.get('key_companies', []))}")
    print(f"   Sectors: {len(parsed.get('sectors', []))}")
    print(f"   Risk Factors: {len(parsed.get('risk_factors', []))}")
    
    # Show some extracted data
    if parsed.get('key_companies'):
        print("   Top Companies:")
        for comp in parsed['key_companies'][:3]:
            print(f"     - {comp['ticker']}: {comp['company']}")
    
    if parsed.get('sectors'):
        print(f"   Sectors: {', '.join(parsed['sectors'][:3])}")
    
    return True

def test_mock_comparison():
    """Test comparison with mock data (simulate having multiple reports)."""
    print("\n" + "="*50)
    print("Testing comparison functionality with mock scenario...")
    
    data_dir = Path(__file__).parent / 'data'
    comparator = ResearchComparator(data_dir)
    
    # Get available reports
    reports = comparator.list_available_research()
    if not reports:
        print("❌ No reports available for comparison test")
        return False
    
    # For testing, we'll try to compare with the same file twice
    # This isn't ideal but will test the comparison logic
    filename = reports[0]['filename']
    
    print(f"Testing comparison logic with: {filename}")
    print("Note: Using same file twice to test comparison structure")
    
    try:
        # This should work even with same file twice
        comparison = comparator.compare_research_reports([filename, filename])
        
        print("✅ Comparison structure generated successfully")
        print(f"   Reports in comparison: {len(comparison['reports'])}")
        print(f"   Comparison date: {comparison['comparison_date'][:10]}")
        
        if 'summary' in comparison:
            summary = comparison['summary']
            print("   Summary:")
            print(f"     - Total tickers: {summary.get('total_tickers', 0)}")
            print(f"     - Common tickers: {len(summary.get('common_tickers', []))}")
            print(f"     - Unique sectors: {len(summary.get('unique_sectors', []))}")
        
        if 'side_by_side' in comparison:
            print("   ✅ Side-by-side comparison structure present")
            
        return True
        
    except Exception as e:
        print(f"❌ Comparison failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("Research Comparison Test Suite")
    print("="*50)
    
    all_passed = True
    
    try:
        all_passed &= test_research_listing()
    except Exception as e:
        print(f"❌ Research listing test failed: {e}")
        all_passed = False
    
    try:
        all_passed &= test_research_parsing()
    except Exception as e:
        print(f"❌ Research parsing test failed: {e}")
        all_passed = False
    
    try:
        all_passed &= test_mock_comparison()
    except Exception as e:
        print(f"❌ Mock comparison test failed: {e}")
        all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("✅ All research comparison tests passed!")
        print("\nThe comparison functionality is ready for use.")
        print("Visit http://127.0.0.1:5001/compare to try the web interface.")
    else:
        print("❌ Some tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()