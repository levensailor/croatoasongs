#!/bin/bash

# Song Lyrics Manager startup script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Song Lyrics Manager...${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Check if requirements are installed
if ! python -c "import fastapi" &> /dev/null; then
    echo -e "${YELLOW}Installing requirements...${NC}"
    pip install -r requirements.txt
fi

# Start the application with auto-reload
echo -e "${GREEN}Starting server at http://localhost:8000 with auto-reload${NC}"
echo -e "${YELLOW}Server will automatically restart when files change${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
