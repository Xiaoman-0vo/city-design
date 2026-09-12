"""Prepare optional application connections without replacing existing MCP entries."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import time
import tomllib
from urllib.request import urlopen
import zipfile

PLUGIN = Path(__file__).resolve().parents[1]
QGIS_COMMIT = "29931a0eea80bf30a40b0b18ca6c60a8191521b6"
QGIS_SHA256 = "6a8c231eea0acaa124c5bc5cbaa9b995d82804470b57f7e87e28b6a276885a14"
QGIS_URL = f"https://github.com/nkarasiak/qgis-mcp/archive/{QGIS_COMMIT}.zip"
HELP_URL = "https://developer.api.autodesk.com/knowledge/public/v1/mcp"


def write_json(path: Path, value: dict) -> None:
    """Create a private receipt; refuse overwriting any existing file."""
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    path.chmod(0o600)


def unpack_qgis(data: bytes, destination: Path) -> Path:
    """Verify the immutable upstream archive before extracting into a new directory."""
    if hashlib.sha256(data).hexdigest() != QGIS_SHA256:
        raise ValueError("QGIS archive checksum mismatch; no files extracted")
    prefix = f"qgis-mcp-{QGIS_COMMIT}"
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for entry in archive.infolist():
            parts = PurePosixPath(entry.filename).parts
            if (
                not parts
                or parts[0] != prefix
                or ".." in parts
                or "\\" in entry.filename
                or (entry.external_attr >> 16) & 0o170000 == 0o120000
            ):
                raise ValueError("Unsafe archive member")
        destination.mkdir(parents=True, exist_ok=False)
        archive.extractall(destination)
    return destination / prefix


def stage_qgis(output: str, install: bool, uv: str) -> dict:
    """Download matching plugin/server sources; optionally install locked server dependencies."""
    target = Path(output).expanduser().resolve()
    if target.exists():
        raise ValueError("Output exists; preserve it and select a new staging directory")
    with urlopen(QGIS_URL, timeout=40) as response:
        data = response.read(10 * 1024 * 1024 + 1)
    source = unpack_qgis(data, target)
    plugin_zip = target / "qgis-mcp-plugin.zip"
    with zipfile.ZipFile(plugin_zip, "x", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted((source / "qgis_mcp_plugin").rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source).as_posix())
        archive.write(source / "LICENSE", "qgis_mcp_plugin/UPSTREAM_LICENSE.txt")
    receipt = {
        "status": "STAGED",
        "source": str(source),
        "upstream_commit": QGIS_COMMIT,
        "archive_sha256": QGIS_SHA256,
        "plugin_zip": str(plugin_zip),
        "license": "GPL-2.0; separate upstream dependency, not relicensed under City Design MIT",
        "native_plugin_installed": False,
        "next_step": "Install the ZIP in the intended QGIS profile, then configure its token and start it",
    }
    write_json(target / "upstream-receipt.json", receipt)
    if install:
        # Run only after checksum validation, with the upstream lockfile retained.
        subprocess.run([uv, "sync", "--frozen", "--no-dev"], cwd=source, check=True, timeout=300)
        receipt["status"] = "SERVER_INSTALLED_PLUGIN_STAGED"
        write_json(target / "server-install-receipt.json", receipt)
    return receipt


def existing_file(value: str) -> str:
    """Resolve a required local file without disclosing its contents."""
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise ValueError("A supplied executable or token file does not exist")
    return str(path)


def make_entries(
    qgis_python: str | None,
    token_file: str | None,
    port: int,
    router: str | None,
    rhino_version: str,
    autodesk_help: bool,
    launcher: Path,
) -> dict:
    """Create explicit connection entries; secrets stay in a separate file."""
    if isinstance(port, bool) or not 1 <= port <= 65535:
        raise ValueError("Port must be between 1 and 65535")
    if rhino_version not in {"8", "9"}:
        raise ValueError("Rhino version must be 8 or 9")
    if bool(qgis_python) != bool(token_file):
        raise ValueError("QGIS requires both --qgis-python and --token-file")
    entries = {}
    if qgis_python:
        entries["qgis"] = {
            "command": existing_file(qgis_python),
            "args": [
                str(launcher),
                "serve-qgis",
                "--token-file",
                existing_file(token_file),
                "--port",
                str(port),
            ],
        }
    if router:
        entries["rhino"] = {
            "command": existing_file(router),
            "args": ["--default-version", rhino_version],
        }
    if autodesk_help:
        entries["autodesk-help"] = {"url": HELP_URL}
    if not entries:
        raise ValueError("Select at least one connection; see catalog and docs/CONNECTIONS.md")
    return entries


def prepare(args: argparse.Namespace) -> dict:
    """Write a relocatable launcher snapshot and a local, reviewable connection plan."""
    output = Path(args.output).expanduser().resolve()
    if output.exists():
        raise ValueError("Output already exists; use its plan or select a new directory")
    launcher = output / "connections.py"
    entries = make_entries(
        args.qgis_python,
        args.token_file,
        args.port,
        args.rhino_router,
        args.rhino_version,
        args.autodesk_help,
        launcher,
    )
    output.mkdir(parents=True, exist_ok=False)
    output.chmod(0o700)
    shutil.copy2(Path(__file__), launcher)
    plan = {
        "schema_version": 1,
        "servers": entries,
        "scope": "Connection registration only; no drawing edits or native acceptance",
    }
    write_json(output / "connections.json", plan)
    # JSON basic strings are valid TOML for these values, including Windows paths.
    lines = []
    for name, entry in entries.items():
        lines.append(f"[mcp_servers.{name}]")
        lines.extend(
            f"{key} = {json.dumps(value, ensure_ascii=False)}" for key, value in entry.items()
        )
        lines.append("")
    (output / "codex-mcp.toml").write_text("\n".join(lines), encoding="utf-8")
    return {
        "status": "PREPARED",
        "plan": str(output / "connections.json"),
        "names": list(entries),
        "registered": False,
    }


def registration_plan(entries: dict, existing: dict) -> tuple[dict, list[str]]:
    """Preserve every pre-existing server, even when its command differs."""
    if not entries or set(entries) - {"qgis", "rhino", "autodesk-help"}:
        raise ValueError("Unknown or empty connection plan")
    for name, entry in entries.items():
        if name == "autodesk-help":
            if entry != {"url": HELP_URL}:
                raise ValueError("Unexpected Autodesk Help endpoint")
        elif (
            set(entry) != {"command", "args"}
            or not isinstance(entry["command"], str)
            or not isinstance(entry["args"], list)
            or not all(isinstance(x, str) for x in entry["args"])
        ):
            raise ValueError("Invalid stdio entry")
    return {k: v for k, v in entries.items() if k not in existing}, sorted(
        set(entries) & set(existing)
    )


def codex_config_path() -> Path:
    """Locate the current Codex configuration without changing environment variables."""
    return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "config.toml"


def register(plan_path: str, codex: str, apply: bool) -> dict:
    """Add only absent entries using Codex's CLI, keeping a private config backup."""
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    config = codex_config_path()
    raw = config.read_bytes() if config.exists() else b""
    existing = tomllib.loads(raw.decode("utf-8")).get("mcp_servers", {})
    pending, preserved = registration_plan(plan["servers"], existing)
    result = {"status": "PLAN_ONLY", "add": list(pending), "existing_preserved": preserved}
    if not apply:
        return result
    if not pending:
        return {**result, "status": "EXISTING_PRESERVED"}
    if raw:
        backup = config.with_name(f"config.toml.city-design.{time.time_ns()}.bak")
        with backup.open("xb") as stream:
            stream.write(raw)
        backup.chmod(0o600)
        result["backup"] = str(backup)
    # Re-read before each mutation; do not replace an entry added concurrently.
    for name, entry in pending.items():
        latest = tomllib.loads(config.read_text(encoding="utf-8")) if config.exists() else {}
        if name in latest.get("mcp_servers", {}):
            raise ValueError("Connection added concurrently; rerun plan to reconcile")
        command = [codex, "mcp", "add", name]
        command += (
            ["--url", entry["url"]] if "url" in entry else ["--", entry["command"], *entry["args"]]
        )
        subprocess.run(command, check=True, timeout=30, capture_output=True)
        readback = tomllib.loads(config.read_text(encoding="utf-8"))["mcp_servers"][name]
        if any(readback.get(k) != v for k, v in entry.items()):
            raise RuntimeError("MCP registration readback differs; inspect config and backup")
    result["status"] = "REGISTERED" if pending else "EXISTING_PRESERVED"
    result["next_step"] = (
        "Start a new Codex session and verify live tools before operating drawings"
    )
    return result


