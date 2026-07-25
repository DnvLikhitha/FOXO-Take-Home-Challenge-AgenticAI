import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from solution import reconstruct_traces  # pyrefly: ignore [missing-import]


def test_sample_input():
    """Let's make sure the example from the actual problem statement works correctly."""
    log = [
        {"correlation_id": "A1", "agent": "Planner", "event": "start", "ts_ms": 100},
        {"correlation_id": "A1", "agent": "Planner", "event": "success", "ts_ms": 200},
        {"correlation_id": "A1", "agent": "Researcher", "event": "start", "ts_ms": 210}
    ]

    expected = {
        "A1": {
            "timeline": [
                {"agent": "Planner", "event": "start", "ts_ms": 100},
                {"agent": "Planner", "event": "success", "ts_ms": 200},
                {"agent": "Researcher", "event": "start", "ts_ms": 210}
            ],
            "status": "incomplete"
        }
    }

    assert reconstruct_traces(log) == expected


def test_complete_session():
    """Happy path: every agent that started also finished gracefully."""
    log = [
        {"correlation_id": "A1", "agent": "Planner", "event": "start", "ts_ms": 100},
        {"correlation_id": "A1", "agent": "Planner", "event": "success", "ts_ms": 200},
        {"correlation_id": "A1", "agent": "Researcher", "event": "start", "ts_ms": 210},
        {"correlation_id": "A1", "agent": "Researcher", "event": "error", "ts_ms": 300}
    ]

    expected = {
        "A1": {
            "timeline": [
                {"agent": "Planner", "event": "start", "ts_ms": 100},
                {"agent": "Planner", "event": "success", "ts_ms": 200},
                {"agent": "Researcher", "event": "start", "ts_ms": 210},
                {"agent": "Researcher", "event": "error", "ts_ms": 300}
            ],
            "status": "complete"
        }
    }

    assert reconstruct_traces(log) == expected


def test_multiple_sessions():
    """What happens when logs from different sessions are all jumbled together?"""
    log = [
        # Session A1 left hanging: Researcher started but never finished
        {"correlation_id": "A1", "agent": "Planner", "event": "start", "ts_ms": 100},
        {"correlation_id": "A1", "agent": "Planner", "event": "success", "ts_ms": 200},
        {"correlation_id": "A1", "agent": "Researcher", "event": "start", "ts_ms": 210},

        # Session A2 looks good
        {"correlation_id": "A2", "agent": "Agent1", "event": "start", "ts_ms": 50},
        {"correlation_id": "A2", "agent": "Agent1", "event": "success", "ts_ms": 150},
        {"correlation_id": "A2", "agent": "Agent2", "event": "start", "ts_ms": 160},
        {"correlation_id": "A2", "agent": "Agent2", "event": "error", "ts_ms": 250}
    ]

    expected = {
        "A1": {
            "timeline": [
                {"agent": "Planner", "event": "start", "ts_ms": 100},
                {"agent": "Planner", "event": "success", "ts_ms": 200},
                {"agent": "Researcher", "event": "start", "ts_ms": 210}
            ],
            "status": "incomplete"
        },
        "A2": {
            "timeline": [
                {"agent": "Agent1", "event": "start", "ts_ms": 50},
                {"agent": "Agent1", "event": "success", "ts_ms": 150},
                {"agent": "Agent2", "event": "start", "ts_ms": 160},
                {"agent": "Agent2", "event": "error", "ts_ms": 250}
            ],
            "status": "complete"
        }
    }

    assert reconstruct_traces(log) == expected


def test_empty_input():
    """Edge case: the log is completely empty. We shouldn't crash."""
    log = []
    expected = {}
    assert reconstruct_traces(log) == expected


def test_only_terminal_events():
    """Weird edge case: we see success/error events but no start events. Spec says this is 'complete'."""
    log = [
        {"correlation_id": "A1", "agent": "Planner", "event": "success", "ts_ms": 100},
        {"correlation_id": "A1", "agent": "Planner", "event": "error", "ts_ms": 200}
    ]

    expected = {
        "A1": {
            "timeline": [
                {"agent": "Planner", "event": "success", "ts_ms": 100},
                {"agent": "Planner", "event": "error", "ts_ms": 200}
            ],
            "status": "complete"  # No agents started, so complete
        }
    }

    assert reconstruct_traces(log) == expected


def test_multiple_starts_one_terminal():
    """An agent restarted itself or logged 'start' twice, but eventually finished."""
    log = [
        {"correlation_id": "A1", "agent": "Planner", "event": "start", "ts_ms": 100},
        {"correlation_id": "A1", "agent": "Planner", "event": "start", "ts_ms": 150},
        {"correlation_id": "A1", "agent": "Planner", "event": "success", "ts_ms": 200}
    ]

    expected = {
        "A1": {
            "timeline": [
                {"agent": "Planner", "event": "start", "ts_ms": 100},
                {"agent": "Planner", "event": "start", "ts_ms": 150},
                {"agent": "Planner", "event": "success", "ts_ms": 200}
            ],
            "status": "complete"  # Agent started and did emit successed at least once
        }
    }

    assert reconstruct_traces(log) == expected


