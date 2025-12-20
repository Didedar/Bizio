#!/bin/bash
# Quick start script for Bizio CRM

set -e

echo "🚀 Starting Bizio CRM..."
echo ""

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install Docker and Docker Compose."
    exit 1
fi

# Check if .env exists, if not copy from example
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ .env created. Please update with your settings if needed."
    else
        echo "⚠️  .env.example not found. Using default values."
    fi
fi

# Start services
echo "🐳 Starting Docker services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
if ! docker-compose ps | grep -q "Up"; then
    echo "❌ Services failed to start. Check logs with: docker-compose logs"
    exit 1
fi

echo "✅ Services started successfully!"
echo ""

# Ask if user wants to seed demo data
read -p "📦 Do you want to seed demo data? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🌱 Seeding demo data..."
    docker-compose exec backend python seed_data.py
    echo "✅ Demo data seeded!"
    echo ""
    echo "📧 Login credentials:"
    echo "   Email: demo@bizio.com"
    echo "   Password: demo123"
fi

echo ""
echo "✅ Bizio CRM is ready!"
echo ""
echo "📍 Available at:"
echo "   - API: http://localhost:8000"
echo "   - Docs: http://localhost:8000/docs"
echo "   - ReDoc: http://localhost:8000/redoc"
echo ""
echo "📋 Useful commands:"
echo "   - View logs: docker-compose logs -f"
echo "   - Stop: docker-compose down"
echo "   - Restart: docker-compose restart"
echo ""
echo "🧪 Run tests:"
echo "   docker-compose exec backend pytest -v"
echo ""
echo "Happy coding! 🎉"

