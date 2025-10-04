"""
API Models for QuantumFlux Trading Platform - Capabilities Framework Compatible

Clean, simple API models that work with the capabilities framework.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime


class ConnectionStatus(BaseModel):
    """Connection status information."""
    webdriver_connected: bool
    websocket_connected: bool
    platform_logged_in: bool
    last_heartbeat: Optional[datetime] = None
    error_message: Optional[str] = None


class StatusResponse(BaseModel):
    """System status response."""
    connection_status: ConnectionStatus
    uptime_seconds: float
    system_health: Dict[str, Any]


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    checks: Dict[str, Any]
    uptime_seconds: float
    message: str


class TradeRequest(BaseModel):
    """Trade execution request."""
    side: str
    amount: Optional[float] = None
    timeout: Optional[int] = 5


class TradeResponse(BaseModel):
    """Trade execution response."""
    status: str
    data: Dict[str, Any]
    trade_params: Dict[str, Any]
    timestamp: str


class CandleResponse(BaseModel):
    """Candle data response."""
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None