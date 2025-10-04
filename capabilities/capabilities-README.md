# API Test Space — Capabilities Guide

This document explains what each capability does, how to run them through the orchestrator, and how our Hybrid Chrome Session (persistent WebDriver state) works. It’s written so both a junior developer and a coding AI agent can follow along.

Contents
- Quick Start
- Persistent WebDriver State (Hybrid Chrome Session)
- Orchestrator and Pipelines
- Capabilities Catalog
  - session_scan
  - profile_scan
  - favorite_select
  - topdown_select
  - trade_click
  - take_screenshot
  - screenshot_control (manual screenshots)
- Artifacts and Conventions
- Troubleshooting

---

## Quick Start

1) Start Chrome with remote debugging (persistent profile):
- PowerShell:
```
python API-test-space/start_hybrid_session.py
```
This keeps you logged in and preserves cookies, tabs, etc. across runs.

2) Run a pipeline:
- Example: run only the 1m timeframe step (from the updown_only pipeline):
```
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/updown_only.json --steps updown_1m --debug --verbose
```

3) Manual screenshots (press “s” to capture, “q” to quit early):
- Example: 4 shots for H1, M15, M5, M1
```
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/updown_only.json --manual-screenshots --manual-count 4 --manual-labels H1,M15,M5,M1 --verbose
```
Output will be saved under: API-test-space/data_output/screenshots/screenhot_control/

Note: Use PowerShell or cmd, and make sure the terminal window has focus while pressing keys.

---

## Persistent WebDriver State (Hybrid Chrome Session)

Why: Many trading UIs require login and keep dynamic state in local storage. If we start a fresh Chrome each time, we lose that context and slow down testing. The Hybrid Chrome Session approach keeps a long-lived Chrome profile we attach to from Selenium.

How it works:
- `API-test-space/start_hybrid_session.py` launches Chrome with:
  - `--remote-debugging-port=9222`
  - `--user-data-dir` pointing to a stable directory (e.g., `~/ChromeSessions/HybridSession`)
- That user-data-dir stores cookies, sessions, extensions, and settings.
- In `run_pipeline.py`, we don’t start a new Chrome; we attach to the existing one:
  - We set `Options().add_experimental_option("debuggerAddress", "127.0.0.1:9222")`
  - Then create `webdriver.Chrome(options=options)`
- Result: the Selenium driver attaches to the already-open Chrome with your logged-in session.

When to use:
- Always start Chrome first using `start_hybrid_session.py`.
- Then run any pipelines or steps; they attach instead of relaunching the browser.

---

## Orchestrator and Pipelines

The orchestrator (`API-test-space/run_pipeline.py`) is the entry point that runs a sequence of steps (capabilities) defined by a pipeline JSON.

High level flow:
1. Load pipeline JSON (plus optional small overrides).
2. Build capabilities registry.
3. Attach to existing Chrome (Hybrid Session).
4. Create a context `Ctx` with:
   - `driver` (Selenium), `artifacts_root`, `debug`, `dry_run`, `verbose`
5. Run each step in order:
   - Respect policies:
     - `--dry-run` skips `trade` steps
     - `--stop-on-error` (default) stops at first error
     - `--debug` enables extra artifacts/meta
6. Print and save a run summary JSON in `artifacts_root`.

Key command-line flags:
- `--pipeline PATH`: pipeline JSON
- `--steps id1,id2`: run only a subset of steps
- `--dry-run`: skip `trade` steps
- `--debug`: enable extra screenshots/diagnostics
- `--verbose`: more console logs
- `--config PATH`: merge small JSON overrides (e.g., change labels or toggles for a step)
- Manual screenshots (see `screenshot_control` below):
  - `--manual-screenshots`
  - `--manual-count N` (1–8)
  - `--manual-letters` (e.g., `cdeg`)
  - `--manual-labels` (e.g., `H1,M15,M5,M1`)

Pipelines (current)
- `API-test-space/pipelines/asset_selection_and_trade.json` includes these step ids (in order):
  - `session` (session_scan)
  - `profile` (profile_scan)  ← NEW dedicated step
  - `updown_1m` (topdown_select)
  - `favorites` (favorite_select)
  - `buy_demo` (trade_click)
