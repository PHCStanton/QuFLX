"""Selenium UI Controls Helpers for QuantumFlux Testing.

This module provides:
- ZoomManager: read-only verification of zoom (no changes applied by default)
- UIControls: resilient operations for key trading UI controls:
  * Trade Duration/Expiry (default "1 min")
  * Trade Amount
  * Payout indicator reading
  * Buy/Sell button presence and clickability checks
  * Balance and Account Type (DEMO/REAL)
  * Favorites scan for assets with payout ≥ threshold
  * (Optional helper) User profile details via dropdown

IMPORTANT:
- Do NOT modify browser zoom or settings here. ZoomManager.verify() is read-only.
- All outputs must stay under tests/test_results/*

Migrated from API-test-space for production use.
"""

from __future__ import annotations

import os
import re
import json
import time
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Any

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException


DEFAULT_TIMEOUT = 10  # seconds
LONG_TIMEOUT = 20


class ZoomManager:
    """Read-only zoom utilities. Does NOT change zoom."""

    @staticmethod
    def get_zoom_scale(driver: WebDriver) -> float:
        """Return current visual viewport scale (~0.67 for 67%)."""
        try:
            scale = driver.execute_script(
                "return (window.visualViewport && window.visualViewport.scale) || 1;"
            )
            if isinstance(scale, (int, float)):
                return float(scale)
            return 1.0
        except Exception:
            return 1.0

    @staticmethod
    def get_device_pixel_ratio(driver: WebDriver) -> float:
        """Return device pixel ratio."""
        try:
            ratio = driver.execute_script("return window.devicePixelRatio || 1;")
            if isinstance(ratio, (int, float)):
                return float(ratio)
            return 1.0
        except Exception:
            return 1.0

    @staticmethod
    def verify_zoom_level(driver: WebDriver) -> Dict[str, Any]:
        """Verify current zoom level without changing it."""
        try:
            scale = ZoomManager.get_zoom_scale(driver)
            ratio = ZoomManager.get_device_pixel_ratio(driver)
            
            # Get window dimensions
            window_size = driver.get_window_size()
            
            return {
                'zoom_scale': scale,
                'device_pixel_ratio': ratio,
                'window_width': window_size.get('width', 0),
                'window_height': window_size.get('height', 0),
                'zoom_percentage': round(scale * 100, 1)
            }
        except Exception as e:
            return {
                'error': str(e),
                'zoom_scale': 1.0,
                'device_pixel_ratio': 1.0,
                'window_width': 0,
                'window_height': 0,
                'zoom_percentage': 100.0
            }


@dataclass
class AssetInfo:
    """Asset information structure"""
    symbol: str
    payout_percentage: float
    is_available: bool
    element_id: Optional[str] = None


@dataclass
class TradeInfo:
    """Trade information structure"""
    amount: float
    duration: str
    direction: str  # 'BUY' or 'SELL'
    asset: str
    payout_percentage: float
    timestamp: str


