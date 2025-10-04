"""Screenshot control capability for manual testing.

Migrated from API-test-space for production use.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, List, Tuple
import os
import time

from .base import Ctx, CapResult, Capability, join_artifact, ensure_dir, timestamp


LETTER_TO_LABEL = {
    # a..h mapping
    "a": "D1",
    "b": "H4",
    "c": "H1",
    "d": "M15",
    "e": "M5",
    "f": "M3",
    "g": "M1",
    "h": "S30",
}


class ScreenshotControl(Capability):
    """
    Capability: Manual screenshot capture controlled from the console.
    - While running, pressing 's' (or 'S') in the PowerShell console will save a screenshot.
    - Press 'q' (or 'Q') to quit early.

    Inputs:
      - mode: str = "manual"   (reserved for future modes)
      - count: int (1..8)      (number of screenshots to capture; if letters/labels shorter, we stop when exhausted)
      - letters: Optional[str] e.g. "cdgh" maps to ["H1","M15","M1","S30"]
      - labels: Optional[List[str]] e.g. ["H1","M15","M5","M1"]
      - subdir: Optional[str] = "screenshot_control" (folder under screenshots/)
      - hotkey: Optional[str] = "s" (future use; currently 's' and 'q' are hardcoded)
    Artifacts:
      - tests/test_results/screenshots/screenshot_control/manual_{LABEL}_{YYYYMMDD_%H%M%S}.png

    Kind: "control-read"
    """
    id = "screenshot_control"
    kind = "control-read"

    def run(self, ctx: Ctx, inputs: Dict[str, Any]) -> CapResult:
        mode = (inputs.get("mode") or "manual").strip().lower()
        if mode != "manual":
            return CapResult(ok=False, data={"mode": mode}, error="Only 'manual' mode is supported right now.", artifacts=())

        # Resolve labels to name screenshots
        count = max(1, min(int(inputs.get("count", 4)), 8))  # clamp to 1..8
        letters = inputs.get("letters", "").strip().lower()
        labels = inputs.get("labels", [])
        subdir = inputs.get("subdir", "screenshot_control").strip()

        planned_labels: List[str] = []
        if labels:
            planned_labels = list(labels)[:count]
        elif letters:
            for ch in letters[:count]:
                if ch in LETTER_TO_LABEL:
                    planned_labels.append(LETTER_TO_LABEL[ch])
        else:
            # Default fallback
            planned_labels = ["H1", "M15", "M5", "M1"][:count]

        total = len(planned_labels)
        if total == 0:
            return CapResult(ok=False, data={"count": count}, error="No valid labels resolved.", artifacts=())

        # Create screenshots directory under test results
        shots_dir_abs = join_artifact(ctx, "screenshots", subdir)
        ensure_dir(shots_dir_abs)

        data = {
            "mode": mode,
            "count": count,
            "total": total,
            "planned_labels": planned_labels,
            "captures": [],
            "subdir": subdir,
        }
        artifacts: List[str] = []

        # Guidance
        if ctx.verbose:
            print(f"[screenshot_control] Manual screenshots enabled. Planned count={total}, labels={planned_labels}")
            print("[screenshot_control] Press 's' to capture, 'q' to quit early. Focus the PowerShell/terminal window.")

        # Use Windows console key reading (no external dependencies)
        try:
            import msvcrt  # Windows-only
        except Exception:
            err = "msvcrt not available on this platform; manual mode requires Windows console."
            if ctx.verbose:
                print(f"[screenshot_control] {err}")
            return CapResult(ok=False, data=data, error=err, artifacts=tuple(artifacts))

        captured = 0
        # simple debounce time to avoid double-captures
        last_press_ts = 0.0

        while captured < total:
            try:
                if msvcrt.kbhit():
                    ch = msvcrt.getch()
                    # Convert to lowercase where possible
                    try:
                        key = ch.decode("utf-8", errors="ignore").lower()
                    except Exception:
                        key = ""
                    now = time.time()
                    # Debounce 100ms
                    if now - last_press_ts < 0.10:
                        time.sleep(0.02)
                        continue
                    last_press_ts = now

                    if key == "q":
                        if ctx.verbose:
                            print("[screenshot_control] Quit signal received ('q'). Exiting early.")
                        break

                    if key == "s":
                        # current label
                        label = planned_labels[captured]
                        ts = timestamp()
                        fname = f"manual_{label}_{ts}.png"
                        abs_path = os.path.join(shots_dir_abs, fname)
                        # Ensure dir exists (nested)
                        ensure_dir(os.path.dirname(abs_path))
                        ok = False
                        try:
                            ok = bool(ctx.driver.save_screenshot(abs_path))
                        except Exception as se:
                            if ctx.verbose:
                                print(f"[screenshot_control] Save failed: {se}")

                        if ok:
                            artifacts.append(abs_path)
                            data["captures"].append({"index": captured + 1, "label": label, "path": abs_path})
                            captured += 1
                            if ctx.verbose:
                                print(f"[screenshot_control] [{captured}/{total}] Saved {label} -> {abs_path}")
                        else:
                            if ctx.verbose:
                                print(f"[screenshot_control] Failed to save screenshot for label {label}")

                time.sleep(0.05)  # keep loop responsive but not CPU heavy
            except KeyboardInterrupt:
                # Respect Ctrl+C
                if ctx.verbose:
                    print("[screenshot_control] KeyboardInterrupt received. Exiting.")
                break
            except Exception as e:
                # Keep running; log and continue
                if ctx.verbose:
                    print(f"[screenshot_control] Listener error: {e}")
                time.sleep(0.15)

        ok = captured > 0
        return CapResult(ok=ok, data=data, error=None if ok else "No screenshots captured", artifacts=tuple(artifacts))


# Factory for orchestrator
def build() -> Capability:
    return ScreenshotControl()