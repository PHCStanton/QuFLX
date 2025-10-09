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
    Also handles candle persistence if enabled.
    """
    global data_streamer, persistence_manager, collect_stream_mode, last_closed_candle_index
    
    try:
        # Use capability's public API method instead of accessing CANDLES directly
        latest_candle = data_streamer.get_latest_candle(asset)
        
        if latest_candle:
            timestamp, open_price, close_price, high_price, low_price = latest_candle
            
            # Persist closed candles if enabled
            if persistence_manager and collect_stream_mode in ['candle', 'both']:
                try:
                    # Get all candles for this asset from capability
                    candles = data_streamer.CANDLES.get(asset, [])
                    if candles and len(candles) >= 2:
                        # Index of last closed candle (current forming candle is last)
                        closed_upto = len(candles) - 2
                        last_written = last_closed_candle_index.get(asset, -1)
                        
                        if closed_upto > last_written:
                            # Determine timeframe from capability's PERIOD
                            tfm = int(data_streamer.PERIOD // 60) if hasattr(data_streamer, 'PERIOD') and data_streamer.PERIOD else 1
                            if tfm < 1:
                                tfm = 1
                            
                            # Write newly closed candles
                            for i in range(last_written + 1, closed_upto + 1):
                                c = candles[i]
                                persistence_manager.add_candle(
                                    asset=asset,
                                    timeframe_minutes=tfm,
                                    candle_ts=c[0],
                                    open_price=c[1],
                                    close_price=c[2],
                                    high_price=c[3],
                                    low_price=c[4]
                                )
                            
                            last_closed_candle_index[asset] = closed_upto
                except Exception as e:
                    print(f"[Persistence] Error saving candle: {e}")
            
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

def monitor_chrome_status():
    """
    Background thread to monitor Chrome connection status and emit updates to clients.
    """
    global chrome_driver
    last_status = None
    
    while True:
        try:
            current_status = "connected" if chrome_driver else "not connected"
            
            # Check if Chrome is still responsive
            if chrome_driver:
                try:
                    _ = chrome_driver.current_url
                except Exception:
                    current_status = "not connected"
                    chrome_driver = None
            
            # Emit status update if changed
            if current_status != last_status:
                socketio.emit('connection_status', {
                    'status': 'connected',
                    'chrome': current_status,
                    'timestamp': datetime.now().isoformat()
                })
                last_status = current_status
            
            time.sleep(5)  # Check every 5 seconds
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
    global current_asset, streaming_active, data_streamer
    
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
        
        # Patch data_streamer's output method to capture ticks (if tick collection enabled)
        if collect_stream_mode in ['tick', 'both']:
            # Save reference to original bound method
            original_output = data_streamer._output_streaming_data
            
            def patched_output(self, asset, current_value, timestamp_str, change_indicator):
                # Keep original console behavior
                try:
                    original_output(asset, current_value, timestamp_str, change_indicator)
                except Exception:
                    pass
                
                # Persist tick data
                try:
                    if persistence_manager:
                        persistence_manager.add_tick(asset, timestamp_str, current_value)
                except Exception as e:
                    print(f"[Persistence] Error saving tick: {e}")
            
            # Bind the patched method
            import types
            data_streamer._output_streaming_data = types.MethodType(patched_output, data_streamer)
            print(f"[Persistence] ✓ Tick persistence hook installed")
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
