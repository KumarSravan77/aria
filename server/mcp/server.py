"""Dependency-free, read-only MCP stdio server for ARIA workflows."""
from __future__ import annotations
import json, os, sys, requests

API_URL = os.getenv("ARIA_API_URL", "http://localhost:8000").rstrip("/")
TOKEN = os.getenv("ARIA_API_TOKEN", "")
TOOLS = [
    {"name": "aria_incident_timeline", "description": "Read an authorized incident evidence timeline.", "inputSchema": {"type": "object", "properties": {"incident_id": {"type": "string"}}, "required": ["incident_id"]}},
    {"name": "aria_service_observability", "description": "Read correlated metrics, logs, traces and topology.", "inputSchema": {"type": "object", "properties": {"service": {"type": "string"}}, "required": ["service"]}},
    {"name": "aria_sdlc_context", "description": "Read code, deployment, alert, decision and incident correlations.", "inputSchema": {"type": "object", "properties": {"service": {"type": "string"}, "window_hours": {"type": "integer", "default": 168}}, "required": ["service"]}},
    {"name": "aria_investigate", "description": "Start an evidence-only investigation; cannot execute remediation.", "inputSchema": {"type": "object", "properties": {"incident_id": {"type": "string"}, "service": {"type": "string"}, "environment": {"type": "string", "default": "prod"}, "severity": {"type": "string", "default": "P2"}, "symptoms": {"type": "array", "items": {"type": "string"}}}, "required": ["incident_id", "service"]}},
]

def api(method: str, path: str, payload: dict | None = None) -> dict:
    response = requests.request(method, f"{API_URL}{path}", headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}, json=payload, timeout=30)
    response.raise_for_status(); return response.json()

def call_tool(name: str, args: dict) -> dict:
    if name == "aria_incident_timeline": result = api("GET", f"/incidents/{args['incident_id']}/timeline")
    elif name == "aria_service_observability": result = api("GET", f"/observability/{args['service']}")
    elif name == "aria_sdlc_context": result = api("GET", f"/oncall/sdlc/{args['service']}/context?window_hours={int(args.get('window_hours', 168))}")
    elif name == "aria_investigate": result = api("POST", "/agents/investigate", {"incident_id": args["incident_id"], "service": args["service"], "environment": args.get("environment", "prod"), "severity": args.get("severity", "P2"), "symptoms": args.get("symptoms", []), "signals": {}})
    else: raise ValueError(f"Unknown tool: {name}")
    return {"content": [{"type": "text", "text": json.dumps(result, indent=2, default=str)}], "isError": False}

def handle(message: dict) -> dict | None:
    method, request_id = message.get("method"), message.get("id")
    if method == "notifications/initialized": return None
    if method == "initialize": result = {"protocolVersion": "2025-06-18", "capabilities": {"tools": {"listChanged": False}}, "serverInfo": {"name": "aria-oncall", "version": "1.0.0"}}
    elif method == "tools/list": result = {"tools": TOOLS}
    elif method == "tools/call": result = call_tool(message.get("params", {}).get("name", ""), message.get("params", {}).get("arguments") or {})
    elif method == "ping": result = {}
    else: return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}
    return {"jsonrpc": "2.0", "id": request_id, "result": result}

def main() -> None:
    for line in sys.stdin:
        try:
            response = handle(json.loads(line))
            if response is not None: print(json.dumps(response), flush=True)
        except Exception as exc: print(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32000, "message": str(exc)}}), flush=True)

if __name__ == "__main__": main()
