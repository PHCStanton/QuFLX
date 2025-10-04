"""Capabilities module for QuantumFlux Testing Platform.

This module provides capability-based testing infrastructure:
- Base capability framework (Capability, CapResult, Ctx)
- Individual capability modules for specific testing scenarios
- Artifact management and debugging support

Migrated from API-test-space for production use.
"""

from .base import Capability, CapResult, Ctx
from .screenshot_control import ScreenshotControl
from .session_scan import SessionScan
from .trade_click_cap import TradeClick
from .profile_scan import ProfileScan

__all__ = [
    'Capability',
    'CapResult', 
    'Ctx',
    'ScreenshotControl',
    'SessionScan',
    'TradeClick',
    'ProfileScan'
]