# tests/conftest.py
import os
import sys

# Insert the project root (one level up) onto the import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
