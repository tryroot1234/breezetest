# BreezeTest

> 端到端测试，应该像微风一样轻松

[English](README.md) | 中文

BreezeTest 是一个基于 Playwright 的 YAML 驱动端到端测试框架。用简单的 YAML 文件定义浏览器测试，一条命令即可执行。

## 特性

- **YAML 驱动** - 用声明式 YAML 编写测试，无需写代码
- **30+ 内置动作** - 导航、交互、断言、等待、截图、JS 执行
- **数据驱动测试** - 用内联数据或 CSV 文件参数化测试
- **精美报告** - 自包含 HTML 报告，内嵌截图
- **CI/CD 就绪** - JUnit XML 输出，GitHub Actions 集成
- **并行执行** - 多浏览器实例并行运行测试
- **插件系统** - 通过自定义动作和钩子扩展功能

## 安装

### 一键安装（推荐）

**macOS / Linux：**

```bash
curl -sSL https://raw.githubusercontent.com/tryroot1234/breezetest/main/install.sh | bash
```

**Windows (PowerShell)：**

```powershell
irm https://raw.githubusercontent.com/tryroot1234/breezetest/main/install.ps1 | iex
```

脚本会自动安装 Python（如需要）、创建虚拟环境、安装 BreezeTest 和 Playwright 浏览器。

### pip 手动安装

```bash
pip install breezetest
playwright install --with-deps chromium
```

### Docker

```bash
docker build -t breezetest .
docker run -v ./tests:/app/tests breezetest run /app/tests
```

或使用 Docker Compose：

```bash
docker compose run breezetest run /app/tests
```

### 从源码安装（开发者）

```bash
# 自动化安装
curl -sSL https://raw.githubusercontent.com/tryroot1234/breezetest/main/install-dev.sh | bash

# 或手动安装
git clone https://github.com/tryroot1234/breezetest.git
cd breezetest
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
playwright install --with-deps chromium
```

详见 [CONTRIBUTING.md](CONTRIBUTING.md) 了解完整开发环境搭建。

## 快速开始

### 创建第一个测试

```bash
breeze init --with-examples
```

### 运行测试

```bash
breeze run tests/
```

## YAML 测试格式

```yaml
config:
  base_url: "https://example.com"
  browser: chromium
  headless: true
  variables:
    username: "testuser"

tests:
  - name: "用户可以登录"
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
        description: "欢迎消息应该出现"
```

## 支持的动作

| 类别 | 动作 |
|------|------|
| 导航 | `goto`, `go_back`, `reload` |
| 交互 | `click`, `fill`, `type`, `select`, `check`, `uncheck`, `hover`, `press_key`, `drag_to`, `scroll_to` |
| 断言 | `assert_visible`, `assert_hidden`, `assert_text`, `assert_value`, `assert_attribute`, `assert_count`, `assert_url`, `assert_title`, `assert_enabled`, `assert_disabled`, `assert_checked` |
| 等待 | `wait_for_selector`, `wait_for_url`, `wait_for_text`, `wait_for_timeout`, `wait_for_load` |
| 截图 | `screenshot`, `capture_text`, `capture_attribute` |
| 脚本 | `evaluate` |

## CLI 命令

```bash
# 运行测试
breeze run tests/ --tags smoke --browser chromium --headed

# 列出测试
breeze list tests/ --tags auth

# 初始化项目
breeze init --with-examples

# 打开报告
breeze report --open
```

## CLI 选项

```
breeze run [PATHS...] [OPTIONS]

选项:
  -t, --tag TEXT          只运行带此标签的测试（可重复）
  -b, --browser TEXT      浏览器: chromium, firefox, webkit（默认: chromium）
  --headless/--headed     无头/有头模式（默认: headless）
  -w, --workers INT       并行 worker 数量（默认: 1）
  -r, --retries INT       失败重试次数
  --timeout INT           全局超时（毫秒）
  --report-dir PATH       报告目录（默认: ./breezetest-reports）
  --html/--no-html        生成 HTML 报告（默认: --html）
  --junit/--no-junit      生成 JUnit XML（默认: --junit）
  --screenshot-mode TEXT   always, failure, never（默认: failure）
  --base-url TEXT         覆盖 YAML 中的 base_url
  -v, --verbose           详细输出
  --dry-run               仅解析验证，不执行
  -e, --env TEXT          设置变量: key=value（可重复）
  --fail-fast             遇到失败立即停止
```

## CI/CD 集成

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

      - name: 安装 BreezeTest
        run: |
          pip install breezetest
          playwright install --with-deps chromium

      - name: 运行 E2E 测试
        run: breeze run tests/ --report-dir ./reports --junit

      - name: 上传报告
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: e2e-report
          path: reports/
```

## 数据驱动测试

```yaml
tests:
  - name: "搜索返回结果"
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

  - name: "CSV 数据测试"
    data: "test_data/users.csv"
    steps:
      - action: goto
        value: "/user/{{user_id}}"
      - action: assert_text
        selector: ".name"
        value: "{{expected_name}}"
```

## 插件开发

```python
# my_plugin.py
from breezetest.actions.registry import register

@register("my_custom_action")
async def action_my_custom(page, locator, step, ctx):
    """自定义动作示例"""
    value = ctx.resolve_variables(step.value)
    await page.evaluate(f"document.title = '{value}'")
```

## 贡献指南

详见 [CONTRIBUTING.md](CONTRIBUTING.md) 了解开发环境搭建和贡献流程。

## 开源协议

MIT - 详见 [LICENSE](LICENSE)
