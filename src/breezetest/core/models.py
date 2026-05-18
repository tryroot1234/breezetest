"""Pydantic models for BreezeTest data structures."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


class ViewportConfig(BaseModel):
    width: int = 1280
    height: int = 720


class BreezeConfig(BaseModel):
    base_url: str | None = None
    browser: Literal["chromium", "firefox", "webkit"] = "chromium"
    headless: bool = True
    viewport: ViewportConfig | None = None
    timeout: int = 30000
    retries: int = 0
    tags: list[str] = Field(default_factory=list)
    variables: dict[str, Any] = Field(default_factory=dict)


class Step(BaseModel):
    action: str
    selector: str | None = None
    value: Any = None
    options: dict[str, Any] = Field(default_factory=dict)
    description: str | None = None
    on_failure: Literal["fail", "warn", "skip_next"] = "fail"


class TestCase(BaseModel):
    name: str
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    skip: bool = False
    retry: int | None = None
    steps: list[Step] = Field(default_factory=list)
    data: list[dict[str, Any]] | str | None = None


class TestSuite(BaseModel):
    config: BreezeConfig = Field(default_factory=BreezeConfig)
    tests: list[TestCase] = Field(default_factory=list)
    source_file: Path | None = None


class StepResult(BaseModel):
    step: Step
    status: Literal["passed", "failed", "skipped", "error"]
    duration_ms: float = 0.0
    screenshot_path: str | None = None
    error_message: str | None = None


class TestResult(BaseModel):
    test_name: str
    status: Literal["passed", "failed", "skipped", "error"]
    duration_ms: float = 0.0
    steps: list[StepResult] = Field(default_factory=list)
    screenshots: list[str] = Field(default_factory=list)
    error_message: str | None = None
    retry_count: int = 0
    parameters: dict[str, Any] | None = None


class SuiteResult(BaseModel):
    suite_name: str
    tests: list[TestResult] = Field(default_factory=list)
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    error: int = 0
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)
    browser: str = "chromium"
    base_url: str | None = None


class RunConfig(BaseModel):
    paths: list[str] = Field(default_factory=lambda: ["."])
    tags: list[str] = Field(default_factory=list)
    browser: str = "chromium"
    headless: bool = True
    workers: int = 1
    retries: int | None = None
    timeout: int | None = None
    report_dir: str = "./breezetest-reports"
    html: bool = True
    junit: bool = True
    screenshot_mode: Literal["always", "failure", "never"] = "failure"
    base_url: str | None = None
    verbose: bool = False
    dry_run: bool = False
    fail_fast: bool = False
    env_vars: dict[str, str] = Field(default_factory=dict)
