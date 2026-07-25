# Trace Reconstruction from Out-of-Order Logs

## Problem Statement

Multiple agents emit log events independently; they arrive out of order and some agents never log completion (a silent failure). Given a flat list of log events, reconstruct one ordered timeline per session and detect any session missing a terminal event.

### Function Signature

```python
def reconstruct_traces(log: list[dict]) -> dict:
    '''
    log: list of {"correlation_id": str, "agent": str, "event": str, "ts_ms": int}
    event is one of: "start", "success", "error"
    Returns: { correlation_id: { "timeline": [ordered list of events by ts_ms], "status": "complete" | "incomplete" } }
    "incomplete" = at least one agent that "start"-ed never emitted "success" or "error" for that session.
    '''
```

### Sample Input

```json
[
  {
    "correlation_id": "A1",
    "agent": "Planner",
    "event": "start",
    "ts_ms": 100
  },
  {
    "correlation_id": "A1",
    "agent": "Planner",
    "event": "success",
    "ts_ms": 200
  },
  {
    "correlation_id": "A1",
    "agent": "Researcher",
    "event": "start",
    "ts_ms": 210
  }
]
```

### Sample Output

```json
{
  "A1": {
    "timeline": [
      { "agent": "Planner", "event": "start", "ts_ms": 100 },
      { "agent": "Planner", "event": "success", "ts_ms": 200 },
      { "agent": "Researcher", "event": "start", "ts_ms": 210 }
    ],
    "status": "incomplete"
  }
}
```

---

## Approach

1. **Group by `correlation_id`** — process each session independently using `defaultdict(list)`.
2. **Sort by `ts_ms` ascending** — reconstruct the chronological timeline from out-of-order events.
3. **Check completeness per agent** — for each agent within a session, if it has at least one `"start"` event but zero `"success"` or `"error"` events, the session is `"incomplete"`.

### Design Decisions

- **`defaultdict(list)`** for O(1) amortised grouping at both the session and agent level.
- **Python's `sorted()`** (stable, Timsort) for O(m log m) per-session sorting — stable sort preserves insertion order for equal timestamps.
- **Count-based completeness check** rather than event-pairing: the spec only requires knowing whether a terminal event was _ever_ emitted, not which specific start it corresponds to.

### Alternatives Considered

| Approach                                   | Why Rejected                                                 |
| ------------------------------------------ | ------------------------------------------------------------ |
| Pair each `start` with a matching terminal | Over-engineered; spec doesn't require 1-to-1 pairing         |
| State machine per agent                    | More complex with no benefit for this problem's requirements |

---

## Algorithm

1. **Grouping** — O(n): iterate events, bucket into `groups[correlation_id]`.
2. **Per-session processing** — O(m log m) per session (Σm = n):
   - Sort events by `ts_ms` → timeline (strip `correlation_id` from output).
   - Re-group by `agent`, check: `len(starts) > 0 and len(terminals) == 0` → incomplete.
3. **Result construction** — O(n): assemble `{timeline, status}` per session.

## Complexity

|       | Complexity                                |
| ----- | ----------------------------------------- |
| Time  | O(n log n) — dominated by sorting         |
| Space | O(n) — grouped events + result dictionary |

---

## Setup & Usage

**No external dependencies** — only the Python standard library is used. Python 3.9+ required.

Install test dependencies:

```bash
pip install -r requirements.txt
```

### Run the demo

```bash
python examples/main.py examples/sample_input.json examples/sample_expected_output.json
```

### Use in code

```python
from src.solution import reconstruct_traces

log = [
    {"correlation_id": "A1", "agent": "Planner",    "event": "start",   "ts_ms": 100},
    {"correlation_id": "A1", "agent": "Planner",    "event": "success", "ts_ms": 200},
    {"correlation_id": "A1", "agent": "Researcher", "event": "start",   "ts_ms": 210},
]

result = reconstruct_traces(log)
print(result)
```

### Run tests

```bash
python -m pytest tests/test_solution.py -v
```

