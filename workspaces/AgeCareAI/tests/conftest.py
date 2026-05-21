"""Pytest configuration and shared fixtures."""

import pytest
import sys
import os

# Ensure app.py and build_report.py are importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
