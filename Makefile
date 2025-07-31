# FutureGolf - Makefile

.PHONY: start backend setup clean help test update-reqs

# Default target
all: start

# Start both services
start:
	@echo "🏌️ Starting FutureGolf..."
	@./start.sh

# Get API base URL
apibase:
	@echo "http://$$(scutil --get LocalHostName).local"

# Start backend only
backend:
	@echo "🔧 Starting backend on $$(make -s apibase):$${PORT:-8000}..." 
	@echo "   Be sure to update your Config.swift!"
	@PORT=$${PORT:-8000} && \
	cd backend && PORT=$$PORT pdm run python start_server.py

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
	@echo "  make backend      - Start backend only (accepts API_BASE_URL and PORT as args)"
	@echo "  make apibase      - Print local hostname URL (e.g., http://hostname.local)"
	@echo "  make setup        - Setup development environment"
	@echo "  make install      - Install dependencies"
	@echo "  make update-reqs  - Update backend/requirements.txt from virtualenv"
	@echo "  make clean        - Stop all services"
	@echo "  make test         - Run tests"
	@echo "  make help         - Show this help"
	@echo ""
	@echo "Usage examples:"
	@echo "  make backend                          # Uses default apibase and port 8000"
	@echo "  make backend http://192.168.1.5       # Custom API base URL, port 8000"
	@echo "  make backend http://192.168.1.5 8080  # Custom API base URL and port"
	@echo ""
	@echo "Quick start: make setup && make start"
