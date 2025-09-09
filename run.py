##!/usr/bin/env python3
"""
Launcher script for Kubernetes TUI
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from kube_tui import main

if __name__ == "__main__":
    main()
