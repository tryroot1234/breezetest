# Contributing to BreezeTest

Thanks for your interest in contributing!

## Development Setup

### Automated (Recommended)

```bash
curl -sSL https://raw.githubusercontent.com/tryroot1234/breezetest/main/install-dev.sh | bash
```

### Manual

```bash
git clone https://github.com/tryroot1234/breezetest.git
cd breezetest
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
playwright install --with-deps chromium
```

## Running Tests

```bash
pytest tests/ -v
```

## Code Style

- Formatter/Linter: `ruff format src/ tests/ && ruff check src/ tests/`
- Type checking: `mypy src/breezetest/`
- Line length: 100 characters

## Adding New Actions

1. Create or edit a file in `src/breezetest/actions/`
2. Use the `@register("action_name")` decorator
3. The handler signature: `async def action_name(page, locator, step, ctx) -> None`
4. Add a test in `tests/`

Example:

```python
from breezetest.actions.registry import register

@register("my_action")
async def action_my_action(page, locator, step, ctx):
    # Your implementation here
    pass
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a PR with a clear description
