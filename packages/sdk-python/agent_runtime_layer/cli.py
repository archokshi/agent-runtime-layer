import argparse
import json
from pathlib import Path

from agent_runtime_layer.capture import capture_command
from agent_runtime_layer.client import AgentRuntimeClient
from agent_runtime_layer.integrations.aider import capture_aider
from agent_runtime_layer.otel import otel_to_trace, trace_to_otel


def main() -> None:
    parser = argparse.ArgumentParser(prog="agent-runtime")
    parser.add_argument("--base-url", default="http://localhost:8000/api")
    subparsers = parser.add_subparsers(dest="command", required=True)
    import_parser = subparsers.add_parser("import")
    import_parser.add_argument("trace_file")
    import_otel_parser = subparsers.add_parser("import-otel")
    import_otel_parser.add_argument("otel_file")
    convert_otel_parser = subparsers.add_parser("convert-otel")
    convert_otel_parser.add_argument("trace_file")
    convert_otel_parser.add_argument("otel_file")
    convert_from_otel_parser = subparsers.add_parser("convert-from-otel")
    convert_from_otel_parser.add_argument("otel_file")
    convert_from_otel_parser.add_argument("trace_file")
    export_otel_parser = subparsers.add_parser("export-otel")
    export_otel_parser.add_argument("task_id")
    export_otel_parser.add_argument("otel_file")
    trace_parser = subparsers.add_parser("trace")
    trace_parser.add_argument("--name", required=True)
    trace_parser.add_argument("--project", default="default")
    trace_parser.add_argument("--upload", action="store_true")
    trace_parser.add_argument("--capture-diff", action="store_true")
    trace_parser.add_argument("--capture-full-logs", action="store_true")
    trace_parser.add_argument("--trace-dir", default=".agent-runtime/traces")
    trace_parser.add_argument("wrapped_command", nargs=argparse.REMAINDER)
    integrate_parser = subparsers.add_parser("integrate")
    integrate_subparsers = integrate_parser.add_subparsers(dest="integration", required=True)
    aider_parser = integrate_subparsers.add_parser("aider")
    aider_parser.add_argument("--name", required=True)
    aider_parser.add_argument("--project", default="default")
    aider_parser.add_argument("--repo", default=".")
    aider_parser.add_argument("--upload", action="store_true")
    aider_parser.add_argument("--capture-full-logs", action="store_true")
    aider_parser.add_argument("--trace-dir", default=".agent-runtime/traces")
    aider_parser.add_argument("wrapped_command", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    client = AgentRuntimeClient(args.base_url)
    if args.command == "import":
        result = client.import_trace_file(args.trace_file)
        print(f"Imported {result['event_count']} events for task {result['task_id']}")
    if args.command == "import-otel":
        result = client.import_otel_file(args.otel_file)
        print(f"Imported OTEL trace with {result['event_count']} events for task {result['task_id']}")
    if args.command == "convert-otel":
        trace = json.loads(Path(args.trace_file).read_text(encoding="utf-8"))
        otel = trace_to_otel(trace)
        Path(args.otel_file).write_text(json.dumps(otel, indent=2), encoding="utf-8")
        print(f"Wrote OTEL JSON {args.otel_file}")
    if args.command == "convert-from-otel":
        otel = json.loads(Path(args.otel_file).read_text(encoding="utf-8"))
        trace = otel_to_trace(otel)
        Path(args.trace_file).write_text(json.dumps(trace, indent=2), encoding="utf-8")
        print(f"Wrote Agent Runtime trace JSON {args.trace_file}")
    if args.command == "export-otel":
        otel = client.export_task_otel(args.task_id)
        Path(args.otel_file).write_text(json.dumps(otel, indent=2), encoding="utf-8")
        print(f"Exported task {args.task_id} to OTEL JSON {args.otel_file}")
    if args.command == "trace":
        wrapped_command = args.wrapped_command
        if wrapped_command and wrapped_command[0] == "--":
            wrapped_command = wrapped_command[1:]
        result = capture_command(
            name=args.name,
            command=wrapped_command,
            project_id=args.project,
            trace_dir=Path(args.trace_dir),
            capture_full_logs=args.capture_full_logs,
            capture_diff=args.capture_diff,
            upload=args.upload,
            base_url=args.base_url,
        )
        print(f"Wrote trace {result.trace_path} for task {result.task_id}")
        print(f"Command exit code: {result.exit_code}")
        if result.uploaded:
            print(f"Uploaded {result.upload_response['event_count']} events for task {result.upload_response['task_id']}")
    if args.command == "integrate" and args.integration == "aider":
        wrapped_command = args.wrapped_command
        if wrapped_command and wrapped_command[0] == "--":
            wrapped_command = wrapped_command[1:]
        result = capture_aider(
            name=args.name,
            command=wrapped_command or ["aider"],
            project_id=args.project,
            repo_path=Path(args.repo),
            trace_dir=Path(args.trace_dir),
            capture_full_logs=args.capture_full_logs,
            upload=args.upload,
            base_url=args.base_url,
        )
        print(f"Wrote Aider integration trace {result.trace_path} for task {result.task_id}")
        print(f"Aider command exit code: {result.exit_code}")
        if result.uploaded:
            print(f"Uploaded {result.upload_response['event_count']} events for task {result.upload_response['task_id']}")


if __name__ == "__main__":
    main()
