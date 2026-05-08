#!/bin/bash
# Render deployment build script

set -o errexit

pip install -r requirements.txt

# Create necessary directories
mkdir -p uploads
mkdir -p crawler/.state

echo "Build complete"