- `API-test-space/pipelines/updown_only.json`

Overrides loader note:
- `run_pipeline.py` reads overrides using `encoding="utf-8-sig"`. This avoids JSONDecodeError on files that contain a UTF‑8 BOM.

Example (conceptual):
```json
{
  "debug": true,
  "dry_run": false,
  "artifacts_root": "API-test-space/data_output",
  "steps": [
    { "id": "profile", "cap": "profile_scan", "enabled": true }
  ]
}
```

---

## Capabilities Catalog

Each capability implements:
- `id`: unique string
- `kind`: one of "read" | "control" | "trade" | "control-read"
- `run(ctx: Ctx, inputs: Dict[str, Any]) -> CapResult`

Common types:
- `Ctx` (context): holds `driver`, `artifacts_root`, and flags
- `CapResult`:
  - `ok: bool`
  - `data: Dict[str, Any]`
  - `error: Optional[str]`
  - `artifacts: Tuple[str, ...]` (paths under `artifacts_root`)

### 1) session_scan
- File: `capabilities/session_scan.py`
- id: `session_scan`
- kind: `read`
- What it does: Read-only snapshot of the session: account type (DEMO/REAL), balance, amount field value, and optional viewport scale check.
- Inputs: none (read-only)
- Outputs:
  ```
  {
    account: "DEMO" | "REAL" | "UNKNOWN",
    balance: float | null,
    strategy: "PLACEHOLDER",
    amount: float | null,
    viewport_scale: float | null,
    raw: { ...diagnostics... }
  }
  ```
- Artifacts: If `--debug` is on, a JSON like `session_scan_YYYYMMDD_HHMMSS.json` under `API-test-space/data_output/session_scan/`.

**Complete Command Examples:**
```powershell
# Basic session scan (minimal output)
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/asset_selection_and_trade.json --steps session --verbose

# Session scan with debug artifacts and JSON format
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/asset_selection_and_trade.json --steps session --debug --format json --verbose

# Session scan with custom output directory
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/asset_selection_and_trade.json --steps session --debug --output-dir "C:/MyResults" --verbose
```

### 2) profile_scan
- File: `capabilities/profile_scan.py`
- id: `profile_scan`
- kind: `read`
- What it does: Opens the avatar/profile dropdown and collects profile/account details. Uses layered selectors plus document-wide fallbacks for robustness.
- Inputs: none
- Outputs:
  ```
  {
    account, balance, amount,
    display_name, user_id, email, currency,
    level_label, xp_current, xp_total,
    account_banner,
    today_stats: { trades, turnover, profit },
    nav_items: [ ... ],
    raw: { ...diagnostics & fallbacks... }
  }
  ```
- Artifacts: If `--debug` is on, saves `profile_scan_YYYYMMDD_HHMMSS.json` under `API-test-space/data_output/`.

**Complete Command Examples:**
```powershell
# Basic profile scan
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/asset_selection_and_trade.json --steps profile --verbose

# Profile scan with debug artifacts and JSON format
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/asset_selection_and_trade.json --steps profile --debug --format json --verbose

# Combined session and profile scan
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/asset_selection_and_trade.json --steps session,profile --debug --verbose
```

### 3) favorite_select
- File: `capabilities/favorite_select.py`
- id: `favorite_select`
- kind: `read`
- What it does: Scans the favorites bar for assets with payout ≥ min_pct and can optionally click the first/last eligible item.
- Inputs:
  - `min_pct: int` (default 92)
  - `select: "first" | "last" | None` (optional)
- Outputs: `data = { eligible: [...], selected, min_pct, select_pref }`
- Artifacts: Pre/post screenshots when `--debug` is on; optional debug JSON.

