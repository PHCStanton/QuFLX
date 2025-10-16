#!/usr/bin/env python3
"""
Real-time Trading Data Streaming Server for GUI
Connects to Chrome (port 9222) to intercept PocketOption WebSocket data
and streams it to the React frontend via Socket.IO
"""

# Import eventlet and apply monkey patching FIRST (before any other imports)
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
import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add paths for imports
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))
gui_dir = root_dir / 'gui' / 'Data-Visualizer-React'
sys.path.insert(0, str(gui_dir))
capabilities_dir = root_dir / 'capabilities'
sys.path.insert(0, str(capabilities_dir))
scripts_dir = root_dir / 'scripts' / 'custom_sessions'
sys.path.insert(0, str(scripts_dir))

from strategies.quantum_flux_strategy import QuantumFluxStrategy
from data_loader import DataLoader, BacktestEngine  # type: ignore

# Import Chrome interception logic from capabilities
from data_streaming import RealtimeDataStreaming  # type: ignore
from base import Ctx  # type: ignore

# Import persistence manager
from stream_persistence import StreamPersistenceManager  # type: ignore

# Import indicator adapter for modular indicator calculations
from strategies.indicator_adapter import get_indicator_adapter  # type: ignore

app = Flask(__name__)
CORS(app)
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode='eventlet',
    ping_timeout=30,
    ping_interval=10
)

# Global state for Chrome session and streaming
chrome_driver = None
streaming_active = False
current_asset = "EURUSD_OTC"

# Create data streaming capability instance to reuse its Chrome interception logic
data_streamer = RealtimeDataStreaming()
capability_ctx = None  # Will be initialized when Chrome connects
period = 60  # 1 minute candles by default

# Data persistence (optional, configured via --collect-stream argument)
persistence_manager: Optional[StreamPersistenceManager] = None
collect_stream_mode = "none"  # none, tick, candle, both
last_closed_candle_index: Dict[str, int] = {}  # Track last written closed candle per asset

# Reconnection tracking
chrome_reconnection_attempts = 0
last_reconnection_time = None
backend_initialized = False  # Track if backend has been initialized with first client
chrome_reconnect_enabled = False  # Only reconnect when clients need Chrome (Platform mode)

# ========================================
# Chrome Connection Functions
# ========================================

def attach_to_chrome(verbose=True):
    """
    Attach to existing Chrome instance started with --remote-debugging-port=9222.
    Returns a selenium webdriver.Chrome instance or None on failure.
    """
    import socket
    
    # Quick check if port 9222 is listening
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', 9222))
        sock.close()
        
        if result != 0:
            if verbose:
                print("[Chrome] ✗ Port 9222 not available")
                print("[Chrome] Start Chrome with: chrome --remote-debugging-port=9222 --user-data-dir=/path/to/profile")
            return None
    except Exception:
        return None
    
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

# Note: WebSocket decoding and data processing reuse capability methods
# _decode_and_parse_payload, _process_realtime_update, _process_chart_settings

# ========================================
# Data Processing Functions (delegating to capability)
# ========================================

def extract_candle_for_emit(asset: str) -> Optional[Dict]:
    """
    Extract latest formed candle from capability's candle data for Socket.IO emission.
    This emits OHLC candles instead of ticks, eliminating duplicate candle formation.
    Uses capability's public API instead of direct state access.
    NOTE: Candle persistence is now handled in stream_from_chrome() directly.
    """
    global data_streamer
    
    try:
        # Use capability's public API method instead of accessing CANDLES directly
        latest_candle = data_streamer.get_latest_candle(asset)
        
        if latest_candle:
            timestamp, open_price, close_price, high_price, low_price = latest_candle
            
            return {
                'asset': asset,
                'timestamp': timestamp,  # Unix timestamp in seconds
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': 0,
                'date': datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
            }
    
    except Exception as e:
        print(f"❌ Error extracting candle: {e}")
    
    return None

