from __future__ import annotations

from typing import Any, Dict, Optional, Tuple, List
import json
import os

from .base import Ctx, CapResult, Capability, timestamp, save_json


class StrategyManagement(Capability):
    """
    Capability for managing trading strategies.

    Interface inputs:
      - action: "list" | "get" | "create" | "update" | "delete" | "performance" (required)
      - strategy_id: str (required for get/update/delete/performance)
      - strategy_data: Dict[str, Any] (required for create/update)

    Behavior:
      - Manages strategy definitions and metadata
      - Tracks strategy performance metrics
      - Provides strategy CRUD operations
    Kind: "read"
    """
    id = "strategy_management"
    kind = "read"

    def __init__(self):
        # In-memory strategy storage (in production, this would be a database)
        self.strategies = self._load_default_strategies()

    def _load_default_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Load default trading strategies."""
        return {
            "quantum_flux_1min": {
                "strategy_id": "quantum_flux_1min",
                "name": "Quantum Flux 1-Minute Strategy",
                "description": "Advanced 1-minute timeframe strategy with multiple indicators",
                "model_path": "strategies/quantum_flux_strategy.py",
                "parameters": {
                    "timeframe": "1m",
                    "indicators": ["SMA", "RSI", "MACD", "Bollinger Bands"],
                    "entry_conditions": ["SMA crossover", "RSI divergence"],
                    "exit_conditions": ["Profit target", "Stop loss", "Trailing stop"]
                },
                "risk_settings": {
                    "max_position_size": 0.01,
                    "max_daily_loss": 0.05,
                    "max_concurrent_trades": 3,
                    "min_confidence": 0.65
                },
                "entry_conditions": [
                    "SMA(10) crosses above SMA(20)",
                    "RSI < 30 (oversold)",
                    "MACD histogram positive"
                ],
                "exit_conditions": [
                    "Profit target: 2:1 reward-to-risk",
                    "Stop loss: 1% of entry price",
                    "Trailing stop: 0.5% from highest high"
                ],
                "position_sizing": "Fixed percentage (1% per trade)",
                "created_at": "2025-01-01T00:00:00Z",
                "performance_metrics": {
                    "total_trades": 0,
                    "win_rate": 0.0,
                    "avg_profit": 0.0,
                    "max_drawdown": 0.0,
                    "sharpe_ratio": 0.0
                }
            },
            "conservative_sma": {
                "strategy_id": "conservative_sma",
                "name": "Conservative SMA Strategy",
                "description": "Simple moving average crossover strategy with conservative risk management",
                "model_path": "strategies/conservative_sma.py",
                "parameters": {
                    "timeframe": "5m",
                    "indicators": ["SMA(20)", "SMA(50)"],
                    "entry_conditions": ["SMA crossover"],
                    "exit_conditions": ["SMA crossover reversal"]
                },
                "risk_settings": {
                    "max_position_size": 0.005,
                    "max_daily_loss": 0.02,
                    "max_concurrent_trades": 1,
                    "min_confidence": 0.7
                },
                "entry_conditions": ["SMA(20) crosses above SMA(50)"],
                "exit_conditions": ["SMA(20) crosses below SMA(50)"],
                "position_sizing": "Fixed amount ($10 per trade)",
                "created_at": "2025-01-15T00:00:00Z",
                "performance_metrics": {
                    "total_trades": 0,
                    "win_rate": 0.0,
                    "avg_profit": 0.0,
                    "max_drawdown": 0.0,
                    "sharpe_ratio": 0.0
                }
            }
        }

    def run(self, ctx: Optional[Ctx], inputs: Dict[str, Any]) -> CapResult:
        action = inputs.get("action", "").strip().lower()
        strategy_id = inputs.get("strategy_id", "").strip()
        strategy_data = inputs.get("strategy_data", {})

        if action not in ["list", "get", "create", "update", "delete", "performance"]:
            return CapResult(
                ok=False,
                data={"inputs": inputs},
                error="action must be 'list', 'get', 'create', 'update', 'delete', or 'performance'",
                artifacts=()
            )

        try:
            if action == "list":
                return self._list_strategies(ctx)
            elif action == "get":
                return self._get_strategy(ctx, strategy_id)
            elif action == "create":
                return self._create_strategy(ctx, strategy_data)
            elif action == "update":
                return self._update_strategy(ctx, strategy_id, strategy_data)
            elif action == "delete":
                return self._delete_strategy(ctx, strategy_id)
            elif action == "performance":
                return self._get_strategy_performance(ctx, strategy_id)

        except Exception as e:
            return CapResult(
                ok=False,
                data={"action": action, "strategy_id": strategy_id},
                error=f"Strategy management operation failed: {str(e)}",
                artifacts=()
            )

        return CapResult(ok=False, data={}, error="Invalid action", artifacts=())

    def _list_strategies(self, ctx: Optional[Ctx]) -> CapResult:
        """List all strategies."""
        strategies_list = []
        for strategy_id, strategy in self.strategies.items():
            strategies_list.append({
                "id": strategy["strategy_id"],
                "name": strategy["name"],
                "description": strategy["description"],
                "created_at": strategy.get("created_at")
            })

        # Save strategy list if debug and ctx is available
        artifacts = []
        if ctx and ctx.debug:
            list_data = {
                "timestamp": timestamp(),
                "count": len(strategies_list),
                "strategies": strategies_list
            }
            artifacts.append(save_json(ctx, f"strategy_list_{timestamp()}.json", list_data, "strategies"))

        return CapResult(
            ok=True,
            data={
                "strategies": strategies_list,
                "count": len(strategies_list)
            },
            artifacts=tuple(artifacts)
        )

    def _get_strategy(self, ctx: Optional[Ctx], strategy_id: str) -> CapResult:
        """Get a specific strategy."""
        if strategy_id not in self.strategies:
            return CapResult(
                ok=False,
                data={"strategy_id": strategy_id},
                error=f"Strategy {strategy_id} not found",
                artifacts=()
            )

        strategy = self.strategies[strategy_id].copy()

        # Save strategy details if debug and ctx is available
        artifacts = []
        if ctx and ctx.debug:
            strategy_data = {
                "timestamp": timestamp(),
                "strategy": strategy
            }
            artifacts.append(save_json(ctx, f"strategy_{strategy_id}_{timestamp()}.json", strategy_data, "strategies"))

        return CapResult(
            ok=True,
            data={"strategy": strategy},
            artifacts=tuple(artifacts)
        )

    def _create_strategy(self, ctx: Optional[Ctx], strategy_data: Dict[str, Any]) -> CapResult:
        """Create a new strategy."""
        required_fields = ["strategy_id", "name", "description"]
        for field in required_fields:
            if field not in strategy_data:
                return CapResult(
                    ok=False,
                    data={"strategy_data": strategy_data},
                    error=f"Required field missing: {field}",
                    artifacts=()
                )

        strategy_id = strategy_data["strategy_id"]
        if strategy_id in self.strategies:
            return CapResult(
                ok=False,
                data={"strategy_id": strategy_id},
                error=f"Strategy {strategy_id} already exists",
                artifacts=()
            )

        # Create new strategy
        new_strategy = {
            "strategy_id": strategy_id,
            "name": strategy_data["name"],
            "description": strategy_data["description"],
            "model_path": strategy_data.get("model_path", ""),
            "parameters": strategy_data.get("parameters", {}),
            "risk_settings": strategy_data.get("risk_settings", {}),
            "entry_conditions": strategy_data.get("entry_conditions", []),
            "exit_conditions": strategy_data.get("exit_conditions", []),
            "position_sizing": strategy_data.get("position_sizing", ""),
            "created_at": timestamp(),
            "performance_metrics": {
                "total_trades": 0,
                "win_rate": 0.0,
                "avg_profit": 0.0,
                "max_drawdown": 0.0,
                "sharpe_ratio": 0.0
            }
        }

        self.strategies[strategy_id] = new_strategy

        # Save creation data if debug and ctx is available
        artifacts = []
        if ctx and ctx.debug:
            creation_data = {
                "timestamp": timestamp(),
                "action": "create",
                "strategy": new_strategy
            }
            artifacts.append(save_json(ctx, f"strategy_create_{strategy_id}_{timestamp()}.json", creation_data, "strategies"))

        return CapResult(
            ok=True,
            data={"strategy": new_strategy},
            artifacts=tuple(artifacts)
        )

    def _update_strategy(self, ctx: Optional[Ctx], strategy_id: str, strategy_data: Dict[str, Any]) -> CapResult:
        """Update an existing strategy."""
        if strategy_id not in self.strategies:
            return CapResult(
                ok=False,
                data={"strategy_id": strategy_id},
                error=f"Strategy {strategy_id} not found",
                artifacts=()
            )

        # Update strategy fields
        current_strategy = self.strategies[strategy_id]
        for key, value in strategy_data.items():
            if key != "strategy_id":  # Don't allow changing ID
                current_strategy[key] = value

        current_strategy["updated_at"] = timestamp()

        # Save update data if debug and ctx is available
        artifacts = []
        if ctx and ctx.debug:
            update_data = {
                "timestamp": timestamp(),
                "action": "update",
                "strategy_id": strategy_id,
                "updated_fields": list(strategy_data.keys()),
                "strategy": current_strategy
            }
            artifacts.append(save_json(ctx, f"strategy_update_{strategy_id}_{timestamp()}.json", update_data, "strategies"))

        return CapResult(
            ok=True,
            data={"strategy": current_strategy},
            artifacts=tuple(artifacts)
        )

    def _delete_strategy(self, ctx: Optional[Ctx], strategy_id: str) -> CapResult:
        """Delete a strategy."""
        if strategy_id not in self.strategies:
            return CapResult(
                ok=False,
                data={"strategy_id": strategy_id},
                error=f"Strategy {strategy_id} not found",
                artifacts=()
            )

        deleted_strategy = self.strategies.pop(strategy_id)

        # Save deletion data if debug and ctx is available
        artifacts = []
        if ctx and ctx.debug:
            deletion_data = {
                "timestamp": timestamp(),
                "action": "delete",
                "strategy_id": strategy_id,
                "deleted_strategy": deleted_strategy
            }
            artifacts.append(save_json(ctx, f"strategy_delete_{strategy_id}_{timestamp()}.json", deletion_data, "strategies"))

        return CapResult(
            ok=True,
            data={"deleted_strategy": deleted_strategy},
            artifacts=tuple(artifacts)
        )

    def _get_strategy_performance(self, ctx: Optional[Ctx], strategy_id: str) -> CapResult:
        """Get performance metrics for a strategy."""
        if strategy_id not in self.strategies:
            return CapResult(
                ok=False,
                data={"strategy_id": strategy_id},
                error=f"Strategy {strategy_id} not found",
                artifacts=()
            )

        strategy = self.strategies[strategy_id]
        performance = strategy.get("performance_metrics", {})

        # In a real implementation, this would calculate actual performance
        # For now, return the stored metrics

        # Save performance data if debug and ctx is available
        artifacts = []
        if ctx and ctx.debug:
            perf_data = {
                "timestamp": timestamp(),
                "strategy_id": strategy_id,
                "performance": performance
            }
            artifacts.append(save_json(ctx, f"strategy_performance_{strategy_id}_{timestamp()}.json", perf_data, "strategies"))

        return CapResult(
            ok=True,
            data={
                "strategy_id": strategy_id,
                "performance": performance
            },
            artifacts=tuple(artifacts)
        )


# Factory for orchestrator
def build() -> Capability:
    return StrategyManagement()
