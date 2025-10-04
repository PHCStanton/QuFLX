from __future__ import annotations

from typing import Any, Dict, Optional, List, Tuple
import os
import sys
import time

# Add project root for direct execution
_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from capabilities.base import (
    Ctx,
    CapResult,
    Capability,
    add_utils_to_syspath,
    take_screenshot_if,
    timestamp,
)

# Ensure utils importable
add_utils_to_syspath()
try:
    from selenium.webdriver.common.by import By
except Exception:
    By = None  # type: ignore

try:
    # HighPriorityControls provides scoped favorites scrolling helpers we can leverage
    from selenium_ui_controls import HighPriorityControls
except Exception:
    HighPriorityControls = None  # type: ignore


class FavoritesBarScroll(Capability):
    """
    Capability: ONLY scroll the favorites bar; no selection, no scanning.
    Inputs:
      - direction: "right" | "left" | "reset_left" | "to_end_right" (default: "right")
      - steps: int (how many page-steps; default 1; ignored by reset_left and to_end_right)
      - delay_ms: int (default 150) settle delay between steps
      - max_steps: int (cap for loops; default 100)
      - step_ratio: float (0.85) used for JS scrollLeft fallback
      - verify: bool (default True) verify progress via scrollLeft delta OR first/last visible label change
      - screenshots_subdir: str (optional) if provided or ctx.debug True, saves pre/post screenshots under screenshots/<subdir>/...

    Output (CapResult.data):
      {
        "direction": "...",
        "steps_requested": N,
        "steps_performed": M,
        "progress": bool,
        "before": {"scrollLeft": x, "first_label": "...", "last_label": "..."},
        "after":  {"scrollLeft": y, "first_label": "...", "last_label": "..."},
        "attempts": [ { step meta... } ]
      }
    """
    id = "favorites_bar_scroll"
    kind = "control"

    def run(self, ctx: Ctx, inputs: Dict[str, Any]) -> CapResult:
        if By is None:
            return CapResult(ok=False, data={}, error="Selenium not available", artifacts=())

        direction = (inputs.get("direction") or "right").strip().lower()
        steps = int(inputs.get("steps", 1))
        delay_ms = int(inputs.get("delay_ms", 150))
        max_steps = int(inputs.get("max_steps", 100))
        step_ratio = float(inputs.get("step_ratio", 0.85))
        verify = bool(inputs.get("verify", True))
        shots_subdir: Optional[str] = inputs.get("screenshots_subdir")

        data: Dict[str, Any] = {
            "direction": direction,
            "steps_requested": steps,
            "steps_performed": 0,
            "progress": False,
            "before": {},
            "after": {},
            "attempts": [],
        }
        artifacts: List[str] = []

        # Optional screenshot (pre)
        if shots_subdir or ctx.debug:
            pre = take_screenshot_if(ctx, f"screenshots/{shots_subdir or 'favorites_scroll'}/favorites_scroll_pre_{timestamp()}.png")
            if pre:
                artifacts.append(pre)

        container = self._find_favorites_container(ctx)
        hpc = HighPriorityControls(ctx.driver) if HighPriorityControls is not None else None
        if not container and hpc is not None:
            try:
                ctx_meta = hpc._favorites_context()
                container = ctx_meta.get("container")
            except Exception:
                container = None

        if container:
            before_state = self._read_state(ctx, container)
        else:
            before_state = self._read_state_global(ctx)
        data["before"] = before_state

        def settle():
            try:
                time.sleep(max(0, delay_ms) / 1000.0)
            except Exception:
                pass

        progressed_any = False
        performed = 0

        # Different modes
        if direction == "reset_left":
            # Prefer helper if available
            if hpc is not None:
                try:
                    _ = hpc.scroll_favorites_reset_left(max_steps=max_steps)
                except Exception:
                    # fallback loop
                    self._loop_scroll(ctx, "left", step_ratio, verify, delay_ms, max_steps, data)
            else:
                self._loop_scroll(ctx, "left", step_ratio, verify, delay_ms, max_steps, data)
            performed = data.get("steps_performed", 0)
            progressed_any = performed > 0

        elif direction == "to_end_right":
            # Loop right until no progress or max_steps reached
            self._loop_scroll(ctx, "right", step_ratio, verify, delay_ms, max_steps, data)
            performed = data.get("steps_performed", 0)
            progressed_any = performed > 0

        elif direction in ("right", "left"):
            # Execute a fixed number of page-steps
            target_steps = max(0, int(steps))
            for i in range(target_steps):
                step_meta: Dict[str, Any] = {"step": i + 1, "dir": direction, "ok": False}
                progressed = False
                # Try helper first
                if hpc is not None:
                    try:
                        if direction == "right":
                            progressed = bool(hpc.scroll_favorites_right_scoped())
                        else:
                            progressed = bool(hpc.scroll_favorites_left_scoped())
                        step_meta["used"] = "hpc"
                    except Exception as e:
                        step_meta["hpc_error"] = str(e)
                        progressed = False

                if not progressed:
                    # Fallback
                    progressed = self._page_once_fallback(ctx, direction, step_ratio, verify, step_meta)

                data["attempts"].append(step_meta)
                settle()

                if progressed:
                    progressed_any = True
                    performed += 1
                else:
                    # stop on stagnation
                    break
        else:
            return CapResult(ok=False, data=data, error=f"Unsupported direction '{direction}'", artifacts=tuple(artifacts))

        data["steps_performed"] = performed

        # Optional screenshot (post)
        if shots_subdir or ctx.debug:
            post = take_screenshot_if(ctx, f"screenshots/{shots_subdir or 'favorites_scroll'}/favorites_scroll_post_{timestamp()}.png")
            if post:
                artifacts.append(post)

        # After state
        container = self._find_favorites_container(ctx) or container
        after_state = self._read_state(ctx, container)
        data["after"] = after_state
        data["progress"] = progressed_any

        return CapResult(ok=True, data=data, error=None, artifacts=tuple(artifacts))

    # ---------- Helpers ----------

    def _find_favorites_container(self, ctx: Ctx) -> Optional[Any]:
        """Ascend from a visible favorites item to find a horizontally scrollable container."""
        try:
            items = ctx.driver.find_elements(By.CSS_SELECTOR, ".assets-favorites-item__line")
        except Exception:
            items = []
        base = None
        for it in items:
            try:
                if it.is_displayed():
                    base = it
                    break
            except Exception:
                continue
        if base is None:
            return None

        current = base
        for _ in range(6):
            try:
                info = ctx.driver.execute_script(
                    "var el=arguments[0];var cs=getComputedStyle(el);"
                    "return {sw:el.scrollWidth||0,cw:el.clientWidth||0,ox:cs.overflowX||'visible'};", current
                )
            except Exception:
                info = None

            try:
                sw = float((info or {}).get("sw") or 0)
                cw = float((info or {}).get("cw") or 0)
                ox = str((info or {}).get("ox") or "")
                if (sw > cw + 5.0) and (ox in ("auto", "scroll")):
                    return current
            except Exception:
                pass

            try:
                current = current.find_element(By.XPATH, "..")
            except Exception:
                break

        return None

    def _first_label(self, ctx: Ctx, container: Any) -> Optional[str]:
        try:
            items = container.find_elements(By.CSS_SELECTOR, ".assets-favorites-item__line")
        except Exception:
            return None
        for it in items:
            try:
                if it.is_displayed():
                    lbl = it.find_element(By.CSS_SELECTOR, ".assets-favorites-item__label")
                    return (lbl.text or "").strip()
            except Exception:
                continue
        return None

    def _last_label(self, ctx: Ctx, container: Any) -> Optional[str]:
        try:
            items = container.find_elements(By.CSS_SELECTOR, ".assets-favorites-item__line")
        except Exception:
            return None
        last = None
        for it in items:
            try:
                if it.is_displayed():
                    last = it
            except Exception:
                continue
        if last is None:
            return None
        try:
            lbl = last.find_element(By.CSS_SELECTOR, ".assets-favorites-item__label")
            return (lbl.text or "").strip()
        except Exception:
            return None

    def _read_state(self, ctx: Ctx, container: Any) -> Dict[str, Any]:
        try:
            sl = ctx.driver.execute_script("return arguments[0].scrollLeft||0;", container)
        except Exception:
            sl = None
        return {
            "scrollLeft": sl,
            "first_label": self._first_label(ctx, container),
            "last_label": self._last_label(ctx, container),
        }

    def _read_state_global(self, ctx: Ctx) -> Dict[str, Any]:
        """
        Read first/last visible favorites labels from the whole document when a specific container cannot be resolved.
        scrollLeft is unavailable globally, so we return None for it.
        """
        try:
            nodes = ctx.driver.find_elements(By.CSS_SELECTOR, ".assets-favorites-item__line")
        except Exception:
            nodes = []
        first_label = None
        last_label = None
        for n in nodes:
            try:
                if n.is_displayed():
                    lbl = n.find_element(By.CSS_SELECTOR, ".assets-favorites-item__label")
                    text = (lbl.text or "").strip()
                    if first_label is None:
                        first_label = text
                    last_label = text
            except Exception:
                continue
        return {
            "scrollLeft": None,
            "first_label": first_label,
            "last_label": last_label,
        }

    def _find_arrow_near(self, ctx: Ctx, container: Any, direction: str) -> Optional[Any]:
        # Prefer semantic selectors; include icons like i.fa.fa-chevron-right/left
        if direction == "right":
            sels = [
                ".assets-favorites__arrow--right",
                ".favorites-nav__right",
                ".favorites-arrow-right",
                "button[aria-label*='right']",
                ".chevron-right",
                "i.fa.fa-chevron-right",
                "i.fa.fa-angle-right",
                "[class*='arrow'][class*='right']",
            ]
        else:
            sels = [
                ".assets-favorites__arrow--left",
                ".favorites-nav__left",
                ".favorites-arrow-left",
                "button[aria-label*='left']",
                ".chevron-left",
                "i.fa.fa-chevron-left",
                "i.fa.fa-angle-left",
                "[class*='arrow'][class*='left']",
            ]

        # If container is None, start with global search for the arrow immediately
        if container is None:
            for sel in sels:
                try:
                    nodes = ctx.driver.find_elements(By.CSS_SELECTOR, sel)
                except Exception:
                    nodes = []
                for n in nodes:
                    try:
                        if not (n.is_displayed() and n.is_enabled()):
                            continue
                        if (n.tag_name or "").lower() == "i":
                            try:
                                cao = n.find_element(By.XPATH, "ancestor::*[self::button or self::a or @role='button'][1]")
                                if cao and cao.is_displayed() and cao.is_enabled():
                                    return cao
                            except Exception:
                                pass
                        return n
                    except Exception:
                        continue
        else:
            # Search inside container
            for sel in sels:
                try:
                    nodes = container.find_elements(By.CSS_SELECTOR, sel)
                except Exception:
                    nodes = []
                for n in nodes:
                    try:
                        if not (n.is_displayed() and n.is_enabled()):
                            continue
                        if (n.tag_name or "").lower() == "i":
                            # prefer clickable ancestor
                            try:
                                anc = n.find_element(By.XPATH, "ancestor::*[self::button or self::a or @role='button'][1]")
                                if anc and anc.is_displayed() and anc.is_enabled():
                                    return anc
                            except Exception:
                                pass
                        return n
                    except Exception:
                        continue

        # Ancestors
        anc = container
        for _ in range(6):
            try:
                anc = anc.find_element(By.XPATH, "..")
            except Exception:
                anc = None
            if anc is None:
                break
            for sel in sels:
                try:
                    nodes = anc.find_elements(By.CSS_SELECTOR, sel)
                except Exception:
                    nodes = []
                for n in nodes:
                    try:
                        if not (n.is_displayed() and n.is_enabled()):
                            continue
                        if (n.tag_name or "").lower() == "i":
                            try:
                                cao = n.find_element(By.XPATH, "ancestor::*[self::button or self::a or @role='button'][1]")
                                if cao and cao.is_displayed() and cao.is_enabled():
                                    return cao
                            except Exception:
                                pass
                        return n
                    except Exception:
                        continue

        # Global fallback
        for sel in sels:
            try:
                nodes = ctx.driver.find_elements(By.CSS_SELECTOR, sel)
            except Exception:
                nodes = []
            for n in nodes:
                try:
                    if not (n.is_displayed() and n.is_enabled()):
                        continue
                    if (n.tag_name or "").lower() == "i":
                        try:
                            cao = n.find_element(By.XPATH, "ancestor::*[self::button or self::a or @role='button'][1]")
                            if cao and cao.is_displayed() and cao.is_enabled():
                                return cao
                        except Exception:
                            pass
                    return n
                except Exception:
                    continue

        return None

    def _verify_progress(self, before: Dict[str, Any], after: Dict[str, Any]) -> bool:
        try:
            sl_b = float(before.get("scrollLeft") or 0)
            sl_a = float(after.get("scrollLeft") or 0)
        except Exception:
            sl_b = before.get("scrollLeft")
            sl_a = after.get("scrollLeft")
        if (sl_b is not None) and (sl_a is not None) and (sl_a != sl_b):
            return True
        if before.get("first_label") != after.get("first_label"):
            return True
        if before.get("last_label") != after.get("last_label"):
            return True
        return False

    def _page_once_fallback(self, ctx: Ctx, direction: str, step_ratio: float, verify: bool, step_meta: Dict[str, Any]) -> bool:
        """Attempt one page step using arrow near container or JS scrollLeft fallback."""
        container = self._find_favorites_container(ctx)
        if not container and HighPriorityControls is not None:
            try:
                hpc_tmp = HighPriorityControls(ctx.driver)
                ctx_meta = hpc_tmp._favorites_context()
                container = ctx_meta.get("container")
            except Exception:
                container = None

        before = (self._read_state(ctx, container) if container else self._read_state_global(ctx))
        step_meta["before"] = before

        progressed = False
        arrow = self._find_arrow_near(ctx, container, direction)
        if arrow is not None:
            try:
                ctx.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", arrow)
            except Exception:
                pass
            try:
                arrow.click()
                progressed = True
                step_meta["method"] = "arrow_click"
            except Exception:
                try:
                    ctx.driver.execute_script("arguments[0].click();", arrow)
                    progressed = True
                    step_meta["method"] = "arrow_js_click"
                except Exception as e:
                    step_meta["arrow_click_error"] = str(e)

        if not progressed and container is not None:
            # JS scrollLeft fallback
            try:
                info = ctx.driver.execute_script("return {cw: arguments[0].clientWidth||0};", container) or {"cw": 0}
                delta = max(50, int(float(info.get("cw") or 0) * float(step_ratio or 0.85)))
                if direction == "left":
                    delta = -delta
                ctx.driver.execute_script("arguments[0].scrollLeft = (arguments[0].scrollLeft||0) + arguments[1];", container, delta)
                progressed = True
                step_meta["method"] = "js_scrollLeft"
                step_meta["delta"] = delta
            except Exception as e:
                step_meta["js_scroll_error"] = str(e)
                progressed = False

        # settle and verify
        try:
            time.sleep(0.15)
        except Exception:
            pass

        after = (self._read_state(ctx, container) if container else self._read_state_global(ctx))
        step_meta["after"] = after

        return (self._verify_progress(before, after) if verify else progressed)

    def _loop_scroll(self, ctx: Ctx, direction: str, step_ratio: float, verify: bool, delay_ms: int, max_steps: int, data: Dict[str, Any]):
        """Repeatedly page in a direction until stagnation or max_steps."""
        performed = data.get("steps_performed", 0)
        for i in range(max_steps):
            step_meta: Dict[str, Any] = {"step": performed + 1, "dir": direction, "ok": False, "loop": True}
            progressed = self._page_once_fallback(ctx, direction, step_ratio, verify, step_meta)
            data["attempts"].append(step_meta)
            try:
                time.sleep(max(0, delay_ms) / 1000.0)
            except Exception:
                pass
            if progressed:
                performed += 1
            else:
                break
        data["steps_performed"] = performed


