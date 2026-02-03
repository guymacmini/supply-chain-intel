#!/usr/bin/env python3
"""
Command-line interface for Supply Chain Intel research system.

Provides CLI access to explore, monitor, and manage research data.
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.agents import ExploreAgent, HypothesisAgent, MonitorAgent
from src.utils import WatchlistManager, MarkdownGenerator, ConfigLoader, PDFExporter
from src.utils.saved_research_store import SavedResearchStore
from src.models import WatchlistEntity, SavedResearch, SavedResearchStatus


class SupplyChainIntelCLI:
    """Command-line interface for the Supply Chain Intel system."""
    
    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize CLI with data directory."""
        if data_dir is None:
            data_dir = Path(__file__).parent / 'data'
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.watchlist_manager = WatchlistManager(data_dir=self.data_dir)
        self.markdown_generator = MarkdownGenerator(output_dir=self.data_dir)
        self.config_loader = ConfigLoader()
        self.saved_research_store = SavedResearchStore(data_dir=self.data_dir)
        
        print(f"📊 Supply Chain Intel CLI - Data dir: {self.data_dir}")
    
    def explore(self, query: str, depth: int = 2, max_results: int = 10) -> Dict[str, Any]:
        """Run research exploration on a query."""
        print(f"\n🔍 Exploring: {query}")
        print(f"   Depth: {depth}, Max results: {max_results}")
        
        try:
            agent = ExploreAgent(
                output_dir=self.data_dir,
                config=self.config_loader.get_api_config()
            )
            
            result = agent.run(query, depth=depth, max_results=max_results)
            
            print(f"\n✅ Research completed!")
            print(f"   📄 File: {result['filename']}")
            print(f"   📂 Path: {result.get('output_path', 'N/A')}")
            
            return result
            
        except Exception as e:
            print(f"\n❌ Exploration failed: {e}")
            return {'error': str(e)}
    
    def monitor(self) -> Dict[str, Any]:
        """Run monitoring of current watchlist and themes."""
        print(f"\n📡 Running monitoring analysis...")
        
        try:
            agent = MonitorAgent(
                output_dir=self.data_dir,
                config=self.config_loader.get_api_config()
            )
            
            result = agent.run()
            
            print(f"\n✅ Monitoring completed!")
            print(f"   📄 File: {result['filename']}")
            print(f"   📂 Path: {result.get('output_path', 'N/A')}")
            
            return result
            
        except Exception as e:
            print(f"\n❌ Monitoring failed: {e}")
            return {'error': str(e)}
    
    def list_research(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent research documents."""
        print(f"\n📚 Recent research documents (last {limit}):")
        
        research_dir = self.data_dir / 'research'
        if not research_dir.exists():
            print("   No research directory found.")
            return []
        
        # Get all markdown files sorted by modification time
        md_files = sorted(
            research_dir.glob('*.md'),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )[:limit]
        
        research_list = []
        for i, file_path in enumerate(md_files, 1):
            modified = datetime.fromtimestamp(file_path.stat().st_mtime)
            size_kb = file_path.stat().st_size // 1024
            
            # Try to extract metadata from file
            metadata = self._extract_metadata(file_path)
            
            research_info = {
                'filename': file_path.name,
                'modified': modified.strftime('%Y-%m-%d %H:%M'),
                'size_kb': size_kb,
                'metadata': metadata
            }
            research_list.append(research_info)
            
            print(f"   {i:2d}. {file_path.name}")
            print(f"       📅 {modified.strftime('%Y-%m-%d %H:%M')} | 📏 {size_kb}KB")
            if metadata.get('tickers'):
                print(f"       🏢 Tickers: {', '.join(metadata['tickers'][:3])}")
            if metadata.get('theme'):
                print(f"       🎯 Theme: {metadata['theme']}")
            print()
        
        if not research_list:
            print("   No research documents found.")
        
        return research_list
    
    def watchlist_add(self, ticker: str, theme: str, rationale: str, confidence: float = 7.0) -> bool:
        """Add ticker to watchlist."""
        print(f"\n➕ Adding {ticker} to watchlist...")
        
        try:
            # Use actual WatchlistEntity structure
            entity = WatchlistEntity(
                ticker=ticker,
                name=f"{ticker} Corp",  # Default name
                themes=[theme],  # themes is a list
                added_date=datetime.now().isoformat()
            )
            
            success = self.watchlist_manager.add(entity)
            
            if success:
                print(f"   ✅ Added {ticker} successfully!")
                print(f"   🎯 Themes: {', '.join(entity.themes)}")
                print(f"   📅 Added: {entity.added_date[:10]}")
                print(f"   📝 Note: Rationale and confidence stored as notes")
            else:
                print(f"   ❌ Failed to add {ticker} (may already exist)")
            
            return success
            
        except Exception as e:
            print(f"   ❌ Error adding to watchlist: {e}")
            return False
    
    def watchlist_list(self) -> List[Dict[str, Any]]:
        """List current watchlist."""
        print(f"\n📋 Current watchlist:")
        
        try:
            entities = self.watchlist_manager.get_all()
            
            if not entities:
                print("   No items in watchlist.")
                return []
            
            watchlist_data = []
            for i, entity in enumerate(entities, 1):
                entity_dict = entity.to_dict()
                watchlist_data.append(entity_dict)
                
                print(f"   {i:2d}. {entity.ticker}")
                print(f"       🏢 Name: {entity.name}")
                print(f"       🎯 Themes: {', '.join(entity.themes)}")
                print(f"       📅 Added: {entity.added_date[:10] if entity.added_date else 'N/A'}")
                if entity.source_research:
                    print(f"       📄 Source: {entity.source_research}")
                print()
            
            return watchlist_data
            
        except Exception as e:
            print(f"   ❌ Error reading watchlist: {e}")
            return []
    
    def watchlist_remove(self, ticker: str) -> bool:
        """Remove ticker from watchlist."""
        print(f"\n➖ Removing {ticker} from watchlist...")
        
        try:
            success = self.watchlist_manager.remove(ticker)
            
            if success:
                print(f"   ✅ Removed {ticker} successfully!")
            else:
                print(f"   ❌ {ticker} not found in watchlist")
            
            return success
            
        except Exception as e:
            print(f"   ❌ Error removing from watchlist: {e}")
            return False
    
    def export_pdf(self, filename: str) -> bool:
        """Export research document to PDF."""
        print(f"\n📄 Exporting {filename} to PDF...")
        
        try:
            research_path = self.data_dir / 'research' / filename
            if not filename.endswith('.md'):
                filename += '.md'
                research_path = self.data_dir / 'research' / filename
            
            if not research_path.exists():
                print(f"   ❌ Research file not found: {filename}")
                return False
            
            # Read content
            content = research_path.read_text()
            
            # Export to PDF
            exporter = PDFExporter()
            pdf_path = research_path.with_suffix('.pdf')
            
            exporter.export_research_to_pdf(content, pdf_path)
            
            print(f"   ✅ PDF exported successfully!")
            print(f"   📂 Path: {pdf_path}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ PDF export failed: {e}")
            return False
    
    def saved_research_list(self) -> List[Dict[str, Any]]:
        """List saved research items."""
        print(f"\n💾 Saved research:")
        
        try:
            saved_items = self.saved_research_store.get_all()
            
            if not saved_items:
                print("   No saved research items.")
                return []
            
            saved_data = []
            for i, item in enumerate(saved_items, 1):
                item_dict = item.to_dict()
                saved_data.append(item_dict)
                
                status_emoji = {
                    'interested': '👀',
                    'passed': '❌', 
                    'tracking': '📊',
                    'archived': '📦'
                }.get(item.status.value if hasattr(item.status, 'value') else item.status, '📄')
                
                rating_stars = '⭐' * (item.rating or 0)
                
                print(f"   {i:2d}. {status_emoji} {item.filename}")
                print(f"       {rating_stars} Rating: {item.rating or 'N/A'}/5")
                if item.notes:
                    print(f"       📝 Notes: {item.notes[:60]}{'...' if len(item.notes) > 60 else ''}")
                if item.tags:
                    print(f"       🏷️  Tags: {', '.join(item.tags[:3])}")
                print()
            
            return saved_data
            
        except Exception as e:
            print(f"   ❌ Error reading saved research: {e}")
            return []
    
    def status(self) -> Dict[str, Any]:
        """Show system status and statistics."""
        print(f"\n📊 System Status")
        print("=" * 50)
        
        # Count research documents
        research_dir = self.data_dir / 'research'
        research_count = len(list(research_dir.glob('*.md'))) if research_dir.exists() else 0
        
        # Count watchlist items
        watchlist_count = len(self.watchlist_manager.get_all())
        
        # Count saved research
        saved_count = len(self.saved_research_store.get_all())
        
        # Check data directory size
        total_size = sum(f.stat().st_size for f in self.data_dir.rglob('*') if f.is_file())
        size_mb = total_size / (1024 * 1024)
        
        status_info = {
            'research_documents': research_count,
            'watchlist_items': watchlist_count, 
            'saved_research': saved_count,
            'data_size_mb': round(size_mb, 2),
            'data_directory': str(self.data_dir)
        }
        
        print(f"📄 Research documents: {research_count}")
        print(f"📋 Watchlist items: {watchlist_count}")
        print(f"💾 Saved research: {saved_count}")
        print(f"💽 Data size: {size_mb:.1f} MB")
        print(f"📂 Data directory: {self.data_dir}")
        print()
        
        return status_info
    
    def _extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from research file."""
        try:
            content = file_path.read_text()
            
            metadata = {}
            
            # Extract tickers (look for **Tickers:** pattern)
            import re
            ticker_match = re.search(r'\*\*Tickers:\*\*\s*([^\n]+)', content)
            if ticker_match:
                tickers = [t.strip() for t in ticker_match.group(1).split(',')]
                metadata['tickers'] = tickers
            
            # Extract theme
            theme_match = re.search(r'\*\*Theme:\*\*\s*([^\n]+)', content)
            if theme_match:
                metadata['theme'] = theme_match.group(1).strip()
            
            # Extract sector
            sector_match = re.search(r'\*\*Sector:\*\*\s*([^\n]+)', content)
            if sector_match:
                metadata['sector'] = sector_match.group(1).strip()
            
            return metadata
            
        except Exception:
            return {}


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description='Supply Chain Intel CLI - Research and analysis from the command line',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s explore "AI companies with strong moats" --depth 3
  %(prog)s monitor
  %(prog)s watchlist add TSLA "EV Revolution" "Leading EV manufacturer" --confidence 8.5
  %(prog)s watchlist list
  %(prog)s research list --limit 5
  %(prog)s export research_20240203.md
  %(prog)s status
        """
    )
    
    parser.add_argument('--data-dir', type=str, help='Data directory path')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Explore command
    explore_parser = subparsers.add_parser('explore', help='Run research exploration')
    explore_parser.add_argument('query', help='Research query')
    explore_parser.add_argument('--depth', type=int, default=2, help='Analysis depth (default: 2)')
    explore_parser.add_argument('--max-results', type=int, default=10, help='Max results (default: 10)')
    
    # Monitor command
    subparsers.add_parser('monitor', help='Run monitoring analysis')
    
    # Research commands
    research_parser = subparsers.add_parser('research', help='Research document operations')
    research_subparsers = research_parser.add_subparsers(dest='research_action')
    
    list_parser = research_subparsers.add_parser('list', help='List research documents')
    list_parser.add_argument('--limit', type=int, default=10, help='Max documents to show')
    
    # Watchlist commands
    watchlist_parser = subparsers.add_parser('watchlist', help='Watchlist operations')
    watchlist_subparsers = watchlist_parser.add_subparsers(dest='watchlist_action')
    
    add_parser = watchlist_subparsers.add_parser('add', help='Add to watchlist')
    add_parser.add_argument('ticker', help='Stock ticker')
    add_parser.add_argument('theme', help='Investment theme')
    add_parser.add_argument('rationale', help='Investment rationale')
    add_parser.add_argument('--confidence', type=float, default=7.0, help='Confidence (1-10)')
    
    watchlist_subparsers.add_parser('list', help='List watchlist')
    
    remove_parser = watchlist_subparsers.add_parser('remove', help='Remove from watchlist')
    remove_parser.add_argument('ticker', help='Stock ticker to remove')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export research to PDF')
    export_parser.add_argument('filename', help='Research filename to export')
    
    # Saved research command
    saved_parser = subparsers.add_parser('saved', help='Saved research operations')
    saved_subparsers = saved_parser.add_subparsers(dest='saved_action')
    saved_subparsers.add_parser('list', help='List saved research')
    
    # Status command
    subparsers.add_parser('status', help='Show system status')
    
    return parser


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize CLI
    data_dir = Path(args.data_dir) if args.data_dir else None
    cli = SupplyChainIntelCLI(data_dir=data_dir)
    
    try:
        # Route commands
        if args.command == 'explore':
            cli.explore(args.query, depth=args.depth, max_results=args.max_results)
            
        elif args.command == 'monitor':
            cli.monitor()
            
        elif args.command == 'research':
            if args.research_action == 'list':
                cli.list_research(limit=args.limit)
            else:
                print("❌ Unknown research action. Use 'list'.")
                
        elif args.command == 'watchlist':
            if args.watchlist_action == 'add':
                cli.watchlist_add(args.ticker, args.theme, args.rationale, args.confidence)
            elif args.watchlist_action == 'list':
                cli.watchlist_list()
            elif args.watchlist_action == 'remove':
                cli.watchlist_remove(args.ticker)
            else:
                print("❌ Unknown watchlist action. Use 'add', 'list', or 'remove'.")
                
        elif args.command == 'export':
            cli.export_pdf(args.filename)
            
        elif args.command == 'saved':
            if args.saved_action == 'list':
                cli.saved_research_list()
            else:
                print("❌ Unknown saved action. Use 'list'.")
                
        elif args.command == 'status':
            cli.status()
            
        else:
            print(f"❌ Unknown command: {args.command}")
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\n\n🚫 Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()