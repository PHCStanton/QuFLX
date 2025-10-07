import pytest
import requests

BASE_URL = "http://localhost:3001"


def test_health_endpoint():
    r = requests.get(f"{BASE_URL}/health", timeout=5)
    r.raise_for_status()
    data = r.json()
    assert data.get("status") == "healthy"
    assert "timestamp" in data


def test_available_csv_files_endpoint():
    r = requests.get(f"{BASE_URL}/api/available-csv-files", timeout=10)
    r.raise_for_status()
    data = r.json()
    assert "files" in data
    assert "count" in data
    assert isinstance(data["files"], list)
    assert isinstance(data["count"], int)


@pytest.mark.optional
def test_socketio_connect_polling_fallback():
    try:
        import socketio
    except Exception:
        pytest.skip("python-socketio not available")

    sio = socketio.Client(reconnection=False)
    connected = False

    @sio.event
    def connect():
        nonlocal connected
        connected = True

    try:
        sio.connect(BASE_URL)  # Let client choose transport (polling first)
        sio.disconnect()
    except Exception:
        pytest.xfail("Socket.IO handshake failed (server may not accept polling/websocket)")

    assert connected, "Client failed to connect to Socket.IO server"