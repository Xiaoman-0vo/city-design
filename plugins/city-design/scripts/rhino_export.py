"""Conservative Rhino 8 exchange export; preserves originals and reconciles retries."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


def sha(path: str | Path) -> str:
    """Hash a file in bounded chunks."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def digest(value: object) -> str:
    """Hash a stable serialized record."""
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def xyz(point: Any) -> list[float]:
    """Extract coordinate values from a Rhino point or vector."""
    return [point.X, point.Y, point.Z]


def require(condition: bool, message: str) -> None:
    """Fail before promoting an unverified output."""
    if not condition:
        raise ValueError(message)


def atomic_json(path: Path, value: dict) -> None:
    """Write a receipt with an explicit staging-file guard."""
    temp = path.with_name(path.name + ".tmp")
    require(not temp.exists(), "Existing receipt staging file needs reconciliation: " + str(temp))
    temp.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    os.replace(temp, path)


def views(items: Any) -> list[dict]:
    """Extract named or active camera projection data."""
    return [
        {
            "name": v.Name,
            "camera": xyz(v.Viewport.CameraLocation),
            "direction": xyz(v.Viewport.CameraDirection),
            "up": xyz(v.Viewport.CameraUp),
            "parallel": v.Viewport.IsParallelProjection,
            "lens": v.Viewport.Camera35mmLensLength,
            "frustum": v.Viewport.GetFrustum(),
        }
        for v in items
    ]


def tables(f: Any) -> dict:
    """Snapshot supported document tables and coordinate metadata."""
    return {
        "document_user_strings": list(f.Strings),
        "layers": [digest(x.Encode()) for x in f.Layers],
        "materials": [digest(x.Encode()) for x in f.Materials],
        "groups": [digest(x.Encode()) for x in f.Groups],
        "definitions": [
            {"id": str(d.Id), "name": d.Name, "objects": [str(x) for x in d.GetObjectIds()]}
            for d in f.InstanceDefinitions
        ],
        "named_views": views(f.NamedViews),
        "views": views(f.Views),
        "units": str(f.Settings.ModelUnitSystem),
        "tolerance": f.Settings.ModelAbsoluteTolerance,
        "relative_tolerance": f.Settings.ModelRelativeTolerance,
        "angle_tolerance": f.Settings.ModelAngleToleranceRadians,
    }


def brep_components(a: Any, b: Any, r: Any) -> dict:
    """Accept serialization differences only after strict component checks."""
    require(
        isinstance(a, r.Brep) and isinstance(b, r.Brep),
        "Geometry serialization changed for a non-Brep",
    )
    require(
        a.IsValid and b.IsValid and a.IsSolid == b.IsSolid, "Brep validity or solid state changed"
    )
    require(
        all(len(getattr(a, k)) == len(getattr(b, k)) for k in ("Faces", "Edges", "Vertices")),
        "Brep topology counts changed",
    )
    require(
        all(
            x.DuplicateFace(False).Encode() == y.DuplicateFace(False).Encode()
            for x, y in zip(a.Faces, b.Faces)
        ),
        "Trimmed face changed",
    )
    require(all(x.Encode() == y.Encode() for x, y in zip(a.Edges, b.Edges)), "Edge changed")
    require(
        [xyz(x.Location) for x in a.Vertices] == [xyz(x.Location) for x in b.Vertices],
        "Vertex changed",
    )
    require(
        [x.OrientationIsReversed for x in a.Faces] == [x.OrientationIsReversed for x in b.Faces],
        "Face orientation changed",
    )
    require(list(a.GetUserStrings()) == list(b.GetUserStrings()), "Geometry user strings changed")
    ab = a.GetBoundingBox()
    bb = b.GetBoundingBox()
    delta = max(abs(x - y) for x, y in zip(xyz(ab.Min) + xyz(ab.Max), xyz(bb.Min) + xyz(bb.Max)))
    require(delta <= 1e-12, "Brep bounding box changed")
    return {
        "method": "exact trimmed faces, edges and vertices",
        "faces": len(a.Faces),
        "bounding_box_max_delta": delta,
    }


