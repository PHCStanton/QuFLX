"""Trade Helpers for QuantumFlux Testing.

This module provides robust trade clicking utilities with diagnostics:
- robust_trade_click_with_meta: Pointer-true clicks with rich diagnostics
- get_open_trades_count: Monitor open trades
- verify_open_trades_increment: Verify trade execution
- Trade execution monitoring and validation
- Artifact saving to tests/test_results/

Migrated from API-test-space for production use.
"""

from __future__ import annotations

import os
import json
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Tuple

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    StaleElementReferenceException,
    ElementClickInterceptedException,
    ElementNotInteractableException
)


DEFAULT_TIMEOUT = 10
CLICK_TIMEOUT = 5
TRADE_VERIFICATION_TIMEOUT = 15


@dataclass
class ClickDiagnostics:
    """Comprehensive click diagnostics"""
    timestamp: str
    button_type: str  # 'BUY' or 'SELL'
    element_found: bool
    element_visible: bool
    element_enabled: bool
    element_clickable: bool
    click_attempted: bool
    click_successful: bool
    coordinates: Optional[Tuple[int, int]]
    element_text: str
    element_classes: List[str]
    element_attributes: Dict[str, str]
    page_url: str
    viewport_size: Dict[str, int]
    scroll_position: Dict[str, int]
    error_message: Optional[str]
    pre_click_trades_count: Optional[int]
    post_click_trades_count: Optional[int]
    trade_increment_verified: bool
    execution_time_ms: float


@dataclass
class TradeExecutionResult:
    """Trade execution result with full context"""
    success: bool
    trade_direction: str
    diagnostics: ClickDiagnostics
    trade_details: Optional[Dict[str, Any]]
    screenshot_path: Optional[str]
    artifacts_saved: List[str]


