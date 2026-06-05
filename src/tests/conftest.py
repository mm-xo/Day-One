import sys
from unittest.mock import MagicMock

# Mock external dependencies that aren't needed for unit tests
sys.modules['aiosqlite'] = MagicMock()
sys.modules['discord'] = MagicMock()