**Complete Command Examples:**
```powershell
# Basic favorites scan (no selection, default 92% minimum payout)
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/asset_selection_and_trade.json --steps favorites --verbose

# Favorites scan with debug screenshots
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/asset_selection_and_trade.json --steps favorites --debug --verbose

# Scan favorites with custom minimum payout (95%) - requires override config
# First create override file: API-test-space/pipelines/overrides/favorites_95pct.json
# Content: {"steps": [{"id": "favorites", "inputs": {"min_pct": 95}}]}
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/asset_selection_and_trade.json --steps favorites --config API-test-space/pipelines/overrides/favorites_95pct.json --debug --verbose

# Scan and select first eligible asset (requires override config)
# Override file content: {"steps": [{"id": "favorites", "inputs": {"min_pct": 90, "select": "first"}}]}
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/asset_selection_and_trade.json --steps favorites --config API-test-space/pipelines/overrides/favorites_select_first.json --debug --verbose

# Scan and select last eligible asset with 88% minimum
# Override file content: {"steps": [{"id": "favorites", "inputs": {"min_pct": 88, "select": "last"}}]}
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/asset_selection_and_trade.json --steps favorites --config API-test-space/pipelines/overrides/favorites_select_last.json --debug --verbose
```

### 4) topdown_select
- File: `capabilities/topdown_select.py`
- id: `topdown_select`
- kind: `control-read`
- What it does: Visits a sequence of timeframe labels and captures screenshots (e.g., H1 → M15 → M5 → M1).
- Inputs:
  - `stack: "1m" | "5m"`
  - `labels: Optional[List[str]]` (override)
  - `delay_ms: int` (default 300)
  - `save: bool` (default True)
  - `screenshots_subdir: str` (default "updown")
  - `reopen_each: bool` (default True)
  - `menu_toggle_selectors: Optional[List[str]]`
  - `iframe_css: Optional[str]` or `iframe_index: Optional[int]`
- Outputs: includes attempts/strategies and screenshot paths per label.
- Artifacts: PNGs under `API-test-space/data_output/screenshots/updown/`.

**Complete Command Examples:**
```powershell
# Basic 1m timeframe sequence (default: H1, M15, M5, M1)
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/updown_only.json --steps updown_1m --debug --verbose

# 5m timeframe sequence (default: H4, H1, M15, M5)
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/updown_only.json --steps updown_5m --debug --verbose

# Custom timeframe labels with override config
# Override file content: {"steps": [{"id": "updown_1m", "inputs": {"labels": ["D1", "H4", "H1", "M30"]}}]}
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/updown_only.json --steps updown_1m --config API-test-space/pipelines/overrides/custom_timeframes.json --debug --verbose

# Updown with custom delay and subdirectory
# Override file content: {"steps": [{"id": "updown_1m", "inputs": {"delay_ms": 1000, "screenshots_subdir": "my_timeframes"}}]}
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/updown_only.json --steps updown_1m --config API-test-space/pipelines/overrides/slow_capture.json --debug --verbose

# Updown with menu toggle (for sites that need menu opening)
# Override file content: {"steps": [{"id": "updown_1m", "inputs": {"menu_toggle_selectors": [".timeframe-menu-button", "#time-selector"]}}]}
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/updown_only.json --steps updown_1m --config API-test-space/pipelines/overrides/menu_toggle.json --debug --verbose
```

### 5) trade_click
- File: `capabilities/trade_click_cap.py`
- id: `trade_click`
- kind: `trade`
- What it does: Executes a robust BUY/SELL click via a helper (`utils/trade_clicker.py`) with diagnostics.
- Inputs:
  - `side: "buy" | "sell"` (required)
  - `timeout: int` (default 5)
  - `root: str` (default "#put-call-buttons-chart-1")
- Outputs: meta from the click operation.
- Artifacts: Pre/post screenshots and diagnostics JSON when available.
- Policy: Skipped if `--dry-run` is used.

