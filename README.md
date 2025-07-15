# pandas_tutor

takes pandas code and outputs json

## Development Setup

This project uses `uv` for fast Python package management and virtual environments.

### Prerequisites

1. Install `uv` if you haven't already:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

### Quick Setup

Run the setup script:

```bash
./setup_env.sh
```

### Manual Setup

1. Sync dependencies (creates virtual environment automatically):

   ```bash
   uv sync --extra dev
   ```

2. Activate the virtual environment:

   ```bash
   source .venv/bin/activate
   ```

   Or for fish shell:

   ```fish
   source .venv/bin/activate.fish
   ```

### Available Dependencies

- **Development**: `uv sync --extra dev` - includes all development tools (black, mypy, testing, etc.)
- **CI**: `uv sync --extra ci` - minimal dependencies for continuous integration
- **Base**: `uv sync` - only the core dependencies

### Lock File

The `uv.lock` file ensures reproducible builds across different environments. It's automatically created and maintained by `uv sync`.

### Running Tests

```bash
# Activate the environment first
source .venv/bin/activate

# Run tests
python -m pytest pandas_tutor/tests/
```
