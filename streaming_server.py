#!/usr/bin/env python3
"""
Real-time Trading Data Streaming Server for GUI
Connects to Chrome (port 9222) to intercept PocketOption WebSocket data
and streams it to the React frontend via Socket.IO
"""

import eventlet
eventlet.monkey_patch()

from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json
import time
import base64
import re
from datetime import datetime, timezone
import threading
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add paths for imports
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))
gui_dir = root_dir / 'gui' / 'Data-Visualizer-React'
sys.path.insert(0, str(gui_dir))

from strategies.quantum_flux_strategy import QuantumFluxStrategy
from data_loader import DataLoader, BacktestEngine

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Global state for Chrome session and streaming
chrome_driver = None
streaming_active = False
current_asset = "EURUSD_OTC"
candles_data = {}  # asset -> [[timestamp, open, close, high, low], ...]
period = 60  # 1 minute candles by default
session_authenticated = False
session_timeframe_detected = False

# ========================================
# Chrome Connection Functions
# ========================================

def attach_to_chrome(verbose=True):
    """
    Attach to existing Chrome instance started with --remote-debugging-port=9222.
    Returns a selenium webdriver.Chrome instance or None on failure.
    """
    try:
        if verbose:
            print("[Chrome] Connecting to Chrome at 127.0.0.1:9222...")
        
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        # Enable performance log to capture WebSocket frames
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        
        # Compatibility flags
        options.add_argument("--ignore-ssl-errors")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-popup-blocking")
        
        driver = webdriver.Chrome(options=options)
        
        if verbose:
            print(f"[Chrome] ✓ Connected! Current URL: {driver.current_url}")
        
        return driver
        
    except Exception as e:
        print(f"[Chrome] ✗ Failed to connect: {e}")
        print("[Chrome] Make sure Chrome is running with: chrome --remote-debugging-port=9222 --user-data-dir=/path/to/profile")
        return None

# ========================================
# WebSocket Frame Decoding Functions
# ========================================

def decode_websocket_payload(encoded_payload: str) -> Optional[Any]:
    """Decode base64 WebSocket payload and parse as JSON."""
    try:
        decoded = base64.b64decode(encoded_payload).decode('utf-8')
        
        # Handle Socket.IO prefixes
        decoded = handle_socketio_format(decoded)
        
        # Parse JSON
        return json.loads(decoded)
        
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as e:
        print(f"⚠️ Payload decode error: {e}")
        return None

def handle_socketio_format(payload: str) -> str:
    """Handle Socket.IO event arrays like 42["event", data]."""
    if not payload or not payload[0].isdigit():
        return payload
    
    # Remove numeric prefix
    match = re.match(r'^\d+', payload)
    if match:
        payload = payload[match.end():]
    
    # Handle event arrays
    if payload.startswith('["') and ']' in payload:
        event_match = re.match(r'\["([^"]+)"(?:,\s*(.+))?\]', payload)
        if event_match:
            event_name = event_match.group(1)
            data_str = event_match.group(2) if event_match.group(2) else '{}'
            try:
                data = json.loads(data_str) if data_str else {}
                return json.dumps({"event": event_name, "data": data})
            except json.JSONDecodeError:
                pass
    
    return payload

# ========================================
# Data Processing Functions
# ========================================

