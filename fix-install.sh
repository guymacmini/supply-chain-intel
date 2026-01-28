#!/usr/bin/env bash

# Supply Chain Intel - Fix Installation Script
# Quick fix for users who already ran setup but have ModuleNotFoundError

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Fixing package installation...${NC}"
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo -e "${RED}Error: Virtual environment not found${NC}"
    echo "Please run ./setup.sh first"
    exit 1
fi

# Activate venv
source venv/bin/activate

# Reinstall package
echo -e "${YELLOW}Reinstalling package with correct configuration...${NC}"
pip install --force-reinstall -e . --quiet

echo ""
echo -e "${GREEN}✓ Package reinstalled successfully${NC}"
echo ""
echo "You can now run:"
echo -e "  ${GREEN}./run.sh explore \"AI infrastructure\"${NC}"
echo -e "  ${GREEN}./run.sh --help${NC}"
echo ""
