# Makefile DevOps Operations

## Overview

The FutureGolf project uses a Makefile at the root directory to streamline development operations. This provides consistent, simple commands for common tasks across the development team.

## Available Commands

### Core Development Commands

#### `make start` (default)
Starts the backend service using the `start.sh` script.

```bash
make start
# or just
make
```

#### `make backend`
Starts only the backend service using PDM.

```bash
make backend
# Equivalent to: cd backend && pdm run python start_server.py
```

### Environment Setup

#### `make setup`
Sets up the complete development environment:
- Sets Python 3.10 as the local version (using pyenv)
- Installs backend dependencies with PDM

```bash
make setup
```

#### `make install`
Installs/updates backend dependencies without environment setup.

```bash
make install
```

### Maintenance Commands

#### `make update-reqs`
Updates the `backend/requirements.txt` file using pipreqs (Note: Primary dependency management is through PDM).

```bash
make update-reqs
```

#### `make clean`
Stops all running services by killing backend processes.

```bash
make clean
```

### Testing

#### `make test`
Displays message about running iOS tests in Xcode.

```bash
make test
```

### Help

#### `make help`
Displays all available commands with descriptions.

```bash
make help
```

## Command Details

### Starting Services

The Makefile provides multiple ways to start services:

1. **Start Backend**: `make start` - Recommended for development
2. **Backend Only**: `make backend` - Alternative way to start backend

### Process Management

The Makefile handles process cleanup gracefully:

```bash
# Clean command kills processes safely
make clean
```

Uses `pkill -f` with `|| true` to avoid errors if processes aren't running.

### Environment Variables

The Makefile works with the project's `.env` files:
- Backend: `backend/.env`

## Best Practices

1. **Always use Make commands** for consistency across the team
2. **Run `make setup`** when first cloning the repository
3. **Use `make clean`** before switching between branches
4. **Check `make help`** if unsure about available commands

## Integration with PDM

The Makefile is updated to work with PDM for Python dependency management:

- `make setup` now uses `pdm install` instead of pip
- `make backend` uses `pdm run` to execute Python scripts
- Ensures Python 3.10 is set as the local version

## Troubleshooting

### Port Already in Use

If you get a "port already in use" error:

```bash
make clean
make start
```

### Dependencies Out of Sync

```bash
make clean
make install
make start
```

### Complete Reset

```bash
make clean
cd backend && pdm venv remove
make setup
make start
```

## Quick Reference

```bash
# Daily development workflow
make start          # Start working
make clean          # Stop working

# Setup new environment
make setup          # First time setup
make install        # Update dependencies

# Backend development
make backend        # Start backend

# Maintenance
make test           # Run tests
make update-reqs    # Update requirements.txt
make help           # Show available commands
```