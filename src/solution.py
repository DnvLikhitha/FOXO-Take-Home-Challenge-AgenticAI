from collections import defaultdict


def reconstruct_traces(log: list[dict]) -> dict[str, dict]:
    """
    Takes a messy list of out-of-order log events and builds chronological timelines for each session. 
    Also flags any sessions where an agent started working but died silently without logging success/error.

    Args:
        log: A list of dicts. Each dict needs correlation_id, agent, event (start/success/error), and ts_ms.

    Returns:
        A dict mapping each correlation_id to its final timeline and status (complete or incomplete).
        "incomplete" means somebody started a job but we never saw them finish it.
    """
    # First pass: bucket everything by correlation_id so we can process sessions one by one
    groups = defaultdict(list)
    for entry in log:
        groups[entry["correlation_id"]].append(entry)

    result = {}
    for correlation_id, events in groups.items():
        # Sort chronologically to get the actual sequence of events
        timeline = sorted(events, key=lambda x: x["ts_ms"])
        
        # The spec says to strip correlation_id from the timeline events, so let's clean that up
        timeline = [
            {
                "agent": event["agent"],
                "event": event["event"],
                "ts_ms": event["ts_ms"]
            }
            for event in timeline
        ]

        # Now let's figure out if this session was left hanging. 
        # We need to look at events per-agent for this.
        agents = defaultdict(list)
        for event in events:
            agents[event["agent"]].append(event)

        # Did anyone start a job but never finish it?
        incomplete = False
        for agent_events in agents.values():
            starts = [e for e in agent_events if e["event"] == "start"]
            terminals = [e for e in agent_events if e["event"] in ("success", "error")]
            if len(starts) > 0 and len(terminals) == 0:
                incomplete = True
                break

        status = "incomplete" if incomplete else "complete"
        result[correlation_id] = {
            "timeline": timeline,
            "status": status
        }

    return result