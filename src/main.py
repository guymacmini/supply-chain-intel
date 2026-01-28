"""Supply Chain Intel CLI - Main entry point."""

import click
from pathlib import Path
from datetime import datetime

from .agents import ExploreAgent, HypothesisAgent, MonitorAgent
from .utils import MarkdownGenerator, WatchlistManager, ConfigLoader


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Supply Chain Intel - Investment research for second-order opportunities.

    Discover non-obvious investment opportunities through supply chain
    analysis, validate hypotheses with evidence, and monitor market
    developments.
    """
    pass


# ============================================================================
# EXPLORE COMMANDS
# ============================================================================

@cli.command()
@click.argument("query")
@click.option("--depth", "-d", default=2, type=int, help="Analysis depth (1-3)")
def explore(query: str, depth: int):
    """Explore a theme, company, or market for investment opportunities.

    Examples:

        supply-chain-intel explore "AI infrastructure"

        supply-chain-intel explore "ASML" --depth 3

        supply-chain-intel explore "renewable energy transition"
    """
    click.echo(f"Exploring: {query} (depth: {depth})")
    click.echo("This may take up to 60 seconds...\n")

    try:
        agent = ExploreAgent()
        output_path = agent.run(query, depth=depth)
        click.echo(f"\nResearch document generated: {output_path}")
        click.echo("\nEntities have been added to your watchlist.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


# ============================================================================
# THESIS COMMANDS
# ============================================================================

@cli.group()
def thesis():
    """Create and manage investment theses."""
    pass


@thesis.command("create")
@click.argument("statement")
def thesis_create(statement: str):
    """Create a new investment thesis for validation.

    Example:

        supply-chain-intel thesis create "I think VRT is undervalued because
        AI data center demand is accelerating faster than expected"
    """
    click.echo(f"Validating thesis...")
    click.echo("This may take up to 60 seconds...\n")

    try:
        agent = HypothesisAgent()
        output_path = agent.run(statement)
        click.echo(f"\nThesis document generated: {output_path}")
        click.echo("\nRelevant entities have been added to your watchlist.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@thesis.command("update")
@click.argument("thesis_id")
@click.option("--add", "-a", "new_evidence", help="New evidence to add")
def thesis_update(thesis_id: str, new_evidence: str):
    """Update an existing thesis with new evidence.

    Example:

        supply-chain-intel thesis update vrt_datacenter_20260128 \\
            --add "Management announced $500M buyback program"
    """
    if not new_evidence:
        click.echo("Please provide new evidence with --add", err=True)
        raise click.Abort()

    click.echo(f"Updating thesis: {thesis_id}")

    try:
        agent = HypothesisAgent()
        output_path = agent.update_thesis(thesis_id, new_evidence)
        if output_path:
            click.echo(f"\nThesis updated: {output_path}")
        else:
            click.echo(f"Thesis not found: {thesis_id}", err=True)
            raise click.Abort()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@thesis.command("list")
@click.option("--status", "-s", type=click.Choice(["active", "confirmed", "refuted", "all"]),
              default="all", help="Filter by status")
def thesis_list(status: str):
    """List investment theses.

    Example:

        supply-chain-intel thesis list --status active
    """
    generator = MarkdownGenerator()

    if status == "all":
        theses = generator.list_theses()
    else:
        theses = generator.list_theses(status=status)

    if not theses:
        click.echo("No theses found.")
        return

    click.echo(f"\n{'ID':<40} {'Status':<12} {'Confidence':<10}")
    click.echo("-" * 62)

    import frontmatter
    for path in theses:
        try:
            post = frontmatter.load(path)
            thesis_id = post.metadata.get("id", path.stem)
            thesis_status = post.metadata.get("status", "unknown")
            confidence = post.metadata.get("confidence", "?")
            click.echo(f"{thesis_id:<40} {thesis_status:<12} {confidence:<10}")
        except Exception:
            click.echo(f"{path.stem:<40} {'error':<12} {'?':<10}")


@thesis.command("show")
@click.argument("thesis_id")
def thesis_show(thesis_id: str):
    """Show a thesis document.

    Example:

        supply-chain-intel thesis show vrt_datacenter_20260128
    """
    generator = MarkdownGenerator()
    result = generator.load_thesis(thesis_id)

    if not result:
        click.echo(f"Thesis not found: {thesis_id}", err=True)
        raise click.Abort()

    metadata, content = result
    click.echo(f"\n--- Thesis: {thesis_id} ---")
    click.echo(f"Status: {metadata.get('status', 'unknown')}")
    click.echo(f"Confidence: {metadata.get('confidence', '?')}")
    click.echo(f"Created: {metadata.get('created', 'unknown')}")
    click.echo(f"Updated: {metadata.get('updated', 'unknown')}")
    click.echo("\n" + content)


@thesis.command("resolve")
@click.argument("thesis_id")
@click.option("--confirmed", is_flag=True, help="Mark thesis as confirmed")
@click.option("--refuted", is_flag=True, help="Mark thesis as refuted")
@click.option("--reason", "-r", help="Reason for resolution")
def thesis_resolve(thesis_id: str, confirmed: bool, refuted: bool, reason: str):
    """Resolve a thesis as confirmed or refuted.

    Example:

        supply-chain-intel thesis resolve vrt_datacenter_20260128 --confirmed

        supply-chain-intel thesis resolve vrt_datacenter_20260128 --refuted \\
            --reason "Thesis broken by competitive pressure"
    """
    if confirmed == refuted:
        click.echo("Please specify either --confirmed or --refuted", err=True)
        raise click.Abort()

    try:
        agent = HypothesisAgent()
        output_path = agent.resolve_thesis(thesis_id, confirmed=confirmed, reason=reason)
        if output_path:
            status = "confirmed" if confirmed else "refuted"
            click.echo(f"\nThesis {status}: {output_path}")
        else:
            click.echo(f"Thesis not found: {thesis_id}", err=True)
            raise click.Abort()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


# ============================================================================
# MONITOR COMMANDS
# ============================================================================

@cli.command()
@click.option("--sources", "-s", help="Custom sources configuration file")
def monitor(sources: str):
    """Run monitoring scan and generate digest.

    Scans news sources for updates on watchlist entities and active
    thesis triggers.

    Example:

        supply-chain-intel monitor

        supply-chain-intel monitor --sources custom_sources.json
    """
    click.echo("Running monitoring scan...")
    click.echo("This may take a few minutes...\n")

    try:
        agent = MonitorAgent()
        output_path = agent.run(sources_file=sources)
        click.echo(f"\nDigest generated: {output_path}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


# ============================================================================
# WATCHLIST COMMANDS
# ============================================================================

@cli.group()
def watchlist():
    """Manage the entity watchlist."""
    pass


@watchlist.command("list")
@click.option("--theme", "-t", help="Filter by theme")
def watchlist_list(theme: str):
    """List watchlist entities.

    Example:

        supply-chain-intel watchlist list

        supply-chain-intel watchlist list --theme ai
    """
    manager = WatchlistManager()

    if theme:
        entities = manager.get_by_theme(theme)
    else:
        entities = manager.get_all()

    if not entities:
        click.echo("Watchlist is empty.")
        return

    click.echo(f"\n{'Ticker':<10} {'Name':<30} {'Themes':<30}")
    click.echo("-" * 70)

    for entity in entities:
        themes_str = ", ".join(entity.themes)[:28]
        click.echo(f"{entity.ticker:<10} {entity.name[:28]:<30} {themes_str:<30}")

    click.echo(f"\nTotal: {len(entities)} entities")


@watchlist.command("add")
@click.argument("ticker")
@click.option("--name", "-n", help="Company name")
@click.option("--theme", "-t", multiple=True, help="Themes (can specify multiple)")
def watchlist_add(ticker: str, name: str, theme: tuple):
    """Add an entity to the watchlist.

    Example:

        supply-chain-intel watchlist add NVDA --theme AI --theme semiconductors

        supply-chain-intel watchlist add ASML --name "ASML Holding" --theme semiconductors
    """
    from .models import WatchlistEntity

    manager = WatchlistManager()

    entity = WatchlistEntity(
        ticker=ticker.upper(),
        name=name or ticker.upper(),
        themes=list(theme) if theme else [],
        added_date=datetime.now().strftime("%Y-%m-%d")
    )

    if manager.add(entity):
        click.echo(f"Added {ticker.upper()} to watchlist")
    else:
        click.echo(f"{ticker.upper()} already in watchlist")


@watchlist.command("remove")
@click.argument("ticker")
def watchlist_remove(ticker: str):
    """Remove an entity from the watchlist.

    Example:

        supply-chain-intel watchlist remove NVDA
    """
    manager = WatchlistManager()

    if manager.remove(ticker):
        click.echo(f"Removed {ticker.upper()} from watchlist")
    else:
        click.echo(f"{ticker.upper()} not found in watchlist")


@cli.command()
@click.option("--theme", "-t", required=True, help="Theme to remove")
def unwatch(theme: str):
    """Remove all entities matching a theme.

    Example:

        supply-chain-intel unwatch --theme "Renewable Energy"
    """
    manager = WatchlistManager()
    count = manager.remove_by_theme(theme)
    click.echo(f"Removed {count} entities with theme '{theme}'")


# ============================================================================
# OUTPUT VIEWING COMMANDS
# ============================================================================

@cli.command()
@click.option("--limit", "-n", default=10, help="Number of digests to show")
def digests(limit: int):
    """List recent monitoring digests.

    Example:

        supply-chain-intel digests --limit 5
    """
    generator = MarkdownGenerator()
    digest_files = generator.list_digests()[:limit]

    if not digest_files:
        click.echo("No digests found. Run 'supply-chain-intel monitor' first.")
        return

    click.echo(f"\nRecent Digests:")
    click.echo("-" * 60)

    for path in digest_files:
        click.echo(f"  {path.name}")


@cli.group()
def research():
    """View research documents."""
    pass


@research.command("list")
def research_list():
    """List research documents.

    Example:

        supply-chain-intel research list
    """
    generator = MarkdownGenerator()
    research_files = generator.list_research()

    if not research_files:
        click.echo("No research documents found. Run 'supply-chain-intel explore' first.")
        return

    click.echo(f"\nResearch Documents:")
    click.echo("-" * 60)

    for path in sorted(research_files, reverse=True):
        click.echo(f"  {path.name}")


# ============================================================================
# GUI COMMAND
# ============================================================================

@cli.command()
@click.option("--host", "-h", default="127.0.0.1", help="Host to bind to")
@click.option("--port", "-p", default=5000, type=int, help="Port to bind to")
@click.option("--debug", is_flag=True, help="Enable debug mode")
def gui(host: str, port: int, debug: bool):
    """Launch the web-based GUI.

    Example:

        supply-chain-intel gui

        supply-chain-intel gui --port 8080

        supply-chain-intel gui --debug
    """
    click.echo(f"Starting Supply Chain Intel GUI...")
    click.echo(f"Open http://{host}:{port} in your browser")
    click.echo("Press Ctrl+C to stop the server\n")

    from .web.app import run_server
    run_server(host=host, port=port, debug=debug)


if __name__ == "__main__":
    cli()
