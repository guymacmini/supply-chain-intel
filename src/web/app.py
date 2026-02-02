"""Flask web application for Supply Chain Intel GUI."""

import os
import json
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agents import ExploreAgent, HypothesisAgent, MonitorAgent
from src.utils import WatchlistManager, MarkdownGenerator, ConfigLoader, PDFExporter, ResearchComparator
from src.models import WatchlistEntity

app = Flask(__name__,
            template_folder=str(Path(__file__).parent / 'templates'),
            static_folder=str(Path(__file__).parent / 'static'))

# Initialize managers
DATA_DIR = Path(__file__).parent.parent.parent / 'data'
watchlist_manager = WatchlistManager(data_dir=DATA_DIR)
markdown_generator = MarkdownGenerator(output_dir=DATA_DIR)
config_loader = ConfigLoader()
research_comparator = ResearchComparator(data_dir=DATA_DIR)


@app.route('/')
def index():
    """Dashboard home page."""
    # Get summary stats
    entities = watchlist_manager.get_all()
    theses = markdown_generator.list_theses()
    digests = markdown_generator.list_digests()
    research = markdown_generator.list_research()

    return render_template('index.html',
                         watchlist_count=len(entities),
                         thesis_count=len(theses),
                         digest_count=len(digests),
                         research_count=len(research))


# ============================================================================
# EXPLORE ROUTES
# ============================================================================

@app.route('/explore')
def explore_page():
    """Explore page for discovering investment opportunities."""
    research_files = markdown_generator.list_research()
    return render_template('explore.html', research_files=research_files)


