import sys
import os
import pytest

# Ensure the parent directory is in sys.path for module resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.core.chaos_agent import inject_chaos

def test_chaos_injection():
    result = inject_chaos({"target": "phoenix-demigod"})
    assert result.get("status") == "chaos_injected", "Expected status to be 'chaos_injected'"
    assert "mock_failure" in result, "'mock_failure' key missing in result"