class UIControls:
    """Resilient UI controls for trading interface testing"""
    
    def __init__(self, driver: WebDriver, timeout: int = DEFAULT_TIMEOUT):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)
    
    def get_account_balance(self) -> Optional[float]:
        """Get current account balance"""
        try:
            # Common selectors for balance
            balance_selectors = [
                "[data-testid='balance']",
                ".balance",
                "#balance",
                "[class*='balance']",
                "[id*='balance']"
            ]
            
            for selector in balance_selectors:
                try:
                    element = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    text = element.text.strip()
                    
                    # Extract numeric value
                    match = re.search(r'([\d,]+\.?\d*)', text.replace(',', ''))
                    if match:
                        return float(match.group(1))
                except (TimeoutException, ValueError):
                    continue
            
            return None
            
        except Exception:
            return None
    
    def get_account_type(self) -> Optional[str]:
        """Get account type (DEMO/REAL)"""
        try:
            # Look for account type indicators
            type_selectors = [
                "[data-testid='account-type']",
                ".account-type",
                "[class*='demo']",
                "[class*='real']",
                "[text*='DEMO']",
                "[text*='REAL']"
            ]
            
            for selector in type_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    text = element.text.upper()
                    
                    if 'DEMO' in text:
                        return 'DEMO'
                    elif 'REAL' in text:
                        return 'REAL'
                except NoSuchElementException:
                    continue
            
            return None
            
        except Exception:
            return None
    
    def get_trade_amount(self) -> Optional[float]:
        """Get current trade amount setting"""
        try:
            # Common selectors for trade amount
            amount_selectors = [
                "[data-testid='trade-amount']",
                "input[name='amount']",
                "input[placeholder*='amount']",
                ".trade-amount input",
                "#trade-amount"
            ]
            
            for selector in amount_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    value = element.get_attribute('value') or element.text
                    
                    if value:
                        # Extract numeric value
                        match = re.search(r'([\d,]+\.?\d*)', value.replace(',', ''))
                        if match:
                            return float(match.group(1))
                except (NoSuchElementException, ValueError):
                    continue
            
            return None
            
        except Exception:
            return None
    
    def set_trade_amount(self, amount: float) -> bool:
        """Set trade amount"""
        try:
            # Find amount input field
            amount_selectors = [
                "[data-testid='trade-amount']",
                "input[name='amount']",
                "input[placeholder*='amount']",
                ".trade-amount input",
                "#trade-amount"
            ]
            
            for selector in amount_selectors:
                try:
                    element = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    
                    # Clear and set new amount
                    element.clear()
                    element.send_keys(str(amount))
                    
                    # Verify the amount was set
                    time.sleep(0.5)  # Allow UI to update
                    current_amount = self.get_trade_amount()
                    
                    return current_amount is not None and abs(current_amount - amount) < 0.01
                    
                except TimeoutException:
                    continue
            
            return False
            
        except Exception:
            return False
    
    def get_trade_duration(self) -> Optional[str]:
        """Get current trade duration/expiry setting"""
        try:
            # Common selectors for trade duration
            duration_selectors = [
                "[data-testid='trade-duration']",
                ".trade-duration",
                "[class*='expiry']",
                "[class*='duration']",
                "select[name='duration']"
            ]
            
            for selector in duration_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    # Handle select elements
                    if element.tag_name.lower() == 'select':
                        from selenium.webdriver.support.ui import Select
                        select = Select(element)
                        return select.first_selected_option.text
                    else:
                        return element.text.strip()
                        
                except NoSuchElementException:
                    continue
            
            return None
            
        except Exception:
            return None
    
    def set_trade_duration(self, duration: str) -> bool:
        """Set trade duration (e.g., '1 min', '5 min')"""
        try:
            # Find duration selector
            duration_selectors = [
                "[data-testid='trade-duration']",
                ".trade-duration select",
                "select[name='duration']",
                "[class*='duration'] select"
            ]
            
            for selector in duration_selectors:
                try:
                    element = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    
                    if element.tag_name.lower() == 'select':
                        from selenium.webdriver.support.ui import Select
                        select = Select(element)
                        
                        # Try to select by visible text
                        try:
                            select.select_by_visible_text(duration)
                            return True
                        except:
                            # Try partial match
                            for option in select.options:
                                if duration.lower() in option.text.lower():
                                    select.select_by_visible_text(option.text)
                                    return True
                    
                except TimeoutException:
                    continue
            
            return False
            
        except Exception:
            return False
    
    def get_payout_percentage(self, asset: str = None) -> Optional[float]:
        """Get payout percentage for current or specified asset"""
        try:
            # Common selectors for payout percentage
            payout_selectors = [
                "[data-testid='payout']",
                ".payout",
                "[class*='payout']",
                "[class*='profit']",
                "[text*='%']"
            ]
            
            for selector in payout_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        text = element.text.strip()
                        
                        # Look for percentage values
                        match = re.search(r'(\d+(?:\.\d+)?)%', text)
                        if match:
                            return float(match.group(1))
                            
                except NoSuchElementException:
                    continue
            
            return None
            
        except Exception:
            return None
    
    def find_buy_sell_buttons(self) -> Tuple[Optional[Any], Optional[Any]]:
        """Find BUY and SELL buttons"""
        try:
            # Common selectors for buy/sell buttons
            buy_selectors = [
                "[data-testid='buy-button']",
                "button[class*='buy']",
                "button[class*='call']",
                "[class*='buy-button']",
                "button:contains('BUY')",
                "button:contains('CALL')"
            ]
            
            sell_selectors = [
                "[data-testid='sell-button']",
                "button[class*='sell']",
                "button[class*='put']",
                "[class*='sell-button']",
                "button:contains('SELL')",
                "button:contains('PUT')"
            ]
            
            buy_button = None
            sell_button = None
            
            # Find buy button
            for selector in buy_selectors:
                try:
                    buy_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            # Find sell button
            for selector in sell_selectors:
                try:
                    sell_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            return buy_button, sell_button
            
        except Exception:
            return None, None
    
    def check_buttons_clickable(self) -> Dict[str, bool]:
        """Check if BUY/SELL buttons are clickable"""
        try:
            buy_button, sell_button = self.find_buy_sell_buttons()
            
            result = {
                'buy_clickable': False,
                'sell_clickable': False,
                'buy_enabled': False,
                'sell_enabled': False
            }
            
            if buy_button:
                result['buy_enabled'] = buy_button.is_enabled()
                result['buy_clickable'] = buy_button.is_enabled() and buy_button.is_displayed()
            
            if sell_button:
                result['sell_enabled'] = sell_button.is_enabled()
                result['sell_clickable'] = sell_button.is_enabled() and sell_button.is_displayed()
            
            return result
            
        except Exception:
            return {
                'buy_clickable': False,
                'sell_clickable': False,
                'buy_enabled': False,
                'sell_enabled': False
            }
    
    def scan_available_assets(self, min_payout: float = 70.0) -> List[AssetInfo]:
        """Scan for available assets with minimum payout percentage"""
        try:
            assets = []
            
            # Common selectors for asset lists
            asset_selectors = [
                "[data-testid='asset-list'] [data-testid='asset-item']",
                ".asset-list .asset-item",
                "[class*='asset'] [class*='item']",
                ".favorites .asset",
                "[class*='instrument']"
            ]
            
            for selector in asset_selectors:
                try:
                    asset_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in asset_elements:
                        try:
                            # Extract asset symbol
                            symbol_element = element.find_element(By.CSS_SELECTOR, "[class*='symbol'], [class*='name'], .asset-name")
                            symbol = symbol_element.text.strip()
                            
                            # Extract payout percentage
                            payout_element = element.find_element(By.CSS_SELECTOR, "[class*='payout'], [class*='profit'], [text*='%']")
                            payout_text = payout_element.text.strip()
                            
                            match = re.search(r'(\d+(?:\.\d+)?)%', payout_text)
                            if match:
                                payout = float(match.group(1))
                                
                                if payout >= min_payout:
                                    assets.append(AssetInfo(
                                        symbol=symbol,
                                        payout_percentage=payout,
                                        is_available=True,
                                        element_id=element.get_attribute('id')
                                    ))
                        
                        except (NoSuchElementException, ValueError):
                            continue
                    
                    if assets:  # If we found assets with this selector, break
                        break
                        
                except NoSuchElementException:
                    continue
            
            return assets
            
        except Exception:
            return []
    
    def get_user_profile_info(self) -> Dict[str, Any]:
        """Get user profile information via dropdown"""
        try:
            profile_info = {}
            
            # Look for profile dropdown or user menu
            profile_selectors = [
                "[data-testid='user-menu']",
                ".user-menu",
                "[class*='profile']",
                "[class*='user-info']",
                ".header .user"
            ]
            
            for selector in profile_selectors:
                try:
                    profile_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    # Click to open dropdown
                    profile_element.click()
                    time.sleep(1)  # Wait for dropdown to open
                    
                    # Extract information from dropdown
                    dropdown_selectors = [
                        ".dropdown-menu",
                        "[class*='dropdown']",
                        "[class*='menu']"
                    ]
                    
                    for dropdown_selector in dropdown_selectors:
                        try:
                            dropdown = self.driver.find_element(By.CSS_SELECTOR, dropdown_selector)
                            
                            # Extract various profile fields
                            text_content = dropdown.text
                            
                            # Look for email
                            email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text_content)
                            if email_match:
                                profile_info['email'] = email_match.group(1)
                            
                            # Look for user ID
                            id_match = re.search(r'ID[:\s]*(\d+)', text_content)
                            if id_match:
                                profile_info['user_id'] = id_match.group(1)
                            
                            # Look for account type
                            if 'DEMO' in text_content.upper():
                                profile_info['account_type'] = 'DEMO'
                            elif 'REAL' in text_content.upper():
                                profile_info['account_type'] = 'REAL'
                            
                            break
                            
                        except NoSuchElementException:
                            continue
                    
                    # Close dropdown by clicking elsewhere
                    self.driver.find_element(By.TAG_NAME, 'body').click()
                    
                    if profile_info:  # If we found info, break
                        break
                        
                except NoSuchElementException:
                    continue
            
            return profile_info
            
        except Exception:
            return {}
    
    def wait_for_page_load(self, timeout: int = None) -> bool:
        """Wait for page to fully load"""
        try:
            timeout = timeout or self.timeout
            
            # Wait for document ready state
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Wait for any loading indicators to disappear
            loading_selectors = [
                ".loading",
                "[class*='loading']",
                ".spinner",
                "[class*='spinner']",
                "[data-testid='loading']"
            ]
            
            for selector in loading_selectors:
                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.invisibility_of_element_located((By.CSS_SELECTOR, selector))
                    )
                except TimeoutException:
                    pass  # Loading indicator might not exist
            
            return True
            
        except Exception:
            return False
    
    def take_screenshot(self, filename: str = None) -> str:
        """Take screenshot and save to test results directory"""
        try:
            if not filename:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
            
            # Ensure test results directory exists
            test_results_dir = os.path.join(os.getcwd(), "tests", "test_results")
            os.makedirs(test_results_dir, exist_ok=True)
            
            screenshot_path = os.path.join(test_results_dir, filename)
            
            # Take screenshot
            self.driver.save_screenshot(screenshot_path)
            
            return screenshot_path
            
        except Exception as e:
            print(f"Failed to take screenshot: {e}")
            return ""
    
    def save_page_source(self, filename: str = None) -> str:
        """Save page source to test results directory"""
        try:
            if not filename:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"page_source_{timestamp}.html"
            
            # Ensure test results directory exists
            test_results_dir = os.path.join(os.getcwd(), "tests", "test_results")
            os.makedirs(test_results_dir, exist_ok=True)
            
            source_path = os.path.join(test_results_dir, filename)
            
            # Save page source
            with open(source_path, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            
            return source_path
            
        except Exception as e:
            print(f"Failed to save page source: {e}")
            return ""


def create_test_report(test_data: Dict[str, Any], filename: str = None) -> str:
    """Create a JSON test report"""
    try:
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"test_report_{timestamp}.json"
        
        # Ensure test results directory exists
        test_results_dir = os.path.join(os.getcwd(), "tests", "test_results")
        os.makedirs(test_results_dir, exist_ok=True)
        
        report_path = os.path.join(test_results_dir, filename)
        
        # Add metadata
        report_data = {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'test_data': test_data
        }
        
        # Save report
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        return report_path
        
    except Exception as e:
        print(f"Failed to create test report: {e}")
        return ""