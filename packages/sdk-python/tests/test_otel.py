import json
from pathlib import Path

from agent_runtime_layer.otel import otel_to_trace, trace_to_otel


ROOT = Path(__file__).resolve().parents[3]


def test_trace_to_otel_round_trip_preserves_events():
    trace = json.loads((ROOT / "examples" / "sample-traces" / "successful-coding-task.json").read_text())

    otel = trace_to_otel(trace)
    converted = otel_to_trace(otel)

    assert "resourceSpans" in otel
    spans = otel["resourceSpans"][0]["scopeSpans"][0]["spans"]
    assert len(spans) == len(trace["events"])
    assert all(span["traceId"] for span in spans)
    assert all(span["spanId"] for span in spans)
    assert converted["task"]["task_id"] == trace["task"]["task_id"]
    assert [event["event_type"] for event in converted["events"]] == [event["event_type"] for event in trace["events"]]