def reset_backend_state():
    """
    Reset backend streaming state and clear caches.
    Called on reconnection to ensure clean state.
    """
    global data_streamer, streaming_active, last_closed_candle_index
    
    print("[Reconnection] Resetting backend state and clearing caches...")
    
    # Reset streaming state
    streaming_active = False
    
    # Clear candle tracking for persistence
    last_closed_candle_index.clear()
    
    # Reset capability state (clear candle buffers, asset tracking, etc.)
    data_streamer._reset_stream_state(inputs={'period': period})
    
    print("[Reconnection] ✓ Backend state reset complete")

def monitor_chrome_status():
    """
    Background thread to monitor Chrome connection status and emit updates to clients.
    Only attempts automatic reconnection when chrome_reconnect_enabled is True (Platform mode active).
    """
    global chrome_driver, chrome_reconnection_attempts, last_reconnection_time, chrome_reconnect_enabled
    last_status = None
    
    while True:
        try:
            current_status = "connected" if chrome_driver else "not connected"
            
            # Check if Chrome is still responsive
            if chrome_driver:
                try:
                    _ = chrome_driver.current_url
                    chrome_reconnection_attempts = 0  # Reset counter on successful check
                except Exception:
                    print("[Monitor] Chrome connection lost - marking as disconnected")
                    current_status = "not connected"
                    chrome_driver = None
            
            # Attempt Chrome reconnection ONLY if enabled (max 3 attempts per minute)
            backoff_delay = 5  # Default monitoring interval
            
            if not chrome_driver and chrome_reconnect_enabled:
                should_reconnect = False
                
                if last_reconnection_time is None:
                    should_reconnect = True
                elif (datetime.now() - last_reconnection_time).total_seconds() > 60:
                    # Reset attempts after 1 minute
                    chrome_reconnection_attempts = 0
                    should_reconnect = True
                elif chrome_reconnection_attempts < 3:
                    should_reconnect = True
                
                if should_reconnect:
                    chrome_reconnection_attempts += 1
                    last_reconnection_time = datetime.now()
                    print(f"[Reconnection] Attempting Chrome reconnection (attempt {chrome_reconnection_attempts}/3)...")
                    
                    new_driver = attach_to_chrome(verbose=False)
                    if new_driver:
                        chrome_driver = new_driver
                        current_status = "connected"
                        print(f"[Reconnection] ✓ Chrome reconnected successfully!")
                        
                        # Emit reconnection success event
                        socketio.emit('chrome_reconnected', {
                            'timestamp': datetime.now().isoformat(),
                            'attempt': chrome_reconnection_attempts
                        })
                    else:
                        # Exponential backoff for failed attempts: 5s, 10s, 20s
                        backoff_delays = {1: 5, 2: 10, 3: 20}
                        backoff_delay = backoff_delays.get(chrome_reconnection_attempts, 5)
                        if backoff_delay > 5:
                            print(f"[Reconnection] Waiting {backoff_delay}s before next attempt (exponential backoff)...")
            
            # Emit status update if changed
            if current_status != last_status:
                socketio.emit('connection_status', {
                    'status': 'connected',
                    'chrome': current_status,
                    'timestamp': datetime.now().isoformat()
                })
                last_status = current_status
            
            time.sleep(backoff_delay)  # Exponential backoff or default 5s interval
        except Exception as e:
            print(f"[Monitor] Error checking Chrome status: {e}")
            time.sleep(5)

