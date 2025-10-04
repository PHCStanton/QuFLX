from __future__ import annotations

from typing import Any, Dict, Optional, Tuple, List
import asyncio
import threading
import time

from .base import Ctx, CapResult, Capability, timestamp, save_json


class AutomatedTrading(Capability):
    """
    Capability for automated trading operations.

    Interface inputs:
      - action: "start" | "stop" | "status" (required)
      - strategy_id: str (optional) - Strategy to use for trading
      - assets: List[str] (optional) - Assets to trade
      - risk_settings: Dict[str, Any] (optional) - Risk management settings

    Behavior:
      - Starts/stops automated trading loops
      - Monitors trading performance
      - Manages risk and position sizing
    Kind: "control"
    """
    id = "automated_trading"
    kind = "control"

    def __init__(self):
        self.is_running = False
        self.trading_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.trading_stats = {
            "is_running": False,
            "start_time": None,
            "trades_executed": 0,
            "total_pnl": 0.0,
            "active_positions": 0,
            "last_update": None
        }
        self.active_trades = []

    def run(self, ctx: Ctx, inputs: Dict[str, Any]) -> CapResult:
        action = inputs.get("action", "").strip().lower()
        strategy_id = inputs.get("strategy_id", "default")
        assets = inputs.get("assets", ["EURUSD", "GBPUSD"])
        risk_settings = inputs.get("risk_settings", {})

        if action not in ["start", "stop", "status"]:
            return CapResult(
                ok=False,
                data={"inputs": inputs},
                error="action must be 'start', 'stop', or 'status'",
                artifacts=()
            )

        if action == "start":
            return self._start_trading(ctx, strategy_id, assets, risk_settings)
        elif action == "stop":
            return self._stop_trading(ctx)
        elif action == "status":
            return self._get_status(ctx)

        return CapResult(ok=False, data={}, error="Invalid action", artifacts=())

    def _start_trading(self, ctx: Ctx, strategy_id: str, assets: List[str], risk_settings: Dict[str, Any]) -> CapResult:
        """Start automated trading."""
        if self.is_running:
            return CapResult(
                ok=False,
                data={"status": "already_running"},
                error="Automated trading is already running",
                artifacts=()
            )

        try:
            # Reset stop event
            self.stop_event.clear()

            # Initialize trading stats
            self.trading_stats = {
                "is_running": True,
                "start_time": timestamp(),
                "trades_executed": 0,
                "total_pnl": 0.0,
                "active_positions": 0,
                "strategy_id": strategy_id,
                "assets": assets,
                "risk_settings": risk_settings,
                "last_update": timestamp()
            }

            # Start trading thread
            self.trading_thread = threading.Thread(
                target=self._trading_loop,
                args=(ctx, strategy_id, assets, risk_settings),
                daemon=True
            )
            self.trading_thread.start()

            self.is_running = True

            # Save initial status if debug
            artifacts = []
            if ctx.debug:
                status_data = {
                    "action": "start",
                    "timestamp": timestamp(),
                    "strategy_id": strategy_id,
                    "assets": assets,
                    "risk_settings": risk_settings,
                    "trading_stats": self.trading_stats
                }
                artifacts.append(save_json(ctx, f"automated_trading_start_{timestamp()}.json", status_data, "trading"))

            return CapResult(
                ok=True,
                data={
                    "status": "started",
                    "strategy_id": strategy_id,
                    "assets": assets,
                    "trading_stats": self.trading_stats
                },
                artifacts=tuple(artifacts)
            )

        except Exception as e:
            return CapResult(
                ok=False,
                data={"strategy_id": strategy_id, "assets": assets},
                error=f"Failed to start automated trading: {str(e)}",
                artifacts=()
            )

    def _stop_trading(self, ctx: Ctx) -> CapResult:
        """Stop automated trading."""
        if not self.is_running:
            return CapResult(
                ok=False,
                data={"status": "not_running"},
                error="Automated trading is not running",
                artifacts=()
            )

        try:
            # Signal stop
            self.stop_event.set()
            self.is_running = False

            # Wait for thread to finish (with timeout)
            if self.trading_thread and self.trading_thread.is_alive():
                self.trading_thread.join(timeout=5.0)

            # Update final stats
            self.trading_stats["is_running"] = False
            self.trading_stats["end_time"] = timestamp()

            # Save final status if debug
            artifacts = []
            if ctx.debug:
                status_data = {
                    "action": "stop",
                    "timestamp": timestamp(),
                    "final_stats": self.trading_stats,
                    "active_trades": self.active_trades
                }
                artifacts.append(save_json(ctx, f"automated_trading_stop_{timestamp()}.json", status_data, "trading"))

            return CapResult(
                ok=True,
                data={
                    "status": "stopped",
                    "final_stats": self.trading_stats,
                    "active_trades": self.active_trades
                },
                artifacts=tuple(artifacts)
            )

        except Exception as e:
            return CapResult(
                ok=False,
                data={"trading_stats": self.trading_stats},
                error=f"Failed to stop automated trading: {str(e)}",
                artifacts=()
            )

    def _get_status(self, ctx: Ctx) -> CapResult:
        """Get current trading status."""
        current_stats = self.trading_stats.copy()
        current_stats["last_update"] = timestamp()

        return CapResult(
            ok=True,
            data={
                "status": "running" if self.is_running else "stopped",
                "trading_stats": current_stats,
                "active_trades": self.active_trades.copy()
            },
            artifacts=()
        )

    def _trading_loop(self, ctx: Ctx, strategy_id: str, assets: List[str], risk_settings: Dict[str, Any]):
        """Main automated trading loop."""
        try:
            while not self.stop_event.is_set():
                try:
                    # Generate signals for each asset
                    for asset in assets:
                        if self.stop_event.is_set():
                            break

                        # Get signal for asset
                        signal_result = self._generate_signal_for_asset(ctx, asset, strategy_id)
                        if signal_result and signal_result.get("signal"):
                            # Execute trade based on signal
                            self._execute_signal_trade(ctx, asset, signal_result, risk_settings)

                        # Small delay between assets
                        time.sleep(0.1)

                    # Update stats
                    self.trading_stats["last_update"] = timestamp()

                    # Wait before next cycle (configurable interval)
                    interval = risk_settings.get("check_interval", 60)  # Default 60 seconds
                    self.stop_event.wait(timeout=interval)

                except Exception as e:
                    print(f"Trading loop error: {e}")
                    time.sleep(5)  # Brief pause on error

        except Exception as e:
            print(f"Trading loop fatal error: {e}")
        finally:
            self.is_running = False
            self.trading_stats["is_running"] = False

    def _generate_signal_for_asset(self, ctx: Ctx, asset: str, strategy_id: str) -> Optional[Dict[str, Any]]:
        """Generate trading signal for a specific asset."""
        try:
            # Import signal generation capability
            from .signal_generation import SignalGeneration

            signal_cap = SignalGeneration()
            result = signal_cap.run(ctx, {
                "asset": asset,
                "min_candles": 30,
                "signal_types": ["SMA", "RSI"]
            })

            if result.ok and result.data.get("signals"):
                # Return the strongest signal
                signals = result.data["signals"]
                best_signal = None
                best_confidence = 0.0

                for signal_type, signal_data in signals.items():
                    if isinstance(signal_data, dict) and signal_data.get("confidence", 0) > best_confidence:
                        best_signal = {
                            "type": signal_type,
                            "signal": signal_data.get("signal"),
                            "confidence": signal_data.get("confidence", 0)
                        }
                        best_confidence = signal_data.get("confidence", 0)

                return best_signal

        except Exception as e:
            print(f"Signal generation error for {asset}: {e}")

        return None

    def _execute_signal_trade(self, ctx: Ctx, asset: str, signal: Dict[str, Any], risk_settings: Dict[str, Any]):
        """Execute a trade based on signal."""
        try:
            # Determine trade direction
            signal_type = signal.get("signal", "")
            if signal_type in ["bullish", "oversold"]:
                side = "buy"
            elif signal_type in ["bearish", "overbought"]:
                side = "sell"
            else:
                return  # No clear signal

            confidence = signal.get("confidence", 0)
            min_confidence = risk_settings.get("min_confidence", 0.6)

            if confidence < min_confidence:
                return  # Signal not strong enough

            # Import trade capability
            from .trade_click_cap import TradeClick

            trade_cap = TradeClick()
            result = trade_cap.run(ctx, {
                "side": side,
                "timeout": 5
            })

            if result.ok:
                # Update trading stats
                self.trading_stats["trades_executed"] += 1

                # Add to active trades
                trade_record = {
                    "asset": asset,
                    "side": side,
                    "signal": signal,
                    "timestamp": timestamp(),
                    "status": "active"
                }
                self.active_trades.append(trade_record)
                self.trading_stats["active_positions"] = len(self.active_trades)

        except Exception as e:
            print(f"Trade execution error for {asset}: {e}")


# Factory for orchestrator
def build() -> Capability:
    return AutomatedTrading()