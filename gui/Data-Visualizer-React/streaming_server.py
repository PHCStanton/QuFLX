#!/usr/bin/env python3
"""
Real-time Trading Data Streaming Server
Streams data from the binary options platform to the frontend via WebSocket
"""

import eventlet
eventlet.monkey_patch()

from flask import Flask, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json
import time
import random
from datetime import datetime
import threading

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Global state for streaming
current_asset = "EURUSD_OTC"
streaming_active = False
base_price = 1.0856

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
    
    # Set different base prices for different assets
    price_map = {
        "EURUSD_OTC": 1.0856,
        "GBPUSD_OTC": 1.2645,
        "AUDCAD_OTC": 0.8923,
        "EURJPY_OTC": 156.45,
    }
    base_price = price_map.get(current_asset, 1.0)
    
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
        
        # Set different base prices for different assets
        price_map = {
            "EURUSD_OTC": 1.0856,
            "GBPUSD_OTC": 1.2645,
            "AUDCAD_OTC": 0.8923,
            "EURJPY_OTC": 156.45,
        }
        base_price = price_map.get(current_asset, 1.0)
        
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
    price_map = {
        "EURUSD_OTC": 1.0856,
        "GBPUSD_OTC": 1.2645,
        "AUDCAD_OTC": 0.8923,
        "EURJPY_OTC": 156.45,
    }
    original_base = price_map.get(current_asset, 1.0)
    
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

if __name__ == '__main__':
    # Start background streaming thread
    stream_thread = threading.Thread(target=stream_data, daemon=True)
    stream_thread.start()
    
    print("Starting streaming server on http://0.0.0.0:3001")
    socketio.run(app, host='0.0.0.0', port=3001, debug=False, use_reloader=False, log_output=True, allow_unsafe_werkzeug=True)
