# original_topdown_select
from __future__ import annotations

from typing import Any, Dict, Optional, List, Tuple
import os
import sys
import time

# Handle imports for both package usage and direct execution
try:
    from .base import Ctx, CapResult, Capability, add_utils_to_syspath, join_artifact, ensure_dir, timestamp
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    this_file = Path(__file__).resolve()
    api_root = this_file.parents[1]  # .../QuFLX
    if str(api_root) not in sys.path:
        sys.path.insert(0, str(api_root))

    # Import from utils
    try:
        from utils.base import Ctx, CapResult, Capability, add_utils_to_syspath, join_artifact, ensure_dir, timestamp
    except ImportError:
        # Create minimal fallback classes/functions
        class Ctx:
            def __init__(self, driver, artifacts_root="", debug=False, dry_run=False, verbose=False):
                self.driver = driver
                self.artifacts_root = artifacts_root
                self.debug = debug
                self.dry_run = dry_run
                self.verbose = verbose

        class CapResult:
            def __init__(self, ok=False, data=None, error=None, artifacts=None):
                self.ok = ok
                self.data = data or {}
                self.error = error
                self.artifacts = artifacts or ()

        class Capability:
            pass

        def add_utils_to_syspath():
            pass

        def join_artifact(ctx, path):
            return os.path.join(ctx.artifacts_root, path)

        def ensure_dir(path):
            os.makedirs(path, exist_ok=True)

        def timestamp():
            from datetime import datetime
            return datetime.now().strftime("%Y%m%d_%H%M%S")

# Ensure we can import selenium and local utils
add_utils_to_syspath()
try:
    from selenium.webdriver.common.by import By
except Exception:
    By = None  # type: ignore

try:
    from utils.selenium_ui_controls import HighPriorityControls
except Exception:
    try:
        # Try absolute import when run as standalone script
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from utils.selenium_ui_controls import HighPriorityControls
    except Exception:
        HighPriorityControls = None  # type: ignore


