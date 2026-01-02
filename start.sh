#!/bin/bash

# RecipeHolder - Quick Start Script
# This script helps you get started with RecipeHolder quickly

set -e

echo "========================================"
echo "  RecipeHolder - Quick Start"
echo "========================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
else
    echo "✅ .env file already exists"
fi
echo ""

# Create data directory
if [ ! -d data ]; then
    echo "📁 Creating data directory..."
    mkdir -p data/recipes
    echo "✅ Data directory created"
else
    echo "✅ Data directory already exists"
fi
echo ""

# Build and start containers
echo "🐳 Building Docker image..."
docker-compose build

echo ""
echo "🚀 Starting RecipeHolder..."
docker-compose up -d

echo ""
echo "⏳ Waiting for application to start..."
sleep 5

# Check if application is running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ RecipeHolder is running!"
    echo ""
    echo "========================================"
    echo "  🎉 Setup Complete!"
    echo "========================================"
    echo ""
    echo "📱 Access the application:"
    echo "   Web Interface: http://localhost:8000"
    echo "   API Docs:      http://localhost:8000/docs"
    echo "   Health Check:  http://localhost:8000/health"
    echo ""
    echo "📁 Your recipes are stored in: ./data/recipes/"
    echo ""
    echo "🛠️  Useful commands:"
    echo "   View logs:     docker-compose logs -f recipe-holder"
    echo "   Stop app:      docker-compose down"
    echo "   Restart:       docker-compose restart"
    echo ""
    echo "📚 For more information, see:"
    echo "   - README.md"
    echo "   - GETTING_STARTED.md"
    echo ""
else
    echo "⚠️  Application may still be starting..."
    echo "   Check logs: docker-compose logs -f recipe-holder"
    echo "   Or visit: http://localhost:8000"
fi