def stream_from_chrome():
    """
    Background thread to capture WebSocket data from Chrome.
    Fully delegates to RealtimeDataStreaming capability's logic.
    """
    global chrome_driver, streaming_active, data_streamer, capability_ctx, current_asset
    
    if not chrome_driver:
        print("[Stream] Chrome not connected. Attempting to connect...")
        chrome_driver = attach_to_chrome()
        if not chrome_driver:
            print("[Stream] Failed to connect to Chrome. Streaming disabled.")
            return
    
    # Initialize capability context
    capability_ctx = Ctx(driver=chrome_driver, artifacts_root=None, debug=False, dry_run=False, verbose=True)
    
    print("[Stream] Starting WebSocket capture from Chrome...")
    processed_messages = set()
    
    while True:
        if streaming_active:
            try:
                # Check if Chrome is still connected before accessing logs
                if not chrome_driver:
                    print("[Stream] Chrome disconnected during streaming - stopping stream")
                    streaming_active = False
                    socketio.emit('stream_error', {
                        'error': 'Chrome disconnected',
                        'timestamp': datetime.now().isoformat()
                    })
                    continue
                
                # Get performance logs (contains WebSocket frames)
                logs = chrome_driver.get_log('performance')
                
                for log_entry in logs:
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
                            # Use capability's decode method
                            payload = data_streamer._decode_and_parse_payload(payload_data)
                            
                            if payload:
                                # Delegate chart settings processing to capability
                                if 'updateCharts' in str(payload) or 'chartPeriod' in str(payload):
                                    data_streamer._process_chart_settings(payload, capability_ctx)
                                
                                # Delegate realtime data processing to capability
                                data_streamer._process_realtime_update(payload, capability_ctx)
                                
                                # CSV Persistence: Save tick and candle data if enabled
                                # This must happen AFTER _process_realtime_update() processes the data
                                if persistence_manager and collect_stream_mode != 'none':
                                    current_focused_asset = data_streamer.get_current_asset()
                                    if current_focused_asset:
                                        # Extract tick data from payload for persistence
                                        try:
                                            tick_asset = None
                                            tick_value = None
                                            tick_timestamp = None
                                            
                                            # Parse tick data from payload (same logic as _process_realtime_update)
                                            if isinstance(payload, list) and len(payload) > 0:
                                                if isinstance(payload[0], list) and len(payload[0]) >= 3:
                                                    tick_asset = payload[0][0]
                                                    tick_timestamp = int(float(payload[0][1]))
                                                    tick_value = payload[0][2]
                                                else:
                                                    tick_value = payload[-1] if isinstance(payload[-1], (int, float)) else None
                                                    tick_timestamp = int(time.time())
                                                    tick_asset = current_focused_asset
                                            elif isinstance(payload, dict):
                                                tick_asset = payload.get('asset') or payload.get('symbol') or current_focused_asset
                                                tick_value = payload.get('quote') or payload.get('price') or payload.get('value')
                                                tick_timestamp = payload.get('timestamp', int(time.time()))
                                                if isinstance(tick_timestamp, str):
                                                    tick_timestamp = int(float(tick_timestamp))
                                            else:
                                                tick_value = float(payload) if isinstance(payload, (int, float, str)) else None
                                                tick_timestamp = int(time.time())
                                                tick_asset = current_focused_asset
                                            
                                            # Persist tick data if enabled and we have valid data
                                            if tick_asset and tick_value is not None and tick_timestamp and collect_stream_mode in ['tick', 'both']:
                                                timestamp_str = datetime.fromtimestamp(tick_timestamp, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                                                persistence_manager.add_tick(tick_asset, timestamp_str, tick_value)
                                            
                                            # Persist candle data if enabled
                                            if tick_asset and collect_stream_mode in ['candle', 'both']:
                                                candles = data_streamer.get_all_candles(tick_asset)
                                                # Save all closed candles (all except the last forming one)
                                                if candles and len(candles) >= 2:
                                                    closed_upto = len(candles) - 2
                                                    last_written = last_closed_candle_index.get(tick_asset, -1)
                                                    
                                                    if closed_upto > last_written:
                                                        # Determine timeframe from capability's PERIOD with safe fallback
                                                        try:
                                                            period = getattr(data_streamer, 'PERIOD', 60)  # Default 60 seconds (1 minute)
                                                            tfm = max(1, int(period // 60))  # Ensure minimum 1 minute
                                                        except (TypeError, ValueError, AttributeError) as e:
                                                            print(f"[Persistence] Invalid PERIOD value, using 1m default: {e}")
                                                            tfm = 1
                                                        
                                                        # Write newly closed candles
                                                        for i in range(last_written + 1, closed_upto + 1):
                                                            c = candles[i]
                                                            persistence_manager.add_candle(
                                                                asset=tick_asset,
                                                                timeframe_minutes=tfm,
                                                                candle_ts=c[0],
                                                                open_price=c[1],
                                                                close_price=c[2],
                                                                high_price=c[3],
                                                                low_price=c[4]
                                                            )
                                                        
                                                        last_closed_candle_index[tick_asset] = closed_upto
                                        
                                        except Exception as e:
                                            print(f"[Persistence] Error saving data: {e}")
                                
                                # Extract processed candle and emit to frontend
                                # Use capability API method to get current asset
                                current_focused_asset = data_streamer.get_current_asset()
                                if current_focused_asset:
                                    candle_data = extract_candle_for_emit(current_focused_asset)
                                    if candle_data:
                                        socketio.emit('candle_update', candle_data)
                
                if len(processed_messages) > 10000:
                    processed_messages.clear()
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"[Stream] Error: {e}")
                # Check if error is Chrome-related
                if "chrome" in str(e).lower() or "driver" in str(e).lower():
                    print("[Stream] Chrome connection error detected - stopping stream")
                    streaming_active = False
                    socketio.emit('stream_error', {
                        'error': f'Chrome error: {str(e)}',
                        'timestamp': datetime.now().isoformat()
                    })
                time.sleep(1)
        else:
            time.sleep(0.5)

# Note: Timeframe detection is now fully handled by data_streamer._process_chart_settings
# No separate detect_timeframe function needed - delegated to capability

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
    """Handle client connection and detect reconnections"""
    global backend_initialized
    
    chrome_status = "connected" if chrome_driver else "not connected"
    
    # Detect if this is a reconnection (backend was previously initialized)
    is_reconnection = backend_initialized
    
    if is_reconnection:
        print(f"[Socket.IO] Client reconnected. Chrome: {chrome_status}")
        # Reset backend state on client reconnection
        reset_backend_state()
        # Emit reconnection event to client
        emit('backend_reconnected', {
            'timestamp': datetime.now().isoformat(),
            'chrome_status': chrome_status
        })
    else:
        print(f"[Socket.IO] Client connected. Chrome: {chrome_status}")
        backend_initialized = True
    
    emit('connection_status', {
        'status': 'connected',
        'chrome': chrome_status,
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    global streaming_active
    
    print(f"[Socket.IO] Client disconnected")
    
    # Stop streaming on client disconnect
    if streaming_active:
        streaming_active = False
        data_streamer.release_asset_focus()
        data_streamer.unlock_timeframe()
        print(f"[Socket.IO] Stream stopped due to client disconnect")

@socketio.on('start_stream')
def handle_start_stream(data):
    """Start streaming real-time data"""
    global current_asset, streaming_active, data_streamer, chrome_reconnect_enabled
    
    # Enable Chrome reconnection since Platform mode is active
    chrome_reconnect_enabled = True
    
    # Check if Chrome is connected
    if not chrome_driver:
        emit('stream_error', {
            'error': 'Chrome not connected',
            'timestamp': datetime.now().isoformat()
        })
        return
    
    if data and 'asset' in data:
        current_asset = data['asset']
        # Use capability API methods instead of direct state manipulation
        data_streamer.set_asset_focus(current_asset)
        data_streamer.set_timeframe(minutes=1, lock=True)
    
    streaming_active = True
    
    print(f"[Stream] Started for {current_asset}")
    emit('stream_started', {
        'asset': current_asset,
        'timestamp': datetime.now().isoformat()
    })
    
    # Stage 1: Seed chart with historical CSV data FIRST, then start live stream
    # This provides context for seamless transition from history to real-time
    
    # Try to load historical candles from CSV files first
    historical_candles_csv = []
    try:
        import pandas as pd
        from pathlib import Path
        
        # Search for CSV files matching the asset (1m timeframe)
        data_collect_dir = Path('data/data_output/assets_data/data_collect/1M_candle_data')
        if data_collect_dir.exists():
            # Normalize asset name for file matching (EURUSD_OTC -> EURUSD_otc)
            asset_normalized = current_asset.replace('_', '').lower()
            matching_files = []
            
            for csv_file in data_collect_dir.glob('*.csv'):
                # Check if filename contains the asset name
                if asset_normalized in csv_file.stem.lower().replace('_', ''):
                    matching_files.append(csv_file)
            
            if matching_files:
                # Use the most recent file
                latest_file = max(matching_files, key=lambda f: f.stat().st_mtime)
                print(f"[Stream] Loading historical CSV data from {latest_file.name}")
                
                df = pd.read_csv(latest_file)
                # Take last 200 candles for context
                df = df.tail(200)
                
                for _, row in df.iterrows():
                    # Safely convert row values with defaults
                    timestamp = int(row['timestamp'])
                    historical_candles_csv.append({
                        'asset': current_asset,
                        'timestamp': timestamp,
                        'open': float(row['open']),
                        'high': float(row['high']),
                        'low': float(row['low']),
                        'close': float(row['close']),
                        'volume': int(row.get('volume', 0) or 0),  # Safely handle None values
                        'date': datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
                    })
                
                print(f"[Stream] Loaded {len(historical_candles_csv)} historical candles from CSV")
    except Exception as e:
        print(f"[Stream] Could not load CSV historical data: {e}")
    
    # If CSV data available, emit it first
    if historical_candles_csv:
        print(f"[Stream] Seeding chart with {len(historical_candles_csv)} historical candles")
        emit('historical_candles_loaded', {
            'asset': current_asset,
            'candles': historical_candles_csv,
            'count': len(historical_candles_csv),
            'source': 'csv',
            'timestamp': datetime.now().isoformat()
        })
    else:
        # Fallback: Try WebSocket historical candles (usually empty at stream start)
        historical_candles_ws = data_streamer.get_all_candles(current_asset)
        if historical_candles_ws and len(historical_candles_ws) > 0:
            formatted_candles = []
            for candle in historical_candles_ws:
                timestamp, open_price, close_price, high_price, low_price = candle
                formatted_candles.append({
                    'asset': current_asset,
                    'timestamp': timestamp,
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'close': close_price,
                    'volume': 0,
                    'date': datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
                })
            
            print(f"[Stream] Emitting {len(formatted_candles)} WebSocket historical candles")
            emit('historical_candles_loaded', {
                'asset': current_asset,
                'candles': formatted_candles,
                'count': len(formatted_candles),
                'source': 'websocket',
                'timestamp': datetime.now().isoformat()
            })
        else:
            print(f"[Stream] No historical data available for {current_asset}")

@socketio.on('stop_stream')
def handle_stop_stream():
    """Stop streaming data"""
    global streaming_active

    streaming_active = False
    print(f"[Stream] Stopped")
    emit('stream_stopped', {'timestamp': datetime.now().isoformat()})
    # Release asset focus when stream stops using API method
    data_streamer.release_asset_focus()
    data_streamer.unlock_timeframe()

@socketio.on('change_asset')
def handle_change_asset(data):
    """Change the streaming asset"""
    global current_asset, data_streamer

    if data and 'asset' in data:
        current_asset = data['asset']
        # Use API method to change asset focus
        data_streamer.set_asset_focus(current_asset)
        
        print(f"[Stream] Asset changed to {current_asset}")
        emit('asset_changed', {
            'asset': current_asset,
            'timestamp': datetime.now().isoformat()
        })

@socketio.on('detect_asset')
def handle_detect_asset():
    """Detect current asset from PocketOption via capability"""
    global chrome_driver, data_streamer, chrome_reconnect_enabled
    
    # Enable Chrome reconnection since Platform mode is active
    chrome_reconnect_enabled = True
    
    if not chrome_driver:
        print("[DetectAsset] Chrome not connected")
        emit('asset_detection_failed', {
            'error': 'Chrome not connected',
            'timestamp': datetime.now().isoformat()
        })
        return
    
    try:
        # Actively detect asset from PocketOption UI
        detected_asset = data_streamer.detect_asset_from_ui(chrome_driver)
        
        if detected_asset:
            print(f"[DetectAsset] Detected asset: {detected_asset}")
            emit('asset_detected', {
                'asset': detected_asset,
                'timestamp': datetime.now().isoformat()
            })
        else:
            print("[DetectAsset] No asset currently selected in PocketOption")
            emit('asset_detection_failed', {
                'error': 'No asset selected in PocketOption. Please click on an asset in the trading platform.',
                'timestamp': datetime.now().isoformat()
            })
    except Exception as e:
        print(f"[DetectAsset] Error detecting asset: {e}")
        emit('asset_detection_failed', {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })

@socketio.on('store_csv_candles')
def handle_store_csv_candles(data):
    """
    Store CSV candle data in backend for indicator calculation.
    Converts frontend candle format to backend storage format.
    """
    global data_streamer
    
    try:
        asset = data.get('asset')
        candles_data = data.get('candles', [])
        
        if not asset:
            emit('csv_storage_error', {'error': 'No asset specified'})
            return
        
        if not candles_data:
            emit('csv_storage_error', {'error': 'No candle data provided'})
            return
        
        # Convert frontend format to backend format
        # Frontend: {timestamp, date, open, close, high, low, volume, symbol}
        # Backend: [timestamp, open, close, high, low]
        backend_candles = []
        for candle in candles_data:
            backend_candles.append([
                candle['timestamp'],
                candle['open'],
                candle['close'],
                candle['high'],
                candle['low']
            ])
        
        # Store in backend (same structure as live streaming)
        data_streamer.CANDLES[asset] = backend_candles
        
        print(f"[CSV Storage] Stored {len(backend_candles)} candles for {asset}")
        emit('csv_storage_success', {
            'asset': asset,
            'candle_count': len(backend_candles),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"[CSV Storage] Exception: {e}")
        emit('csv_storage_error', {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })

@socketio.on('calculate_indicators')
def handle_calculate_indicators(data):
    """
    Calculate technical indicators for given asset and configuration.
    Uses modular TechnicalIndicatorsPipeline via IndicatorAdapter.
    
    Supports instance-based format (recommended):
    {
        'asset': 'EURUSD_OTC',
        'instances': {
            'SMA-20': {'type': 'sma', 'params': {'period': 20}},
            'RSI-14': {'type': 'rsi', 'params': {'period': 14}},
            'BB-20': {'type': 'bollinger', 'params': {'period': 20, 'std_dev': 2}}
        }
    }
    
    Now supports all 13+ indicators via TechnicalIndicatorsPipeline:
    - Trend: SMA, EMA, WMA, MACD, Bollinger Bands
    - Momentum: RSI, Stochastic, Williams %R, ROC, Schaff TC, DeMarker, CCI
    - Volatility: ATR, Bollinger Bands
    - Custom: SuperTrend
    """
    global data_streamer
    
    try:
        asset = data.get('asset')
        instances = data.get('instances')
        
        if not asset:
            emit('indicators_error', {
                'error': 'No asset specified',
                'timestamp': datetime.now().isoformat()
            })
            return
        
        # Get candles from data_streamer
        if asset not in data_streamer.CANDLES or not data_streamer.CANDLES[asset]:
            emit('indicators_error', {
                'error': f'No candle data available for {asset}',
                'timestamp': datetime.now().isoformat()
            })
            return
        
        candles = data_streamer.CANDLES[asset]
        
        # Handle empty instances (no indicators selected)
        if not instances:
            empty_result = {
                "asset": asset,
                "indicators": {},
                "series": {},
                "signals": {},
                "timestamp": datetime.now().isoformat()
            }
            print(f"[Indicators] No indicators specified for {asset} - sending empty result")
            emit('indicators_calculated', empty_result)
            return
        
        # Use IndicatorAdapter for modular calculation
        print(f"[Indicators] Processing {len(instances)} indicator instances for {asset} using TechnicalIndicatorsPipeline")
        
        # Get the actual timeframe period from data_streamer
        timeframe_seconds = data_streamer.PERIOD if hasattr(data_streamer, 'PERIOD') and data_streamer.PERIOD else 60
        
        adapter = get_indicator_adapter()
        result = adapter.calculate_indicators_for_instances(asset, candles, instances, timeframe_seconds)
        
        if 'error' in result:
            print(f"[Indicators] Error: {result['error']}")
            emit('indicators_error', result)
        else:
            print(f"[Indicators] ✓ Calculated {len(result.get('indicators', {}))} indicator instances for {asset}")
            emit('indicators_calculated', result)
            
    except Exception as e:
        print(f"[Indicators] Exception: {e}")
        import traceback
        traceback.print_exc()
        emit('indicators_error', {
            'error': str(e),
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
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='QuantumFlux Trading Platform - GUI Backend Server')
    parser.add_argument(
        '--collect-stream',
        choices=['tick', 'candle', 'both', 'none'],
        default='none',
        help='Enable optional data collection: tick=ticks only, candle=candles only, both=both, none=no collection (default: none)'
    )
    parser.add_argument(
        '--candle-chunk-size',
        type=int,
        default=100,
        help='Number of candles per CSV file chunk (default: 100)'
    )
    parser.add_argument(
        '--tick-chunk-size',
        type=int,
        default=1000,
        help='Number of ticks per CSV file chunk (default: 1000)'
    )
    
    args = parser.parse_args()
    collect_stream_mode = args.collect_stream
    
    print("=" * 60)
    print("QuantumFlux Trading Platform - GUI Backend Server")
    print("=" * 60)
    
    # Initialize persistence manager if collection is enabled
    if collect_stream_mode != 'none':
        candle_dir = root_dir / "data" / "data_output" / "assets_data" / "realtime_stream" / "1M_candle_data"
        tick_dir = root_dir / "data" / "data_output" / "assets_data" / "realtime_stream" / "1M_tick_data"
        
        persistence_manager = StreamPersistenceManager(
            candle_dir=candle_dir,
            tick_dir=tick_dir,
            candle_chunk_size=args.candle_chunk_size,
            tick_chunk_size=args.tick_chunk_size,
        )
        print(f"\n[Persistence] ✓ Stream collection enabled: {collect_stream_mode}")
        print(f"[Persistence]   Candle output: {candle_dir}")
        print(f"[Persistence]   Tick output: {tick_dir}")
        print(f"[Persistence]   Chunk sizes: candles={args.candle_chunk_size}, ticks={args.tick_chunk_size}")
        
        # NOTE: CSV persistence is now handled directly in stream_from_chrome() 
        # This patch is kept as a fallback for any code paths that use _output_streaming_data
        # (e.g., if data_streamer is used via stream_continuous() instead of stream_from_chrome())
        if collect_stream_mode in ['tick', 'both']:
            # Save reference to original bound method
            original_output = data_streamer._output_streaming_data
            
            def patched_output(self, asset, current_value, timestamp_str, change_indicator):
                # Keep original console behavior
                try:
                    original_output(asset, current_value, timestamp_str, change_indicator)
                except Exception:
                    pass
                
                # Persist tick data (fallback path)
                try:
                    if persistence_manager:
                        persistence_manager.add_tick(asset, timestamp_str, current_value)
                except Exception as e:
                    print(f"[Persistence] Error saving tick: {e}")
            
            # Bind the patched method
            import types
            data_streamer._output_streaming_data = types.MethodType(patched_output, data_streamer)
            print(f"[Persistence] ✓ Tick persistence fallback hook installed")
    else:
        print("\n[Persistence] Stream collection disabled (use --collect-stream to enable)")
    
    # Try to connect to Chrome on startup
    print("\n[Startup] Attempting to connect to Chrome...")
    chrome_driver = attach_to_chrome(verbose=True)
    
    # Start Chrome status monitor thread (always running)
    monitor_thread = threading.Thread(target=monitor_chrome_status, daemon=True)
    monitor_thread.start()
    print("[Startup] ✓ Chrome status monitor started")
    
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
        allow_unsafe_werkzeug=True,
        log_output=False
    )
