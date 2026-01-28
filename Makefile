.PHONY: help setup explore thesis monitor watchlist digests research gui test clean

# Default target - show help
help:
	@echo "Supply Chain Intel - Make Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make setup              Run one-time setup"
	@echo ""
	@echo "Commands:"
	@echo "  make explore QUERY=\"AI infrastructure\"    Explore investment theme"
	@echo "  make thesis TEXT=\"Your thesis...\"        Create investment thesis"
	@echo "  make monitor                              Run news monitoring"
	@echo "  make watchlist                            Show watchlist"
	@echo "  make digests                              Show monitoring digests"
	@echo "  make research                             List research documents"
	@echo "  make gui                                  Launch web-based GUI"
	@echo ""
	@echo "Development:"
	@echo "  make test               Run test suite"
	@echo "  make clean              Remove virtual environment and cache"
	@echo ""
	@echo "Examples:"
	@echo "  make explore QUERY=\"semiconductor supply chain\""
	@echo "  make thesis TEXT=\"NVDA is undervalued due to AI demand\""
	@echo ""

# One-time setup
setup:
	@bash setup.sh

# Explore investment themes
explore:
ifndef QUERY
	@echo "Error: QUERY is required"
	@echo "Usage: make explore QUERY=\"AI infrastructure\""
	@exit 1
endif
	@./run.sh explore "$(QUERY)"

# Create investment thesis
thesis:
ifndef TEXT
	@echo "Error: TEXT is required"
	@echo "Usage: make thesis TEXT=\"Your investment thesis\""
	@exit 1
endif
	@./run.sh thesis create "$(TEXT)"

# List all theses
thesis-list:
	@./run.sh thesis list

# Show specific thesis
thesis-show:
ifndef ID
	@echo "Error: ID is required"
	@echo "Usage: make thesis-show ID=thesis_id"
	@exit 1
endif
	@./run.sh thesis show "$(ID)"

# Run monitoring
monitor:
	@./run.sh monitor

# Show watchlist
watchlist:
	@./run.sh watchlist list

# Add to watchlist
watchlist-add:
ifndef TICKER
	@echo "Error: TICKER is required"
	@echo "Usage: make watchlist-add TICKER=NVDA THEME=AI"
	@exit 1
endif
ifdef THEME
	@./run.sh watchlist add "$(TICKER)" --theme "$(THEME)"
else
	@./run.sh watchlist add "$(TICKER)"
endif

# Remove from watchlist
watchlist-remove:
ifndef TICKER
	@echo "Error: TICKER is required"
	@echo "Usage: make watchlist-remove TICKER=NVDA"
	@exit 1
endif
	@./run.sh watchlist remove "$(TICKER)"

# Show monitoring digests
digests:
	@./run.sh digests

# List research documents
research:
	@./run.sh research list

# Launch web-based GUI
gui:
	@./run.sh gui

# Run tests
test:
	@if [ ! -d "venv" ]; then echo "Error: Run 'make setup' first"; exit 1; fi
	@source venv/bin/activate && pytest tests/ -v

# Clean up
clean:
	@echo "Removing virtual environment and cache files..."
	@rm -rf venv
	@rm -rf __pycache__ .pytest_cache
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Cleaned up successfully"
