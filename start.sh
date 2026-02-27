#!/usr/bin/env bash
set -euo pipefail

# Start the Flask application
# The hosting environment will provide $PORT
python -m flask run --host=0.0.0.0 --port=${PORT:-10000}
