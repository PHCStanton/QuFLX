#!/usr/bin/env python3
"""
Real-time Trading Data Streaming Server
Streams data from the binary options platform to the frontend via WebSocket
"""

import eventlet
eventlet.monkey_patch()

from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json
import time
import random
from datetime import datetime
import threading
import sys
from pathlib import Path

# Add paths for imports
script_dir = Path(__file__).parent
root_dir = script_dir.parent.parent  # Go up two levels to workspace root
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(script_dir))

from strategies.quantum_flux_strategy import QuantumFluxStrategy
from data_loader import DataLoader, BacktestEngine

app = Flask(__name__)
CORS(app)
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='eventlet',
    ping_timeout=30,   # seconds
    ping_interval=10   # seconds
)

# Asset base prices
ASSET_PRICES = {
    "EURUSD_OTC": 1.0856,
    "GBPUSD_OTC": 1.2645,
    "AUDCAD_OTC": 0.8923,
    "EURJPY_OTC": 156.45,
}

# Global state for streaming
current_asset = "EURUSD_OTC"
streaming_active = False
base_price = ASSET_PRICES[current_asset]

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/assets')
def get_assets():
    """Get available assets"""
    assets = [
        {"id": "EURUSD_OTC", "name": "EUR/USD OTC"},
        {"id": "GBPUSD_OTC", "name": "GBP/USD OTC"},
        {"id": "AUDCAD_OTC", "name": "AUD/CAD OTC"},
        {"id": "EURJPY_OTC", "name": "EUR/JPY OTC"},
    ]
    return jsonify(assets)

@app.route('/api/available-csv-files')
def get_available_csv_files():
    """Get list of all available CSV files from root data folder, optionally filtered by timeframe"""
    import glob
    import os
    
    # Get optional timeframe filter from query parameters
    timeframe_filter = request.args.get('timeframe', None)
    
    files = []
    
    # Search in root data folder
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
    
    # Build search paths based on timeframe filter
    search_paths = []
    if timeframe_filter and timeframe_filter in timeframe_dirs:
        # Search in directories matching the selected timeframe
        for dir_name in timeframe_dirs[timeframe_filter]:
            search_paths.append(str(data_dir / 'data_collect' / dir_name / '*.csv'))
        
        # Also include realtime_stream directories for 1m timeframe
        if timeframe_filter == '1m':
            search_paths.extend([
                str(data_dir / 'realtime_stream' / '1M_candle_data' / '*.csv'),
                str(data_dir / 'realtime_stream' / '1M_tick_data' / '*.csv'),
            ])
    else:
        # Search all timeframe directories
        search_paths = [
            str(data_dir / 'realtime_stream' / '1M_candle_data' / '*.csv'),
            str(data_dir / 'realtime_stream' / '1M_tick_data' / '*.csv'),
            str(data_dir / 'data_collect' / '*_candles' / '*.csv'),
            str(data_dir / 'data_collect' / '*_candles_utc' / '*.csv'),
        ]
    
    for pattern in search_paths:
        for filepath in glob.glob(pattern):
            filename = os.path.basename(filepath)
            
            # Parse asset name from filename - keep more of the name for proper identification
            parts = filename.split('_')
            if len(parts) >= 2:
                # Extract asset by finding where timeframe indicators start
                asset_parts = []
                for i, part in enumerate(parts):
                    # Stop when we hit a timeframe, timestamp, or common separators
                    if part in ['1m', '5m', '15m', '1h', '4h', '60m', 'otc'] or part.isdigit() or len(part) > 10:
                        break
                    asset_parts.append(part)
                
                # If we didn't get enough parts, use first part + 'otc' if present
                if len(asset_parts) == 0:
                    asset_parts = [parts[0]]
                if len(parts) > 1 and 'otc' in parts[1].lower():
                    asset_parts.append('otc')
                
                asset = '_'.join(asset_parts).upper()
                
                # Determine timeframe from parent directory
                parent_dir = os.path.basename(os.path.dirname(filepath))
                timeframe = '1m'  # default
                
                if '1M' in parent_dir or '1m' in parent_dir:
                    timeframe = '1m'
                elif '5M' in parent_dir or '5m' in parent_dir:
                    timeframe = '5m'
                elif '15M' in parent_dir or '15m' in parent_dir:
                    timeframe = '15m'
                elif '1H' in parent_dir or '1h' in parent_dir or '60m' in parent_dir:
                    timeframe = '1h'
                elif '4H' in parent_dir or '4h' in parent_dir or '240m' in parent_dir:
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
    
    # Search for the file in data directories
    data_dir = root_dir / 'data' / 'data_output' / 'assets_data'
    
    # Search in all possible timeframe directories
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

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"Client connected: {datetime.now().isoformat()}")
    emit('connection_status', {'status': 'connected', 'timestamp': datetime.now().isoformat()})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"Client disconnected: {datetime.now().isoformat()}")

@socketio.on('start_stream')
def handle_start_stream(data):
    """Start streaming data for a specific asset"""
    global current_asset, streaming_active, base_price
    
    if data and 'asset' in data:
        current_asset = data['asset']
    
    streaming_active = True
    base_price = ASSET_PRICES.get(current_asset, 1.0)
    
    print(f"Starting stream for {current_asset} at {datetime.now().isoformat()}")
    emit('stream_started', {
        'asset': current_asset, 
        'timestamp': datetime.now().isoformat(),
        'base_price': base_price
    })

