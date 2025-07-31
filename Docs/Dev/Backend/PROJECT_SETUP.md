# PDM Setup and Usage

## Overview

The FutureGolf backend uses PDM (Python Dependency Manager) for managing Python dependencies. PDM is a modern Python package manager that supports PEP 582, simplifying virtual environment management.

## Prerequisites

- Python 3.10.x (required)
- pyenv (recommended for Python version management)

## Initial Setup

### 1. Install Python 3.10 with pyenv

```bash
# Install pyenv if not already installed
brew install pyenv

# Install Python 3.10
pyenv install 3.10.14

# Set local Python version for the backend
cd backend
pyenv local 3.10
```

### 2. Install PDM

```bash
# Install PDM globally
pip install pdm

# Or using pipx (recommended)
pipx install pdm
```

### 3. Install Backend Dependencies

```bash
cd backend
pdm install
```

This will:
- Create a virtual environment automatically
- Install all dependencies from `pyproject.toml`
- Set up the project for development

## Usage

### Running the Backend Server

```bash
# Using PDM
cd backend
pdm run python start_server.py

# Or using the Makefile
make backend
```

### Installing New Dependencies

```bash
cd backend

# Add a production dependency
pdm add fastapi

# Add a development dependency
pdm add -dG test pytest

# Add a specific version
pdm add "pydantic>=2.0"
```

### Updating Dependencies

```bash
# Update all dependencies
pdm update

# Update a specific dependency
pdm update fastapi

# Show outdated packages
pdm list --outdated
```

### Managing Virtual Environment

PDM automatically manages the virtual environment, but you can access it if needed:

```bash
# Show virtual environment info
pdm info

# Run a shell in the virtual environment
pdm shell

# Run any command in the virtual environment
pdm run <command>
```

## Configuration

The backend configuration is in `pyproject.toml`:

- **[project]**: Basic project metadata
- **dependencies**: Production dependencies
- **[dependency-groups]**: Development and test dependencies
- **requires-python**: Python version constraint (3.10.*)

## Troubleshooting

### Python Version Issues

If you get a Python version error:

```bash
cd backend
pyenv local 3.10
pdm use python
```

### Dependency Conflicts

```bash
# Clear cache and reinstall
pdm cache clear
pdm install --clean
```

### Virtual Environment Issues

```bash
# Remove existing virtual environment
pdm venv remove

# Recreate and install
pdm install
```

## Migration from pip

If migrating from `requirements.txt`:

```bash
# Import from requirements.txt
pdm import requirements.txt

# This will update pyproject.toml with the dependencies
```

## Best Practices

1. **Always use PDM commands** when working with the backend
2. **Commit both** `pyproject.toml` and `pdm.lock` to version control
3. **Use `pdm run`** prefix for all Python commands
4. **Keep Python 3.10** as the local version for consistency