#!/bin/bash
# Start Yggdrasil API

cd /home/aaa/fibra/yggdrasil_api

# Load environment
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Default values
YGG_HOST=${YGG_HOST:-"200:421e:6385:4a8b:dca7:cfb:197f:e9c3"}
YGG_PORT=${YGG_PORT:-6040}

echo "🚀 Starting FTTH Yggdrasil API..."
echo "📍 Host: [$YGG_HOST]:$YGG_PORT"
echo "📚 Docs: http://[$YGG_HOST]:$YGG_PORT/docs"
echo ""

# Activate venv if exists
if [ -d "../venv" ]; then
    source ../venv/bin/activate
fi

# Run the API
python -m uvicorn main:app --host "$YGG_HOST" --port $YGG_PORT --reload