@socketio.on('stop_stream')
def handle_stop_stream():
    """Stop streaming data"""
    global streaming_active
    streaming_active = False
    print(f"Stopping stream at {datetime.now().isoformat()}")
    emit('stream_stopped', {'timestamp': datetime.now().isoformat()})

@socketio.on('change_asset')
def handle_change_asset(data):
    """Change the streaming asset"""
    global current_asset, base_price
    
    if data and 'asset' in data:
        current_asset = data['asset']
        base_price = ASSET_PRICES.get(current_asset, 1.0)
        
        print(f"Asset changed to {current_asset}")
        emit('asset_changed', {
            'asset': current_asset,
            'base_price': base_price,
            'timestamp': datetime.now().isoformat()
        })

def generate_price_update():
    """Generate realistic price updates"""
    global base_price, current_asset
    
    # Get the original base price for mean reversion
    original_base = ASSET_PRICES.get(current_asset, 1.0)
    
    # Random walk with mean reversion to original base price
    change = random.gauss(0, 0.0002)  # Small random changes
    mean_reversion = (original_base - base_price) * 0.01  # Slight mean reversion to original base
    new_price = base_price + change + mean_reversion
    
    return round(new_price, 5)

def stream_data():
    """Background thread to stream data"""
    global streaming_active, base_price
    
    while True:
        if streaming_active:
            timestamp = int(time.time() * 1000)  # milliseconds
            price = generate_price_update()
            base_price = price  # Update base for next iteration
            
            # Emit tick data
            socketio.emit('tick_update', {
                'asset': current_asset,
                'price': price,
                'timestamp': timestamp,
                'time_string': datetime.now().isoformat()
            })
            
            # Small delay between updates (simulating real-time ticks)
            time.sleep(0.1)  # 10 updates per second
        else:
            time.sleep(0.5)  # Check less frequently when not streaming


@socketio.on('run_backtest')
def handle_run_backtest(data):
    """Run strategy backtest on historical data"""
    try:
        file_path = data.get('file_path')
        strategy_type = data.get('strategy', 'quantum_flux')
        
        if not file_path:
            emit('backtest_error', {'error': 'No file path provided'})
            return
        
        # Load data
        loader = DataLoader()
        df = loader.load_csv(file_path)
        candles = loader.df_to_candles(df)
        
        # Initialize strategy
        if strategy_type == 'quantum_flux':
            strategy = QuantumFluxStrategy()
        else:
            emit('backtest_error', {'error': f'Unknown strategy: {strategy_type}'})
            return
        
        # Run backtest
        engine = BacktestEngine(strategy)
        results = engine.run_backtest(candles)
        
        emit('backtest_complete', {
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        emit('backtest_error', {'error': str(e)})


@socketio.on('get_available_data')
def handle_get_available_data():
    """Get list of available data files"""
    try:
        loader = DataLoader()
        files = loader.get_available_files()
        emit('available_data', {'files': files})
    except Exception as e:
        emit('data_error', {'error': str(e)})


@socketio.on('generate_signal')
def handle_generate_signal(data):
    """Generate trading signal from current candle data"""
    try:
        candles = data.get('candles', [])
        strategy_type = data.get('strategy', 'quantum_flux')
        
        if not candles:
            emit('signal_error', {'error': 'No candles provided'})
            return
        
        # Initialize strategy
        if strategy_type == 'quantum_flux':
            strategy = QuantumFluxStrategy()
        else:
            emit('signal_error', {'error': f'Unknown strategy: {strategy_type}'})
            return
        
        # Generate signal
        signal_result = strategy.generate_signal(candles)
        
        if signal_result:
            emit('signal_generated', {
                'signal': signal_result.direction.value,
                'confidence': signal_result.confidence,
                'strength': signal_result.strength,
                'indicators': signal_result.indicators,
                'timestamp': datetime.now().isoformat()
            })
        else:
            emit('signal_generated', {
                'signal': 'neutral',
                'confidence': 0.0,
                'strength': 0.0,
                'timestamp': datetime.now().isoformat()
            })
            
    except Exception as e:
        emit('signal_error', {'error': str(e)})


@socketio.on('execute_strategy')
def handle_execute_strategy(data):
    """Execute strategy on live streaming data"""
    try:
        candles = data.get('candles', [])
        strategy_type = data.get('strategy', 'quantum_flux')
        
        if not candles:
            emit('strategy_error', {'error': 'No candles provided'})
            return
        
        # Initialize strategy
        if strategy_type == 'quantum_flux':
            strategy = QuantumFluxStrategy()
        else:
            emit('strategy_error', {'error': f'Unknown strategy: {strategy_type}'})
            return
        
        # Execute strategy
        signal = strategy.execute(candles)
        
        emit('strategy_result', {
            'signal': signal if signal else 'neutral',
            'asset': current_asset,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        emit('strategy_error', {'error': str(e)})


if __name__ == '__main__':
    # Start background streaming thread
    stream_thread = threading.Thread(target=stream_data, daemon=True)
    stream_thread.start()
    
    print("Starting streaming server on http://0.0.0.0:3001")
    socketio.run(app, host='0.0.0.0', port=3001, debug=False, use_reloader=False, log_output=True, allow_unsafe_werkzeug=True)