**Complete Command Examples:**
```powershell
# Execute BUY trade (REAL TRADING - BE CAREFUL!)
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/asset_selection_and_trade.json --steps buy_demo --debug --verbose

# Execute SELL trade with override config
# Override file content: {"steps": [{"id": "buy_demo", "inputs": {"side": "sell"}}]}
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/asset_selection_and_trade.json --steps buy_demo --config API-test-space/pipelines/overrides/sell_trade.json --debug --verbose

# DRY RUN - Test trade logic without actual execution (SAFE)
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/asset_selection_and_trade.json --steps buy_demo --dry-run --debug --verbose

# Trade with custom timeout and root selector
# Override file content: {"steps": [{"id": "buy_demo", "inputs": {"side": "buy", "timeout": 10, "root": "#custom-trade-buttons"}}]}
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/asset_selection_and_trade.json --steps buy_demo --config API-test-space/pipelines/overrides/custom_trade.json --debug --verbose

# Full trading pipeline (session → profile → timeframes → favorites → trade)
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/asset_selection_and_trade.json --debug --verbose

# Full trading pipeline in DRY RUN mode (SAFE)
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/asset_selection_and_trade.json --dry-run --debug --verbose
```

### 6) screenshot_control (Manual screenshots)
- File: `capabilities/screenshot_control.py`
- id: `screenshot_control`
- kind: `control-read`
- What it does: While running, press `s` to save a screenshot and `q` to quit early. Keeps it simple and avoids global hooks (Windows console only).
- Inputs:
  - `mode: "manual"` (current mode)
  - `count: int` (1–8, number of captures)
  - Provide either:
    - `letters: str` (maps to labels using a..h), or
    - `labels: List[str]` (explicit)
  - `subdir: str` defaults to `screenhot_control`
- Letter-to-label mapping:
  - a → D1, b → H4, c → H1, d → M15, e → M5, f → M3, g → M1, h → S30
- Artifacts:
  - Saved PNGs to `API-test-space/data_output/screenshots/screenhot_control/`
  - File format: `manual_{LABEL}_{YYYYMMDD_HHMMSS}.png`

**Complete Command Examples:**
```powershell
# Manual screenshots using letter mapping (c=H1, d=M15, e=M5, g=M1)
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/updown_only.json --manual-screenshots --manual-count 4 --manual-letters cdeg --verbose

# Manual screenshots with explicit labels
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/updown_only.json --manual-screenshots --manual-count 4 --manual-labels H1,M15,M5,M1 --verbose

# Manual screenshots with custom subdirectory
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/updown_only.json --manual-screenshots --manual-count 3 --manual-labels D1,H4,H1 --manual-subdir my_captures --verbose

# Run only manual screenshots (no other pipeline steps)
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/updown_only.json --steps manual_screens --manual-screenshots --manual-count 6 --manual-letters abcdef --verbose

# Manual screenshots after running updown timeframes
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/updown_only.json --steps updown_1m --manual-screenshots --manual-count 2 --manual-labels M5,M1 --debug --verbose

# Single manual screenshot with custom label
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/updown_only.json --manual-screenshots --manual-count 1 --manual-labels "Current_View" --verbose

# All available timeframes using letter mapping (a=D1, b=H4, c=H1, d=M15, e=M5, f=M3, g=M1, h=S30)
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/updown_only.json --manual-screenshots --manual-count 8 --manual-letters abcdefgh --verbose
```