def process_realtime_tick(data: Any) -> Optional[Dict]:
    """Process real-time tick update from PocketOption."""
    global current_asset, candles_data, period
    
    try:
        asset = None
        price = None
        timestamp = None
        
        # Parse different payload formats
        if isinstance(data, list) and len(data) > 0:
            if isinstance(data[0], list) and len(data[0]) >= 3:
                # Format: [[asset, timestamp, price], ...]
                asset = data[0][0]
                timestamp = int(float(data[0][1]))
                price = data[0][2]
            else:
                price = data[-1] if isinstance(data[-1], (int, float)) else None
                timestamp = int(time.time())
                asset = current_asset
        
        elif isinstance(data, dict):
            # Format: {"asset": "EURUSD", "price": 1.1234, "timestamp": 1234567890}
            asset = data.get('asset') or data.get('symbol') or current_asset
            price = data.get('quote') or data.get('price') or data.get('value')
            timestamp = data.get('timestamp', int(time.time()))
            if isinstance(timestamp, str):
                timestamp = int(float(timestamp))
        
        else:
            # Scalar value
            price = float(data) if isinstance(data, (int, float, str)) else None
            timestamp = int(time.time())
            asset = current_asset
        
        if asset and price is not None and timestamp is not None:
            # Update candles
            if asset not in candles_data:
                candles_data[asset] = []
            
            candles = candles_data[asset]
            
            if not candles:
                # First candle
                candles.append([timestamp, price, price, price, price])
            else:
                # Update current candle
                candles[-1][2] = price  # close
                candles[-1][3] = max(candles[-1][3], price)  # high
                candles[-1][4] = min(candles[-1][4], price)  # low
                
                # Create new candle if period boundary crossed
                if period and (timestamp - candles[-1][0]) >= period:
                    candles.append([timestamp, price, price, price, price])
            
            return {
                'asset': asset,
                'price': price,
                'timestamp': timestamp * 1000,  # Convert to milliseconds for frontend
                'volume': 0,
                'time_string': datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
            }
    
    except Exception as e:
        print(f"❌ Error processing tick: {e}")
    
    return None

def stream_from_chrome():
    """Background thread to capture WebSocket data from Chrome."""
    global chrome_driver, streaming_active, session_authenticated, session_timeframe_detected
    
    if not chrome_driver:
        print("[Stream] Chrome not connected. Attempting to connect...")
        chrome_driver = attach_to_chrome()
        if not chrome_driver:
            print("[Stream] Failed to connect to Chrome. Streaming disabled.")
            return
    
    print("[Stream] Starting WebSocket capture from Chrome...")
    processed_messages = set()
    
    while True:
        if streaming_active:
            try:
                # Get performance logs (contains WebSocket frames)
                logs = chrome_driver.get_log('performance')
                
                for log_entry in logs:
                    # Create unique message ID
                    msg_id = f"{log_entry.get('timestamp', 0)}_{hash(log_entry.get('message', ''))}"
                    if msg_id in processed_messages:
                        continue
                    
                    processed_messages.add(msg_id)
                    
                    # Parse log entry
                    message = json.loads(log_entry['message'])['message']
                    response = message.get('params', {}).get('response', {})
                    
                    # Look for WebSocket frames (opcode 2 = binary frame)
                    if response.get('opcode', 0) == 2:
                        payload_data = response.get('payloadData')
                        if payload_data:
                            # Decode and process
                            payload = decode_websocket_payload(payload_data)
                            
                            if payload:
                                # Check for chart settings to detect timeframe
                                if 'updateCharts' in str(payload) or 'chartPeriod' in str(payload):
                                    detect_timeframe(payload)
                                
                                # Process as real-time tick data
                                tick_data = process_realtime_tick(payload)
                                
                                if tick_data:
                                    # Emit to frontend
                                    socketio.emit('tick_update', tick_data)
                
                # Keep processed messages set from growing indefinitely
                if len(processed_messages) > 10000:
                    processed_messages.clear()
                
                time.sleep(0.1)  # 10 checks per second
                
            except Exception as e:
                print(f"[Stream] Error: {e}")
                time.sleep(1)
        else:
            time.sleep(0.5)

def detect_timeframe(payload: Any):
    """Detect and set the timeframe from chart settings."""
    global period, session_timeframe_detected
    
    try:
        if isinstance(payload, dict):
            # Look for period/timeframe indicators
            settings = payload.get('settings', {})
            if isinstance(settings, str):
                settings = json.loads(settings)
            
            period_map = {
                1: 1, 2: 2, 3: 3, 4: 5, 5: 10, 6: 15, 7: 30, 8: 60, 9: 240, 10: 1440,
                '1m': 1, '5m': 5, '15m': 15, '30m': 30, '1h': 60, '4h': 240
            }
            
            chart_period = settings.get('chartPeriod') or settings.get('period')
            if chart_period:
                minutes = period_map.get(chart_period, 1)
                period = minutes * 60
                session_timeframe_detected = True
                print(f"⏱️ Timeframe detected: {minutes} minutes")
    
    except Exception as e:
        print(f"Error detecting timeframe: {e}")

