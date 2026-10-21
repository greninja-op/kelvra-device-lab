"""
KELVRA Device Lab — Standalone Server Launcher
Dedicated Port: 8098
"""

import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.server import main

if __name__ == "__main__":
    main()
