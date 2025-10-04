from .base import Ctx, CapResult, Capability

# Import all capability classes
try:
    from .data_streaming import RealtimeDataStreaming  # noqa: F401
except ImportError:
    RealtimeDataStreaming = None

try:
    from .session_scan import SessionScan  # noqa: F401
except ImportError:
    SessionScan = None

try:
    from .profile_scan import ProfileScan  # noqa: F401
except ImportError:
    ProfileScan = None

try:
    from .favorite_select import FavoriteSelect  # noqa: F401
except ImportError:
    FavoriteSelect = None

try:
    from .trade_click_cap import TradeClick  # noqa: F401
except ImportError:
    TradeClick = None

try:
    from .TF_dropdown_retract import TF_Dropdown_Retract  # noqa: F401
except ImportError:
    TF_Dropdown_Retract = None

try:
    from .timestamp_convert_utc import TimestampConvertUTC  # noqa: F401
except ImportError:
    TimestampConvertUTC = None

try:
    from .favorite_star_select import FavoriteStarSelect  # noqa: F401
except ImportError:
    FavoriteStarSelect = None

try:
    from .TF_dropdown_open_close_screenshot import TF_Dropdown_Open_Close_Screenshot  # noqa: F401
except ImportError:
    TF_Dropdown_Open_Close_Screenshot = None

try:
    from .take_screenshot import TakeScreenshot  # noqa: F401
except ImportError:
    TakeScreenshot = None