**Usage Instructions:**
1. Run the command and wait for the "Press 's' to capture screenshot, 'q' to quit early" message
2. Navigate to the desired view in your browser
3. Press 's' to capture a screenshot (you'll see confirmation)
4. Repeat for each capture (up to the specified count)
5. Press 'q' to quit early if you don't need all screenshots
6. Screenshots are saved to `API-test-space/data_output/screenshots/screenhot_control/`

**Notes:**
- Terminal window must have focus for keypresses to register
- Works without `--debug` flag
- Letter-to-label mapping: a→D1, b→H4, c→H1, d→M15, e→M5, f→M3, g→M1, h→S30
- File format: `manual_{LABEL}_{YYYYMMDD_HHMMSS}.png`

---

## Artifacts and Conventions

Artifacts root:
- Default: `API-test-space/data_output` (overridable with `--output-dir`)

Common locations:
- Run summaries: `API-test-space/data_output/run_summary_*.json` and `data_output/run_summary/run_summary_*.json`
- Screenshots:
  - Updown timeframes: `API-test-space/data_output/screenshots/updown/`
  - Manual screenshots: `API-test-space/data_output/screenshots/screenhot_control/`
- Capability-specific JSONs (when `--debug` is enabled):
  - e.g., `session_scan_YYYYMMDD_HHMMSS.json`, `profile_scan_*.json`, `favorites_scan_*.json`

Naming:
- Screenshots are generally timestamped to avoid overwrites.
- Capability steps report `artifacts` with absolute paths for easy scraping/aggregation.

---

## Quick Reference - Copy & Paste Commands

### Essential Setup
```powershell
# 1. Always start Chrome session first
python API-test-space/start_hybrid_session.py

# 2. Basic pipeline run (safe - no trading)
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/updown_only.json --debug --verbose
```

### Individual Capabilities
```powershell
# Session scan
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/asset_selection_and_trade.json --steps session --debug --verbose

# Profile scan
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/asset_selection_and_trade.json --steps profile --debug --verbose

# Favorites scan
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/asset_selection_and_trade.json --steps favorites --debug --verbose

# Timeframe screenshots (1m stack)
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/updown_only.json --steps updown_1m --debug --verbose

# Manual screenshots
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/updown_only.json --manual-screenshots --manual-count 4 --manual-letters cdeg --verbose

# Trade execution (DRY RUN - SAFE)
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/asset_selection_and_trade.json --steps buy_demo --dry-run --debug --verbose
```

### Common Combinations
```powershell
# Session + Profile analysis
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/asset_selection_and_trade.json --steps session,profile --debug --verbose

# Full analysis pipeline (no trading)
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/asset_selection_and_trade.json --steps session,profile,updown_1m,favorites --debug --verbose

# Complete pipeline with DRY RUN (SAFE)
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/asset_selection_and_trade.json --dry-run --debug --verbose

# Timeframes + Manual screenshots
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/updown_only.json --steps updown_1m --manual-screenshots --manual-count 3 --manual-labels M15,M5,M1 --debug --verbose
```

### Override Config Examples
```powershell
# Create override files in API-test-space/pipelines/overrides/

# favorites_custom.json - Custom payout threshold and selection
{"steps": [{"id": "favorites", "inputs": {"min_pct": 95, "select": "first"}}]}

# timeframes_custom.json - Custom timeframe sequence
{"steps": [{"id": "updown_1m", "inputs": {"labels": ["D1", "H4", "H1", "M30"], "delay_ms": 1000}}]}

# trade_sell.json - Execute SELL instead of BUY
{"steps": [{"id": "buy_demo", "inputs": {"side": "sell", "timeout": 10}}]}

# Use with --config flag:
python API-test-space/run_pipeline.py --pipeline API-test-space/pipelines/asset_selection_and_trade.json --steps favorites --config API-test-space/pipelines/overrides/favorites_custom.json --debug --verbose
```

---

## Troubleshooting

- "Attach failed" or can't connect to 127.0.0.1:9222  
  Start Chrome using: `python API-test-space/start_hybrid_session.py`. Ensure no firewall/port conflict.

- A timeframe label isn't clickable in `topdown_select`
  Provide `menu_toggle_selectors` via overrides to explicitly open the menu.  
  If the control lives in an iframe, set `iframe_css` or `iframe_index`.  
  Example override file: `API-test-space/pipelines/overrides/updown_open_menu_overrides.json`

- `--dry-run` and `trade_click`  
  In dry-run mode, the orchestrator will skip `trade` steps by policy.

- profile_scan shows unexpected `display_name`  
  The dropdown UI sometimes renders labels in different containers/shadow roots.  
  `profile_scan` includes robust fallbacks; enable `--debug` and inspect the saved `profile_scan_*.json`'s `raw` meta (fallback sources are indicated) to fine-tune selectors if needed.

- Manual screenshots not responding to keypresses  
  Ensure the terminal window (PowerShell/cmd) has focus, not the browser. The 's' and 'q' keys must be pressed in the terminal.

- Pipeline fails with "capability not found"  
  Check that the step `id` in your pipeline JSON matches the capability `id`. Use `--verbose` to see available capabilities.
