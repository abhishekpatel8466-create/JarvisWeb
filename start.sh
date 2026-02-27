#!/usr/bin/env bash
set -euo pipefail

# Start the Ollama server in the background so the Python API can use it
ollama serve &
# Give the server a few seconds to initialize
sleep 5

# Start the Flask application – the Space runtime will provide $PORT.
# Ensure Flask binds to 0.0.0.0 and the correct port.
python -m flask run --host=0.0.0.0 --port=${PORT:-5000}
