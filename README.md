# Supply Chain Intel

Investment research platform for discovering second and third-order market opportunities through supply chain analysis.

## Overview

Supply Chain Intel helps fundamental investors identify non-obvious investment opportunities by:

1. **Exploring** themes, companies, or markets to discover second and third-order dependencies
2. **Validating** investment hypotheses with evidence-based analysis
3. **Monitoring** news continuously to alert when new information impacts theses

## Quick Start

### Simple Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/supply-chain-intel.git
cd supply-chain-intel

# Run one-time setup (installs dependencies and configures API key)
./setup.sh
```

That's it! The setup script will:
- Check Python version (3.11+ required)
- Create virtual environment
- Install all dependencies
- Prompt for your Anthropic API key
- Save configuration securely

### Manual Installation

If you prefer manual setup:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .

# Create .env file with your API key
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
chmod 600 .env
```

## Usage

You can run commands using either the `./run.sh` wrapper or `make` commands.

### Explore Investment Themes

Discover second and third-order investment opportunities:

```bash
# Using run.sh (simple)
./run.sh explore "AI infrastructure"
./run.sh explore "ASML"
./run.sh explore "renewable energy" --depth 3

# Using make (even simpler)
make explore QUERY="AI infrastructure"
make explore QUERY="semiconductor supply chain"
```

### Validate Investment Theses

Submit and validate investment hypotheses:

```bash
# Create a thesis
./run.sh thesis create "I think VRT is undervalued because AI data center demand is accelerating"
make thesis TEXT="NVDA undervalued due to AI infrastructure demand"

# List theses
./run.sh thesis list --status active
make thesis-list

# Update with new evidence
./run.sh thesis update vrt_thesis_20260128 --add "Management announced buyback"

# Resolve a thesis
./run.sh thesis resolve vrt_thesis_20260128 --confirmed
```

### Monitor News

Run monitoring scans for watchlist entities and active thesis triggers:

```bash
# Run monitoring
./run.sh monitor
make monitor

# Use custom sources
./run.sh monitor --sources custom_sources.json
```

### Manage Watchlist

```bash
# List watchlist
./run.sh watchlist list
make watchlist

# Add entity
./run.sh watchlist add NVDA --theme AI --theme semiconductors
make watchlist-add TICKER=NVDA THEME="AI"

# Remove entity
./run.sh watchlist remove NVDA
make watchlist-remove TICKER=NVDA
```

### View Outputs

```bash
# List digests
./run.sh digests
make digests

# List research documents
./run.sh research list
make research
```

### Launch Web-Based GUI

For a visual interface, launch the web GUI:

```bash
# Launch GUI (default port 5000)
./run.sh gui
make gui

# Custom port (if 5000 is in use)
./run.sh gui --port 8080

# Then open http://127.0.0.1:5000 in your browser (or your custom port)
```

**Note**: If you see "Address already in use" error on port 5000, it's likely macOS AirPlay Receiver. Either:
- Use a different port: `./run.sh gui --port 5001`
- Or disable AirPlay Receiver in System Settings > General > AirDrop & Handoff

The GUI provides:
- Dashboard with project statistics
- Interactive explore interface
- Thesis management
- Monitoring digest viewer
- Watchlist management
- Document history browser

### Get Help

```bash
# Show all available commands
./run.sh --help

# Show all make targets
make help
```

## Project Structure

```
supply-chain-intel/
├── src/
│   ├── agents/          # AI agents (explore, hypothesis, monitor)
│   ├── utils/           # Utilities (config, markdown, watchlist)
│   ├── models.py        # Data models
│   └── main.py          # CLI entry point
├── config/
│   └── sources.json     # News source configuration
├── data/
│   ├── watchlist.json   # Entity watchlist
│   ├── research/        # Research documents
│   ├── theses/          # Investment theses
│   └── digests/         # Monitoring digests
└── tests/               # Test suite
```

## Development

```bash
# Run tests
make test

# Or manually with pytest
source venv/bin/activate
pytest

# Run with coverage
pytest --cov=src tests/

# Clean up virtual environment and cache
make clean
```

## License

MIT License
