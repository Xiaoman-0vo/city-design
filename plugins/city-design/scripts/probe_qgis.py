"""Read-only MCP initialize, tool discovery, ping and version-match check for QGIS."""

from __future__ import annotations

import argparse
from datetime import timedelta
import json
import os
from pathlib import Path


def evaluate(ping: dict, diagnostic: dict) -> dict:
    """Keep native connection and version agreement separate from model acceptance."""
    checks = diagnostic.get("checks", [])
    version = next((c for c in checks if c.get("name") == "version_match"), {})
    connected = ping.get("pong") is True
    matched = version.get("status") == "ok"
    return {
        "status": "CONNECTED_VERSION_MATCHED" if connected and matched else "NEEDS_ATTENTION",
        "native_ping": connected,
        "version_match": matched,
        "drawing_acceptance": "NOT_TESTED",
        "scope": "MCP discovery, ping and version check; no geometry modification",
    }


async def probe(plan: dict) -> dict:
    """Use the external server's installed MCP SDK; suppress upstream logs in the result."""
    import anyio
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    entry = plan["servers"]["qgis"]
    parameters = StdioServerParameters(command=entry["command"], args=entry["args"])
    with open(os.devnull, "w", encoding="utf-8") as errors:
        with anyio.fail_after(25):
            async with stdio_client(parameters, errlog=errors) as (reader, writer):
                async with ClientSession(
                    reader, writer, read_timeout_seconds=timedelta(seconds=10)
                ) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    names = {tool.name for tool in tools.tools}
                    if not {"ping", "diagnose"} <= names:
                        return {"status": "MCP_TOOLS_MISSING", "drawing_acceptance": "NOT_TESTED"}
                    ping = await session.call_tool("ping", {})
                    if ping.isError:
                        return {
                            "status": "MCP_READY_QGIS_UNAVAILABLE",
                            "native_ping": False,
                            "drawing_acceptance": "NOT_TESTED",
                        }
                    diagnostic = await session.call_tool("diagnose", {})
                    if diagnostic.isError:
                        return {"status": "DIAGNOSTIC_FAILED", "drawing_acceptance": "NOT_TESTED"}
                    result = evaluate(
                        ping.structuredContent or {}, diagnostic.structuredContent or {}
                    )
                    result["mcp_tools_discovered"] = len(names)
                    return result


def main() -> int:
    """Print only a sanitized connection outcome, never an upstream error body."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True)
    args = parser.parse_args()
    try:
        import anyio

        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
        result = anyio.run(probe, plan)
    except (OSError, ValueError, KeyError, ImportError, TimeoutError, ExceptionGroup) as exc:
        result = {
            "status": "CONNECTION_UNAVAILABLE",
            "error_type": type(exc).__name__,
            "drawing_acceptance": "NOT_TESTED",
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "CONNECTED_VERSION_MATCHED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
