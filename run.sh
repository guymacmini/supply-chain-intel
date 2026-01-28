#!/usr/bin/env bash

# Supply Chain Intel - Run Script
# Simple wrapper to run commands with automatic environment setup

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if setup has been run
if [ ! -d "venv" ]; then
    echo -e "${RED}Error: Virtual environment not found${NC}"
    echo "Please run setup first:"
    echo "  ./setup.sh"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    echo "Please run setup first:"
    echo "  ./setup.sh"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Load environment variables
set -a
source .env
set +a

# Check if API key is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${RED}Error: ANTHROPIC_API_KEY not set in .env${NC}"
    echo "Please run setup again:"
    echo "  ./setup.sh"
    exit 1
fi

# Add project root to PYTHONPATH so src module can be found
export PYTHONPATH="${PWD}:${PYTHONPATH}"

# Run the command
supply-chain-intel "$@"
