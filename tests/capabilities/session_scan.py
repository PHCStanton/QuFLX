"""Session scan capability for reading trading session state.

Migrated from API-test-space for production use.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple, List

from .base import Ctx, CapResult, Capability, add_utils_to_syspath, save_json, timestamp

# Ensure we can import local utils
add_utils_to_syspath()
try:
    from selenium_helpers import UIControls, ZoomManager
    from selenium.webdriver.common.by import By
except Exception:
    UIControls = None  # type: ignore
    ZoomManager = None  # type: ignore
    By = None  # type: ignore


class SessionScan(Capability):
    """
    Capability: Read session state only (no automation):
      - Account: DEMO/REAL
      - Balance: $x.xx
      - Strategy: placeholder string
      - Trade Amount: read-only
      - Optional viewport scale check (read-only)
    Interface: run(ctx, {})
    Outputs: {account, balance, strategy: "PLACEHOLDER", amount, viewport_scale}
    Kind: "read"
    """
    id = "session_scan"
    kind = "read"

    def run(self, ctx: Ctx, inputs: Dict[str, Any]) -> CapResult:
        data: Dict[str, Any] = {
            "account": "UNKNOWN",
            "balance": None,
            "strategy": "PLACEHOLDER",
            "amount": None,
            "viewport_scale": None,
            "raw": {},
        }
        artifacts: List[str] = []

        if UIControls is None or By is None:
            return CapResult(ok=False, data=data, error="Selenium helpers not available", artifacts=tuple(artifacts))

        ui_controls = UIControls(ctx.driver)

        # Account & balance
        try:
            # Get account type
            account_type = ui_controls.get_account_type()
            if account_type in ("DEMO", "REAL"):
                data["account"] = account_type
            
            # Get balance
            balance = ui_controls.get_account_balance()
            data["balance"] = balance
            
            data["raw"]["balance_and_account_meta"] = {
                "account_type": account_type,
                "balance": balance
            }
        except Exception as e:
            data["raw"]["balance_error"] = str(e)

        # Amount (read-only)
        try:
            amount_val, amount_meta = self._read_amount_value(ctx)
            data["amount"] = amount_val
            data["raw"]["amount_meta"] = amount_meta
        except Exception as e:
            data["raw"]["amount_error"] = str(e)

        # Viewport scale
        try:
            if ZoomManager is not None:
                scale = ZoomManager.get_zoom_scale(ctx.driver)
                data["viewport_scale"] = scale
                # Check if scale is within expected range (around 0.67 with 0.05 tolerance)
                expected = 0.67
                tolerance = 0.05
                ok_zoom = abs(scale - expected) <= tolerance if scale else False
                data["raw"]["viewport_scale_ok"] = ok_zoom
        except Exception:
            pass

        if ctx.debug:
            try:
                ts = timestamp()
                path = save_json(ctx, f"session_scan_{ts}.json", data)
                artifacts.append(path)
            except Exception:
                pass

        return CapResult(ok=True, data=data, error=None, artifacts=tuple(artifacts))

    # ---------- helpers ----------

    def _parse_money(self, text: str) -> Optional[float]:
        """Parse money string to float"""
        try:
            t = text.replace(",", "").replace(" ", "")
            for sym in ["$", "€", "£"]:
                t = t.replace(sym, "")
            if t.count(".") > 1 and "," in t:
                t = t.replace(".", "").replace(",", ".")
            return float(t)
        except Exception:
            try:
                t = text.replace(" ", "").replace(".", "").replace(",", ".")
                for sym in ["$", "€", "£"]:
                    t = t.replace(sym, "")
                return float(t)
            except Exception:
                return None

    def _read_amount_value(self, ctx: Ctx) -> Tuple[Optional[float], Dict[str, Any]]:
        """Read current trade amount value"""
        meta: Dict[str, Any] = {"strategies": [], "raw_value": None, "parsed": None}
        strategies = [
            ("xpath", "//*[contains(normalize-space(.), 'Amount')]/following::input[1]"),
            ("xpath", "//input[contains(@placeholder,'Amount') or contains(@aria-label,'Amount')]"),
            ("css", "input.amount, .amount input, input[name*='amount']"),
        ]
        el = None
        for strat, sel in strategies:
            try:
                if strat == "xpath":
                    els = ctx.driver.find_elements(By.XPATH, sel)
                else:
                    els = ctx.driver.find_elements(By.CSS_SELECTOR, sel)
            except Exception:
                els = []
            cand = next((e for e in els if self._is_displayed(e)), None)
            meta["strategies"].append({"strategy": strat, "selector": sel, "found": bool(cand)})
            if cand:
                el = cand
                break

        if not el:
            return None, meta

        try:
            val = (el.get_attribute("value") or "").strip()
            meta["raw_value"] = val
            norm = val.replace(" ", "").replace(",", "")
            parsed = None
            try:
                parsed = float(norm)
            except Exception:
                try:
                    parsed = float(val.replace(" ", "").replace(",", "."))
                except Exception:
                    parsed = None
            meta["parsed"] = parsed
            return parsed, meta
        except Exception as e:
            meta["error"] = str(e)
            return None, meta

    def _is_displayed(self, el) -> bool:
        """Check if element is displayed"""
        try:
            return el.is_displayed()
        except Exception:
            return False


# Factory
def build() -> Capability:
    return SessionScan()