#!/bin/ash

# Run the Docker container
docker run --rm -p 8000:8000 -e PORT=8000 -e PYTHONUNBUFFERED=1 lemme-draw-that
