#!/usr/bin/env python3

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.cli.book_manager import app

if __name__ == "__main__":
    app()