class TradeClickHelper:
    """Robust trade clicking with comprehensive diagnostics"""
    
    def __init__(self, driver: WebDriver, timeout: int = DEFAULT_TIMEOUT):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)
        self.artifacts_dir = self._ensure_artifacts_dir()
    
    def _ensure_artifacts_dir(self) -> str:
        """Ensure artifacts directory exists"""
        artifacts_dir = os.path.join(os.getcwd(), "tests", "test_results", "trade_artifacts")
        os.makedirs(artifacts_dir, exist_ok=True)
        return artifacts_dir
    
    def _get_element_info(self, element: WebElement) -> Dict[str, Any]:
        """Extract comprehensive element information"""
        try:
            return {
                'tag_name': element.tag_name,
                'text': element.text.strip(),
                'classes': element.get_attribute('class').split() if element.get_attribute('class') else [],
                'id': element.get_attribute('id') or '',
                'data_testid': element.get_attribute('data-testid') or '',
                'enabled': element.is_enabled(),
                'displayed': element.is_displayed(),
                'location': element.location,
                'size': element.size,
                'attributes': {
                    'type': element.get_attribute('type') or '',
                    'name': element.get_attribute('name') or '',
                    'value': element.get_attribute('value') or '',
                    'onclick': element.get_attribute('onclick') or '',
                    'disabled': element.get_attribute('disabled') or 'false'
                }
            }
        except StaleElementReferenceException:
            return {'error': 'stale_element_reference'}
        except Exception as e:
            return {'error': str(e)}
    
    def _get_viewport_info(self) -> Dict[str, Any]:
        """Get viewport and scroll information"""
        try:
            viewport_size = self.driver.execute_script(
                "return {width: window.innerWidth, height: window.innerHeight};"
            )
            scroll_position = self.driver.execute_script(
                "return {x: window.pageXOffset, y: window.pageYOffset};"
            )
            return {
                'viewport_size': viewport_size,
                'scroll_position': scroll_position
            }
        except Exception:
            return {
                'viewport_size': {'width': 0, 'height': 0},
                'scroll_position': {'x': 0, 'y': 0}
            }
    
    def get_open_trades_count(self) -> Optional[int]:
        """Get current number of open trades"""
        try:
            # Common selectors for open trades
            trades_selectors = [
                "[data-testid='open-trades'] .trade-item",
                ".open-trades .trade",
                "[class*='open-trade']",
                ".trades-list .trade-item",
                "[class*='position']",
                "[data-testid='position']"
            ]
            
            for selector in trades_selectors:
                try:
                    trades = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if trades:
                        return len(trades)
                except NoSuchElementException:
                    continue
            
            # Alternative: look for trades counter
            counter_selectors = [
                "[data-testid='trades-count']",
                ".trades-count",
                "[class*='count']"
            ]
            
            for selector in counter_selectors:
                try:
                    counter = self.driver.find_element(By.CSS_SELECTOR, selector)
                    text = counter.text.strip()
                    
                    # Extract number from text
                    import re
                    match = re.search(r'(\d+)', text)
                    if match:
                        return int(match.group(1))
                except (NoSuchElementException, ValueError):
                    continue
            
            return 0  # Default to 0 if no trades found
            
        except Exception:
            return None
    
    def verify_open_trades_increment(self, 
                                   initial_count: int, 
                                   expected_increment: int = 1,
                                   timeout: int = TRADE_VERIFICATION_TIMEOUT) -> bool:
        """Verify that open trades count increased by expected amount"""
        try:
            end_time = time.time() + timeout
            
            while time.time() < end_time:
                current_count = self.get_open_trades_count()
                
                if current_count is not None:
                    actual_increment = current_count - initial_count
                    
                    if actual_increment >= expected_increment:
                        return True
                    elif actual_increment < 0:
                        # Trades count decreased, something went wrong
                        return False
                
                time.sleep(0.5)  # Check every 500ms
            
            return False
            
        except Exception:
            return False
    
    def _find_trade_button(self, button_type: str) -> Optional[WebElement]:
        """Find BUY or SELL button with multiple strategies"""
        button_type = button_type.upper()
        
        # Strategy 1: Direct data-testid
        testid_selectors = [
            f"[data-testid='{button_type.lower()}-button']",
            f"[data-testid='trade-{button_type.lower()}']",
            f"[data-testid='{button_type.lower()}']"
        ]
        
        for selector in testid_selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element.is_displayed():
                    return element
            except NoSuchElementException:
                continue
        
        # Strategy 2: Class-based selectors
        class_selectors = [
            f"button[class*='{button_type.lower()}']",
            f".{button_type.lower()}-button",
            f"[class*='{button_type.lower()}-btn']"
        ]
        
        if button_type == 'BUY':
            class_selectors.extend([
                "button[class*='call']",
                ".call-button",
                "[class*='up']"
            ])
        elif button_type == 'SELL':
            class_selectors.extend([
                "button[class*='put']",
                ".put-button",
                "[class*='down']"
            ])
        
        for selector in class_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed():
                        return element
            except NoSuchElementException:
                continue
        
        # Strategy 3: Text-based search
        text_patterns = [button_type]
        if button_type == 'BUY':
            text_patterns.extend(['CALL', 'UP', '↑'])
        elif button_type == 'SELL':
            text_patterns.extend(['PUT', 'DOWN', '↓'])
        
        for pattern in text_patterns:
            try:
                xpath = f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern.lower()}')]"
                elements = self.driver.find_elements(By.XPATH, xpath)
                for element in elements:
                    if element.is_displayed():
                        return element
            except NoSuchElementException:
                continue
        
        return None
    
    def _perform_click_with_diagnostics(self, 
                                      element: WebElement, 
                                      button_type: str) -> ClickDiagnostics:
        """Perform click with comprehensive diagnostics"""
        start_time = time.time()
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Get pre-click state
        element_info = self._get_element_info(element)
        viewport_info = self._get_viewport_info()
        pre_click_trades = self.get_open_trades_count()
        
        # Initialize diagnostics
        diagnostics = ClickDiagnostics(
            timestamp=timestamp,
            button_type=button_type,
            element_found=True,
            element_visible=element_info.get('displayed', False),
            element_enabled=element_info.get('enabled', False),
            element_clickable=False,
            click_attempted=False,
            click_successful=False,
            coordinates=None,
            element_text=element_info.get('text', ''),
            element_classes=element_info.get('classes', []),
            element_attributes=element_info.get('attributes', {}),
            page_url=self.driver.current_url,
            viewport_size=viewport_info['viewport_size'],
            scroll_position=viewport_info['scroll_position'],
            error_message=None,
            pre_click_trades_count=pre_click_trades,
            post_click_trades_count=None,
            trade_increment_verified=False,
            execution_time_ms=0.0
        )
        
        try:
            # Check if element is clickable
            try:
                WebDriverWait(self.driver, CLICK_TIMEOUT).until(
                    EC.element_to_be_clickable(element)
                )
                diagnostics.element_clickable = True
            except TimeoutException:
                diagnostics.element_clickable = False
                diagnostics.error_message = "Element not clickable within timeout"
            
            if diagnostics.element_clickable:
                # Get element coordinates
                location = element.location
                size = element.size
                center_x = location['x'] + size['width'] // 2
                center_y = location['y'] + size['height'] // 2
                diagnostics.coordinates = (center_x, center_y)
                
                # Attempt click
                diagnostics.click_attempted = True
                
                try:
                    # Method 1: Direct click
                    element.click()
                    diagnostics.click_successful = True
                    
                except (ElementClickInterceptedException, ElementNotInteractableException) as e:
                    # Method 2: ActionChains click
                    try:
                        ActionChains(self.driver).move_to_element(element).click().perform()
                        diagnostics.click_successful = True
                    except Exception as e2:
                        # Method 3: JavaScript click
                        try:
                            self.driver.execute_script("arguments[0].click();", element)
                            diagnostics.click_successful = True
                        except Exception as e3:
                            diagnostics.error_message = f"All click methods failed: {str(e)}, {str(e2)}, {str(e3)}"
                
                # Wait a moment for trade to register
                if diagnostics.click_successful:
                    time.sleep(1)
                    
                    # Get post-click trades count
                    post_click_trades = self.get_open_trades_count()
                    diagnostics.post_click_trades_count = post_click_trades
                    
                    # Verify trade increment
                    if pre_click_trades is not None and post_click_trades is not None:
                        diagnostics.trade_increment_verified = self.verify_open_trades_increment(
                            pre_click_trades, 1, 10
                        )
        
        except Exception as e:
            diagnostics.error_message = str(e)
        
        finally:
            diagnostics.execution_time_ms = (time.time() - start_time) * 1000
        
        return diagnostics
    
    def robust_trade_click_with_meta(self, 
                                   button_type: str, 
                                   save_artifacts: bool = True) -> TradeExecutionResult:
        """Execute trade click with comprehensive diagnostics and artifact saving"""
        button_type = button_type.upper()
        
        # Find the button
        element = self._find_trade_button(button_type)
        
        if not element:
            # Create diagnostics for button not found
            diagnostics = ClickDiagnostics(
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                button_type=button_type,
                element_found=False,
                element_visible=False,
                element_enabled=False,
                element_clickable=False,
                click_attempted=False,
                click_successful=False,
                coordinates=None,
                element_text='',
                element_classes=[],
                element_attributes={},
                page_url=self.driver.current_url,
                viewport_size=self._get_viewport_info()['viewport_size'],
                scroll_position=self._get_viewport_info()['scroll_position'],
                error_message=f"{button_type} button not found",
                pre_click_trades_count=self.get_open_trades_count(),
                post_click_trades_count=None,
                trade_increment_verified=False,
                execution_time_ms=0.0
            )
            
            return TradeExecutionResult(
                success=False,
                trade_direction=button_type,
                diagnostics=diagnostics,
                trade_details=None,
                screenshot_path=None,
                artifacts_saved=[]
            )
        
        # Perform click with diagnostics
        diagnostics = self._perform_click_with_diagnostics(element, button_type)
        
        # Gather trade details if successful
        trade_details = None
        if diagnostics.click_successful:
            trade_details = self._gather_trade_details(button_type)
        
        # Save artifacts if requested
        artifacts_saved = []
        screenshot_path = None
        
        if save_artifacts:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            
            # Save screenshot
            try:
                screenshot_filename = f"trade_{button_type.lower()}_{timestamp}.png"
                screenshot_path = os.path.join(self.artifacts_dir, screenshot_filename)
                self.driver.save_screenshot(screenshot_path)
                artifacts_saved.append(screenshot_path)
            except Exception:
                pass
            
            # Save diagnostics
            try:
                diagnostics_filename = f"diagnostics_{button_type.lower()}_{timestamp}.json"
                diagnostics_path = os.path.join(self.artifacts_dir, diagnostics_filename)
                
                with open(diagnostics_path, 'w', encoding='utf-8') as f:
                    json.dump(asdict(diagnostics), f, indent=2, default=str)
                
                artifacts_saved.append(diagnostics_path)
            except Exception:
                pass
            
            # Save page source
            try:
                source_filename = f"page_source_{button_type.lower()}_{timestamp}.html"
                source_path = os.path.join(self.artifacts_dir, source_filename)
                
                with open(source_path, 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                
                artifacts_saved.append(source_path)
            except Exception:
                pass
        
        return TradeExecutionResult(
            success=diagnostics.click_successful and diagnostics.trade_increment_verified,
            trade_direction=button_type,
            diagnostics=diagnostics,
            trade_details=trade_details,
            screenshot_path=screenshot_path,
            artifacts_saved=artifacts_saved
        )
    
    def _gather_trade_details(self, button_type: str) -> Dict[str, Any]:
        """Gather trade details after successful click"""
        try:
            details = {
                'direction': button_type,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                'amount': None,
                'asset': None,
                'duration': None,
                'payout_percentage': None
            }
            
            # Try to get trade amount
            try:
                amount_selectors = [
                    "[data-testid='trade-amount']",
                    "input[name='amount']",
                    ".trade-amount input"
                ]
                
                for selector in amount_selectors:
                    try:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        value = element.get_attribute('value') or element.text
                        if value:
                            import re
                            match = re.search(r'([\d,]+\.?\d*)', value.replace(',', ''))
                            if match:
                                details['amount'] = float(match.group(1))
                                break
                    except (NoSuchElementException, ValueError):
                        continue
            except Exception:
                pass
            
            # Try to get current asset
            try:
                asset_selectors = [
                    "[data-testid='current-asset']",
                    ".current-asset",
                    "[class*='asset-name']",
                    ".asset-selector .selected"
                ]
                
                for selector in asset_selectors:
                    try:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        details['asset'] = element.text.strip()
                        break
                    except NoSuchElementException:
                        continue
            except Exception:
                pass
            
            # Try to get trade duration
            try:
                duration_selectors = [
                    "[data-testid='trade-duration']",
                    ".trade-duration",
                    "select[name='duration'] option[selected]"
                ]
                
                for selector in duration_selectors:
                    try:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        details['duration'] = element.text.strip()
                        break
                    except NoSuchElementException:
                        continue
            except Exception:
                pass
            
            # Try to get payout percentage
            try:
                payout_selectors = [
                    "[data-testid='payout']",
                    ".payout",
                    "[class*='payout']"
                ]
                
                for selector in payout_selectors:
                    try:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        text = element.text.strip()
                        
                        import re
                        match = re.search(r'(\d+(?:\.\d+)?)%', text)
                        if match:
                            details['payout_percentage'] = float(match.group(1))
                            break
                    except (NoSuchElementException, ValueError):
                        continue
            except Exception:
                pass
            
            return details
            
        except Exception:
            return {
                'direction': button_type,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                'error': 'Failed to gather trade details'
            }


def execute_buy_trade(driver: WebDriver, save_artifacts: bool = True) -> TradeExecutionResult:
    """Execute BUY trade with diagnostics"""
    helper = TradeClickHelper(driver)
    return helper.robust_trade_click_with_meta('BUY', save_artifacts)


def execute_sell_trade(driver: WebDriver, save_artifacts: bool = True) -> TradeExecutionResult:
    """Execute SELL trade with diagnostics"""
    helper = TradeClickHelper(driver)
    return helper.robust_trade_click_with_meta('SELL', save_artifacts)


def monitor_trade_execution(driver: WebDriver, 
                          expected_trades: int = 1, 
                          timeout: int = 30) -> Dict[str, Any]:
    """Monitor trade execution and return comprehensive results"""
    helper = TradeClickHelper(driver)
    
    start_time = time.time()
    initial_trades = helper.get_open_trades_count() or 0
    
    monitoring_result = {
        'start_time': time.strftime("%Y-%m-%d %H:%M:%S"),
        'initial_trades_count': initial_trades,
        'expected_trades': expected_trades,
        'final_trades_count': None,
        'trades_increment': 0,
        'success': False,
        'timeout_reached': False,
        'monitoring_duration_seconds': 0.0,
        'trade_snapshots': []
    }
    
    end_time = start_time + timeout
    
    while time.time() < end_time:
        current_trades = helper.get_open_trades_count()
        
        if current_trades is not None:
            trades_increment = current_trades - initial_trades
            
            # Take snapshot
            monitoring_result['trade_snapshots'].append({
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                'trades_count': current_trades,
                'increment': trades_increment
            })
            
            if trades_increment >= expected_trades:
                monitoring_result['final_trades_count'] = current_trades
                monitoring_result['trades_increment'] = trades_increment
                monitoring_result['success'] = True
                break
        
        time.sleep(1)  # Check every second
    
    if not monitoring_result['success']:
        monitoring_result['timeout_reached'] = True
        final_trades = helper.get_open_trades_count()
        monitoring_result['final_trades_count'] = final_trades
        if final_trades is not None:
            monitoring_result['trades_increment'] = final_trades - initial_trades
    
    monitoring_result['monitoring_duration_seconds'] = time.time() - start_time
    
    return monitoring_result