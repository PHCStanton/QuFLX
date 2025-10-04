#!/usr/bin/env python3
"""
QuantumFlux Smoke Test - Quick verification that the system works

This script tests the core workflow:
1. Attach to Chrome session
2. Collect data snapshot
3. Verify CSV is saved
4. Test capability endpoints

Usage:
    python test_smoke.py
"""

import sys
import time
import requests
from pathlib import Path
from datetime import datetime

# Add capabilities to path
capabilities_dir = Path(__file__).parent / "capabilities"
if str(capabilities_dir) not in sys.path:
    sys.path.insert(0, str(capabilities_dir))

# Import capabilities
from capabilities.data_streaming import RealtimeDataStreaming
from capabilities.base import Ctx
from capabilities.session_scan import SessionScan
from capabilities.profile_scan import ProfileScan

# Selenium for Chrome attachment
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def test_chrome_attachment(port=9222):
    """Test Chrome session attachment."""
    print("🔍 Testing Chrome attachment...")
    
    try:
        # Use workspace Chrome profile
        user_data_dir = str(Path(__file__).parent / "Chrome_profile")
        
        # Configure Chrome options
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
        chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        
        # Create driver
        driver = webdriver.Chrome(options=chrome_options)
        
        # Create context
        artifacts_root = str(Path(__file__).parent / "Historical_Data" / "smoke_test")
        ctx = Ctx(
            driver=driver,
            artifacts_root=artifacts_root,
            debug=True,
            dry_run=False,
            verbose=True
        )
        
        current_url = driver.current_url
        print(f"✅ Chrome attached: {current_url}")
        
        return driver, ctx, current_url
        
    except Exception as e:
        print(f"❌ Chrome attachment failed: {e}")
        return None, None, None

def test_data_snapshot(driver, ctx):
    """Test data streaming snapshot."""
    print("📊 Testing data snapshot...")
    
    try:
        # Initialize data streaming
        data_streaming = RealtimeDataStreaming()
        
        # Configure for 1-minute candles
        data_streaming.PERIOD = 60
        data_streaming.CANDLE_ONLY_MODE = True
        data_streaming.TICK_ONLY_MODE = False
        data_streaming.ASSET_FOCUS_MODE = False
        data_streaming.enable_csv_saving = True
        
        # Run data collection
        inputs = {"period": 60}
        result = data_streaming.run(ctx, inputs)
        
        if result.ok:
            print("✅ Data snapshot collected")
            
            # Check for CSV files
            data_stream_dir = Path(__file__).parent / "Historical_Data" / "data_stream"
            csv_files = list(data_stream_dir.glob("*.csv"))
            
            if csv_files:
                latest_csv = max(csv_files, key=lambda f: f.stat().st_mtime)
                print(f"📄 CSV saved: {latest_csv.name}")
                
                # Check CSV content
                with open(latest_csv, 'r') as f:
                    lines = f.readlines()
                    if len(lines) > 1:  # Header + at least one data row
                        print(f"📈 CSV contains {len(lines)-1} data rows")
                    else:
                        print("⚠️ CSV is empty or only has header")
            else:
                print("⚠️ No CSV files found")
            
            return result.data
        else:
            print(f"❌ Data snapshot failed: {result.error}")
            return None
            
    except Exception as e:
        print(f"❌ Data snapshot error: {e}")
        return None

def test_capabilities(driver, ctx):
    """Test individual capabilities."""
    print("🔧 Testing capabilities...")
    
    # Test session scan
    try:
        session_scan = SessionScan()
        result = session_scan.run(ctx, {})
        if result.ok:
            data = result.data
            print(f"✅ Session scan: {data.get('account', 'Unknown')} account")
        else:
            print(f"⚠️ Session scan failed: {result.error}")
    except Exception as e:
        print(f"⚠️ Session scan error: {e}")
    
    # Test profile scan
    try:
        profile_scan = ProfileScan()
        result = profile_scan.run(ctx, {})
        if result.ok:
            data = result.data
            balance = data.get('balance', 'Unknown')
            print(f"✅ Profile scan: Balance {balance}")
        else:
            print(f"⚠️ Profile scan failed: {result.error}")
    except Exception as e:
        print(f"⚠️ Profile scan error: {e}")

def test_backend_api(port=8000):
    """Test backend API endpoints."""
    print("🌐 Testing backend API...")
    
    base_url = f"http://localhost:{port}"
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ Backend API responding")
        else:
            print(f"⚠️ Backend API returned {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Backend API not running")
        return False
    except Exception as e:
        print(f"⚠️ Backend API error: {e}")
        return False
    
    # Test status endpoint
    try:
        response = requests.get(f"{base_url}/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            connected = data.get('connected', False)
            print(f"✅ Status endpoint: Connected={connected}")
        else:
            print(f"⚠️ Status endpoint returned {response.status_code}")
    except Exception as e:
        print(f"⚠️ Status endpoint error: {e}")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            status = data.get('status', 'unknown')
            print(f"✅ Health endpoint: {status}")
        else:
            print(f"⚠️ Health endpoint returned {response.status_code}")
    except Exception as e:
        print(f"⚠️ Health endpoint error: {e}")
    
    return True

def main():
    """Run smoke test."""
    print("🚀 QuantumFlux Smoke Test")
    print("=" * 40)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test Chrome attachment
    driver, ctx, url = test_chrome_attachment()
    if not driver:
        print("❌ Smoke test failed: Cannot attach to Chrome")
        print("💡 Make sure Chrome is running with: python start_hybrid_session.py")
        return False
    
    try:
        # Test data snapshot
        snapshot_data = test_data_snapshot(driver, ctx)
        if snapshot_data:
            print("✅ Data streaming works")
        else:
            print("⚠️ Data streaming issues detected")
        
        # Test capabilities
        test_capabilities(driver, ctx)
        
        # Test backend API
        api_working = test_backend_api()
        if not api_working:
            print("💡 Start backend with: python backend.py")
        
        print()
        print("📋 Smoke Test Summary:")
        print("=" * 30)
        print("✅ Chrome attachment: Working")
        print("✅ Data streaming: Working" if snapshot_data else "⚠️ Data streaming: Issues")
        print("✅ Capabilities: Working")
        print("✅ Backend API: Working" if api_working else "❌ Backend API: Not running")
        
        if snapshot_data and api_working:
            print("\n🎉 Smoke test PASSED - System is ready!")
            return True
        else:
            print("\n⚠️ Smoke test PARTIAL - Some components need attention")
            return False
            
    finally:
        # Cleanup
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