def verify_models(a: Any, b: Any, r: Any) -> dict:
    """Verify readable objects and supported tables in linear object traversal."""
    require(b.ArchiveVersion == 80, "Output archive is not Rhino 8")
    left = {str(o.Attributes.Id): o for o in a.Objects}
    right = {str(o.Attributes.Id): o for o in b.Objects}
    require(len(left) == len(a.Objects) and len(right) == len(b.Objects), "Duplicate object GUIDs")
    require(left.keys() == right.keys(), "Object records or GUIDs changed")
    exceptions = []
    for key, obj in left.items():
        other = right[key]
        require(
            obj.Geometry is not None and other.Geometry is not None,
            "Unsupported or missing geometry",
        )
        require(
            obj.Geometry.IsValid and other.Geometry.IsValid,
            "Source or output contains invalid geometry",
        )
        require(type(obj.Geometry) is type(other.Geometry), "Geometry type changed")
        require(
            obj.Attributes.Encode() == other.Attributes.Encode(),
            "Object attributes changed: " + key,
        )
        if obj.Geometry.Encode() != other.Geometry.Encode():
            exceptions.append(
                {"object_id": key, **brep_components(obj.Geometry, other.Geometry, r)}
            )
    before = tables(a)
    after = tables(b)
    changed = [k for k in before if before[k] != after[k]]
    require(not changed, "Document tables changed: " + ", ".join(changed))
    return {
        "geometry_records": len(left),
        "top_objects": sum(not o.Attributes.IsInstanceDefinitionObject for o in b.Objects),
        "layers": len(b.Layers),
        "materials": len(b.Materials),
        "block_definitions": len(b.InstanceDefinitions),
        "named_views": len(b.NamedViews),
        "exact_geometry_serializations": len(left) - len(exceptions),
        "brep_component_equivalence": exceptions,
        "invalid_geometry": 0,
        "checked_tables": list(before),
        "object_attributes_exact": True,
    }


def export_rhino8(source: str | Path, target: str | Path) -> dict:
    """Preserve the source and publish a separately verified Rhino 8 copy."""
    try:
        import rhino3dm as r
    except ImportError as exc:
        raise ValueError(
            "Rhino 8 export requires the optional requirements-rhino.txt dependency"
        ) from exc
    source = Path(source).expanduser().resolve()
    target = Path(target).expanduser().resolve()
    require(
        source.is_file() and source.suffix.lower() == ".3dm", "Source must be an existing .3dm file"
    )
    require(
        target.suffix.lower() == ".3dm" and source != target,
        "Use a separate .3dm output to preserve the source",
    )
    source_hash = sha(source)
    receipt = target.with_suffix(".verification.json")
    pending = target.with_name(target.stem + ".pending.3dm")
    journal = target.with_suffix(".pending.json")
    if target.exists():
        if receipt.is_file():
            saved = json.loads(receipt.read_text(encoding="utf-8"))
            if (
                saved.get("status") == "PASSED"
                and saved.get("source_sha256") == source_hash
                and saved.get("output_sha256") == sha(target)
            ):
                if journal.exists() and not pending.exists():
                    orphan = json.loads(journal.read_text(encoding="utf-8"))
                    require(
                        orphan
                        == {
                            "source_sha256": source_hash,
                            "target_name": target.name,
                            "archive_version": 80,
                        },
                        "Conflicting journal beside completed output",
                    )
                    journal.unlink()
                return {**saved, "reused_verified_output": True}
        raise ValueError(
            "Existing target cannot be overwritten; reconcile it or select another output"
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    expected = {"source_sha256": source_hash, "target_name": target.name, "archive_version": 80}
    if journal.exists():
        require(
            json.loads(journal.read_text(encoding="utf-8")) == expected,
            "Pending export belongs to a different input",
        )
    else:
        require(not pending.exists(), "Unidentified pending model needs reconciliation")
        require(not receipt.exists(), "Orphan verification receipt needs reconciliation")
        atomic_json(journal, expected)
    a = r.File3dm.Read(str(source))
    require(a is not None, "Source could not be read by the SDK")
    if not pending.exists():
        require(
            a.Write(str(pending), 8), "Writing failed; pending state retained for reconciliation"
        )
    # Compare against a fresh source read; a writer may normalize in-memory caches.
    a = r.File3dm.Read(str(source))
    require(a is not None, "Source readback failed")
    b = r.File3dm.Read(str(pending))
    require(b is not None, "Pending file is unreadable; original preserved")
    checks = verify_models(a, b, r)
    require(sha(source) == source_hash, "Source changed during export; pending output not promoted")
    result = {
        "status": "PASSED",
        "source_name": source.name,
        "source_sha256": source_hash,
        "source_archive_version": a.ArchiveVersion,
        "output_name": target.name,
        "output_sha256": sha(pending),
        "output_archive_version": 80,
        "library": "rhino3dm " + r.__version__,
        "source_preserved": True,
        "rhino8_desktop_tested": False,
        **checks,
        "limits": "SDK readback of the listed data only; custom plugin data, unsupported Rhino 9 features, render environments and desktop display require native application acceptance.",
    }
    # Receipt first: after a crash between these operations, the existing journal
    # allows verification to resume. Never silently replay a completed mutation.
    atomic_json(receipt, result)
    require(not target.exists(), "Target appeared during validation; pending state preserved")
    os.replace(pending, target)
    journal.unlink()
    return result
