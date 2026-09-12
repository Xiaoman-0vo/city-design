"""Check connection setup does not overwrite state, leak tokens or overstate readiness."""

import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import connections as c
from probe_qgis import evaluate


class ConnectionTests(unittest.TestCase):
    """Exercise path escaping, immutable input and configuration preservation."""

    def test_existing_servers_preserved(self) -> None:
        entry = {"rhino": {"command": "new-router", "args": []}}
        pending, preserved = c.registration_plan(entry, {"rhino": {"command": "old-router"}})
        self.assertEqual(pending, {})
        self.assertEqual(preserved, ["rhino"])

    def test_unrecognized_endpoint_rejected(self) -> None:
        with self.assertRaises(ValueError):
            c.registration_plan({"autodesk-help": {"url": "https://example.org"}}, {})

    def test_secret_is_never_embedded_and_paths_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            token = root / "private token.txt"
            token.write_text("private-test-secret", encoding="utf-8")
            executable = root / "python with spaces"
            executable.touch()
            args = argparse.Namespace(
                output=str(root / "连接"),
                qgis_python=str(executable),
                token_file=str(token),
                port=9988,
                rhino_router=str(executable),
                rhino_version="9",
                autodesk_help=True,
            )
            c.prepare(args)
            plan = (root / "连接/connections.json").read_text(encoding="utf-8")
            config = (root / "连接/codex-mcp.toml").read_text(encoding="utf-8")
            self.assertNotIn("private-test-secret", plan + config)
            self.assertEqual(tomllib.loads(config)["mcp_servers"], json.loads(plan)["servers"])
            with self.assertRaises(ValueError):
                c.prepare(args)

    def test_invalid_options_fail_before_output(self) -> None:
        for port in [0, 65536, True]:
            with self.assertRaises(ValueError):
                c.make_entries(None, None, port, None, "8", True, Path("launcher"))
        with self.assertRaises(ValueError):
            c.make_entries("python", None, 9876, None, "8", False, Path("launcher"))

    def test_checksum_failure_does_not_create_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "new"
            with self.assertRaises(ValueError):
                c.unpack_qgis(b"bad archive", dest)
            self.assertFalse(dest.exists())

    def test_archive_traversal_rejected(self) -> None:
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w") as z:
            z.writestr(f"qgis-mcp-{c.QGIS_COMMIT}/../escape", "data")
        payload = data.getvalue()
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(c, "QGIS_SHA256", hashlib.sha256(payload).hexdigest()):
                with self.assertRaises(ValueError):
                    c.unpack_qgis(payload, Path(tmp) / "new")
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_register_dry_run_does_not_modify_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "config.toml"
            config.write_text('[mcp_servers.rhino]\ncommand = "old-router"\n', encoding="utf-8")
            original = config.read_bytes()
            plan = root / "plan.json"
            c.write_json(
                plan,
                {
                    "servers": {
                        "rhino": {"command": "new", "args": []},
                        "autodesk-help": {"url": c.HELP_URL},
                    }
                },
            )
            with (
                patch.object(c, "codex_config_path", return_value=config),
                patch.object(c.subprocess, "run") as run,
            ):
                result = c.register(str(plan), "codex", False)
                run.assert_not_called()
            self.assertEqual(result["add"], ["autodesk-help"])
            self.assertEqual(config.read_bytes(), original)

    def test_register_apply_backup_readback_and_noop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "config.toml"
            original = b'model = "test-model"\n[mcp_servers.rhino]\ncommand = "keep-router"\n'
            config.write_bytes(original)
            plan = root / "plan.json"
            c.write_json(plan, {"servers": {"autodesk-help": {"url": c.HELP_URL}}})

            def fake_cli(command: list, **kwargs: object) -> None:
                self.assertEqual(
                    command, ["codex", "mcp", "add", "autodesk-help", "--url", c.HELP_URL]
                )
                config.write_text(
                    original.decode()
                    + "\n[mcp_servers.autodesk-help]\nurl = "
                    + json.dumps(c.HELP_URL)
                    + "\n",
                    encoding="utf-8",
                )

            with (
                patch.object(c, "codex_config_path", return_value=config),
                patch.object(c.subprocess, "run", side_effect=fake_cli) as run,
            ):
                result = c.register(str(plan), "codex", True)
                self.assertEqual(result["status"], "REGISTERED")
                self.assertEqual(Path(result["backup"]).read_bytes(), original)
                self.assertEqual(
                    c.register(str(plan), "codex", True)["status"], "EXISTING_PRESERVED"
                )
                self.assertEqual(run.call_count, 1)
            self.assertEqual(len(list(root.glob("*.bak"))), 1)

    def test_ping_without_version_check_is_not_pass(self) -> None:
        self.assertEqual(evaluate({"pong": True}, {})["status"], "NEEDS_ATTENTION")

    def test_matched_connection_does_not_accept_drawing(self) -> None:
        result = evaluate({"pong": True}, {"checks": [{"name": "version_match", "status": "ok"}]})
        self.assertEqual(result["status"], "CONNECTED_VERSION_MATCHED")
        self.assertEqual(result["drawing_acceptance"], "NOT_TESTED")

    def test_version_mismatch_is_reported(self) -> None:
        result = evaluate(
            {"pong": True}, {"checks": [{"name": "version_match", "status": "mismatch"}]}
        )
        self.assertFalse(result["version_match"])


if __name__ == "__main__":
    unittest.main()
