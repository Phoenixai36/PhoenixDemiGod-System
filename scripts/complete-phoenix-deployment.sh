#!/bin/bash

# Phoenix Hydra Complete Deployment Script
# This script completes the Phoenix Hydra deployment with all monetization features

set -e

echo "🚀 Starting Phoenix Hydra Complete Deployment"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
print_status "Checking prerequisites..."

if ! command -v podman &> /dev/null; then
    print_error "Podman is not installed. Please install Podman first."
    exit 1
fi

if ! command -v podman-compose &> /dev/null; then
    print_warning "podman-compose not found. Installing..."
    pip3 install podman-compose
fi

if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js first."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Install Node.js dependencies
print_status "Installing Node.js dependencies..."
cd scripts
npm install
cd ..

# Deploy affiliate badges
print_status "Deploying affiliate badges..."
node scripts/deploy-badges.js

# Generate NEOTEC application
print_status "Generating NEOTEC grant application..."
python3 scripts/neotec-generator.py

# Setup Podman rootless
print_status "Setting up Podman rootless environment..."
systemctl --user enable --now podman.socket
loginctl enable-linger $USER

# Create systemd user directory
mkdir -p ~/.config/containers/systemd
mkdir -p ~/.config/systemd/user

# Copy systemd files
print_status "Installing systemd container definitions..."
cp infra/podman/systemd/*.container ~/.config/containers/systemd/
cp infra/podman/systemd/*.pod ~/.config/containers/systemd/
cp infra/podman/systemd/.env ~/.config/containers/systemd/

# Reload systemd
systemctl --user daemon-reload

# Start Phoenix Hydra services
print_status "Starting Phoenix Hydra services..."
systemctl --user enable phoenix-hydra.pod
systemctl --user start phoenix-hydra.pod

# Wait for services to start
print_status "Waiting for services to initialize..."
sleep 30

# Health checks
print_status "Performing health checks..."

# Check if services are running
if systemctl --user is-active --quiet phoenix-hydra.pod; then
    print_status "✅ Phoenix Hydra pod is running"
else
    print_error "❌ Phoenix Hydra pod failed to start"
    systemctl --user status phoenix-hydra.pod
fi

# Check individual services
services=("phoenix-core" "n8n-phoenix" "windmill-phoenix" "revenue-db" "nca-toolkit")
for service in "${services[@]}"; do
    if systemctl --user is-active --quiet "${service}.container"; then
        print_status "✅ ${service} is running"
    else
        print_warning "⚠️  ${service} may not be running properly"
    fi
done

# Test API endpoints
print_status "Testing API endpoints..."

# Test Phoenix Core
if curl -f -s http://localhost:8080/health > /dev/null; then
    print_status "✅ Phoenix Core API is responding"
else
    print_warning "⚠️  Phoenix Core API not responding on port 8080"
fi

# Test n8n
if curl -f -s http://localhost:5678 > /dev/null; then
    print_status "✅ n8n is responding"
else
    print_warning "⚠️  n8n not responding on port 5678"
fi

# Test Windmill
if curl -f -s http://localhost:8000 > /dev/null; then
    print_status "✅ Windmill is responding"
else
    print_warning "⚠️  Windmill not responding on port 8000"
fi

# Update revenue metrics
print_status "Updating revenue metrics..."
node scripts/revenue-tracking.js

# Display final status
echo ""
echo "🎉 Phoenix Hydra Deployment Complete!"
echo "======================================"
echo ""
echo "📊 Access Points:"
echo "  • Phoenix Core:    http://localhost:8080"
echo "  • n8n Workflows:   http://localhost:5678"
echo "  • Windmill:        http://localhost:8000"
echo "  • NCA Toolkit:     http://localhost:8081"
echo ""
echo "💰 Monetization Status:"
echo "  • Affiliate badges: ✅ Deployed"
echo "  • NEOTEC application: ✅ Generated"
echo "  • Revenue tracking: ✅ Active"
echo ""
echo "🎯 Next Steps:"
echo "  1. Review NEOTEC application and submit before June 12, 2025"
echo "  2. Configure AWS Marketplace listing"
echo "  3. Set up Prometheus/Grafana monitoring"
echo "  4. Apply for ENISA FEPYME loan (€300k)"
echo ""
echo "📈 Revenue Target 2025: €400k+"
echo "🚀 Phoenix Hydra is ready for enterprise scaling!"

exit 0