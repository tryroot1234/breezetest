# BreezeTest

> E2E testing should be a breeze

English | [中文](README_CN.md)

BreezeTest is a YAML-driven end-to-end testing framework powered by Playwright. Define your browser tests in simple YAML files and run them with a single command.

## Features

- **YAML-driven** - Write tests in declarative YAML, no code needed
- **30+ built-in actions** - Navigation, interaction, assertions, waits, screenshots
- **Data-driven testing** - Parameterize tests with inline data or CSV files
- **Beautiful reports** - Self-contained HTML reports with embedded screenshots
- **CI/CD ready** - JUnit XML output, GitHub Actions integration
- **Parallel execution** - Run tests across multiple browser instances
- **Plugin system** - Extend with custom actions and hooks

## Quick Start

### Install

```bash
pip install breezetest
playwright install chromium
```

### Create your first test

```bash
breeze init --with-examples
```

### Run tests

```bash
breeze run tests/
```

## YAML Test Format

```yaml
config:
  base_url: "https://example.com"
  browser: chromium
  headless: true
  variables:
    username: "testuser"

tests:
  - name: "User can log in"
    tags: [auth, smoke]
    steps:
      - action: goto
        value: "/login"

      - action: fill
        selector: "#username"
        value: "{{username}}"

      - action: fill
        selector: "#password"
        value: "secret123"

      - action: click
        selector: "button[type='submit']"

      - action: assert_visible
        selector: ".welcome-message"
        description: "Welcome message should appear"
```

## Supported Actions

| Category | Actions |
|----------|---------|
| Navigation | `goto`, `go_back`, `reload` |
| Interaction | `click`, `fill`, `type`, `select`, `check`, `uncheck`, `hover`, `press_key`, `drag_to`, `scroll_to` |
| Assertions | `assert_visible`, `assert_hidden`, `assert_text`, `assert_value`, `assert_attribute`, `assert_count`, `assert_url`, `assert_title`, `assert_enabled`, `assert_disabled`, `assert_checked` |
| Waits | `wait_for_selector`, `wait_for_url`, `wait_for_text`, `wait_for_timeout`, `wait_for_load` |
| Capture | `screenshot`, `capture_text`, `capture_attribute` |
| Script | `evaluate` |

## CLI Commands

```bash
# Run tests
breeze run tests/ --tags smoke --browser chromium --headed

# List tests
breeze list tests/ --tags auth

# Initialize project
breeze init --with-examples

# Open report
breeze report --open
```

## CLI Options

```
breeze run [PATHS...] [OPTIONS]

Options:
  -t, --tag TEXT          Run only tests with this tag (repeatable)
  -b, --browser TEXT      Browser: chromium, firefox, webkit (default: chromium)
  --headless/--headed     Run in headless or headed mode (default: headless)
  -w, --workers INT       Number of parallel workers (default: 1)
  -r, --retries INT       Retry failed tests N times
  --timeout INT           Global timeout in ms
  --report-dir PATH       Directory for reports (default: ./breezetest-reports)
  --html/--no-html        Generate HTML report (default: --html)
  --junit/--no-junit      Generate JUnit XML (default: --junit)
  --screenshot-mode TEXT   always, failure, never (default: failure)
  --base-url TEXT         Override base_url from YAML
  -v, --verbose           Verbose output
  --dry-run               Parse and validate without executing
  -e, --env TEXT          Set variable: key=value (repeatable)
  --fail-fast             Stop on first failure
```

## CI/CD Integration

### GitHub Actions

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install BreezeTest
        run: |
          pip install breezetest
          playwright install --with-deps chromium

      - name: Run E2E Tests
        run: breeze run tests/ --report-dir ./reports --junit

      - name: Upload Report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: e2e-report
          path: reports/
```

## Data-Driven Testing

```yaml
tests:
  - name: "Search returns results"
    data:
      - query: "python"
        expected_min: 1
      - query: "testing"
        expected_min: 1
    steps:
      - action: goto
        value: "/search?q={{query}}"
      - action: assert_count
        selector: ".result-item"
        value: ">={{expected_min}}"

  - name: "CSV data test"
    data: "test_data/users.csv"
    steps:
      - action: goto
        value: "/user/{{user_id}}"
      - action: assert_text
        selector: ".name"
        value: "{{expected_name}}"
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

MIT - See [LICENSE](LICENSE)
