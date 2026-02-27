#!/usr/bin/env bash
set -euo pipefail

# Pull a quantized GGUF model (small RAM footprint)
# Use a guard so we only download once – this speeds up restarts.
# Change the model name if you prefer a different one.
if ! ollama list | grep -q "gemma2:2b-q4_k_m"; then
  echo "Downloading Gemma 2B model (q4_k_m)..."
  ollama pull gemma2:2b-q4_k_m
else
  echo "Gemma 2B model already cached – skipping download."
fi

# Start the Flask application – the Space runtime will provide $PORT.
# Ensure Flask binds to 0.0.0.0 and the correct port.
python -m flask run --host=0.0.0.0 --port=${PORT:-5000}
