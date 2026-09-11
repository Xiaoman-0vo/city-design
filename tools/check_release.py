"""Check public package structure and common accidental private-file leakage."""

import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/city-design"


def main() -> int:
    """Check only public source, reporting unexpected paths and artifacts."""
    errors = []
    required = [
        "README.md",
        "LICENSE",
        ".gitignore",
        ".agents/plugins/marketplace.json",
        ".github/workflows/test.yml",
        "plugins/city-design/LICENSE",
        "plugins/city-design/.codex-plugin/plugin.json",
        "plugins/city-design/config/local-binding.example.json",
    ]
    for name in required:
        if not (ROOT / name).is_file():
            errors.append("Missing " + name)
    manifest = json.loads((PLUGIN / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    if manifest.get("name") != "city-design" or not manifest.get("version"):
        errors.append("Invalid plugin identity")
    marketplace = json.loads(
        (ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8")
    )
    entry = next((x for x in marketplace["plugins"] if x.get("name") == "city-design"), None)
    if not entry or (ROOT / entry["source"]["path"]).resolve() != PLUGIN:
        errors.append("Marketplace source mismatch")
    if (ROOT / "LICENSE").read_bytes() != (PLUGIN / "LICENSE").read_bytes():
        errors.append("License copies differ")
    private_path = re.compile(r"/(?:Users|home)/[^/\s]+/|[A-Z]:[\\/]Users[\\/]", re.I)
    credentials = re.compile(
        r"(?:ghp_|github_pat_)[A-Za-z0-9_]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    )
    excluded = {".git", "__pycache__", ".ruff_cache", ".venv", "demo-project", "demo-rhino", "dist"}
    forbidden_extensions = {".3dm", ".dwg", ".qgz", ".gpkg", ".heic", ".jpg", ".pdf"}
    count = 0
    for path in ROOT.rglob("*"):
        rel = path.relative_to(ROOT)
        if any(x in excluded for x in rel.parts) or not path.is_file():
            continue
        count += 1
        if path.is_symlink():
            errors.append("Symlink in public source: " + str(rel))
            continue
        if (
            path.name == "local-binding.json"
            or path.name.startswith(".env")
            or path.suffix.lower() in forbidden_extensions
        ):
            errors.append("Private or unreviewed artifact: " + str(rel))
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeError:
            errors.append("Unexpected binary: " + str(rel))
            continue
        if private_path.search(content):
            errors.append("Personal absolute path: " + str(rel))
        if credentials.search(content):
            errors.append("Possible credential: " + str(rel))
        if path.suffix == ".json":
            try:
                json.loads(content)
            except ValueError:
                errors.append("Invalid JSON: " + str(rel))
    print(
        json.dumps(
            {
                "status": "PASSED" if not errors else "FAILED",
                "files_checked": count,
                "errors": errors,
                "scope": "Package structure and common leakage patterns; not a complete security audit",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return int(bool(errors))


if __name__ == "__main__":
    sys.exit(main())
