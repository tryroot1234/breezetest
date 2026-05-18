"""CLI entry point for BreezeTest."""

from __future__ import annotations

import click

from breezetest import __version__


@click.group()
@click.version_option(version=__version__, prog_name="breezetest")
def cli() -> None:
    """BreezeTest - E2E testing should be a breeze."""


@cli.command()
@click.argument("paths", nargs=-1, type=click.Path())
@click.option("-t", "--tag", multiple=True, help="Run only tests with this tag")
@click.option("-b", "--browser", default="chromium", help="Browser: chromium, firefox, webkit")
@click.option("--headless/--headed", default=True, help="Run in headless or headed mode")
@click.option("-w", "--workers", default=1, type=int, help="Number of parallel workers")
@click.option("-r", "--retries", default=None, type=int, help="Retry failed tests N times")
@click.option("--timeout", default=None, type=int, help="Global timeout in ms")
@click.option("--report-dir", default="./breezetest-reports", help="Directory for reports")
@click.option("--html/--no-html", default=True, help="Generate HTML report")
@click.option("--junit/--no-junit", default=True, help="Generate JUnit XML")
@click.option("--screenshot-mode", default="failure", type=click.Choice(["always", "failure", "never"]))
@click.option("--base-url", default=None, help="Override base_url from YAML")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.option("--dry-run", is_flag=True, help="Parse and validate without executing")
@click.option("-e", "--env", multiple=True, help="Set variable: key=value")
@click.option("--fail-fast", is_flag=True, help="Stop on first failure")
def run(
    paths: tuple[str, ...],
    tag: tuple[str, ...],
    browser: str,
    headless: bool,
    workers: int,
    retries: int | None,
    timeout: int | None,
    report_dir: str,
    html: bool,
    junit: bool,
    screenshot_mode: str,
    base_url: str | None,
    verbose: bool,
    dry_run: bool,
    env: tuple[str, ...],
    fail_fast: bool,
) -> None:
    """Run E2E tests from YAML files."""
    import asyncio
    import sys
    from pathlib import Path

    from breezetest.core.models import RunConfig
    from breezetest.core.parser import parse_suite_file
    from breezetest.core.runner import TestRunner

    # Parse env vars
    env_vars: dict[str, str] = {}
    for e in env:
        if "=" in e:
            k, v = e.split("=", 1)
            env_vars[k] = v

    # Find YAML files
    yaml_paths = list(paths) if paths else ["."]
    yaml_files: list[Path] = []
    for p in yaml_paths:
        path = Path(p)
        if path.is_file():
            yaml_files.append(path)
        elif path.is_dir():
            yaml_files.extend(sorted(path.glob("**/*.yml")))
            yaml_files.extend(sorted(path.glob("**/*.yaml")))

    if not yaml_files:
        click.echo("No YAML test files found.", err=True)
        sys.exit(3)

    # Parse suites
    suites = []
    for f in yaml_files:
        try:
            suites.append(parse_suite_file(f))
        except Exception as e:
            click.echo(f"Error parsing {f}: {e}", err=True)
            sys.exit(2)

    # Build run config
    config = RunConfig(
        paths=[str(p) for p in yaml_files],
        tags=list(tag),
        browser=browser,
        headless=headless,
        workers=workers,
        retries=retries,
        timeout=timeout,
        report_dir=report_dir,
        html=html,
        junit=junit,
        screenshot_mode=screenshot_mode,
        base_url=base_url,
        verbose=verbose,
        dry_run=dry_run,
        fail_fast=fail_fast,
        env_vars=env_vars,
    )

    runner = TestRunner(config)
    result = asyncio.run(runner.run_suites(suites))

    if result.failed > 0 or result.error > 0:
        sys.exit(1)
    sys.exit(0)


@cli.command()
@click.option("--dir", default=".", help="Directory to initialize")
@click.option("--with-examples", is_flag=True, help="Include example test files")
def init(dir: str, with_examples: bool) -> None:
    """Scaffold a new BreezeTest project."""
    from pathlib import Path

    target = Path(dir)
    test_dir = target / "tests"
    test_dir.mkdir(parents=True, exist_ok=True)

    config_content = """\
config:
  base_url: "https://example.com"
  browser: chromium
  headless: true
  timeout: 30000

tests: []
"""
    (target / "breeze.yml").write_text(config_content)
    click.echo(f"Created {target / 'breeze.yml'}")

    if with_examples:
        example_content = """\
config:
  base_url: "https://example.com"
  browser: chromium
  headless: true

tests:
  - name: "Page loads successfully"
    tags: [smoke]
    steps:
      - action: goto
        value: "/"
        description: "Navigate to home page"
      - action: assert_visible
        selector: "h1"
        description: "Title should be visible"

  - name: "Has correct title"
    tags: [smoke]
    steps:
      - action: goto
        value: "/"
      - action: assert_title
        value: "Example Domain"
"""
        (test_dir / "example.yml").write_text(example_content)
        click.echo(f"Created {test_dir / 'example.yml'}")

    click.echo("Done! Run 'breeze run' to execute tests.")


@cli.command("list")
@click.argument("paths", nargs=-1, type=click.Path())
@click.option("-t", "--tag", multiple=True, help="Filter by tag")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_tests(paths: tuple[str, ...], tag: tuple[str, ...], as_json: bool) -> None:
    """List available tests without running them."""
    import json
    from pathlib import Path

    from breezetest.core.parser import expand_parameterized, parse_suite_file

    yaml_paths = list(paths) if paths else ["."]
    yaml_files: list[Path] = []
    for p in yaml_paths:
        path = Path(p)
        if path.is_file():
            yaml_files.append(path)
        elif path.is_dir():
            yaml_files.extend(sorted(path.glob("**/*.yml")))
            yaml_files.extend(sorted(path.glob("**/*.yaml")))

    tag_set = set(tag)
    test_list = []

    for f in yaml_files:
        try:
            suite = parse_suite_file(f)
        except Exception as e:
            click.echo(f"Error parsing {f}: {e}", err=True)
            continue

        for test in suite.tests:
            if tag_set and not tag_set.intersection(test.tags):
                continue
            expanded = expand_parameterized(test)
            for t in expanded:
                entry = {
                    "file": str(f),
                    "name": t.name,
                    "tags": t.tags,
                    "skip": t.skip,
                    "steps": len(t.steps),
                }
                test_list.append(entry)

    if as_json:
        click.echo(json.dumps(test_list, indent=2))
    else:
        if not test_list:
            click.echo("No tests found.")
            return
        for entry in test_list:
            skip = " [SKIP]" if entry["skip"] else ""
            tags = f" ({', '.join(entry['tags'])})" if entry["tags"] else ""
            click.echo(f"  {entry['name']}{tags}{skip} - {entry['steps']} steps")


@cli.command()
@click.option("--report-dir", default="./breezetest-reports", help="Report directory")
@click.option("--open", "open_browser", is_flag=True, help="Open HTML report in browser")
def report(report_dir: str, open_browser: bool) -> None:
    """View or open test reports."""
    import webbrowser
    from pathlib import Path

    report_path = Path(report_dir) / "report.html"
    if not report_path.exists():
        click.echo(f"No report found at {report_path}")
        return

    if open_browser:
        webbrowser.open(f"file://{report_path.resolve()}")
    else:
        click.echo(f"Report: {report_path.resolve()}")