@app.route('/api/explore', methods=['POST'])
def api_explore():
    """API endpoint to run exploration."""
    data = request.get_json()
    query = data.get('query', '')
    depth = data.get('depth', 2)

    if not query:
        return jsonify({'error': 'Query is required'}), 400

    try:
        agent = ExploreAgent()
        output_path = agent.run(query, depth=depth)

        # Read the generated content
        with open(output_path, 'r') as f:
            content = f.read()

        return jsonify({
            'success': True,
            'path': str(output_path),
            'filename': output_path.name,
            'content': content
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/research/followup', methods=['POST'])
def api_research_followup():
    """API endpoint to run follow-up analysis on existing research."""
    data = request.get_json()
    filename = data.get('filename', '')
    question = data.get('question', '')

    if not filename:
        return jsonify({'error': 'Original research filename is required'}), 400
    if not question:
        return jsonify({'error': 'Follow-up question is required'}), 400

    try:
        agent = ExploreAgent()
        output_path = agent.run_followup(filename, question)

        # Read the generated content
        with open(output_path, 'r') as f:
            content = f.read()

        return jsonify({
            'success': True,
            'path': str(output_path),
            'filename': output_path.name,
            'content': content,
            'parent_research': filename
        })
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/research/<path:filename>')
def view_research(filename):
    """View a research document."""
    research_path = DATA_DIR / 'research' / filename
    if not research_path.exists():
        return "Research not found", 404

    with open(research_path, 'r') as f:
        content = f.read()

    import markdown
    html_content = markdown.markdown(content, extensions=['tables', 'fenced_code'])

    # Find related research (follow-ups or parent)
    related_research = _find_related_research(filename)

    return render_template('document.html',
                         title=filename,
                         content=html_content,
                         raw_content=content,
                         doc_type='research',
                         filename=filename,
                         related_research=related_research)


@app.route('/export/<path:filename>/pdf')
def export_research_pdf(filename):
    """Export a research document as PDF."""
    research_path = DATA_DIR / 'research' / filename
    if not research_path.exists():
        return "Research not found", 404

    try:
        # Initialize PDF exporter
        pdf_exporter = PDFExporter()
        
        # Create PDF output directory
        pdf_output_dir = DATA_DIR / 'exports' / 'pdf'
        pdf_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Export to PDF
        pdf_path = pdf_exporter.export_research_file(research_path, pdf_output_dir)
        
        # Send PDF file for download
        from flask import send_file
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f"{research_path.stem}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        app.logger.error(f"PDF export error for {filename}: {str(e)}")
        return f"Error generating PDF: {str(e)}", 500


def _find_related_research(filename: str) -> list:
    """Find related research documents (follow-ups or parent)."""
    related = []
    research_dir = DATA_DIR / 'research'

    if not research_dir.exists():
        return related

    stem = Path(filename).stem

    # Check if this is a follow-up (contains '_followup_')
    if '_followup_' in stem:
        # Find parent research
        parent_stem = stem.split('_followup_')[0]
        for f in research_dir.glob(f"{parent_stem}*.md"):
            if '_followup_' not in f.name:
                related.append({
                    'name': f.name,
                    'type': 'parent',
                    'label': 'Original Research'
                })
                break

    # Find follow-ups of this research
    base_stem = stem.split('_followup_')[0] if '_followup_' in stem else stem
    for f in research_dir.glob(f"{base_stem}_followup_*.md"):
        if f.name != filename:
            related.append({
                'name': f.name,
                'type': 'followup',
                'label': 'Follow-up'
            })

    return related


# ============================================================================
# THESIS ROUTES
# ============================================================================

@app.route('/thesis')
def thesis_page():
    """Thesis management page."""
    theses = []

    import frontmatter
    for path in markdown_generator.list_theses():
        try:
            post = frontmatter.load(path)
            theses.append({
                'id': post.metadata.get('id', path.stem),
                'status': post.metadata.get('status', 'unknown'),
                'confidence': post.metadata.get('confidence', '?'),
                'created': post.metadata.get('created', 'unknown'),
                'path': path.name
            })
        except Exception:
            theses.append({
                'id': path.stem,
                'status': 'error',
                'confidence': '?',
                'created': 'unknown',
                'path': path.name
            })

    return render_template('thesis.html', theses=theses)


@app.route('/api/thesis', methods=['POST'])
def api_create_thesis():
    """API endpoint to create a new thesis."""
    data = request.get_json()
    statement = data.get('statement', '')

    if not statement:
        return jsonify({'error': 'Thesis statement is required'}), 400

    try:
        agent = HypothesisAgent()
        output_path = agent.run(statement)

        with open(output_path, 'r') as f:
            content = f.read()

        return jsonify({
            'success': True,
            'path': str(output_path),
            'content': content
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/thesis/<path:filename>')
def view_thesis(filename):
    """View a thesis document."""
    # Search in all thesis directories
    for subdir in ['active', 'confirmed', 'refuted']:
        thesis_path = DATA_DIR / 'theses' / subdir / filename
        if thesis_path.exists():
            break
    else:
        return "Thesis not found", 404

    with open(thesis_path, 'r') as f:
        content = f.read()

    import markdown
    # Remove frontmatter for display
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            content = parts[2]

    html_content = markdown.markdown(content, extensions=['tables', 'fenced_code'])

    return render_template('document.html',
                         title=filename,
                         content=html_content,
                         raw_content=content,
                         doc_type='thesis')


# ============================================================================
# MONITOR ROUTES
# ============================================================================

@app.route('/monitor')
def monitor_page():
    """Monitoring page showing digests."""
    digests = []
    for path in markdown_generator.list_digests()[:20]:  # Last 20
        digests.append({
            'name': path.name,
            'date': path.stem.replace('digest_', '').replace('_', ' ')
        })

    return render_template('monitor.html', digests=digests)


@app.route('/api/monitor', methods=['POST'])
def api_run_monitor():
    """API endpoint to run monitoring scan."""
    try:
        agent = MonitorAgent()
        output_path = agent.run()

        with open(output_path, 'r') as f:
            content = f.read()

        return jsonify({
            'success': True,
            'path': str(output_path),
            'content': content
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/digest/<path:filename>')
def view_digest(filename):
    """View a monitoring digest."""
    digest_path = DATA_DIR / 'digests' / filename
    if not digest_path.exists():
        return "Digest not found", 404

    with open(digest_path, 'r') as f:
        content = f.read()

    import markdown
    html_content = markdown.markdown(content, extensions=['tables', 'fenced_code'])

    return render_template('document.html',
                         title=filename,
                         content=html_content,
                         raw_content=content,
                         doc_type='digest')


# ============================================================================
# COMPARISON ROUTES  
# ============================================================================

@app.route('/compare')
def compare_page():
    """Research comparison page."""
    # Get list of available research reports
    available_reports = research_comparator.list_available_research()
    return render_template('compare.html', available_reports=available_reports)


@app.route('/api/compare', methods=['POST'])
def api_compare_research():
    """API endpoint to compare research reports."""
    data = request.get_json()
    filenames = data.get('filenames', [])
    
    if len(filenames) < 2:
        return jsonify({'error': 'Need at least 2 reports to compare'}), 400
    if len(filenames) > 4:
        return jsonify({'error': 'Maximum 4 reports can be compared'}), 400
    
    try:
        comparison = research_comparator.compare_research_reports(filenames)
        return jsonify({
            'success': True,
            'comparison': comparison
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/research/list', methods=['GET'])
def api_list_research():
    """API endpoint to get list of available research reports."""
    try:
        reports = research_comparator.list_available_research()
        return jsonify({
            'success': True,
            'reports': reports
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# WATCHLIST ROUTES
# ============================================================================

@app.route('/watchlist')
def watchlist_page():
    """Watchlist management page."""
    entities = watchlist_manager.get_all()
    return render_template('watchlist.html', entities=entities)


@app.route('/api/watchlist', methods=['GET'])
def api_get_watchlist():
    """Get all watchlist entities."""
    entities = watchlist_manager.get_all()
    return jsonify([e.to_dict() for e in entities])


@app.route('/api/watchlist', methods=['POST'])
def api_add_to_watchlist():
    """Add entity to watchlist."""
    data = request.get_json()
    ticker = data.get('ticker', '').upper()
    name = data.get('name', ticker)
    themes = data.get('themes', [])

    if not ticker:
        return jsonify({'error': 'Ticker is required'}), 400

    entity = WatchlistEntity(
        ticker=ticker,
        name=name,
        themes=themes if isinstance(themes, list) else [themes],
        added_date=datetime.now().strftime('%Y-%m-%d')
    )

    if watchlist_manager.add(entity):
        return jsonify({'success': True, 'message': f'Added {ticker}'})
    else:
        return jsonify({'success': False, 'message': f'{ticker} already exists'})


@app.route('/api/watchlist/<ticker>', methods=['DELETE'])
def api_remove_from_watchlist(ticker):
    """Remove entity from watchlist."""
    if watchlist_manager.remove(ticker):
        return jsonify({'success': True, 'message': f'Removed {ticker}'})
    else:
        return jsonify({'success': False, 'message': f'{ticker} not found'})


# ============================================================================
# HISTORY ROUTES
# ============================================================================

@app.route('/history')
def history_page():
    """History page showing all generated documents."""
    research_files = markdown_generator.list_research()
    research = []
    for p in research_files:
        is_followup = '_followup_' in p.name
        research.append({
            'name': p.name,
            'type': 'research',
            'is_followup': is_followup,
            'label': 'Follow-up' if is_followup else 'Original'
        })

    theses = [{'name': p.name, 'type': 'thesis', 'is_followup': False, 'label': ''} for p in markdown_generator.list_theses()]
    digests = [{'name': p.name, 'type': 'digest', 'is_followup': False, 'label': ''} for p in markdown_generator.list_digests()]

    # Combine and sort by name (which includes timestamp)
    all_docs = research + theses + digests
    all_docs.sort(key=lambda x: x['name'], reverse=True)

    return render_template('history.html', documents=all_docs[:50])


def run_server(host='127.0.0.1', port=5000, debug=False):
    """Run the Flask development server."""
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_server(debug=True)
