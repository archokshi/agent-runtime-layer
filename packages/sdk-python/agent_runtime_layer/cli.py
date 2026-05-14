import argparse
import json
import sys
from pathlib import Path

from agent_runtime_layer.capture import capture_command
from agent_runtime_layer.client import AgentRuntimeClient
from agent_runtime_layer.integrations.aider import capture_aider
from agent_runtime_layer.integrations.codex import (
    capture_codex_session_jsonl,
    codex_hook_status,
    install_codex_hooks,
    run_codex_hook,
    uninstall_codex_hooks,
)
from agent_runtime_layer.integrations.claude_code import (
    claude_hook_status,
    install_claude_hooks,
    run_claude_hook,
    uninstall_claude_hooks,
)
from agent_runtime_layer.integrations.cursor_agent import (
    cursor_capture_status,
    install_cursor_capture,
    run_cursor_stream,
    uninstall_cursor_capture,
)
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
    integrations_parser = subparsers.add_parser("integrations")
    integrations_subparsers = integrations_parser.add_subparsers(dest="action", required=True)
    for action in ("install", "uninstall", "status"):
        action_parser = integrations_subparsers.add_parser(action)
        action_subparsers = action_parser.add_subparsers(dest="integration", required=True)
        codex_parser = action_subparsers.add_parser("codex")
        codex_parser.add_argument("--repo", default=".")
        codex_parser.add_argument("--project", default=None)
        codex_parser.add_argument("--global", dest="global_install", action="store_true")
        claude_parser = action_subparsers.add_parser("claude-code")
        claude_parser.add_argument("--repo", default=".")
        claude_parser.add_argument("--project", default=None)
        cursor_parser = action_subparsers.add_parser("cursor")
        cursor_parser.add_argument("--repo", default=".")
        cursor_parser.add_argument("--project", default=None)
    codex_hook_parser = subparsers.add_parser("codex-hook")
    codex_hook_parser.add_argument("--event", required=True)
    codex_hook_parser.add_argument("--repo", default=".")
    codex_hook_parser.add_argument("--project", default=None)
    codex_session_parser = subparsers.add_parser("codex-session")
    codex_session_parser.add_argument("session_file")
    codex_session_parser.add_argument("--project", default="default")
    codex_session_parser.add_argument("--upload", action="store_true")
    codex_session_parser.add_argument("--trace-dir", default=".agent-runtime/traces")
    claude_hook_parser = subparsers.add_parser("claude-hook")
    claude_hook_parser.add_argument("--event", required=True)
    claude_hook_parser.add_argument("--repo", default=".")
    claude_hook_parser.add_argument("--project", default=None)
    cursor_stream_parser = subparsers.add_parser("cursor-stream")
    cursor_stream_parser.add_argument("--repo", default=".")
    cursor_stream_parser.add_argument("--project", default=None)
    cursor_stream_parser.add_argument("--name", default=None)
    proxy_parser = subparsers.add_parser("proxy", help="Phase 1.9: Start the Agentium Context Fabric proxy")
    proxy_parser.add_argument("--port", type=int, default=8100)
    proxy_parser.add_argument("--anthropic-url", default="https://api.anthropic.com")
    budget_init_parser = subparsers.add_parser("budget-init", help="Phase 1.8: Write default .agentium/config.yaml")
    budget_init_parser.add_argument("--repo", default=".")
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
    if args.command == "integrations" and args.integration == "codex":
        repo_path = Path(args.repo)
        if args.action == "install":
            config_path = install_codex_hooks(
                repo_path=repo_path,
                base_url=args.base_url,
                project_id=args.project,
                global_install=args.global_install,
            )
            scope = "global" if args.global_install else "repo-local"
            print(f"Installed {scope} Codex hooks at {config_path}")
        if args.action == "uninstall":
            config_path = uninstall_codex_hooks(repo_path=repo_path, global_install=args.global_install)
            scope = "global" if args.global_install else "repo-local"
            print(f"Removed Agent Runtime {scope} Codex hooks from {config_path}")
        if args.action == "status":
            status = codex_hook_status(repo_path=repo_path, global_install=args.global_install)
            print(json.dumps(status, indent=2))
    if args.command == "integrations" and args.integration == "claude-code":
        repo_path = Path(args.repo)
        if args.action == "install":
            config_path = install_claude_hooks(repo_path=repo_path, base_url=args.base_url, project_id=args.project)
            print(f"Installed Claude Code hooks at {config_path}")
        if args.action == "uninstall":
            config_path = uninstall_claude_hooks(repo_path=repo_path)
            print(f"Removed Agent Runtime Claude Code hooks from {config_path}")
        if args.action == "status":
            status = claude_hook_status(repo_path=repo_path)
            print(json.dumps(status, indent=2))
    if args.command == "integrations" and args.integration == "cursor":
        repo_path = Path(args.repo)
        if args.action == "install":
            config_path = install_cursor_capture(repo_path=repo_path, project_id=args.project)
            print(f"Installed Cursor capture helper at {config_path}")
            print("Run Cursor with: cursor-agent --print --output-format stream-json | agent-runtime cursor-stream")
        if args.action == "uninstall":
            config_path = uninstall_cursor_capture(repo_path=repo_path)
            print(f"Removed Agent Runtime Cursor capture helper from {config_path}")
        if args.action == "status":
            status = cursor_capture_status(repo_path=repo_path)
            print(json.dumps(status, indent=2))
    if args.command == "codex-hook":
        result = run_codex_hook(
            event_name=args.event,
            repo_path=Path(args.repo),
            base_url=args.base_url,
            project_id=args.project,
        )
        if result.reason:
            print(f"Agent Runtime Codex hook skipped: {result.reason}", file=sys.stderr)
        else:
            print(
                f"Agent Runtime Codex hook handled {result.event_name}"
                f" task={result.task_id or 'none'} events={result.emitted_events}",
                file=sys.stderr,
            )
    if args.command == "codex-session":
        result = capture_codex_session_jsonl(
            session_file=Path(args.session_file),
            project_id=args.project,
            trace_dir=Path(args.trace_dir),
            upload=args.upload,
            base_url=args.base_url,
        )
        print(f"Wrote Codex session trace {result.trace_path} for task {result.task_id}")
        print(f"Captured {result.event_count} events from Codex session JSONL")
        if result.uploaded and result.upload_response:
            print(f"Uploaded {result.upload_response['event_count']} events for task {result.upload_response['task_id']}")
    if args.command == "claude-hook":
        result = run_claude_hook(
            event_name=args.event,
            repo_path=Path(args.repo),
            base_url=args.base_url,
            project_id=args.project,
        )
        if result.reason:
            print(f"Agent Runtime Claude Code hook skipped: {result.reason}", file=sys.stderr)
        else:
            print(
                f"Agent Runtime Claude Code hook handled {result.event_name}"
                f" task={result.task_id or 'none'} events={result.emitted_events}",
                file=sys.stderr,
            )
    if args.command == "cursor-stream":
        result = run_cursor_stream(
            repo_path=Path(args.repo),
            base_url=args.base_url,
            project_id=args.project,
            name=args.name,
        )
        if result.reason:
            print(f"Agent Runtime Cursor stream skipped: {result.reason}", file=sys.stderr)
        else:
            print(
                f"Agent Runtime Cursor stream handled task={result.task_id or 'none'} events={result.emitted_events}",
                file=sys.stderr,
            )
    if args.command == "proxy":
        from agent_runtime_layer.proxy import run_proxy
        run_proxy(
            port=args.port,
            agentium_url=args.base_url,
            anthropic_url=args.anthropic_url,
        )
    if args.command == "budget-init":
        from agent_runtime_layer.budget import write_default_config
        config_path = write_default_config(repo_path=args.repo)
        print(f"Wrote Agentium budget config: {config_path}")
        print("Edit .agentium/config.yaml to set your budget limits, then re-install hooks.")


if __name__ == "__main__":
    main()