# Factory for orchestrator
def build() -> Capability:
    return FavoritesBarScroll()


if __name__ == "__main__":
    import argparse
    import json as _json
    from pathlib import Path

    # Try to attach using qf if available (shares global ctx/driver)
    ctx = None
    driver = None
    try:
        import qf  # type: ignore
        ok, _res = qf.attach_chrome_session(port=9222, verbose=True)
        if ok:
            ctx = qf.ctx
            driver = qf.driver
    except Exception:
        pass

    # Fallback direct attach
    if ctx is None:
        try:
            from selenium import webdriver  # type: ignore
            from selenium.webdriver.chrome.options import Options  # type: ignore
            opts = Options()
            opts.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            opts.set_capability("goog:loggingPrefs", {"performance": "ALL"})
            driver = webdriver.Chrome(options=opts)
            artifacts_root = str(Path(__file__).resolve().parents[1] / "Historical_Data" / "cli_artifacts")
            ctx = Ctx(driver=driver, artifacts_root=artifacts_root, debug=False, dry_run=False, verbose=True)
            print("✅ Attached to Chrome session:", getattr(driver, "current_url", "unknown"))
        except Exception as e:
            print(f"❌ Failed to attach to Chrome session: {e}")
            raise SystemExit(1)

    parser = argparse.ArgumentParser(description="ONLY scroll the favorites bar; no selection.")
    parser.add_argument("--direction", choices=["right", "left", "reset_left", "to_end_right"], default="right")
    parser.add_argument("--steps", type=int, default=1, help="Page steps (ignored for reset_left / to_end_right)")
    parser.add_argument("--delay-ms", type=int, default=150)
    parser.add_argument("--max-steps", type=int, default=100)
    parser.add_argument("--step-ratio", type=float, default=0.85, help="JS scrollLeft step = clientWidth * ratio")
    parser.add_argument("--no-verify", action="store_true", help="Disable verification of progress")
    parser.add_argument("--shots-subdir", default=None, help="Subdir under screenshots/ for pre/post shots")
    args = parser.parse_args()

    cap = FavoritesBarScroll()
    inputs = {
        "direction": args.direction,
        "steps": int(args.steps),
        "delay_ms": int(args.delay_ms),
        "max_steps": int(args.max_steps),
        "step_ratio": float(args.step_ratio),
        "verify": (not bool(args.no_verify)),
        "screenshots_subdir": (args.shots_subdir or None),
    }

    res = cap.run(ctx, inputs)
    out = {
        "ok": res.ok,
        "error": res.error,
        "data": res.data,
        "artifacts": list(res.artifacts) if getattr(res, "artifacts", None) else [],
    }
    print(_json.dumps(out, ensure_ascii=False, indent=2))
