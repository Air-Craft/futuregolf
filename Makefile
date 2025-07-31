# FutureGolf - Makefile

.PHONY: start backend setup clean help test update-reqs

# Default target
all: start

# Start both services
start:
	@echo "🏌️ Starting FutureGolf..."
	@./start.sh

# Start backend only
backend:
	@echo "🔧 Starting backend..."
	@cd backend && pdm run python start_server.py

# Setup development environment
setup:
	@echo "⚙️ Setting up development environment..."
	@cd backend && pyenv local 3.10 && pdm install
	@echo "✅ Setup complete!"

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	@cd backend && pdm install

# Update requirements.txt using pipreqs
update-reqs:
	@echo "📝 Updating backend/requirements.txt with pipreqs..."
	@bash -c "cd backend && pdm run pip install pipreqs && pdm run pipreqs . --force"
	@echo "✅ requirements.txt updated."

# Clean up processes
clean:
	@echo "🧹 Cleaning up..."
	@pkill -f "python start_server.py" || true
	@echo "✅ Cleanup complete!"

# Run tests
test:
	@echo "🧪 Running tests..."
	@echo "🧪 No tests configured for iOS app. Run tests in Xcode."

# Show help
help:
	@echo "FutureGolf Development Commands:"
	@echo ""
	@echo "  make start        - Start backend server"
	@echo "  make backend      - Start backend only"
	@echo "  make setup        - Setup development environment"
	@echo "  make install      - Install dependencies"
	@echo "  make update-reqs  - Update backend/requirements.txt from virtualenv"
	@echo "  make clean        - Stop all services"
	@echo "  make test         - Run tests"
	@echo "  make help         - Show this help"
	@echo ""
	@echo "Quick start: make setup && make start"