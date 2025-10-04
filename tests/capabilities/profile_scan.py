"""Profile scan capability for reading user profile and account information.

Migrated from API-test-space for production use.
Simplified to work with existing selenium_helpers infrastructure.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple, List
import re
import time

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


class ProfileScan(Capability):
    """
    Capability: Read profile/account information from the user interface.

    Interface: run(ctx, {})
    Outputs (top-level):
      - account: "DEMO" | "REAL" | "UNKNOWN"
      - balance: float | None
      - amount: float | None
      - display_name: str | None
      - user_id: str | None
      - email: str | None
      - currency: str | None
      - account_banner: str | None
      - viewport_scale: float | None
      - raw: diagnostics/meta

    Kind: "read"
    """
    id = "profile_scan"
    kind = "read"

    def run(self, ctx: Ctx, inputs: Dict[str, Any]) -> CapResult:
        data: Dict[str, Any] = {
            "account": "UNKNOWN",
            "balance": None,
            "amount": None,
            "display_name": None,
            "user_id": None,
            "email": None,
            "currency": None,
            "account_banner": None,
            "viewport_scale": None,
            "raw": {},
        }
        artifacts: List[str] = []

        if UIControls is None or By is None:
            return CapResult(ok=False, data=data, error="Selenium helpers not available", artifacts=tuple(artifacts))

        ui_controls = UIControls(ctx.driver)

        # Account type + balance
        try:
            # Get account type
            account_type = ui_controls.get_account_type()
            if account_type in ("DEMO", "REAL"):
                data["account"] = account_type
            
            # Get balance
            balance = ui_controls.get_account_balance()
            data["balance"] = balance
            
            # Try to detect currency from balance text
            if balance is not None:
                data["currency"] = self._detect_currency_from_balance(balance)
            
            data["raw"]["balance_and_account_meta"] = {
                "account_type": account_type,
                "balance": balance
            }
        except Exception as e:
            data["raw"]["balance_error"] = str(e)

        # Amount field (read-only)
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
                # Check if scale is within expected range
                expected = 0.67
                tolerance = 0.05
                ok_zoom = abs(scale - expected) <= tolerance if scale else False
                data["raw"]["viewport_scale_ok"] = ok_zoom
        except Exception as e:
            data["raw"]["viewport_scale_error"] = str(e)

        # Try to extract profile information from page
        try:
            profile_info = self._extract_profile_info(ctx)
            data.update(profile_info)
            data["raw"]["profile_extraction_meta"] = profile_info.get("_meta", {})
        except Exception as e:
            data["raw"]["profile_error"] = str(e)

        # Debug artifacts
        if ctx.debug:
            try:
                ts = timestamp()
                path = save_json(ctx, f"profile_scan_{ts}.json", data)
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

    def _detect_currency_from_balance(self, balance: float) -> Optional[str]:
        """Try to detect currency from balance display"""
        try:
            # Look for currency symbols in balance-related elements
            currency_selectors = [
                "[class*='currency']",
                "[class*='balance'] [class*='symbol']",
                ".currency-symbol",
                "[data-testid*='currency']"
            ]
            
            for selector in currency_selectors:
                try:
                    elements = ctx.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text in ["USD", "EUR", "GBP", "$", "€", "£"]:
                            return text
                except Exception:
                    continue
                    
            return None
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

    def _extract_profile_info(self, ctx: Ctx) -> Dict[str, Any]:
        """Extract profile information from page elements"""
        info = {"_meta": {}}
        
        try:
            # Try to find user avatar or profile button
            avatar_selectors = [
                "[data-testid='user-avatar']",
                "[class*='avatar']",
                "[class*='profile']",
                "[class*='user-menu']",
                ".user-info",
                "[role='button'][class*='user']"
            ]
            
            avatar_element = None
            for selector in avatar_selectors:
                try:
                    avatar_element = ctx.driver.find_element(By.CSS_SELECTOR, selector)
                    if avatar_element.is_displayed():
                        break
                except Exception:
                    continue
            
            if avatar_element:
                # Try to click avatar to open profile menu
                try:
                    avatar_element.click()
                    time.sleep(1)  # Wait for menu to open
                    
                    # Look for profile information in opened menu
                    profile_menu_selectors = [
                        "[class*='dropdown']",
                        "[class*='menu']",
                        "[class*='popover']",
                        "[role='menu']"
                    ]
                    
                    for menu_selector in profile_menu_selectors:
                        try:
                            menu = ctx.driver.find_element(By.CSS_SELECTOR, menu_selector)
                            if menu.is_displayed():
                                menu_text = menu.text
                                
                                # Extract email
                                email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', menu_text)
                                if email_match:
                                    info["email"] = email_match.group(1)
                                
                                # Extract display name (usually before email or at top)
                                lines = menu_text.split('\n')
                                for line in lines:
                                    line = line.strip()
                                    if line and not '@' in line and not line.upper() in ['DEMO', 'REAL', 'LOGOUT', 'SETTINGS']:
                                        if len(line) > 2 and len(line) < 50:  # Reasonable name length
                                            info["display_name"] = line
                                            break
                                
                                # Look for account banner
                                if 'DEMO' in menu_text.upper():
                                    info["account_banner"] = "DEMO ACCOUNT"
                                elif 'REAL' in menu_text.upper():
                                    info["account_banner"] = "REAL ACCOUNT"
                                
                                info["_meta"]["menu_text"] = menu_text
                                break
                        except Exception:
                            continue
                    
                    # Close menu by clicking elsewhere
                    try:
                        ctx.driver.find_element(By.TAG_NAME, "body").click()
                    except Exception:
                        pass
                        
                except Exception as e:
                    info["_meta"]["avatar_click_error"] = str(e)
            
            # Fallback: search page text for email patterns
            if not info.get("email"):
                try:
                    page_text = ctx.driver.find_element(By.TAG_NAME, "body").text
                    email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', page_text)
                    if email_match:
                        info["email"] = email_match.group(1)
                        info["_meta"]["email_source"] = "page_text_fallback"
                except Exception:
                    pass
            
        except Exception as e:
            info["_meta"]["extraction_error"] = str(e)
        
        return info


# Factory
def build() -> Capability:
    return ProfileScan()