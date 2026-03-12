"""
LexZero Configuration
"""

# UI Settings
UI_THEME = "dark"  # dark or light
SIDEBAR_WIDTH = 30
TABLE_CURSOR_TYPE = "row"  # row, cell, column, none

# Export Settings
EXPORT_DIR = "~/lexzero_exports"
DEFAULT_EXPORT_FORMAT = "csv"  # csv, json, txt

# Logging Settings
LOG_FILE = "/tmp/lexzero.log"
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR

# Volatility3 Settings
VOLATILITY_PLUGINS_PATH = None  # Custom plugins path, None for default
VOLATILITY_SYMBOLS_PATH = None  # Custom symbols path, None for default

# Performance Settings
MAX_TABLE_ROWS = 10000  # Maximum rows to display in table
ENABLE_PAGINATION = False  # Enable pagination for large results

# Feature Flags
ENABLE_EXPORT = True
ENABLE_FILTER = True
ENABLE_SORT = True
ENABLE_AUTO_REFRESH = False
AUTO_REFRESH_INTERVAL = 60  # seconds
