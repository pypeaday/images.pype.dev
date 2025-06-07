#!/bin/bash
set -e

export VIRTUAL_ENV=/opt/venv

# Start the application
echo "Starting web server..."
exec "$@"
