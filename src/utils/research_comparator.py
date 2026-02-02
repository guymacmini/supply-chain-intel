"""Research comparison utility for side-by-side analysis of investment reports."""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import frontmatter
import markdown


class ResearchComparator:
    """Compare investment research reports side-by-side."""
    
    def __init__(self, data_dir: Path):
        """Initialize with data directory."""
        self.data_dir = data_dir
        self.research_dir = data_dir / 'research'
    
    def list_available_research(self) -> List[Dict]:
        """Get list of available research reports with metadata."""
        if not self.research_dir.exists():
            return []
        
        reports = []
        for file_path in self.research_dir.glob('*.md'):
            if file_path.name.startswith('.'):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    post = frontmatter.load(f)
                    
                metadata = post.metadata
                content_preview = post.content[:200] + "..." if len(post.content) > 200 else post.content
                
                reports.append({
                    'filename': file_path.name,
                    'theme': metadata.get('theme', file_path.stem),
                    'query': metadata.get('query', ''),
                    'generated': metadata.get('generated', ''),
                    'tickers_found': metadata.get('tickers_found', 0),
                    'depth': metadata.get('depth', 1),
                    'size_kb': round(file_path.stat().st_size / 1024, 1),
                    'preview': content_preview
                })
            except Exception as e:
                # Fallback for files without frontmatter
                reports.append({
                    'filename': file_path.name,
                    'theme': file_path.stem.replace('_', ' ').title(),
                    'query': '',
                    'generated': '',
                    'tickers_found': 0,
                    'depth': 1,
                    'size_kb': round(file_path.stat().st_size / 1024, 1),
                    'preview': f'Error parsing metadata: {e}'
                })
        
        # Sort by generated date (newest first)
        reports.sort(key=lambda x: x['generated'], reverse=True)
        return reports
    
    def parse_research_content(self, filename: str) -> Optional[Dict]:
        """Parse research report and extract comparable elements."""
        file_path = self.research_dir / filename
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)
            
            content = post.content
            metadata = post.metadata
            
            # Extract key elements
            parsed = {
                'filename': filename,
                'metadata': metadata,
                'theme': metadata.get('theme', 'Unknown'),
                'generated': metadata.get('generated', ''),
                'tickers_found': metadata.get('tickers_found', 0),
                'tldr': self._extract_tldr(content),
                'executive_summary': self._extract_executive_summary(content),
                'key_companies': self._extract_key_companies(content),
                'sectors': self._extract_sectors(content),
                'risk_factors': self._extract_risk_factors(content),
                'valuation_metrics': self._extract_valuation_metrics(content),
                'market_cap_exposure': self._calculate_market_cap_exposure(content),
                'top_tickers': self._extract_top_tickers(content)
            }
            
            return parsed
            
        except Exception as e:
            return {
                'filename': filename,
                'error': f'Failed to parse: {str(e)}',
                'metadata': {},
                'theme': 'Error',
                'generated': '',
                'tickers_found': 0
            }
    
    def compare_research_reports(self, filenames: List[str]) -> Dict:
        """Compare multiple research reports side-by-side."""
        if len(filenames) < 2:
            raise ValueError("Need at least 2 reports to compare")
        if len(filenames) > 4:
            raise ValueError("Maximum 4 reports can be compared")
        
        # Parse each report
        reports = []
        for filename in filenames:
            parsed = self.parse_research_content(filename)
            if parsed:
                reports.append(parsed)
            else:
                reports.append({
                    'filename': filename,
                    'error': 'File not found',
                    'theme': 'Not Found'
                })
        
        if len(reports) < 2:
            raise ValueError("Could not parse enough reports for comparison")
        
        # Build comparison structure
        comparison = {
            'reports': reports,
            'comparison_date': datetime.now().isoformat(),
            'summary': self._generate_comparison_summary(reports),
            'side_by_side': self._build_side_by_side_comparison(reports)
        }
        
        return comparison
    
    def _extract_tldr(self, content: str) -> str:
        """Extract TLDR section from content."""
        # Look for TLDR section
        tldr_patterns = [
            r'## 📌 TLDR\s*\n\s*\*\*TLDR:\*\*\s*(.+?)(?=\n\n|\n---|\n##|$)',
            r'##\s*TLDR\s*\n\s*\*\*TLDR:\*\*\s*(.+?)(?=\n\n|\n---|\n##|$)',
            r'\*\*TLDR:\*\*\s*(.+?)(?=\n\n|\n---|\n##|$)'
        ]
        
        for pattern in tldr_patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "No TLDR found"
    
    def _extract_executive_summary(self, content: str) -> str:
        """Extract executive summary from content."""
        # Look for Executive Summary section
        patterns = [
            r'## Executive Summary\s*\n\s*(.+?)(?=\n\n##|\n---|\n\n\n|$)',
            r'##\s*Summary\s*\n\s*(.+?)(?=\n\n##|\n---|\n\n\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                summary = match.group(1).strip()
                # Limit to first paragraph if very long
                if len(summary) > 500:
                    first_para = summary.split('\n\n')[0]
                    return first_para[:500] + "..." if len(first_para) > 500 else first_para
                return summary
        
        return "No executive summary found"
    
    def _extract_key_companies(self, content: str) -> List[Dict]:
        """Extract key companies and their tickers from tables."""
        companies = []
        
        # Find all table rows with tickers
        table_pattern = r'\|\s*([A-Z]{1,5})\s*\|\s*([^|]+)\s*\|\s*([^|]*)\s*\|\s*([^|]*)\s*\|'
        matches = re.findall(table_pattern, content)
        
        # Filter out header rows and non-ticker entries
        exclude_words = {'Ticker', 'Symbol', 'Company', 'Name', 'Role', 'Market', 'Cap', 'High', 'Low', 'P', 'E'}
        
        seen_tickers = set()
        for match in matches:
            ticker = match[0].strip()
            company = match[1].strip()
            
            if ticker not in exclude_words and len(ticker) >= 2 and ticker not in seen_tickers:
                seen_tickers.add(ticker)
                companies.append({
                    'ticker': ticker,
                    'company': company,
                    'additional_info': match[2].strip() if len(match) > 2 else ''
                })
        
        # Limit to top 10 companies
        return companies[:10]
    
    def _extract_sectors(self, content: str) -> List[str]:
        """Extract sectors mentioned in the research."""
        # Look for sector breakdown or sector mentions
        sector_patterns = [
            r'### (.+?)\n(?=\||\n\n)',  # Section headers before tables
            r'\*\*(.+?):\*\*',  # Bold sector names
            r'## (.+?) Sector',  # Sector headers
        ]
        
        sectors = set()
        for pattern in sector_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                sector = match.strip()
                # Filter out generic headers
                if len(sector) > 3 and sector not in {'Materials', 'Hardware', 'Software', 'Analysis', 'Summary'}:
                    if any(word in sector.lower() for word in ['technology', 'semiconductor', 'healthcare', 'energy', 'finance', 'industrial', 'consumer']):
                        sectors.add(sector)
        
        return list(sectors)[:5]  # Top 5 sectors
    
    def _extract_risk_factors(self, content: str) -> List[str]:
        """Extract risk factors from content."""
        risks = []
        
        # Look for risk-related sections
        risk_patterns = [
            r'(?:risk|Risk|RISK).{0,50}?:\s*(.+?)(?=\n\n|\n-|\n\*|\.|$)',
            r'\*\*.*?risk.*?\*\*\s*(.+?)(?=\n\n|\n-|\n\*|$)',
            r'## Risks?\s*\n\s*(.+?)(?=\n\n##|\n---|\n\n\n|$)'
        ]
        
        for pattern in risk_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                risk_text = match.strip()
                if len(risk_text) > 20:  # Filter out very short matches
                    risks.append(risk_text[:200])  # Limit length
        
        return risks[:3]  # Top 3 risks
    
    def _extract_valuation_metrics(self, content: str) -> Dict:
        """Extract valuation-related metrics from content."""
        metrics = {
            'market_size': None,
            'growth_rate': None,
            'key_multiples': [],
            'price_targets': []
        }
        
        # Extract market size
        market_size_pattern = r'market.{0,20}(\$[\d.]+[BMT]|\$[\d,]+.{0,10}(?:billion|million|trillion))'
        market_match = re.search(market_size_pattern, content, re.IGNORECASE)
        if market_match:
            metrics['market_size'] = market_match.group(1)
        
        # Extract growth rates
        growth_pattern = r'(?:CAGR|growth|Growth).{0,20}(\d+%-?\d*%|\d+\.\d+%-?\d*\.\d*%)'
        growth_matches = re.findall(growth_pattern, content, re.IGNORECASE)
        if growth_matches:
            metrics['growth_rate'] = growth_matches[0]
        
        # Extract P/E ratios and other multiples
        pe_pattern = r'P/E.{0,10}(\d+\.?\d*)'
        pe_matches = re.findall(pe_pattern, content, re.IGNORECASE)
        metrics['key_multiples'] = pe_matches[:3]
        
        return metrics
    
    def _calculate_market_cap_exposure(self, content: str) -> Dict:
        """Calculate market cap exposure distribution."""
        exposure = {'mega': 0, 'large': 0, 'mid': 0, 'small': 0, 'micro': 0}
        
        # Look for market cap classifications
        patterns = [
            r'Mega \(\$\d+[BMT]?\)',
            r'Large \(\$\d+[BMT]?\)',
            r'Mid \(\$\d+[BMT]?\)',
            r'Small \(\$\d+[BMT]?\)',
            r'Micro \(\$\d+[BMT]?\)'
        ]
        
        for i, pattern in enumerate(patterns):
            matches = len(re.findall(pattern, content, re.IGNORECASE))
            key = ['mega', 'large', 'mid', 'small', 'micro'][i]
            exposure[key] = matches
        
        return exposure
    
    def _extract_top_tickers(self, content: str, limit: int = 5) -> List[str]:
        """Extract the top ticker symbols mentioned in the research."""
        companies = self._extract_key_companies(content)
        return [comp['ticker'] for comp in companies[:limit]]
    
    def _generate_comparison_summary(self, reports: List[Dict]) -> Dict:
        """Generate a high-level comparison summary."""
        if not reports or any('error' in report for report in reports):
            return {'error': 'Cannot generate summary - reports have errors'}
        
        summary = {
            'themes': [report['theme'] for report in reports],
            'total_tickers': sum(report.get('tickers_found', 0) for report in reports),
            'common_tickers': self._find_common_tickers(reports),
            'unique_sectors': self._find_unique_sectors(reports),
            'generation_dates': [report.get('generated', 'Unknown') for report in reports]
        }
        
        return summary
    
    def _find_common_tickers(self, reports: List[Dict]) -> List[str]:
        """Find tickers common across multiple reports."""
        all_tickers = [set(report.get('top_tickers', [])) for report in reports]
        if len(all_tickers) < 2:
            return []
        
        common = all_tickers[0]
        for ticker_set in all_tickers[1:]:
            common = common.intersection(ticker_set)
        
        return list(common)
    
    def _find_unique_sectors(self, reports: List[Dict]) -> List[str]:
        """Find all unique sectors across reports."""
        all_sectors = []
        for report in reports:
            all_sectors.extend(report.get('sectors', []))
        
        return list(set(all_sectors))
    
    def _build_side_by_side_comparison(self, reports: List[Dict]) -> Dict:
        """Build side-by-side comparison structure."""
        comparison = {
            'basic_info': {},
            'tldr_comparison': {},
            'top_companies': {},
            'sector_exposure': {},
            'risk_comparison': {},
            'valuation_metrics': {}
        }
        
        # Basic info comparison
        for i, report in enumerate(reports):
            key = f'report_{i+1}'
            comparison['basic_info'][key] = {
                'theme': report.get('theme', 'Unknown'),
                'filename': report.get('filename', ''),
                'generated': report.get('generated', ''),
                'tickers_found': report.get('tickers_found', 0)
            }
            
            comparison['tldr_comparison'][key] = report.get('tldr', 'No TLDR')
            
            comparison['top_companies'][key] = report.get('key_companies', [])[:5]
            
            comparison['sector_exposure'][key] = report.get('sectors', [])
            
            comparison['risk_comparison'][key] = report.get('risk_factors', [])
            
            comparison['valuation_metrics'][key] = report.get('valuation_metrics', {})
        
        return comparison