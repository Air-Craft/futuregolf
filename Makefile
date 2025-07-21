# FutureGolf - Makefile

.PHONY: start backend frontend setup clean help test

# Default target
all: start

# Start both services
start:
	@echo "🏌️ Starting FutureGolf..."
	@./start.sh

# Start backend only
backend:
	@echo "🔧 Starting backend..."
	@cd backend && source venv/bin/activate && python start_server.py

# Start frontend only
frontend:
	@echo "📱 Starting frontend..."
	@cd frontend && npx expo start --ios

# Setup development environment
setup:
	@echo "⚙️ Setting up development environment..."
	@cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
	@cd frontend && npm install
	@echo "✅ Setup complete!"

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	@cd backend && source venv/bin/activate && pip install -r requirements.txt
	@cd frontend && npm install

# Clean up processes
clean:
	@echo "🧹 Cleaning up..."
	@pkill -f "python start_server.py" || true
	@pkill -f "expo start" || true
	@echo "✅ Cleanup complete!"

# Run tests
test:
	@echo "🧪 Running tests..."
	@cd frontend && npm test

# Show help
help:
	@echo "FutureGolf Development Commands:"
	@echo ""
	@echo "  make start     - Start both backend and frontend"
	@echo "  make backend   - Start backend only"
	@echo "  make frontend  - Start frontend only"
	@echo "  make setup     - Setup development environment"
	@echo "  make install   - Install dependencies"
	@echo "  make clean     - Stop all services"
	@echo "  make test      - Run tests"
	@echo "  make help      - Show this help"
	@echo ""
	@echo "Quick start: make setup && make start"