class TopdownSelect(Capability):
    """
    Capability: Visit timeframe stack for analysis and take screenshots for AI.
    Interface:
      run(ctx, {
        "stack": "1m"|"5m",
        "labels": Optional[List[str]],              # override order e.g. ["H1","M15","M5","M1"]
        "delay_ms": int=300,
        "save": bool=True,
        "screenshots_subdir": str="topdown_analysis",
        "reopen_each": bool=True,                  # reopen the dropdown before each selection
        "menu_toggle_selectors": Optional[List[str]],  # CSS selectors to open timeframe dropdown/menu
        "iframe_css": Optional[str],               # if timeframe controls live in an iframe, provide CSS
        "iframe_index": Optional[int],             # or provide an index
      })
    Behavior:
      - Default stacks:
          For 1m: H1 → M15 → M5 → M1
          For 5m: H4 → H1 → M15 → M5
      - Explicitly opens the timeframe dropdown (if present), then clicks anchors for each label.
      - Robust anchor strategies:
          * By.LINK_TEXT / PARTIAL_LINK_TEXT for "A" tags
          * CSS: a[data-value='M1'], a[data-period='M1'], a[aria-label='M1'], a[title='M1']
          * Fallback text/XPath and known containers
      - If selector not found, skip with warning in data.attempts
      - If ctx.debug or save=True: write screenshots to screenshots/topdown_analysis/<label>.png
    Kind: "control-read"
    """
    id = "topdown_select"
    kind = "control-read"

    def run(self, ctx: Ctx, inputs: Dict[str, Any]) -> CapResult:
        if By is None:
            return CapResult(ok=False, data={}, error="Selenium not available", artifacts=())

        stack = (inputs.get("stack") or "1m").strip().lower()
        labels_override = inputs.get("labels")
        delay_ms = int(inputs.get("delay_ms", 300))
        save = bool(inputs.get("save", True))
        subdir = inputs.get("screenshots_subdir", "topdown_analysis") or "topdown_analysis"
        reopen_each = bool(inputs.get("reopen_each", True))
        menu_toggle_selectors: Optional[List[str]] = inputs.get("menu_toggle_selectors")
        iframe_css: Optional[str] = inputs.get("iframe_css")
        iframe_index: Optional[int] = inputs.get("iframe_index")

        sequences = {
            "1m": ["H1", "M15", "M5", "M1"],
            "5m": ["H4", "H1", "M15", "M5"],
        }
        labels = labels_override or sequences.get(stack)
        if not labels:
            return CapResult(ok=False, data={"stack": stack}, error="Unsupported stack. Use '1m' or '5m' or provide 'labels'", artifacts=())

        data: Dict[str, Any] = {
            "stack": stack,
            "labels": labels,
            "delay_ms": delay_ms,
            "save": save,
            "screenshots_subdir": subdir,
            "attempts": [],
            "screenshots": {},
        }
        artifacts: List[str] = []

        # Try to switch iframe if requested
        try:
            data["frame_switch"] = self._maybe_switch_iframe(ctx, iframe_css, iframe_index)
        except Exception as e:
            data["frame_switch_error"] = str(e)

        # Best-effort ensure right panel expanded (chart/timeframe area visible often tied to layout)
        try:
            if HighPriorityControls is not None:
                hpc = HighPriorityControls(ctx.driver)
                data["right_panel_meta"] = hpc.ensure_right_panel_expanded_with_meta(min_width=200)
        except Exception as e:
            data["right_panel_meta_error"] = str(e)

        # Prepare screenshot directory if saving - use project root for screenshots
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        shots_dir_abs = os.path.join(project_root, "screenshots", subdir)
        try:
            ensure_dir(shots_dir_abs)
        except Exception:
            pass

        # Pre-open menu one time if not reopening each time
        pre_open_meta = None
        if not reopen_each:
            pre_open_meta = self._open_timeframe_menu(ctx, menu_toggle_selectors)
            data["menu_open_initial"] = pre_open_meta

        # Visit each timeframe and optionally capture a screenshot
        for label in labels:
            att_rec: Dict[str, Any] = {"label": label, "ok": False, "strategy_used": None, "selector": None, "error": None}
            try:
                # Open timeframe dropdown and track the opening button
                menu_open_result = self._open_timeframe_menu(ctx, menu_toggle_selectors)
                att_rec["menu_open_attempt"] = menu_open_result
                opening_button = menu_open_result.get("opening_button")

                clicked, used, sel = self._click_timeframe(ctx, label)
                att_rec["ok"] = bool(clicked)
                att_rec["strategy_used"] = used
                att_rec["selector"] = sel

                # Toggle close dropdown by clicking the same button that opened it
                if clicked and opening_button:
                    try:
                        self._toggle_close_dropdown(ctx, opening_button)
                        att_rec["toggle_close_attempted"] = True
                        att_rec["toggle_close_success"] = True
                    except Exception as te:
                        att_rec["toggle_close_attempted"] = True
                        att_rec["toggle_close_error"] = str(te)
                        att_rec["toggle_close_success"] = False
                else:
                    att_rec["toggle_close_attempted"] = False
                    att_rec["toggle_close_success"] = False

                # Allow UI to settle after toggle close
                self._sleep_ms(delay_ms)

                # Screenshot policy
                if save or ctx.debug:
                    shot_name = f"{label}.png"
                    shot_path = os.path.join(shots_dir_abs, shot_name)
                    try:
                        ctx.driver.save_screenshot(shot_path)
                        data["screenshots"][label] = shot_path
                        artifacts.append(shot_path)
                    except Exception as se:
                        att_rec["screenshot_error"] = str(se)
            except Exception as e:
                att_rec["error"] = str(e)

            data["attempts"].append(att_rec)

        ok = any(a.get("ok") for a in data["attempts"])
        return CapResult(ok=ok, data=data, error=None if ok else "No timeframe buttons could be activated", artifacts=tuple(artifacts))

    # ---------- helpers ----------

    def _sleep_ms(self, ms: int):
        try:
            time.sleep(max(0, ms) / 1000.0)
        except Exception:
            pass

    def _maybe_switch_iframe(self, ctx: Ctx, iframe_css: Optional[str], iframe_index: Optional[int]) -> Dict[str, Any]:
        """
        Switch into iframe if css or index is provided. Returns meta info about the switch.
        """
        meta: Dict[str, Any] = {"switched": False}
        drv = ctx.driver
        try:
            # Always reset to default first
            drv.switch_to.default_content()
            meta["reset_to_default"] = True
        except Exception as e:
            meta["reset_error"] = str(e)

        if iframe_css:
            try:
                frames = drv.find_elements(By.CSS_SELECTOR, iframe_css)
            except Exception as e:
                meta["find_iframe_error"] = f"css:{iframe_css} -> {e}"
                return meta
            if frames:
                try:
                    drv.switch_to.frame(frames[0])
                    meta["switched"] = True
                    meta["method"] = "css"
                    meta["selector"] = iframe_css
                except Exception as e:
                    meta["switch_error"] = str(e)
            else:
                meta["iframe_not_found"] = iframe_css
        elif iframe_index is not None:
            try:
                drv.switch_to.frame(int(iframe_index))
                meta["switched"] = True
                meta["method"] = "index"
                meta["index"] = int(iframe_index)
            except Exception as e:
                meta["switch_error"] = str(e)
        return meta

    def _open_timeframe_menu(self, ctx: Ctx, selectors: Optional[List[str]]) -> Dict[str, Any]:
        """
        Attempts to open the timeframe dropdown/menu using enhanced detection from HighPriorityControls.
        Returns meta info with success flag, selector used, and the opening button element for toggle closing.
        """
        if HighPriorityControls is None:
            return {"opened": False, "used": None, "opening_button": None, "error": "HighPriorityControls not available"}

        try:
            hpc = HighPriorityControls(ctx.driver)
            click_meta = hpc.click_chart_timeframe_dropdown_with_meta()

            return {
                "opened": click_meta.get("ok", False),
                "used": click_meta.get("selector_used"),
                "opening_button": click_meta.get("button_element"),
                "dropdown_opened": click_meta.get("dropdown_opened", False),
                "click_method": click_meta.get("click_method"),
                "enhanced_detection": True
            }

        except Exception as e:
            return {
                "opened": False,
                "used": None,
                "opening_button": None,
                "error": f"Enhanced detection failed: {str(e)}",
                "fallback_available": True
            }

    def _label_variants(self, label: str) -> List[str]:
        """
        Build common textual variants e.g. 'M1' -> '1m', 'H1' -> '1h', also lowercase variants.
        """
        L = [label, label.upper(), label.lower()]
        try:
            if label.upper().startswith("M"):
                n = label[1:]
                if n.isdigit():
                    L += [f"{n}m", f"{n}M"]
            if label.upper().startswith("H"):
                n = label[1:]
                if n.isdigit():
                    L += [f"{n}h", f"{n}H"]
        except Exception:
            pass
        # Deduplicate preserving order
        seen = set()
        out: List[str] = []
        for t in L:
            if t not in seen:
                seen.add(t)
                out.append(t)
        return out

    def _click_timeframe(self, ctx: Ctx, label: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Try layered selectors focused on anchors (<a>) and then fallbacks.
        Return (clicked, strategy, selector_detail)
        """
        driver = ctx.driver
        labels_to_try = self._label_variants(label)

        # 0) Anchor-focused strategies
        # Link text and partial link text (only for <a>)
        for lab in labels_to_try:
            try:
                el = driver.find_element(By.LINK_TEXT, lab)
                if el and el.is_displayed():
                    self._scroll_into_view(ctx, el)
                    if self._click(el, driver):
                        return True, "link_text", lab
            except Exception:
                pass
            try:
                el = driver.find_element(By.PARTIAL_LINK_TEXT, lab)
                if el and el.is_displayed():
                    self._scroll_into_view(ctx, el)
                    if self._click(el, driver):
                        return True, "partial_link_text", lab
            except Exception:
                pass

        # 1) Anchor attributes
        for lab in labels_to_try:
            for css in [
                f"a[data-value='{lab}']",
                f"a[data-period='{lab}']",
                f"a[aria-label='{lab}']",
                f"a[title='{lab}']",
                f"a[href*='{lab}']",
            ]:
                try:
                    el = self._first_visible(driver, "css", css)
                    if el:
                        self._scroll_into_view(ctx, el)
                        if self._click(el, driver):
                            return True, "css", css
                except Exception:
                    continue

        # 2) Strict text match anywhere
        strategies: List[Tuple[str, str]] = []
        for lab in labels_to_try:
            strategies.extend([
                ("xpath", f"//*[normalize-space(text())='{lab}']"),
                ("xpath", f"//a[normalize-space(text())='{lab}']"),
                ("xpath", f"//*[contains(@aria-label,'{lab}') or contains(@title,'{lab}')]"),
            ])

        # 3) Generic candidates containing label (case-insensitive)
        for lab in labels_to_try:
            lower = lab.lower()
            strategies.append(
                ("xpath", f"//*[self::a or self::button or self::div][contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'{lower}')]")
            )

        # 4) Common classes seen on timeframe strips (best-effort)
        strategies.append(("css", ".timeframes, .timeframe, .chart-controls, .chart__timeframes"))

        for strat, sel in strategies:
            try:
                if strat == "css":
                    containers = driver.find_elements(By.CSS_SELECTOR, sel)
                    for cont in containers:
                        node = self._find_visible_by_xpath(
                            cont,
                            f".//*[self::a or self::button or self::div][normalize-space(text())='{label}']"
                        )
                        if not node:
                            # try variants
                            for lab in labels_to_try:
                                node = self._find_visible_by_xpath(
                                    cont,
                                    f".//*[self::a or self::button or self::div][normalize-space(text())='{lab}']"
                                )
                                if node:
                                    break
                        if not node:
                            # text-contains fallback
                            for lab in labels_to_try:
                                lower = lab.lower()
                                node = self._find_visible_by_xpath(
                                    cont,
                                    f".//*[self::a or self::button or self::div][contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'{lower}')]"
                                )
                                if node:
                                    break
                        if node:
                            self._scroll_into_view(ctx, node)
                            if self._click(node, driver):
                                return True, strat, f"{sel} -> inner:{label}"
                else:
                    node = self._first_visible(driver, strat, sel)
                    if node:
                        # Refine within subtree for a labeled child if possible
                        exact_child = self._find_visible_by_xpath(
                            node,
                            f".//*[self::a or self::button or self::div][normalize-space(text())='{label}']"
                        )
                        if not exact_child:
                            for lab in labels_to_try:
                                exact_child = self._find_visible_by_xpath(
                                    node,
                                    f".//*[self::a or self::button or self::div][normalize-space(text())='{lab}']"
                                )
                                if exact_child:
                                    break
                        target = exact_child or node
                        self._scroll_into_view(ctx, target)
                        if self._click(target, driver):
                            return True, strat, sel
            except Exception:
                continue

        # 5) Last resort: elementFromPoint probe near top chart area
        try:
            w_h = driver.execute_script("return [window.innerWidth||0, window.innerHeight||0];")
            if isinstance(w_h, list) and len(w_h) == 2:
                width, height = float(w_h[0] or 0), float(w_h[1] or 0)
                probe_points = [
                    (width * 0.20, height * 0.15),
                    (width * 0.30, height * 0.15),
                    (width * 0.40, height * 0.15),
                    (width * 0.50, height * 0.15),
                ]
                for x, y in probe_points:
                    el = driver.execute_script("return document.elementFromPoint(arguments[0], arguments[1]);", x, y)
                    if el:
                        try:
                            txt = (el.text or "").strip()
                        except Exception:
                            txt = ""
                        if txt:
                            for lab in labels_to_try:
                                if lab.lower() in txt.lower():
                                    self._scroll_into_view(ctx, el)
                                    if self._click(el, driver):
                                        return True, "elementFromPoint", f"{x:.0f},{y:.0f}"
        except Exception:
            pass

        return False, None, None

    def _first_visible(self, driver, strat: str, sel: str):
        try:
            if strat == "xpath":
                els = driver.find_elements(By.XPATH, sel)
            else:
                els = driver.find_elements(By.CSS_SELECTOR, sel)
        except Exception:
            return None
        for e in els:
            try:
                if e.is_displayed():
                    return e
            except Exception:
                continue
        return None

    def _find_visible_by_xpath(self, container, xp: str):
        try:
            els = container.find_elements(By.XPATH, xp)
        except Exception:
            return None
        for e in els:
            try:
                if e.is_displayed():
                    return e
            except Exception:
                continue
        return None

    def _scroll_into_view(self, ctx: Ctx, el: Any):
        try:
            ctx.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        except Exception:
            pass

    def _click(self, el, driver) -> bool:
        # Try native click then JS fallback
        try:
            el.click()
            return True
        except Exception:
            try:
                driver.execute_script("arguments[0].click();", el)
                return True
            except Exception:
                return False

    def _toggle_close_dropdown(self, ctx: Ctx, opening_button):
        """
        Close the dropdown using robust strategies with verification and pointer de-hover.
        Returns True only if the dropdown is confirmed closed.
        """
        try:
            driver = ctx.driver

            def dropdown_open() -> bool:
                try:
                    return bool(driver.execute_script("""
                        const nodes = Array.from(document.querySelectorAll(
                            '.dropdown.open, .dropdown.show, .menu.open, .menu.show, [role="menu"], [role="listbox"]'
                        ));
                        for (const el of nodes) {
                            const cs = getComputedStyle(el);
                            const r = el.getBoundingClientRect();
                            if (r.width > 5 && r.height > 5 && cs.visibility !== 'hidden' && cs.display !== 'none') return true;
                        }
                        return false;
                    """))
                except Exception:
                    # If detection fails, be conservative and assume still open
                    return True

            def move_pointer_to_chart_center():
                try:
                    driver.execute_script("""
                        const cx = Math.floor(window.innerWidth/2);
                        const cy = Math.floor(window.innerHeight/2);
                        const el = document.elementFromPoint(cx, cy);
                        if (el) {
                          el.dispatchEvent(new MouseEvent('mousemove', {bubbles:true,cancelable:true}));
                        }
                        return true;
                    """)
                except Exception:
                    pass

            # Strategy 1: ActionChains click at multiple offsets on the toggle button
            if opening_button and opening_button.is_displayed():
                try:
                    rect = driver.execute_script(
                        "const r = arguments[0].getBoundingClientRect(); return {w:r.width,h:r.height};",
                        opening_button
                    ) or {"w": 10, "h": 10}
                    offsets = [
                        (max(2.0, rect["w"] * 0.30), max(2.0, rect["h"] * 0.50)),
                        (max(2.0, rect["w"] * 0.70), max(2.0, rect["h"] * 0.50)),
                        (max(2.0, rect["w"] * 0.50), max(2.0, rect["h"] * 0.50)),
                    ]
                    from selenium.webdriver.common.action_chains import ActionChains
                    for ox, oy in offsets:
                        try:
                            ActionChains(driver).move_to_element_with_offset(opening_button, int(ox), int(oy)).click().perform()
                            move_pointer_to_chart_center()
                            time.sleep(0.1)
                            if not dropdown_open():
                                if ctx.verbose:
                                    print(f"✅ [TOPDOWN] Dropdown closed via Actions offset ({int(ox)},{int(oy)})")
                                return True
                        except Exception as e:
                            if ctx.verbose:
                                print(f"⚠️ [TOPDOWN] Actions offset close failed: {e}")
                except Exception as e:
                    if ctx.verbose:
                        print(f"⚠️ [TOPDOWN] Actions prep failed: {e}")

            # Strategy 2: JS event dispatching
            if opening_button:
                try:
                    driver.execute_script("""
                        const el = arguments[0];
                        const fire = (type) => {
                          let evt;
                          try { evt = new PointerEvent(type, {bubbles:true,cancelable:true,composed:true}); }
                          catch(e) { evt = new MouseEvent(type, {bubbles:true,cancelable:true,composed:true}); }
                          el.dispatchEvent(evt);
                        };
                        ['pointerdown','mousedown','mouseup','click'].forEach(fire);
                    """, opening_button)
                    move_pointer_to_chart_center()
                    time.sleep(0.1)
                    if not dropdown_open():
                        if ctx.verbose:
                            print("✅ [TOPDOWN] Dropdown closed via JS dispatch")
                        return True
                except Exception as e:
                    if ctx.verbose:
                        print(f"⚠️ [TOPDOWN] JS dispatch close failed: {e}")

            # Strategy 3: JS click
            if opening_button:
                try:
                    driver.execute_script("arguments[0].click();", opening_button)
                    move_pointer_to_chart_center()
                    time.sleep(0.1)
                    if not dropdown_open():
                        if ctx.verbose:
                            print("✅ [TOPDOWN] Dropdown closed via JS click")
                        return True
                except Exception as e:
                    if ctx.verbose:
                        print(f"⚠️ [TOPDOWN] JS click close failed: {e}")

            # Strategy 4: Blind click in center (outside menu)
            try:
                closed = driver.execute_script("""
                    const centerX = Math.floor(window.innerWidth / 2);
                    const centerY = Math.floor(window.innerHeight / 2);
                    const element = document.elementFromPoint(centerX, centerY);
                    if (element && !element.closest('[role="menu"], [role="listbox"], .dropdown, .menu')) {
                        element.click();
                        return true;
                    }
                    return false;
                """)
                move_pointer_to_chart_center()
                time.sleep(0.1)
                if closed and not dropdown_open():
                    if ctx.verbose:
                        print("✅ [TOPDOWN] Dropdown closed via blind center click")
                    return True
            except Exception as e:
                if ctx.verbose:
                    print(f"⚠️ [TOPDOWN] Blind center click failed: {e}")

            # Strategy 5: Escape key
            try:
                from selenium.webdriver.common.keys import Keys
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                move_pointer_to_chart_center()
                time.sleep(0.1)
                if not dropdown_open():
                    if ctx.verbose:
                        print("✅ [TOPDOWN] Dropdown closed via ESC")
                    return True
            except Exception as e:
                if ctx.verbose:
                    print(f"⚠️ [TOPDOWN] ESC close failed: {e}")

            if ctx.verbose:
                print("⚠️ [TOPDOWN] Dropdown could not be confirmed closed")
            return False

        except Exception as e:
            if ctx.verbose:
                print(f"❌ [TOPDOWN] Toggle close dropdown failed: {e}")
            return False

    def _blind_click_to_close_dropdown(self, ctx: Ctx):
        """
        LEGACY: Perform a blind click to close any open dropdown menus before taking screenshots.
        Tries safe click targets to avoid interfering with UI functionality.
        This method is kept for backward compatibility but toggle_close is preferred.
        """
        try:
            driver = ctx.driver

            # Strategy 1: Try clicking on chart canvas/area (safest)
            try:
                chart_selectors = ["canvas", ".chart", ".tradingview-widget", ".chart-container"]
                for selector in chart_selectors:
                    try:
                        chart_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for chart in chart_elements:
                            if chart and chart.is_displayed() and chart.size['width'] > 100 and chart.size['height'] > 100:
                                # Click near the center of the chart area
                                driver.execute_script("""
                                    arguments[0].scrollIntoView({block: 'center'});
                                    var rect = arguments[0].getBoundingClientRect();
                                    var x = rect.left + rect.width * 0.5;
                                    var y = rect.top + rect.height * 0.5;
                                    var element = document.elementFromPoint(x, y);
                                    if (element && element !== arguments[0]) {
                                        element.click();
                                    } else {
                                        // Fallback: click the chart itself
                                        arguments[0].click();
                                    }
                                """, chart)
                                if ctx.verbose:
                                    print(f"✅ [TOPDOWN] Blind click on chart area: {selector}")
                                return
                    except Exception:
                        continue
            except Exception as e:
                if ctx.verbose:
                    print(f"⚠️ [TOPDOWN] Chart click failed: {e}")

            # Strategy 2: Click at safe coordinates (center-right area, avoiding common UI elements)
            try:
                driver.execute_script("""
                    // Click in a safe area (center-right, avoiding common UI positions)
                    const viewport = {
                        width: Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0),
                        height: Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0)
                    };

                    // Try center-right area first (avoids left sidebar, top toolbar)
                    const safeX = Math.floor(viewport.width * 0.75);
                    const safeY = Math.floor(viewport.height * 0.5);

                    const element = document.elementFromPoint(safeX, safeY);
                    if (element) {
                        // Make sure we're not clicking on interactive elements
                        const tagName = element.tagName.toLowerCase();
                        const clickableTags = ['a', 'button', 'input', 'select', 'textarea'];

                        if (!clickableTags.includes(tagName) &&
                            !element.onclick &&
                            element.getAttribute('role') !== 'button' &&
                            !element.closest('[role="menu"]')) {
                            element.click();
                            return true;
                        }
                    }

                    // Fallback: center of page
                    const centerX = Math.floor(viewport.width * 0.5);
                    const centerY = Math.floor(viewport.height * 0.5);
                    const centerElement = document.elementFromPoint(centerX, centerY);
                    if (centerElement) {
                        centerElement.click();
                        return true;
                    }

                    return false;
                """)

                if ctx.verbose:
                    print("✅ [TOPDOWN] Blind click at safe coordinates")

            except Exception as e:
                if ctx.verbose:
                    print(f"⚠️ [TOPDOWN] Safe coordinate click failed: {e}")

        except Exception as e:
            if ctx.verbose:
                print(f"❌ [TOPDOWN] Blind click failed completely: {e}")


# Factory for orchestrator
def build() -> Capability:
    return TopdownSelect()


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

    # Fallback direct attach to an existing Chrome with remote debugging port 9222
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

    parser = argparse.ArgumentParser(description="Top-down timeframe selection with optional screenshots.")
    parser.add_argument("--stack", choices=["1m", "5m"], default="1m", help="Predefined sequence: 1m→[H1,M15,M5,M1], 5m→[H4,H1,M15,M5]")
    parser.add_argument("--labels", nargs="+", help="Override labels order, e.g. H1 M15 M5 M1")
    parser.add_argument("--delay-ms", type=int, default=300, help="Delay after actions (ms)")
    parser.add_argument("--save", dest="save", action="store_true", help="Save screenshots (default)")
    parser.add_argument("--no-save", dest="save", action="store_false", help="Do not save screenshots")
    parser.set_defaults(save=True)
    parser.add_argument("--screenshots-subdir", default="topdown_analysis", help="Subdir under screenshots/")
    parser.add_argument("--reopen-each", dest="reopen_each", action="store_true", help="Reopen dropdown before each selection (default)")
    parser.add_argument("--no-reopen", dest="reopen_each", action="store_false", help="Do not reopen before each selection")
    parser.set_defaults(reopen_each=True)
    parser.add_argument("--iframe-css", help="CSS selector for iframe containing timeframe controls")
    parser.add_argument("--iframe-index", type=int, help="Index of iframe containing timeframe controls")
    parser.add_argument("--menu-toggle-selectors", nargs="+", help="Optional CSS selectors to open timeframe dropdown/menu")
    args = parser.parse_args()

    cap = TopdownSelect()
    inputs = {
        "stack": args.stack,
        "labels": args.labels,
        "delay_ms": int(args.delay_ms),
        "save": bool(args.save),
        "screenshots_subdir": args.screenshots_subdir,
        "reopen_each": bool(args.reopen_each),
        "iframe_css": args.iframe_css,
        "iframe_index": args.iframe_index,
        "menu_toggle_selectors": args.menu_toggle_selectors,
    }
    res = cap.run(ctx, inputs)
    out = {
        "ok": res.ok,
        "error": res.error,
        "data": res.data,
        "artifacts": list(getattr(res, "artifacts", [])) if getattr(res, "artifacts", None) else [],
    }
    print(_json.dumps(out, ensure_ascii=False, indent=2))
