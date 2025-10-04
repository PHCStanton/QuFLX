"""Trade click capability for BUY/SELL execution.

Migrated from API-test-space for production use.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple, List

from .base import Ctx, CapResult, Capability, add_utils_to_syspath, timestamp

# Ensure we can import local utils
add_utils_to_syspath()
try:
    from trade_helpers import TradeClickHelper
except Exception:
    TradeClickHelper = None  # type: ignore


class TradeClick(Capability):
    """
    Capability wrapper around TradeClickHelper for BUY/SELL execution.

    Interface inputs:
      - side: "buy" | "sell" (required)
      - timeout: int = 5
      - save_artifacts: bool = True (controlled by ctx.debug)

    Behavior:
      - Uses TradeClickHelper.robust_trade_click_with_meta for execution
      - Returns comprehensive diagnostics and trade details
      - Saves artifacts (screenshots, diagnostics JSON) when ctx.debug is True
    Kind: "trade"
    """
    id = "trade_click"
    kind = "trade"

    def run(self, ctx: Ctx, inputs: Dict[str, Any]) -> CapResult:
        if TradeClickHelper is None:
            return CapResult(ok=False, data={}, error="TradeClickHelper not available/importable", artifacts=())

        side = (inputs.get("side") or "").strip().lower()
        timeout = int(inputs.get("timeout", 5))
        save_artifacts = bool(ctx.debug)  # Control artifact saving with debug flag

        if side not in ("buy", "sell"):
            return CapResult(ok=False, data={"inputs": inputs}, error="side must be 'buy' or 'sell'", artifacts=())

        # Create trade click helper
        helper = TradeClickHelper(ctx.driver, timeout=timeout)
        
        # Execute trade click with diagnostics
        try:
            result = helper.robust_trade_click_with_meta(
                button_type=side.upper(),
                save_artifacts=save_artifacts
            )
            
            # Convert TradeExecutionResult to capability format
            data = {
                "ok": result.success,
                "trade_direction": result.trade_direction,
                "diagnostics": {
                    "timestamp": result.diagnostics.timestamp,
                    "button_type": result.diagnostics.button_type,
                    "element_found": result.diagnostics.element_found,
                    "element_visible": result.diagnostics.element_visible,
                    "element_enabled": result.diagnostics.element_enabled,
                    "element_clickable": result.diagnostics.element_clickable,
                    "click_attempted": result.diagnostics.click_attempted,
                    "click_successful": result.diagnostics.click_successful,
                    "coordinates": result.diagnostics.coordinates,
                    "element_text": result.diagnostics.element_text,
                    "element_classes": result.diagnostics.element_classes,
                    "element_attributes": result.diagnostics.element_attributes,
                    "page_url": result.diagnostics.page_url,
                    "viewport_size": result.diagnostics.viewport_size,
                    "scroll_position": result.diagnostics.scroll_position,
                    "error_message": result.diagnostics.error_message,
                    "pre_click_trades_count": result.diagnostics.pre_click_trades_count,
                    "post_click_trades_count": result.diagnostics.post_click_trades_count,
                    "trade_increment_verified": result.diagnostics.trade_increment_verified,
                    "execution_time_ms": result.diagnostics.execution_time_ms
                },
                "trade_details": result.trade_details,
                "screenshot_path": result.screenshot_path
            }
            
            # Collect artifact paths
            artifacts: List[str] = []
            if result.screenshot_path:
                artifacts.append(result.screenshot_path)
            artifacts.extend(result.artifacts_saved)
            
            return CapResult(
                ok=result.success, 
                data=data, 
                error=None if result.success else "trade_click reported failure", 
                artifacts=tuple(artifacts)
            )
            
        except Exception as e:
            return CapResult(
                ok=False, 
                data={"inputs": inputs, "error": str(e)}, 
                error=f"Trade click execution failed: {str(e)}", 
                artifacts=()
            )


# Factory for orchestrator
def build() -> Capability:
    return TradeClick()