import sys
import os
from src.core.demigod_agent import make_decision

print(f"VIRTUAL_ENV: {os.environ.get('VIRTUAL_ENV')}")

# Ensure the parent directory is in sys.path for module resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))  # noqa: E402


def test_demigod_decision_with_input():
    result = make_decision({"input": "task1"})
    assert result["status"] == "success"
    assert "decision" in result
    assert "This is a mock decision based on input: task1" in result["decision"]


def test_demigod_decision_no_input():
    result = make_decision({})
    assert result["status"] == "error"
    assert "No input provided" in result["decision"]
