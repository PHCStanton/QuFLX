from __future__ import annotations

from typing import Any, Dict, Optional, Tuple, List
import asyncio
import threading
import time
import json
import random

from .base import Ctx, CapResult, Capability, timestamp, save_json


class ABTesting(Capability):
    """
    Capability for A/B testing of trading strategies.

    Interface inputs:
      - action: "start" | "status" | "results" (required)
      - test_name: str (required for start)
      - strategy_a: str (required for start) - Strategy ID for group A
      - strategy_b: str (required for start) - Strategy ID for group B
      - assets: List[str] (optional) - Assets to test
      - duration_minutes: int = 60 - Test duration in minutes
      - sample_size: int = 100 - Minimum trades per group

    Behavior:
      - Runs parallel A/B tests comparing two strategies
      - Tracks performance metrics for each strategy
      - Provides statistical analysis of results
    Kind: "control"
    """
    id = "ab_testing"
    kind = "control"

    def __init__(self):
        self.active_tests = {}
        self.test_results = {}

    def run(self, ctx: Ctx, inputs: Dict[str, Any]) -> CapResult:
        action = inputs.get("action", "").strip().lower()
        test_name = inputs.get("test_name", "").strip()

        if action not in ["start", "status", "results"]:
            return CapResult(
                ok=False,
                data={"inputs": inputs},
                error="action must be 'start', 'status', or 'results'",
                artifacts=()
            )

        if action == "start":
            return self._start_test(ctx, inputs)
        elif action == "status":
            return self._get_test_status(ctx, test_name)
        elif action == "results":
            return self._get_test_results(ctx, test_name)

        return CapResult(ok=False, data={}, error="Invalid action", artifacts=())

    def _start_test(self, ctx: Ctx, inputs: Dict[str, Any]) -> CapResult:
        """Start an A/B test."""
        test_name = inputs.get("test_name", "").strip()
        strategy_a = inputs.get("strategy_a", "").strip()
        strategy_b = inputs.get("strategy_b", "").strip()
        assets = inputs.get("assets", ["EURUSD", "GBPUSD"])
        duration_minutes = int(inputs.get("duration_minutes", 60))
        sample_size = int(inputs.get("sample_size", 100))

        if not test_name:
            return CapResult(ok=False, data={"inputs": inputs}, error="test_name is required", artifacts=())
        if not strategy_a or not strategy_b:
            return CapResult(ok=False, data={"inputs": inputs}, error="strategy_a and strategy_b are required", artifacts=())

        if test_name in self.active_tests:
            return CapResult(
                ok=False,
                data={"test_name": test_name},
                error=f"Test {test_name} is already running",
                artifacts=()
            )

        try:
            # Initialize test data
            test_data = {
                "test_name": test_name,
                "strategy_a": strategy_a,
                "strategy_b": strategy_b,
                "assets": assets,
                "duration_minutes": duration_minutes,
                "sample_size": sample_size,
                "start_time": timestamp(),
                "end_time": None,
                "status": "running",
                "groups": {
                    "A": {
                        "strategy": strategy_a,
                        "trades": [],
                        "metrics": {
                            "total_trades": 0,
                            "win_rate": 0.0,
                            "total_pnl": 0.0,
                            "avg_profit": 0.0,
                            "max_drawdown": 0.0
                        }
                    },
                    "B": {
                        "strategy": strategy_b,
                        "trades": [],
                        "metrics": {
                            "total_trades": 0,
                            "win_rate": 0.0,
                            "total_pnl": 0.0,
                            "avg_profit": 0.0,
                            "max_drawdown": 0.0
                        }
                    }
                }
            }

            self.active_tests[test_name] = test_data

            # Start test thread
            test_thread = threading.Thread(
                target=self._run_test,
                args=(ctx, test_name),
                daemon=True
            )
            test_thread.start()

            # Save test data if debug
            artifacts = []
            if ctx.debug:
                test_info = {
                    "action": "start",
                    "timestamp": timestamp(),
                    "test_data": test_data
                }
                artifacts.append(save_json(ctx, f"ab_test_start_{test_name}_{timestamp()}.json", test_info, "ab_testing"))

            return CapResult(
                ok=True,
                data={
                    "test_name": test_name,
                    "status": "started",
                    "strategy_a": strategy_a,
                    "strategy_b": strategy_b,
                    "duration_minutes": duration_minutes,
                    "sample_size": sample_size
                },
                artifacts=tuple(artifacts)
            )

        except Exception as e:
            return CapResult(
                ok=False,
                data={"test_name": test_name, "inputs": inputs},
                error=f"Failed to start A/B test: {str(e)}",
                artifacts=()
            )

    def _run_test(self, ctx: Ctx, test_name: str):
        """Run the A/B test."""
        try:
            test_data = self.active_tests[test_name]
            start_time = test_data["start_time"]
            duration_seconds = test_data["duration_minutes"] * 60
            sample_size = test_data["sample_size"]

            end_time = start_time + duration_seconds

            while time.time() < end_time:
                # Simulate trading for both strategies
                for group in ["A", "B"]:
                    if self._should_generate_trade(sample_size, test_data["groups"][group]):
                        trade = self._generate_simulated_trade(test_data["groups"][group]["strategy"])
                        test_data["groups"][group]["trades"].append(trade)
                        self._update_group_metrics(test_data["groups"][group])

                # Check if sample size reached for both groups
                if (len(test_data["groups"]["A"]["trades"]) >= sample_size and
                    len(test_data["groups"]["B"]["trades"]) >= sample_size):
                    break

                time.sleep(1)  # Check every second

            # Mark test as completed
            test_data["status"] = "completed"
            test_data["end_time"] = timestamp()

            # Calculate final results
            self._calculate_test_results(test_name)

            # Move to results
            self.test_results[test_name] = self.active_tests.pop(test_name)

        except Exception as e:
            print(f"A/B test {test_name} error: {e}")
            if test_name in self.active_tests:
                self.active_tests[test_name]["status"] = "error"
                self.active_tests[test_name]["error"] = str(e)

    def _should_generate_trade(self, target_sample_size: int, group_data: Dict[str, Any]) -> bool:
        """Determine if a trade should be generated for this group."""
        current_trades = len(group_data["trades"])
        if current_trades >= target_sample_size:
            return False

        # Simulate random trade generation (in real implementation, this would be based on strategy signals)
        return random.random() < 0.1  # 10% chance per check

    def _generate_simulated_trade(self, strategy_id: str) -> Dict[str, Any]:
        """Generate a simulated trade for testing."""
        # Simulate trade outcome
        is_win = random.random() > 0.4  # 60% win rate
        profit = random.uniform(0.5, 2.0) if is_win else random.uniform(-2.0, -0.5)

        return {
            "timestamp": timestamp(),
            "strategy": strategy_id,
            "asset": random.choice(["EURUSD", "GBPUSD", "USDJPY"]),
            "side": random.choice(["buy", "sell"]),
            "entry_price": random.uniform(1.0, 1.2),
            "exit_price": random.uniform(1.0, 1.2),
            "profit": profit,
            "is_win": is_win
        }

    def _update_group_metrics(self, group_data: Dict[str, Any]):
        """Update performance metrics for a group."""
        trades = group_data["trades"]
        if not trades:
            return

        total_trades = len(trades)
        wins = sum(1 for trade in trades if trade["is_win"])
        win_rate = wins / total_trades if total_trades > 0 else 0
        total_pnl = sum(trade["profit"] for trade in trades)
        avg_profit = total_pnl / total_trades if total_trades > 0 else 0

        # Calculate drawdown (simplified)
        cumulative_pnl = 0
        peak = 0
        max_drawdown = 0
        for trade in trades:
            cumulative_pnl += trade["profit"]
            peak = max(peak, cumulative_pnl)
            drawdown = peak - cumulative_pnl
            max_drawdown = max(max_drawdown, drawdown)

        group_data["metrics"] = {
            "total_trades": total_trades,
            "win_rate": round(win_rate, 3),
            "total_pnl": round(total_pnl, 2),
            "avg_profit": round(avg_profit, 2),
            "max_drawdown": round(max_drawdown, 2)
        }

    def _calculate_test_results(self, test_name: str):
        """Calculate final A/B test results and statistical significance."""
        if test_name not in self.active_tests:
            return

        test_data = self.active_tests[test_name]
        group_a = test_data["groups"]["A"]
        group_b = test_data["groups"]["B"]

        # Calculate statistical significance (simplified t-test simulation)
        a_win_rate = group_a["metrics"]["win_rate"]
        b_win_rate = group_b["metrics"]["win_rate"]
        a_trades = group_a["metrics"]["total_trades"]
        b_trades = group_b["metrics"]["total_trades"]

        # Simple significance test (in real implementation, use proper statistical tests)
        if a_trades > 10 and b_trades > 10:
            # Calculate z-score approximation
            p1 = a_win_rate
            p2 = b_win_rate
            n1 = a_trades
            n2 = b_trades

            p_combined = (p1 * n1 + p2 * n2) / (n1 + n2)
            se = ((p_combined * (1 - p_combined)) * (1/n1 + 1/n2)) ** 0.5

            if se > 0:
                z_score = abs(p1 - p2) / se
                # Z-score > 1.96 indicates 95% confidence
                significant = z_score > 1.96
                confidence_level = "95%" if significant else "not_significant"
            else:
                significant = False
                confidence_level = "insufficient_data"
        else:
            significant = False
            confidence_level = "insufficient_sample"

        # Determine winner
        a_pnl = group_a["metrics"]["total_pnl"]
        b_pnl = group_b["metrics"]["total_pnl"]

        if abs(a_pnl - b_pnl) < 0.1:  # Within 0.1 difference
            winner = "tie"
        elif a_pnl > b_pnl:
            winner = "A"
        else:
            winner = "B"

        test_data["results"] = {
            "winner": winner,
            "confidence_level": confidence_level,
            "significant": significant,
            "pnl_difference": round(a_pnl - b_pnl, 2),
            "win_rate_difference": round(a_win_rate - b_win_rate, 3),
            "recommendation": f"Use strategy {test_data['groups'][winner]['strategy']} ({winner})" if winner != "tie" else "No clear winner - strategies perform similarly"
        }

    def _get_test_status(self, ctx: Ctx, test_name: str) -> CapResult:
        """Get status of an A/B test."""
        if not test_name:
            # Return status of all tests
            return CapResult(
                ok=True,
                data={
                    "active_tests": list(self.active_tests.keys()),
                    "completed_tests": list(self.test_results.keys())
                },
                artifacts=()
            )

        if test_name in self.active_tests:
            test_data = self.active_tests[test_name].copy()
            # Remove large trade lists for status response
            for group in test_data["groups"].values():
                group["trades"] = f"{len(group['trades'])} trades"

            return CapResult(
                ok=True,
                data={"test_name": test_name, "status": "running", "test_data": test_data},
                artifacts=()
            )

        elif test_name in self.test_results:
            return CapResult(
                ok=True,
                data={"test_name": test_name, "status": "completed", "results": self.test_results[test_name]["results"]},
                artifacts=()
            )

        else:
            return CapResult(
                ok=False,
                data={"test_name": test_name},
                error=f"Test {test_name} not found",
                artifacts=()
            )

    def _get_test_results(self, ctx: Ctx, test_name: str) -> CapResult:
        """Get results of a completed A/B test."""
        if test_name not in self.test_results:
            return CapResult(
                ok=False,
                data={"test_name": test_name},
                error=f"Test {test_name} not found or not completed",
                artifacts=()
            )

        test_data = self.test_results[test_name]

        # Save results if debug
        artifacts = []
        if ctx.debug:
            results_data = {
                "timestamp": timestamp(),
                "test_name": test_name,
                "results": test_data
            }
            artifacts.append(save_json(ctx, f"ab_test_results_{test_name}_{timestamp()}.json", results_data, "ab_testing"))

        return CapResult(
            ok=True,
            data={
                "test_name": test_name,
                "results": test_data["results"],
                "groups": {
                    group: {
                        "strategy": data["strategy"],
                        "metrics": data["metrics"]
                    } for group, data in test_data["groups"].items()
                },
                "test_duration_minutes": test_data["duration_minutes"],
                "completed_at": test_data["end_time"]
            },
            artifacts=tuple(artifacts)
        )


# Factory for orchestrator
def build() -> Capability:
    return ABTesting()