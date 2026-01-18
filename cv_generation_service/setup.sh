#!/bin/bash
# Quick setup script for CV Generation Service
# Run this on your NAS to set up the service quickly

set -e

echo "=== CV Generation Service Setup ==="
echo ""

SERVICE_DIR="${1:-.}"
echo "Installing to: $SERVICE_DIR"

# Create directories
echo "Creating directories..."
mkdir -p "$SERVICE_DIR/templates/assets"
mkdir -p "$SERVICE_DIR/output"

echo "✓ Directories created"
echo ""

# Check Docker
if ! command -v docker-compose &> /dev/null; then
    echo "✗ Docker Compose not found. Please install Docker first."
    exit 1
fi
echo "✓ Docker Compose is installed"
echo ""

# Build
echo "Building Docker image..."
cd "$SERVICE_DIR"
docker-compose build

echo ""
echo "✓ Build complete"
echo ""

# Start
echo "Starting service..."
docker-compose up -d
sleep 5

# Test
echo "Testing service..."
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo "✓ Service is running!"
    echo ""
    echo "=== Setup Complete ==="
    echo ""
    echo "Your API is available at: http://localhost:5000"
    echo ""
    echo "Next steps:"
    echo "1. Find your NAS IP: hostname -I"
    echo "2. Update cv.html with your NAS IP"
    echo "3. Test: curl http://localhost:5000/health"
    echo ""
    echo "Service commands:"
    echo "  docker-compose up -d      # Start"
    echo "  docker-compose down        # Stop"
    echo "  docker-compose logs -f     # View logs"
    echo ""
else
    echo "✗ Service failed to start"
    echo "Check logs: docker-compose logs cv-generator"
    exit 1
fi