# ========================================
# Flask REST API Endpoints (CSV serving, etc.)
# ========================================

@app.route('/health')
def health():
    """Health check endpoint"""
    chrome_status = "connected" if chrome_driver else "disconnected"
    return jsonify({
        "status": "healthy",
        "chrome": chrome_status,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/available-csv-files')
def get_available_csv_files():
    """Get list of all available CSV files, optionally filtered by timeframe"""
    import glob
    import os
    
    timeframe_filter = request.args.get('timeframe', None)
    
    files = []
    data_dir = root_dir / 'data' / 'data_output' / 'assets_data'
    
    # Map timeframe to directory names
    timeframe_dirs = {
        '1m': ['1M_candles', '1M_candles_utc'],
        '5m': ['5M_candles', '5M_candles_utc'],
        '15m': ['15M_candles', '15M_candles_utc'],
        '1h': ['1H_candles', '1H_candles_utc'],
        '4h': ['4H_candles', '4H_candles_utc'],
        'tick': ['0M_candles'],
    }
    
    # Build search paths
    search_paths = []
    if timeframe_filter and timeframe_filter in timeframe_dirs:
        for dir_name in timeframe_dirs[timeframe_filter]:
            search_paths.append(str(data_dir / 'data_collect' / dir_name / '*.csv'))
        
        if timeframe_filter == '1m':
            search_paths.extend([
                str(data_dir / 'realtime_stream' / '1M_candle_data' / '*.csv'),
                str(data_dir / 'realtime_stream' / '1M_tick_data' / '*.csv'),
            ])
    else:
        search_paths = [
            str(data_dir / 'realtime_stream' / '1M_candle_data' / '*.csv'),
            str(data_dir / 'realtime_stream' / '1M_tick_data' / '*.csv'),
            str(data_dir / 'data_collect' / '*_candles' / '*.csv'),
            str(data_dir / 'data_collect' / '*_candles_utc' / '*.csv'),
        ]
    
    for pattern in search_paths:
        for filepath in glob.glob(pattern):
            filename = os.path.basename(filepath)
            
            # Parse asset name
            parts = filename.split('_')
            if len(parts) >= 2:
                asset_parts = []
                for i, part in enumerate(parts):
                    if part in ['1m', '5m', '15m', '1h', '4h', '60m', 'otc'] or part.isdigit() or len(part) > 10:
                        break
                    asset_parts.append(part)
                
                if len(asset_parts) == 0:
                    asset_parts = [parts[0]]
                if len(parts) > 1 and 'otc' in parts[1].lower():
                    asset_parts.append('otc')
                
                asset = '_'.join(asset_parts).upper()
                
                # Determine timeframe from parent directory
                parent_dir = os.path.basename(os.path.dirname(filepath))
                timeframe = '1m'
                
                if '1M' in parent_dir or '1m' in parent_dir:
                    timeframe = '1m'
                elif '5M' in parent_dir or '5m' in parent_dir:
                    timeframe = '5m'
                elif '15M' in parent_dir or '15m' in parent_dir:
                    timeframe = '15m'
                elif '1H' in parent_dir or '1h' in parent_dir:
                    timeframe = '1h'
                elif '4H' in parent_dir or '4h' in parent_dir:
                    timeframe = '4h'
                elif '0M' in parent_dir or 'tick' in parent_dir.lower():
                    timeframe = 'tick'
                
                files.append({
                    'path': filepath,
                    'filename': filename,
                    'asset': asset,
                    'timeframe': timeframe,
                    'size': os.path.getsize(filepath)
                })
    
    return jsonify({'files': files, 'count': len(files)})

@app.route('/api/csv-data/<path:filename>')
def serve_csv_file(filename):
    """Serve CSV file content"""
    import os
    from flask import send_file
    
    data_dir = root_dir / 'data' / 'data_output' / 'assets_data'
    
    search_dirs = [
        data_dir / 'realtime_stream' / '1M_candle_data',
        data_dir / 'realtime_stream' / '1M_tick_data',
        data_dir / 'data_collect' / '1M_candles',
        data_dir / 'data_collect' / '5M_candles',
        data_dir / 'data_collect' / '15M_candles',
        data_dir / 'data_collect' / '1H_candles',
        data_dir / 'data_collect' / '4H_candles',
        data_dir / 'data_collect' / '0M_candles',
        data_dir / 'data_collect' / '1M_candles_utc',
        data_dir / 'data_collect' / '5M_candles_utc',
        data_dir / 'data_collect' / '15M_candles_utc',
    ]
    
    for search_dir in search_dirs:
        filepath = search_dir / filename
        if filepath.exists():
            return send_file(str(filepath), mimetype='text/csv')
    
    return jsonify({'error': 'File not found'}), 404

# ========================================
# Socket.IO Event Handlers
# ========================================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    chrome_status = "connected" if chrome_driver else "not connected"
    print(f"[Socket.IO] Client connected. Chrome: {chrome_status}")
    emit('connection_status', {
        'status': 'connected',
        'chrome': chrome_status,
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"[Socket.IO] Client disconnected")

@socketio.on('start_stream')
def handle_start_stream(data):
    """Start streaming real-time data"""
    global current_asset, streaming_active
    
    if data and 'asset' in data:
        current_asset = data['asset']
    
    streaming_active = True
    
    print(f"[Stream] Started for {current_asset}")
    emit('stream_started', {
        'asset': current_asset,
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('stop_stream')
def handle_stop_stream():
    """Stop streaming data"""
    global streaming_active
    
    streaming_active = False
    print(f"[Stream] Stopped")
    emit('stream_stopped', {'timestamp': datetime.now().isoformat()})

@socketio.on('change_asset')
def handle_change_asset(data):
    """Change the streaming asset"""
    global current_asset
    
    if data and 'asset' in data:
        current_asset = data['asset']
        print(f"[Stream] Asset changed to {current_asset}")
        emit('asset_changed', {
            'asset': current_asset,
            'timestamp': datetime.now().isoformat()
        })

# ========================================
# Backtest Handlers (from original)
# ========================================

@socketio.on('run_backtest')
def handle_run_backtest(data):
    """Run strategy backtest on historical data"""
    try:
        file_path = data.get('file_path')
        strategy_type = data.get('strategy', 'quantum_flux')
        
        if not file_path:
            emit('backtest_error', {'error': 'No file path provided'})
            return
        
        loader = DataLoader()
        df = loader.load_csv(file_path)
        candles = loader.df_to_candles(df)
        
        if strategy_type == 'quantum_flux':
            strategy = QuantumFluxStrategy()
        else:
            emit('backtest_error', {'error': f'Unknown strategy: {strategy_type}'})
            return
        
        engine = BacktestEngine(strategy)
        results = engine.run_backtest(candles)
        
        emit('backtest_complete', {
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        emit('backtest_error', {'error': str(e)})

# ========================================
# Main Entry Point
# ========================================

if __name__ == '__main__':
    print("=" * 60)
    print("QuantumFlux Trading Platform - GUI Backend Server")
    print("=" * 60)
    
    # Try to connect to Chrome on startup
    print("\n[Startup] Attempting to connect to Chrome...")
    chrome_driver = attach_to_chrome(verbose=True)
    
    if chrome_driver:
        print("[Startup] ✓ Chrome connected successfully")
        # Start background streaming thread
        stream_thread = threading.Thread(target=stream_from_chrome, daemon=True)
        stream_thread.start()
        print("[Startup] ✓ WebSocket streaming thread started")
    else:
        print("[Startup] ⚠️ Chrome not connected. Live streaming will be unavailable.")
        print("[Startup] To enable: Start Chrome with --remote-debugging-port=9222")
    
    print(f"\n[Startup] Starting server on http://0.0.0.0:3001")
    print("=" * 60)
    
    socketio.run(
        app,
        host='0.0.0.0',
        port=3001,
        debug=False,
        use_reloader=False,
        log_output=True,
        allow_unsafe_werkzeug=True
    )
