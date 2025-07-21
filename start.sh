#!/bin/bash

# FutureGolf - Startup Script
# Starts both backend and frontend services

set -e

echo "🏌️ Starting FutureGolf..."

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

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    print_error "Please run this script from the FutureGolf root directory"
    exit 1
fi

# Cleanup function
cleanup() {
    print_status "Shutting down FutureGolf services..."
    
    # Kill backend process
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        print_status "Backend stopped"
    fi
    
    # Kill frontend process
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        print_status "Frontend stopped"
    fi
    
    # Kill any remaining processes
    pkill -f "python start_server.py" 2>/dev/null || true
    pkill -f "expo start" 2>/dev/null || true
    
    print_status "All services stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

print_status "Starting backend server..."

# Start backend in background
cd backend
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found. Please run: cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

source venv/bin/activate
python start_server.py &
BACKEND_PID=$!

print_status "Backend started (PID: $BACKEND_PID)"

# Wait for backend to be ready
print_status "Waiting for backend to start..."
sleep 5

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    print_warning "Backend may not be ready yet, continuing anyway..."
fi

print_status "Starting frontend..."

# Start frontend
cd ../frontend
npx expo start --ios &
FRONTEND_PID=$!

print_status "Frontend started (PID: $FRONTEND_PID)"

# Print status
echo
echo -e "${BLUE}🎉 FutureGolf is starting up!${NC}"
echo
echo -e "${GREEN}Backend:${NC}  http://localhost:8000 (local)"
echo -e "${GREEN}Backend:${NC}  http://192.168.1.228:8000 (network)"
echo -e "${GREEN}Frontend:${NC} http://localhost:8081"
echo -e "${GREEN}Simulator:${NC} iOS Simulator should open automatically"
echo
echo -e "${BLUE}📱 For device testing:${NC}"
echo -e "${GREEN}1.${NC} Install Expo Go app on your device"
echo -e "${GREEN}2.${NC} Scan the QR code that appears"
echo -e "${GREEN}3.${NC} App will connect to http://192.168.1.228:8000"
echo
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID