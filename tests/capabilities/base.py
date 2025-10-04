"""Base classes and utilities for QuantumFlux testing capabilities.

Migrated from API-test-space for production use.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple, Protocol, runtime_checkable, List
import os
import json
import datetime
import sys


@dataclass
class Ctx:
    """Context object for capability execution"""
    driver: Any
    artifacts_root: str
    debug: bool
    dry_run: bool
    verbose: bool = False


@dataclass
class CapResult:
    """Result object for capability execution"""
    ok: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    artifacts: Tuple[str, ...] = tuple()


@runtime_checkable
class Capability(Protocol):
    """Protocol for testing capabilities"""
    id: str
    kind: str  # "read" | "control" | "trade" | "control-read"

    def run(self, ctx: Ctx, inputs: Dict[str, Any]) -> CapResult:
        ...


def ensure_dir(path: str) -> str:
    """Ensure directory exists and return path"""
    os.makedirs(path, exist_ok=True)
    return path


def join_artifact(ctx: Ctx, *parts: str) -> str:
    """Join artifact path components"""
    base = ensure_dir(ctx.artifacts_root)
    return os.path.join(base, *parts)


def save_json(ctx: Ctx, rel_filename: str, data: Dict[str, Any]) -> str:
    """Save JSON data to artifacts directory"""
    out_path = join_artifact(ctx, rel_filename)
    ensure_dir(os.path.dirname(out_path))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return out_path


def timestamp() -> str:
    """Generate timestamp string"""
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def add_utils_to_syspath():
    """Add utils directory to Python path"""
    # Get the project root directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    utils_path = os.path.join(project_root, "tests", "utils")
    
    if utils_path not in sys.path:
        sys.path.insert(0, utils_path)


def take_screenshot_if(ctx: Ctx, rel_path: str) -> Optional[str]:
    """Take screenshot if driver is available"""
    if not ctx.driver:
        return None
    try:
        full_path = join_artifact(ctx, rel_path)
        ensure_dir(os.path.dirname(full_path))
        ctx.driver.save_screenshot(full_path)
        return full_path
    except Exception as e:
        if ctx.debug:
            print(f"Screenshot failed: {e}")
        return None


def first_non_empty(*vals: Optional[str]) -> Optional[str]:
    """Return first non-empty string value"""
    for v in vals:
        if v and v.strip():
            return v.strip()
    return None