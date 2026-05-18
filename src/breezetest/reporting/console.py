"""Rich console output for test execution."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from breezetest.core.models import RunConfig, SuiteResult, TestResult


STATUS_COLORS = {
    "passed": "green",
    "failed": "red",
    "skipped": "yellow",
    "error": "bold red",
}

STATUS_LABELS = {
    "passed": "PASS",
    "failed": "FAIL",
    "skipped": "SKIP",
    "error": "ERR ",
}


class ConsoleReporter:
    def __init__(self, verbose: bool = False) -> None:
        self.console = Console()
        self.verbose = verbose

    def print_header(self, config: RunConfig, test_count: int) -> None:
        header = Text()
        header.append("BreezeTest ", style="bold cyan")
        header.append(f"v0.1.0", style="dim")
        self.console.print(header)

        info = Text()
        info.append(f"Browser: {config.browser}", style="dim")
        info.append(f" | Workers: {config.workers}", style="dim")
        info.append(f" | Tests: {test_count}", style="dim")
        self.console.print(info)
        self.console.print()

    def print_test_result(self, result: TestResult) -> None:
        color = STATUS_COLORS.get(result.status, "white")
        label = STATUS_LABELS.get(result.status, "????")

        text = Text()
        text.append(f"  [{label}] ", style=color)
        text.append(result.test_name, style="bold" if result.status == "failed" else "")
        text.append(f" ({result.duration_ms / 1000:.2f}s)", style="dim")

        if result.parameters:
            params = ", ".join(f"{k}={v}" for k, v in result.parameters.items())
            text.append(f" [{params}]", style="dim")

        self.console.print(text)

        if result.status in ("failed", "error"):
            for step in result.steps:
                if step.error_message:
                    self.console.print(f"         {step.error_message}", style="red")
                if step.screenshot_path:
                    self.console.print(
                        f"         Screenshot: {step.screenshot_path}", style="dim"
                    )

    def print_retry_header(self, attempt: int, count: int) -> None:
        self.console.print()
        self.console.print(
            f"  Retry #{attempt}: {count} failed test(s)", style="yellow bold"
        )

    def print_report_path(self, path: str) -> None:
        self.console.print(f"  Report: {path}", style="dim")

    def print_summary(self, result: SuiteResult) -> None:
        self.console.print()

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Metric", style="bold")
        table.add_column("Value", justify="right")

        table.add_row("Total", str(result.total))
        table.add_row("Passed", f"[green]{result.passed}[/green]")
        table.add_row("Failed", f"[red]{result.failed}[/red]")
        table.add_row("Skipped", f"[yellow]{result.skipped}[/yellow]")
        table.add_row("Errors", f"[bold red]{result.error}[/bold red]")
        table.add_row("Duration", f"{result.duration_ms / 1000:.2f}s")

        color = "green" if result.failed == 0 and result.error == 0 else "red"
        panel = Panel(table, title=f"[{color}]Summary[/{color}]", border_style=color)
        self.console.print(panel)