def serve_qgis(token_file: str, port: int) -> None:
    """Start the separately installed upstream server with a private loopback token."""
    if not 1 <= port <= 65535:
        raise ValueError("Invalid QGIS port")
    token = Path(token_file).expanduser().read_text(encoding="utf-8").strip()
    if not token:
        raise ValueError("QGIS token file is empty; set the same token in the QGIS plugin")
    # Do not inherit remote/multi-instance overrides from an unrelated terminal session.
    os.environ.pop("QGIS_MCP_INSTANCES", None)
    os.environ["QGIS_MCP_HOST"] = "127.0.0.1"
    os.environ["QGIS_MCP_PORT"] = str(port)
    os.environ["QGIS_MCP_TOKEN"] = token
    os.environ["QGIS_MCP_LOG_FILE"] = str(
        Path(token_file).expanduser().resolve().parent / "qgis-mcp.log"
    )
    from qgis_mcp.server import main as upstream_main

    upstream_main()


def main() -> int:
    """Dispatch setup commands; never dump tokens or captured subprocess output."""
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("catalog")
    stage = sub.add_parser("stage-qgis")
    stage.add_argument("--output", required=True)
    stage.add_argument("--install-server", action="store_true")
    stage.add_argument("--uv", default="uv")
    prep = sub.add_parser("prepare")
    prep.add_argument("--output", required=True)
    prep.add_argument("--qgis-python")
    prep.add_argument("--token-file")
    prep.add_argument("--port", type=int, default=9876)
    prep.add_argument("--rhino-router")
    prep.add_argument("--rhino-version", choices=["8", "9"], default="8")
    prep.add_argument("--autodesk-help", action="store_true")
    reg = sub.add_parser("register")
    reg.add_argument("--plan", required=True)
    reg.add_argument("--codex", default="codex")
    reg.add_argument("--apply", action="store_true")
    serve = sub.add_parser("serve-qgis")
    serve.add_argument("--token-file", required=True)
    serve.add_argument("--port", type=int, default=9876)
    args = parser.parse_args()
    try:
        if args.action == "catalog":
            result = json.loads(
                (PLUGIN / "references/connections.json").read_text(encoding="utf-8")
            )
        elif args.action == "stage-qgis":
            result = stage_qgis(args.output, args.install_server, args.uv)
        elif args.action == "prepare":
            result = prepare(args)
        elif args.action == "register":
            result = register(args.plan, args.codex, args.apply)
        else:
            serve_qgis(args.token_file, args.port)
            return 0
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (
        OSError,
        ValueError,
        KeyError,
        RuntimeError,
        subprocess.SubprocessError,
        ImportError,
    ) as exc:
        # Errors may originate in an upstream process; do not echo its raw logs or credentials.
        print(
            json.dumps(
                {
                    "status": "BLOCKED",
                    "error_type": type(exc).__name__,
                    "next_step": "Check paths, dependency installation, existing plan and private backup",
                }
            ),
            file=sys.stderr if args.action == "serve-qgis" else sys.stdout,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