---

## Examples

### Complete session

```json
[
  {
    "correlation_id": "A1",
    "agent": "Planner",
    "event": "start",
    "ts_ms": 100
  },
  {
    "correlation_id": "A1",
    "agent": "Planner",
    "event": "success",
    "ts_ms": 200
  },
  {
    "correlation_id": "A1",
    "agent": "Researcher",
    "event": "start",
    "ts_ms": 210
  },
  {
    "correlation_id": "A1",
    "agent": "Researcher",
    "event": "error",
    "ts_ms": 300
  }
]
```

```json
{
  "A1": {
    "timeline": [
      { "agent": "Planner", "event": "start", "ts_ms": 100 },
      { "agent": "Planner", "event": "success", "ts_ms": 200 },
      { "agent": "Researcher", "event": "start", "ts_ms": 210 },
      { "agent": "Researcher", "event": "error", "ts_ms": 300 }
    ],
    "status": "complete"
  }
}
```

### Multiple sessions (mixed status)

```json
[
  {
    "correlation_id": "A1",
    "agent": "Planner",
    "event": "start",
    "ts_ms": 100
  },
  {
    "correlation_id": "A1",
    "agent": "Planner",
    "event": "success",
    "ts_ms": 200
  },
  {
    "correlation_id": "A1",
    "agent": "Researcher",
    "event": "start",
    "ts_ms": 210
  },
  { "correlation_id": "A2", "agent": "Agent1", "event": "start", "ts_ms": 50 },
  {
    "correlation_id": "A2",
    "agent": "Agent1",
    "event": "success",
    "ts_ms": 150
  },
  { "correlation_id": "A2", "agent": "Agent2", "event": "start", "ts_ms": 160 },
  { "correlation_id": "A2", "agent": "Agent2", "event": "error", "ts_ms": 250 }
]
```

```json
{
  "A1": {
    "timeline": [
      { "agent": "Planner", "event": "start", "ts_ms": 100 },
      { "agent": "Planner", "event": "success", "ts_ms": 200 },
      { "agent": "Researcher", "event": "start", "ts_ms": 210 }
    ],
    "status": "incomplete"
  },
  "A2": {
    "timeline": [
      { "agent": "Agent1", "event": "start", "ts_ms": 50 },
      { "agent": "Agent1", "event": "success", "ts_ms": 150 },
      { "agent": "Agent2", "event": "start", "ts_ms": 160 },
      { "agent": "Agent2", "event": "error", "ts_ms": 250 }
    ],
    "status": "complete"
  }
}
```

---

## Edge Cases

| Scenario                                         | Status                                         |
| ------------------------------------------------ | ---------------------------------------------- |
| Empty input                                      | `{}`                                           |
| Only terminal events (no starts)                 | `complete` — no agent started                  |
| Agent has multiple starts, at least one terminal | `complete`                                     |
| Agent has multiple starts, zero terminals        | `incomplete`                                   |
| Terminal event appears before start in log       | `complete` — terminal was still emitted        |
| Duplicate timestamps                             | Handled — stable sort preserves relative order |
| Out-of-order log entries                         | Sorted correctly by `ts_ms`                    |

---

## Project Structure

```
Trace_Reconstruction_from_Out-of-Order_Logs/
│
├── src/
│   └── solution.py                  # Core implementation
├── tests/
│   └── test_solution.py             # Test suite (11 test cases)
├── examples/
│   ├── main.py                      # CLI demo runner
│   ├── sample_input.json            # Sample input from problem statement
│   └── sample_expected_output.json  # Expected output for sample input
├── docs/
│   └── AI - D.docx.pdf              # Original task description
├── requirements.txt                 # Test dependencies (pytest)
├── README.md                        # This file
└── .gitignore
```

---

## Future Improvements

1. **Streaming / online processing** — maintain running state per session/agent instead of buffering all events.
2. **Parallel processing** — sessions are independent and can be processed concurrently.
3. **Extended metrics** — latency, throughput, or agent-level error rates per session.
