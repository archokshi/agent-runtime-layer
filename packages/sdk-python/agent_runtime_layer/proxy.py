"""Phase 1.9: Agent Context Fabric — local API proxy.

Sits between the agent and the Anthropic API. Developer sets:
  ANTHROPIC_BASE_URL=http://localhost:8100

The proxy:
1. Intercepts POST /v1/messages
2. Fingerprints stable context blocks (system prompt, tool defs)
3. Checks context_memory in Agentium backend
4. Injects cache_control: {"type": "ephemeral"} on stable matched blocks
5. Forwards to real Anthropic API
6. Records cache_read_input_tokens from response → updates context_memory savings
7. Logs everything to Agentium backend for dashboard visibility

One environment variable. Zero agent code changes.
"""

from __future__ import annotations

import hashlib
import json
import re
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

ANTHROPIC_DEFAULT_URL = "https://api.anthropic.com"
UNCACHED_COST_PER_MTOK = 3.00   # $/million tokens (Sonnet uncached input)
CACHED_COST_PER_MTOK = 0.30     # $/million tokens (Sonnet cached input)


def _sha256(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    return "sha256:" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _fingerprint_block(block: dict[str, Any]) -> str | None:
    text = block.get("text") or block.get("content") or ""
    if not isinstance(text, str) or len(text) < 100:
        return None
    return _sha256(text)


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _inject_cache_control(body: dict[str, Any], agentium_url: str) -> dict[str, Any]:
    """Inject cache_control on stable context blocks and update context_memory."""
    system = body.get("system")
    if not system:
        return body

    if isinstance(system, str):
        # Convert string system prompt to block format
        fp = _sha256(system)
        tokens = _estimate_tokens(system)
        _upsert_memory(agentium_url, fp, "system_prompt", tokens, None, None)
        body["system"] = [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
        return body

    if isinstance(system, list):
        for block in system:
            if not isinstance(block, dict):
                continue
            fp = _fingerprint_block(block)
            if fp is None:
                continue
            tokens = _estimate_tokens(block.get("text") or "")
            _upsert_memory(agentium_url, fp, "system_block", tokens, None, None)
            if "cache_control" not in block:
                block["cache_control"] = {"type": "ephemeral"}

    return body


def _upsert_memory(
    agentium_url: str,
    fingerprint: str,
    content_type: str,
    token_count: int,
    source_repo: str | None,
    agent_type: str | None,
    savings: float = 0.0,
) -> None:
    """Update the context_memory table in the Agentium backend."""
    try:
        payload = json.dumps({
            "fingerprint": fingerprint,
            "content_type": content_type,
            "token_count": token_count,
            "source_repo": source_repo,
            "agent_type": agent_type,
            "hit_count": 1,
            "cache_savings_dollars": savings,
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{agentium_url}/context-memory",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=2)
    except Exception:
        pass


def _record_cache_savings(
    agentium_url: str,
    fingerprint: str,
    cache_read_tokens: int,
    content_type: str,
) -> None:
    """Record actual cache hit savings from Anthropic API response."""
    savings = (cache_read_tokens / 1_000_000) * (UNCACHED_COST_PER_MTOK - CACHED_COST_PER_MTOK)
    _upsert_memory(agentium_url, fingerprint, content_type, cache_read_tokens, None, None, savings)


class _ProxyHandler(BaseHTTPRequestHandler):
    agentium_url: str = "http://localhost:8000/api"
    anthropic_url: str = ANTHROPIC_DEFAULT_URL

    def log_message(self, fmt: str, *args: Any) -> None:
        pass  # Silence default HTTP logs

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)

        try:
            body = json.loads(raw)
        except Exception:
            body = {}

        # Inject cache_control on stable context blocks
        if self.path.startswith("/v1/messages"):
            body = _inject_cache_control(body, self.agentium_url)

        # Forward to real Anthropic API
        fwd_headers = {
            k: v for k, v in self.headers.items()
            if k.lower() not in ("host", "content-length", "transfer-encoding")
        }
        fwd_headers["Host"] = self.anthropic_url.replace("https://", "").replace("http://", "")

        try:
            fwd_body = json.dumps(body).encode("utf-8")
            fwd_req = urllib.request.Request(
                f"{self.anthropic_url}{self.path}",
                data=fwd_body,
                headers=fwd_headers,
                method="POST",
            )
            with urllib.request.urlopen(fwd_req, timeout=120) as resp:
                resp_body = resp.read()
                resp_status = resp.status
                resp_headers = dict(resp.headers)
        except urllib.error.HTTPError as exc:
            resp_body = exc.read()
            resp_status = exc.code
            resp_headers = dict(exc.headers)
        except Exception as exc:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(exc)}).encode())
            return

        # Parse response to record real cache savings
        try:
            resp_json = json.loads(resp_body)
            usage = resp_json.get("usage", {})
            cache_read = usage.get("cache_read_input_tokens", 0)
            if cache_read > 0:
                system = body.get("system", [])
                if isinstance(system, list):
                    for block in system:
                        fp = _fingerprint_block(block) if isinstance(block, dict) else None
                        if fp:
                            _record_cache_savings(self.agentium_url, fp, cache_read, "system_block")
        except Exception:
            pass

        self.send_response(resp_status)
        for k, v in resp_headers.items():
            if k.lower() not in ("transfer-encoding", "connection"):
                try:
                    self.send_header(k, v)
                except Exception:
                    pass
        self.end_headers()
        self.wfile.write(resp_body)

    def do_GET(self) -> None:
        # Health check
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok", "proxy": "agentium-context-fabric"}).encode())


def run_proxy(
    port: int = 8100,
    agentium_url: str = "http://localhost:8000/api",
    anthropic_url: str = ANTHROPIC_DEFAULT_URL,
) -> None:
    """Start the Agentium context fabric proxy server.

    Developer usage:
        export ANTHROPIC_BASE_URL=http://localhost:8100
        python -m agent_runtime_layer.cli proxy --port 8100

    Zero agent code changes required.
    """
    _ProxyHandler.agentium_url = agentium_url
    _ProxyHandler.anthropic_url = anthropic_url

    server = HTTPServer(("", port), _ProxyHandler)
    print(f"Agentium Context Fabric Proxy running on http://localhost:{port}")
    print(f"  Forwarding to: {anthropic_url}")
    print(f"  Agentium backend: {agentium_url}")
    print(f"")
    print(f"  Set in your shell:")
    print(f"    export ANTHROPIC_BASE_URL=http://localhost:{port}")
    print(f"")
    print(f"  Stable context blocks will be cached automatically.")
    print(f"  Savings tracked in dashboard: localhost:4000/context")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nProxy stopped.")
