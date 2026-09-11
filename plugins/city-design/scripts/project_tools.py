"""Portable project setup and an original synthetic example (standard library)."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]


def read_binding(explicit: str | Path | None = None) -> tuple[dict, Path | None]:
    """Load optional private configuration with path-relative resolution."""
    selected = explicit or os.environ.get("CITY_DESIGN_CONFIG")
    path = (
        Path(selected).expanduser().resolve() if selected else PLUGIN / "config/local-binding.json"
    )
    if not path.exists():
        if selected:
            raise ValueError("Configuration file does not exist: " + str(path))
        return {"project_root": None, "applications": {}}, None
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Configuration must be a JSON object")
    for key in ("project_root", "mcp_python"):
        if value.get(key):
            p = Path(value[key]).expanduser()
            value[key] = str((path.parent / p).resolve() if not p.is_absolute() else p.resolve())
    value.setdefault("applications", {})
    if not isinstance(value["applications"], dict):
        raise ValueError("applications must be an object of application paths")
    return value, path


def write_json(path: str | Path, value: object) -> None:
    """Write finite JSON values as UTF-8."""
    Path(path).write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def create_project(
    destination: str | Path, *, demo: bool = False, with_rhino: bool = False
) -> dict:
    """Create a new project; refuse existing outputs and preserve partial failures."""
    out = Path(destination).expanduser().resolve()
    if out.exists():
        raise ValueError("Output already exists; preserve it and choose a new project directory")
    if with_rhino:
        try:
            import rhino3dm  # noqa: F401
        except ImportError as exc:
            raise ValueError(
                "Optional 3DM example requires requirements-rhino.txt; no software was opened"
            ) from exc
    out.mkdir(parents=True)
    for folder in ("state", "inputs", "outputs", "drawings"):
        (out / folder).mkdir()
    (out / "AGENTS.md").write_text(
        "# City Design project\n\nPreserve supplied originals. Read state/PROJECT_STATE.json before changes. "
        "Use stable object IDs and controlled output revisions. Record units and frame evidence. "
        "Synthetic inputs do not establish site accuracy or submission compliance.\n",
        encoding="utf-8",
    )
    state = {
        "schema_version": 1,
        "status": "INITIALIZED",
        "synthetic": demo,
        "frame_id": "SYNTHETIC_LOCAL_METRES" if demo else "UNCONFIRMED",
        "units": "m" if demo else "unconfirmed",
        "scale_status": "synthetic" if demo else "unconfirmed",
        "placement_status": "synthetic" if demo else "unconfirmed",
        "frozen_objects": [],
        "current_model": None,
    }
    write_json(out / "state/PROJECT_STATE.json", state)
    result = {
        "status": "CREATED",
        "project": str(out),
        "synthetic": demo,
        "native_applications_opened": False,
    }
    if not demo:
        return result
    scene = {
        "synthetic": True,
        "frame_id": state["frame_id"],
        "unit": "m",
        "storey_height": 3.0,
        "parcel": [[0, 0], [100, 0], [100, 110], [0, 110]],
        "buildings": [],
    }
    for i, (x, y, floors) in enumerate([(10, 15, 8), (55, 15, 12), (10, 60, 8), (55, 60, 12)], 1):
        scene["buildings"].append(
            {
                "feature_id": f"B{i:03d}",
                "x": x,
                "y": y,
                "width": 20,
                "depth": 25,
                "baseline_floors": 10,
                "floors": floors,
            }
        )
    write_json(out / "inputs/scene.json", scene)
    for source in (PLUGIN / "examples/drawing-manifests").glob("*.json"):
        (out / "drawings" / source.name).write_bytes(source.read_bytes())
    baseline = sum(b["width"] * b["depth"] * b["baseline_floors"] for b in scene["buildings"])
    revised = sum(b["width"] * b["depth"] * b["floors"] for b in scene["buildings"])
    result.update(
        {
            "scope": "Original synthetic demonstration; no site or statutory accuracy claim",
            "buildings": 4,
            "baseline_demo_floor_area_m2": baseline,
            "revised_demo_floor_area_m2": revised,
            "area_preserved": baseline == revised,
            "rhino_files": [],
        }
    )
    rectangles = "\n".join(
        f'<rect x="{b["x"] * 4 + 40}" y="{b["y"] * 4 + 40}" width="80" height="100" fill="#c5cfd6" stroke="#355269"/>'
        f'<text x="{b["x"] * 4 + 80}" y="{b["y"] * 4 + 93}" text-anchor="middle" font-size="14">{b["feature_id"]} · {b["floors"]}F</text>'
        for b in scene["buildings"]
    )
    (out / "outputs/plan.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="560" viewBox="0 0 480 560">'
        '<rect width="480" height="560" fill="#f6f5f0"/><text x="40" y="26" font-size="16">City Design · synthetic example</text>'
        '<rect x="40" y="40" width="400" height="440" fill="#e9ede1" stroke="#555"/>'
        + rectangles
        + '<text x="40" y="520" font-size="13">Metres · local frame · illustrative geometry</text></svg>',
        encoding="utf-8",
    )
    if with_rhino:
        result["rhino_files"] = create_rhino_example(out, scene)
        state["current_model"] = "outputs/revised.3dm"
    state["status"] = "DEMO_CHECKED"
    write_json(out / "state/PROJECT_STATE.json", state)
    write_json(out / "outputs/demo_receipt.json", result)
    return result


def create_rhino_example(out: Path, scene: dict) -> list[dict]:
    """Write original synthetic geometry and independently verify saved files."""
    import rhino3dm as r

    results = []
    for name, floor_key in (("baseline", "baseline_floors"), ("revised", "floors")):
        f = r.File3dm()
        f.Settings.ModelUnitSystem = r.UnitSystem.Meters
        f.Settings.ModelAbsoluteTolerance = 0.01
        f.Strings["CityDesign:synthetic"] = "true"
        layer = r.Layer()
        layer.Name = "Buildings"
        layer.Color = (180, 192, 199, 255)
        index = f.Layers.Add(layer)
        expected = {}
        for b in scene["buildings"]:
            height = b[floor_key] * scene["storey_height"]
            shape = r.Brep.CreateFromBox(
                r.Box(
                    r.BoundingBox(
                        b["x"], b["y"], 0, b["x"] + b["width"], b["y"] + b["depth"], height
                    )
                )
            )
            a = r.ObjectAttributes()
            a.Name = b["feature_id"]
            a.LayerIndex = index
            a.SetUserString("feature_id", b["feature_id"])
            a.SetUserString("floors", str(b[floor_key]))
            a.SetUserString("evidence_status", "synthetic")
            a.SetUserString("frame_id", scene["frame_id"])
            f.Objects.AddBrep(shape, a)
            expected[b["feature_id"]] = (height, str(b[floor_key]))
        path = out / "outputs" / (name + ".3dm")
        if not f.Write(str(path), 8):
            raise ValueError(
                "3DM example write failed; inspect the partial project before retrying"
            )
        saved = r.File3dm.Read(str(path))
        if (
            saved is None
            or saved.ArchiveVersion != 80
            or len(saved.Objects) != 4
            or saved.Settings.ModelUnitSystem != r.UnitSystem.Meters
        ):
            raise ValueError("3DM example readback failed")
        observed = {}
        for obj in saved.Objects:
            box = obj.Geometry.GetBoundingBox()
            if not obj.Geometry.IsValid:
                raise ValueError("Invalid example geometry")
            observed[obj.Attributes.GetUserString("feature_id")] = (
                box.Max.Z - box.Min.Z,
                obj.Attributes.GetUserString("floors"),
            )
        if observed != expected:
            raise ValueError("Saved example IDs, heights or floors changed")
        results.append(
            {
                "path": str(path.relative_to(out)),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "archive_version": 80,
                "objects": 4,
                "sdk_readback": "PASSED",
                "desktop_application_tested": False,
            }
        )
    return results
