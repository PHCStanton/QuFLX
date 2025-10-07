import time
import sys

try:
    import socketio
except Exception as e:
    print("python-socketio not available:", e)
    sys.exit(1)


def main():
    sio = socketio.Client(logger=False, engineio_logger=False, reconnection=False)

    @sio.event
    def connect():
        print("[Client] Connected to server")

    @sio.event
    def disconnect():
        print("[Client] Disconnected from server")

    @sio.on('connection_status')
    def on_connection_status(data):
        print("[Event] connection_status:", data)

    @sio.on('stream_started')
    def on_stream_started(data):
        print("[Event] stream_started:", data)

    @sio.on('stream_error')
    def on_stream_error(data):
        print("[Event] stream_error:", data)

    @sio.on('tick_update')
    def on_tick_update(data):
        print("[Event] tick_update:", data)

    try:
        print("[Client] Connecting to http://localhost:3001 ...")
        sio.connect('http://localhost:3001', transports=['websocket'])
    except Exception as e:
        print("[Client] Connect failed:", e)
        sys.exit(2)

    # Request stream start for a default asset
    print("[Client] Emitting start_stream for EURUSD_OTC")
    sio.emit('start_stream', {'asset': 'EURUSD_OTC'})

    # Wait for some events
    time.sleep(3)

    print("[Client] Emitting stop_stream")
    sio.emit('stop_stream')

    time.sleep(1)
    sio.disconnect()
    print("[Client] Done")


if __name__ == '__main__':
    main()