def test_multiple_starts_zero_terminals():
    """An agent logged 'start' repeatedly but never actually finished."""
    log = [
        {"correlation_id": "A1", "agent": "Planner", "event": "start", "ts_ms": 100},
        {"correlation_id": "A1", "agent": "Planner", "event": "start", "ts_ms": 150}
    ]

    expected = {
        "A1": {
            "timeline": [
                {"agent": "Planner", "event": "start", "ts_ms": 100},
                {"agent": "Planner", "event": "start", "ts_ms": 150}
            ],
            "status": "incomplete"  # Agent started but never success/error
        }
    }

    assert reconstruct_traces(log) == expected


def test_out_of_order_logs():
    """The real test: events arriving completely out of chronological order."""
    log = [
        {"correlation_id": "A1", "agent": "Researcher", "event": "start", "ts_ms": 300},
        {"correlation_id": "A1", "agent": "Planner", "event": "success", "ts_ms": 100},
        {"correlation_id": "A1", "agent": "Planner", "event": "start", "ts_ms": 200}
    ]

    expected = {
        "A1": {
            "timeline": [
                {"agent": "Planner", "event": "success", "ts_ms": 100},
                {"agent": "Planner", "event": "start", "ts_ms": 200},
                {"agent": "Researcher", "event": "start", "ts_ms": 300}
            ],
            "status": "incomplete"  # Researcher started but no terminal
        }
    }

    assert reconstruct_traces(log) == expected


def test_duplicate_timestamps():
    """What if two events happened at the exact same millisecond? We shouldn't drop either of them."""
    log = [
        {"correlation_id": "A1", "agent": "Planner", "event": "start", "ts_ms": 100},
        {"correlation_id": "A1", "agent": "Planner", "event": "success", "ts_ms": 100},  # Same timestamp
        {"correlation_id": "A1", "agent": "Researcher", "event": "start", "ts_ms": 200}
    ]

    expected = {
        "A1": {
            "timeline": [
                {"agent": "Planner", "event": "start", "ts_ms": 100},
                {"agent": "Planner", "event": "success", "ts_ms": 100},
                {"agent": "Researcher", "event": "start", "ts_ms": 200}
            ],
            "status": "incomplete"  # Researcher started but no terminal
        }
    }

    # Note: sorted() is stable, but we don't care about order of equal timestamps
    result = reconstruct_traces(log)
    assert result["A1"]["status"] == "incomplete"
    assert len(result["A1"]["timeline"]) == 3
    # Check that events are present (order of equal timestamps may vary)
    timeline_events = {(e["agent"], e["event"], e["ts_ms"]) for e in result["A1"]["timeline"]}
    expected_events = {
        ("Planner", "start", 100),
        ("Planner", "success", 100),
        ("Researcher", "start", 200)
    }
    assert timeline_events == expected_events


def test_session_with_only_start_events():
    """A completely abandoned session where everyone started but nobody finished."""
    log = [
        {"correlation_id": "A1", "agent": "Planner", "event": "start", "ts_ms": 100},
        {"correlation_id": "A1", "agent": "Researcher", "event": "start", "ts_ms": 200}
    ]

    expected = {
        "A1": {
            "timeline": [
                {"agent": "Planner", "event": "start", "ts_ms": 100},
                {"agent": "Researcher", "event": "start", "ts_ms": 200}
            ],
            "status": "incomplete"  # Both agents started but no terminals
        }
    }

    assert reconstruct_traces(log) == expected


def test_agent_with_multiple_terminals_no_start():
    """Agent forgot to log 'start' but logged 'success'. We should still consider it complete."""
    log = [
        {"correlation_id": "A1", "agent": "Planner", "event": "success", "ts_ms": 100},
        {"correlation_id": "A1", "agent": "Planner", "event": "error", "ts_ms": 200},
        {"correlation_id": "A1", "agent": "Researcher", "event": "start", "ts_ms": 300}
    ]

    expected = {
        "A1": {
            "timeline": [
                {"agent": "Planner", "event": "success", "ts_ms": 100},
                {"agent": "Planner", "event": "error", "ts_ms": 200},
                {"agent": "Researcher", "event": "start", "ts_ms": 300}
            ],
            "status": "incomplete"  # Researcher started but no terminal
        }
    }

    assert reconstruct_traces(log) == expected


def run_tests():
    """A poor man's test runner to execute everything without needing pytest installed."""
    test_functions = [
        test_sample_input,
        test_complete_session,
        test_multiple_sessions,
        test_empty_input,
        test_only_terminal_events,
        test_multiple_starts_one_terminal,
        test_multiple_starts_zero_terminals,
        test_out_of_order_logs,
        test_duplicate_timestamps,
        test_session_with_only_start_events,
        test_agent_with_multiple_terminals_no_start
    ]

    failed = []
    for test_func in test_functions:
        try:
            test_func()
            print(f"PASS: {test_func.__name__}")
        except Exception as e:
            failed.append((test_func.__name__, str(e)))
            print(f"FAIL: {test_func.__name__}: {e}")

    if failed:
        print(f"\n{len(failed)} tests failed:")
        for name, error in failed:
            print(f"  {name}: {error}")
        return False
    else:
        print(f"\nAll {len(test_functions)} tests passed!")
        return True


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)