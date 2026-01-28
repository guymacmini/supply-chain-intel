#!/usr/bin/env bash

# Supply Chain Intel - Setup Script
# One-time setup to install dependencies and configure environment

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Supply Chain Intel - Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 not found${NC}"
    echo "Please install Python 3.11 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}Error: Python $REQUIRED_VERSION or higher required${NC}"
    echo "Current version: $PYTHON_VERSION"
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
echo ""

# Create virtual environment
if [ -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists${NC}"
else
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi
echo ""

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip --quiet
echo -e "${GREEN}✓ pip upgraded${NC}"
echo ""

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install --force-reinstall -e . --quiet
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Configure API key
if [ -f ".env" ]; then
    echo -e "${YELLOW}.env file already exists${NC}"
    read -p "Do you want to update your API key? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}Keeping existing .env file${NC}"
        API_KEY_CONFIGURED=true
    fi
fi

if [ -z "$API_KEY_CONFIGURED" ]; then
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  API Key Configuration${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo "Please enter your Anthropic API key:"
    echo "(Get one at: https://console.anthropic.com/settings/keys)"
    echo ""
    read -p "API Key: " -r API_KEY

    if [ -z "$API_KEY" ]; then
        echo -e "${RED}Error: API key cannot be empty${NC}"
        exit 1
    fi

    echo "ANTHROPIC_API_KEY=$API_KEY" > .env
    chmod 600 .env
    echo ""
    echo -e "${GREEN}✓ API key saved to .env${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Setup Complete! 🎉${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "You can now use Supply Chain Intel:"
echo ""
echo -e "  ${BLUE}./run.sh explore \"AI infrastructure\"${NC}"
echo -e "  ${BLUE}./run.sh thesis create \"Your thesis...\"${NC}"
echo -e "  ${BLUE}./run.sh monitor${NC}"
echo -e "  ${BLUE}./run.sh watchlist list${NC}"
echo ""
echo "Or use make commands:"
echo ""
echo -e "  ${BLUE}make explore QUERY=\"AI infrastructure\"${NC}"
echo -e "  ${BLUE}make monitor${NC}"
echo ""
echo "For help:"
echo -e "  ${BLUE}./run.sh --help${NC}"
echo ""
