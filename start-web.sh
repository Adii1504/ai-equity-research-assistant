#!/usr/bin/env bash
# Start the web application (FastAPI + browser UI)
# Open http://localhost:8080 after startup

set -e
cd "$(dirname "$0")"

if [ ! -f .env ]; then
  echo "Copy .env.example to .env and set GROQ_API_KEY first."
  cp .env.example .env
  echo "Created .env — edit it with your API keys, then run this script again."
  exit 1
fi

echo "Installing web dependencies..."
pip install -r requirements-web.txt -q

echo ""
echo "Starting web server at http://localhost:8080"
echo "Press Ctrl+C to stop."
echo ""

python -m uvicorn web.server:app --host 0.0.0.0 --port 8080 --reload
