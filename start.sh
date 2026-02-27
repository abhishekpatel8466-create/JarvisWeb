#!/usr/bin/env bash
set -euo pipefail

# Pull a quantized GGUF model (small RAM footprint)
# Change the model name if you prefer a different one
ollama pull qwen2.5:1.5b-q4_k_m

# Start the Flask application – the Space runtime will provide $PORT
python app.py
