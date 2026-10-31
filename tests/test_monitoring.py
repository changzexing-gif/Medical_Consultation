from core.monitoring import Event, Monitor


def test_monitoring_dashboard(tmp_path):
    monitor = Monitor(tmp_path / "monitor.db")
    monitor.record(Event("retrieval", agent="retrieval", latency_ms=20, metadata={"hit_count": 0}))
    monitor.record(Event("agent_call", agent="risk", success=False, failure_mode="timeout"))
    monitor.set_index_state("test", 12, "bge")
    monitor.add_feedback("q1", 1)
    data = monitor.dashboard(24)
    assert data["retrieval_count"] == 1
    assert data["no_hit_rate"] == 1.0
    assert data["index_state"][0]["chunks"] == 12
    assert data["failures"][0]["mode"] == "timeout"
