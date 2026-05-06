import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from app.schemas import Event, Task, TaskCreate, TraceImport


def _hex_id(value: str, length: int) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def _parse_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized).astimezone(timezone.utc)


def _timestamp_to_nanos(value: str) -> str:
    dt = _parse_timestamp(value)
    return str(int(dt.timestamp() * 1_000_000_000))


def _nanos_to_timestamp(value: str | int) -> str:
    seconds = int(value) / 1_000_000_000
    return datetime.fromtimestamp(seconds, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _any_value(value: Any) -> dict[str, Any]:
    if isinstance(value, bool):
        return {"boolValue": value}
    if isinstance(value, int):
        return {"intValue": str(value)}
    if isinstance(value, float):
        return {"doubleValue": value}
    if value is None:
        return {"stringValue": ""}
    if isinstance(value, str):
        return {"stringValue": value}
    return {"stringValue": json.dumps(value, sort_keys=True)}


def _attribute(key: str, value: Any) -> dict[str, Any]:
    return {"key": key, "value": _any_value(value)}


def _attribute_value(attribute: dict[str, Any]) -> Any:
    value = attribute.get("value", {})
    if "stringValue" in value:
        return value["stringValue"]
    if "intValue" in value:
        return int(value["intValue"])
    if "doubleValue" in value:
        return float(value["doubleValue"])
    if "boolValue" in value:
        return bool(value["boolValue"])
    return None


def _attributes_to_dict(attributes: list[dict[str, Any]]) -> dict[str, Any]:
    return {attribute["key"]: _attribute_value(attribute) for attribute in attributes}


def _event_status(event: Event) -> dict[str, Any]:
    status = event.attributes.get("status") or event.payload.get("status")
    if status in {"failed", "error"}:
        return {"code": "STATUS_CODE_ERROR"}
    if status in {"success", "completed"}:
        return {"code": "STATUS_CODE_OK"}
    return {"code": "STATUS_CODE_UNSET"}


def trace_to_otel(task: Task, events: list[Event]) -> dict[str, Any]:
    trace_id = _hex_id(task.task_id, 32)
    resource_attributes = [
        _attribute("service.name", "agent-runtime-layer"),
        _attribute("service.version", "0.5"),
        _attribute("arl.project_id", task.project_id),
        _attribute("arl.task_id", task.task_id),
        _attribute("arl.task.goal", task.goal),
        _attribute("arl.task.agent_type", task.agent_type),
    ]
    spans = []
    for event in events:
        span_attributes = [
            _attribute("arl.event_id", event.event_id),
            _attribute("arl.event_type", event.event_type),
            _attribute("arl.task_id", event.task_id),
            _attribute("arl.name", event.name),
            _attribute("arl.attributes_json", event.attributes),
            _attribute("arl.payload_json", event.payload),
        ]
        spans.append(
            {
                "traceId": trace_id,
                "spanId": _hex_id(event.span_id, 16),
                "parentSpanId": _hex_id(event.parent_span_id, 16) if event.parent_span_id else "",
                "name": event.name,
                "kind": "SPAN_KIND_INTERNAL",
                "startTimeUnixNano": _timestamp_to_nanos(event.timestamp),
                "endTimeUnixNano": _timestamp_to_nanos(event.timestamp),
                "attributes": span_attributes,
                "status": _event_status(event),
            }
        )
    return {
        "resourceSpans": [
            {
                "resource": {"attributes": resource_attributes},
                "scopeSpans": [
                    {
                        "scope": {"name": "agent-runtime-layer", "version": "0.5"},
                        "spans": spans,
                    }
                ],
            }
        ]
    }


def otel_to_trace(payload: dict[str, Any]) -> TraceImport:
    resource_spans = payload.get("resourceSpans") or []
    if not resource_spans:
        raise ValueError("OTEL payload must include resourceSpans")
    resource = resource_spans[0].get("resource", {})
    resource_attrs = _attributes_to_dict(resource.get("attributes", []))
    project_id = str(resource_attrs.get("arl.project_id") or "default")
    task_id = str(resource_attrs.get("arl.task_id") or f"task_otel_{_hex_id(json.dumps(payload, sort_keys=True), 12)}")
    task = TaskCreate(
        task_id=task_id,
        project_id=project_id,
        goal=str(resource_attrs.get("arl.task.goal") or "Imported OpenTelemetry trace"),
        agent_type=str(resource_attrs.get("arl.task.agent_type") or "otel_import"),
    )
    events: list[Event] = []
    for resource_span in resource_spans:
        for scope_span in resource_span.get("scopeSpans", []):
            for span in scope_span.get("spans", []):
                attrs = _attributes_to_dict(span.get("attributes", []))
                attributes_json = attrs.get("arl.attributes_json") or "{}"
                payload_json = attrs.get("arl.payload_json") or "{}"
                event_attributes = json.loads(attributes_json) if isinstance(attributes_json, str) else attributes_json
                event_payload = json.loads(payload_json) if isinstance(payload_json, str) else payload_json
                event_type = str(attrs.get("arl.event_type") or "terminal_event")
                event_id = str(attrs.get("arl.event_id") or f"evt_otel_{_hex_id(span.get('spanId', ''), 12)}")
                events.append(
                    Event(
                        event_id=event_id,
                        task_id=task_id,
                        timestamp=_nanos_to_timestamp(span.get("startTimeUnixNano", 0)),
                        event_type=event_type,
                        span_id=str(span.get("spanId") or event_id),
                        parent_span_id=str(span.get("parentSpanId") or "") or None,
                        name=str(attrs.get("arl.name") or span.get("name") or event_type),
                        attributes=event_attributes,
                        payload=event_payload,
                    )
                )
    return TraceImport(project_id=project_id, task=task, events=events)
