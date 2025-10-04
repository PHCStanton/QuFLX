Short answer
Yes, you can package this as a clean, developer‑friendly Python library + CLI that exposes an unofficial PocketOption WebSocket client with streaming and optional persistence. Keep the core reusable, provide typed models and async iterators, ship a simple CLI, and document the Chrome attach requirement and ToS risks.

Recommended packaging strategy

1) Shape the product
- Deliverables:
  - A Python library (“SDK”) that developers import (no automation baked in).
  - A small CLI for quick data streaming/collection and sanity checks.
  - Examples (scripts + notebooks) that show how to integrate into bots/pipelines.
  - Documentation site + README with quickstart and ToS/legal disclaimers.

- Public API (clean, async-first)
  - pocketws.Client(attach=…)  # abstraction around your Selenium/Chrome attach
  - await client.connect()
  - async for event in client.stream_ticks(assets=[…]): yield TickEvent(…)
  - async for candle in client.stream_candles(assets=[…], timeframe=“1m”): yield Candle(…)
  - Built‑in aggregation to form closed candles reliably (what you already have)
  - Optional persistence sinks (CSV out of the box); JSONL/Parquet as extras

- Non‑official API disclaimer
  - Prominently document that this uses reverse‑engineered WebSocket traffic from a running browser session, can break without notice, and may violate ToS. “Use at your own risk, educational purposes only.”

2) Library design (proposed modules)
- pocketws/
  - __init__.py
  - client.py            # high‑level async client, connect/subscribe/stream
  - attach.py            # Chrome attach (remote debugging) abstraction
  - decoder.py           # base64/Socket.IO frame normalization and parsing
  - models.py            # pydantic/dataclasses: TickEvent, Candle, SessionInfo
  - aggregator.py        # tick→candle formation (closed candle semantics)
  - persistence/
    - base.py            # Sink interface: write_tick, write_candle, rotate
    - csv_sink.py        # CSV sink with chunk rotation (100/1000 defaults)
    - jsonl_sink.py      # optional
    - parquet_sink.py    # optional (pyarrow)
  - utils/logging.py     # structured logging config
  - exceptions.py
- cli/
  - __init__.py
  - main.py              # console entrypoint “po”
- examples/
  - stream_ticks.py
  - stream_candles.py
  - save_both_csv.py
  - notebook.ipynb
- docs/
  - getting-started.md
  - chrome-attach.md
  - persistence.md
  - api-reference.md

3) Public API sketch (illustrative)

```python
# pip install pocketws
import asyncio
from pocketws import Client, CsvSink

async def main():
    client = Client(
        attach_host="127.0.0.1",
        attach_port=9222,
        verbose=False
    )
    await client.connect()

    # Optional persistence
    sink = CsvSink(
        candles_dir="data/.../1M_candle_data",
        ticks_dir="data/.../1M_tick_data",
        candle_chunk=100,
        tick_chunk=1000,
    )

    # Stream both: ticks + closed candles (via aggregator)
    async for evt in client.stream_both(assets=["EURUSD_otc"], timeframe="1m", sink=sink):
        if evt.kind == "tick":
            print("tick", evt.asset, evt.price, evt.ts)
        elif evt.kind == "candle":
            print("candle", evt.asset, evt.o, evt.h, evt.l, evt.c, evt.ts)

asyncio.run(main())
```

4) CLI design
- Installable console script “po”
- Examples:
  - po stream --assets EURUSD_otc --mode both --tf 1m --save-candles --save-ticks
  - po stream --assets EURUSD_otc,GBPUSD_otc --mode tick --tick-chunk 500
  - po check --attach 127.0.0.1:9222   # quick connectivity check
- Flags map to your current sessions:
  - --save-candles / --save-ticks
  - --candle-chunk-size / --tick-chunk-size
  - --out-dirs for target folders
  - --log-level

5) Packaging details (simple to install/compile)
- Use pyproject.toml (PEP 621) with hatchling or setuptools:
  - project.name = "pocketws"
  - project.dependencies = ["selenium", "pydantic>=2", "websockets? (if needed)", "typing-extensions", "colorlog", "rich"]
  - optional-dependencies = {"parquet": ["pyarrow"], "dev": ["ruff","black","mypy","pytest","pytest-asyncio"]}
  - entry points (console_scripts): {"po" = "pocketws.cli.main:app"}
- Type hints + mypy; ruff/black pre-commit; pytest + pytest-asyncio.
- GitHub Actions:
  - lint/test matrix on 3.10–3.12
  - build wheels
  - publish to TestPyPI / PyPI (manual release)
- Docker (optional):
  - Dev image with Python + Chrome + debugging port docs
  - For end users: they typically run their own Chrome; provide doc page.

6) Distribution + monetization options
- Open-source core + commercial extras
  - Core SDK on GitHub under a permissive or source-available license.
  - “Pro sinks” (Parquet, SQLite/Postgres sink), auto-resume, reconnect, or multi-asset charts as paid add-ons.
- Dual license (AGPL/commercial)
  - Public repo under AGPL (forces network usage disclosure) + sell commercial exceptions for closed use.
- Closed-source binary/wheel distribution
  - Private PyPI (Gemfury/Cloudsmith) and license key check.
  - Pros: more control; Cons: friction + maintenance.
- Simpler “one-off fee” approach
  - Sell access to a private GitHub repo via GitHub Sponsors/Stripe/Gumroad; ship source + license file.
  - Provide a “pro” branch with added sinks and reconnect features; automate access on payment.

7) Legal/ToS considerations
- Prominently warn users:
  - This is an unofficial integration using reverse-engineered WebSocket traffic.
  - It may break at any time; use at own risk; may violate the platform’s ToS.
  - No guarantee of fitness; for research/educational purposes.
- Require the user to run their own PocketOption account + local Chrome instance and to comply with laws/ToS.

8) Roadmap features (to add real value)
- Resilience:
  - Heartbeat detection, auto-reconnect, backoff
  - Duplicate suppression, gap detection
- Structured models:
  - pydantic models for TickEvent, Candle, SessionInfo, FavoriteList
- Storage providers:
  - CSV (built-in), JSONL (built-in), Parquet (optional), SQLite (optional)
- Adapter abstraction:
  - AdapterSelenium (current), future AdapterCDP (devtools protocol direct) if you later bypass Selenium
- Docs:
  - “Getting started in 5 minutes” + cookbook recipes
  - Examples for strategy backtesting, ML feature extraction

9) Branding and naming
- Avoid trademark conflicts in package/repo name (e.g., “pocketws”, “poption-ws”, “qx-ws-stream”).
- Tag releases with semantic versioning (v0.1.0, v0.2.0 …).

What I can implement next (concrete steps)
- Extract the clean SDK boundary into pocketws/ with pyproject.toml, add console entrypoint.
- Move your current persistence pieces into a sinks/ layer (CSV first).
- Provide async wrappers around the existing streaming loop (or keep sync with asyncio executor where needed).
- Write quickstart docs and a small CLI (“po stream …”).

If you want, toggle to Act mode and I’ll scaffold the package with:
- pyproject.toml + src/pocketws/* + CLI entrypoint
- migration of your current code paths into the new structure without breaking your working sessions
- minimal tests + docs + a sample release workflow