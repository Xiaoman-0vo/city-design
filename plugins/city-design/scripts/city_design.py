#!/usr/bin/env python3
"""Local project entrypoint; uses existing runtimes and never downloads dependencies."""

from __future__ import annotations

import argparse
import json
import math
import re
import socket
import subprocess
import os
from pathlib import Path
from project_tools import read_binding, create_project

PLUGIN = Path(__file__).resolve().parents[1]
DRAWING_TYPES = {
    "master_plan",
    "partition_plan",
    "detailed_plan",
    "analysis_map",
    "site_plan",
    "architectural_plan",
    "architectural_elevation",
    "architectural_section",
    "architectural_detail",
    "municipal_plan",
    "municipal_profile",
    "municipal_section",
    "other",
}


def load(path: str | Path) -> dict:
    """Read a UTF-8 JSON record."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def project_path(
    value: str | None, config_file: str | Path | None = None, required: bool = True
) -> tuple[Path | None, dict]:
    """Resolve an explicit or private-bound controlled project."""
    binding, _ = read_binding(config_file)
    selected = value or os.environ.get("CITY_DESIGN_PROJECT") or binding.get("project_root")
    if not selected:
        if required:
            raise ValueError("Select --project or run init-project --output <new-directory>")
        return None, binding
    root = Path(selected).expanduser().resolve()
    if not (root / "AGENTS.md").is_file() or not (root / "state/PROJECT_STATE.json").is_file():
        raise ValueError("Selected directory is not a configured City Design project")
    return root, binding


def inside(root: Path, relative: str | Path) -> Path:
    """Resolve a project path and reject escapes, including symlinks."""
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Evidence path escapes project")
    return path


def write_report(root: Path, relative: str, data: dict) -> str:
    """Atomically replace a project-relative report."""
    path = inside(root, relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
    return str(path)


def non_collinear(points: object, tolerance: float = 1e-9) -> bool:
    """Check finite XY controls, permitting duplicate observations."""
    if not isinstance(points, list) or len(points) < 3:
        return False
    try:
        if any(
            len(point) < 2 or any(isinstance(value, bool) for value in point[:2])
            for point in points
        ):
            return False
        points = [(float(point[0]), float(point[1])) for point in points]
        if not all(math.isfinite(value) for point in points for value in point):
            return False
        a = points[0]
        b = next((point for point in points[1:] if math.dist(a, point) > tolerance), None)
        if b is None:
            return False
        for c in points[1:]:
            cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            if abs(cross) > tolerance:
                return True
    except (IndexError, TypeError, ValueError, OverflowError):
        return False
    return False


def check_drawing(root: Path, args: argparse.Namespace) -> dict:
    """Evaluate declared facts; missing evidence never implies acceptance."""
    manifest_path = inside(root, args.manifest)
    manifest = load(manifest_path)
    if not isinstance(manifest, dict):
        raise ValueError("Drawing manifest must be a JSON object")
    drawing_type = manifest.get("drawing_type")
    if drawing_type not in DRAWING_TYPES:
        raise ValueError("Unknown drawing_type in drawing manifest")
    if not isinstance(manifest.get("electronic_submission"), bool):
        raise ValueError("electronic_submission must be true or false")
    electronic = manifest.get("electronic_submission") is True
    adopted = manifest.get("receiving_authority_adoption") is True
    findings = []

    def add(rule: str, status: str, summary: str, evidence: object = None) -> None:
        """Append one rule finding."""
        findings.append({"rule": rule, "status": status, "summary": summary, "evidence": evidence})

    planning_scope = {
        "master_plan": "PASS",
        "partition_plan": "PASS",
        "detailed_plan": "MANUAL_REVIEW",
        "analysis_map": "NOT_APPLICABLE",
    }
    scope_status = planning_scope.get(drawing_type, "NOT_APPLICABLE")
    scope_summary = {
        "PASS": "CJJ/T97-2003 is within its stated planning drawing scope.",
        "MANUAL_REVIEW": "Detailed planning may reference CJJ/T97-2003; applicability must be declared.",
        "NOT_APPLICABLE": "CJJ/T97-2003 planning scope was not selected for this drawing type.",
    }[scope_status]
    add("CN-PLAN-001", scope_status, scope_summary, {"drawing_type": drawing_type})

    if drawing_type == "master_plan":
        required = [
            "title",
            "drawing_boundary",
            "north_arrow",
            "wind_rose",
            "numeric_scale",
            "scale_bar",
            "planning_period",
            "legend",
            "signature",
            "compilation_date",
            "title_block",
        ]
        missing = [field for field in required if not manifest.get(field)]
        add(
            "CN-PLAN-002",
            "FAIL" if missing else "PASS",
            "Master-plan sheet elements are incomplete."
            if missing
            else "Declared master-plan sheet elements are complete.",
            {"missing": missing, "checked": required},
        )
    else:
        add(
            "CN-PLAN-002",
            "NOT_APPLICABLE",
            "Master-plan sheet checklist does not apply to this drawing type.",
        )

    if not electronic:
        for rule in [
            "CN-SUBMIT-001",
            "CN-SUBMIT-002",
            "CN-SUBMIT-003",
            "CN-SUBMIT-004",
            "CN-SUBMIT-005",
        ]:
            add(rule, "NOT_APPLICABLE", "Electronic-submission profile was not selected.")
    elif not adopted:
        for rule in [
            "CN-SUBMIT-001",
            "CN-SUBMIT-002",
            "CN-SUBMIT-003",
            "CN-SUBMIT-004",
            "CN-SUBMIT-005",
        ]:
            add(
                rule,
                "SOURCE_REQUIRED",
                "Confirm that the receiving authority adopts this submission contract and obtain its version.",
            )
    else:
        control_points = manifest.get("control_points")
        crs_ok = bool(
            manifest.get("plane_coordinate_system")
            and manifest.get("elevation_system")
            and manifest.get("coordinate_system_source") == "receiving_authority"
            and manifest.get("synthetic") is not True
        )
        point_ok = non_collinear(control_points)
        add(
            "CN-SUBMIT-001",
            "PASS" if crs_ok and point_ok else "FAIL",
            "Coordinate contract and control points are declared."
            if crs_ok and point_ok
            else "Coordinate contract is not authoritative, is synthetic, or lacks three non-collinear control points.",
            {
                "plane_coordinate_system": manifest.get("plane_coordinate_system"),
                "elevation_system": manifest.get("elevation_system"),
                "coordinate_system_source": manifest.get("coordinate_system_source"),
                "synthetic": manifest.get("synthetic"),
                "non_collinear_control_points": point_ok,
            },
        )

        metres = {
            "site_plan",
            "master_plan",
            "partition_plan",
            "municipal_plan",
            "municipal_profile",
            "municipal_section",
        }
        millimetres = {
            "architectural_plan",
            "architectural_elevation",
            "architectural_section",
            "architectural_detail",
        }
        expected_unit = (
            "m" if drawing_type in metres else "mm" if drawing_type in millimetres else None
        )
        if expected_unit is None:
            add(
                "CN-SUBMIT-002",
                "MANUAL_REVIEW",
                "No unit profile is mapped for this drawing type.",
                {"drawing_type": drawing_type},
            )
        else:
            actual_unit = manifest.get("export_unit")
            add(
                "CN-SUBMIT-002",
                "PASS" if actual_unit == expected_unit else "FAIL",
                "Export unit matches the mapped drawing type."
                if actual_unit == expected_unit
                else "Export unit does not match the mapped drawing type.",
                {
                    "expected": expected_unit,
                    "actual": actual_unit,
                    "model_unit": manifest.get("model_unit"),
                },
            )

        count_fields = [
            "external_references",
            "duplicate_lines",
            "zero_length_lines",
            "elevated_lines",
            "anonymous_blocks",
        ]
        missing_entities = [
            field for field in count_fields + ["whole_drawing_block"] if field not in manifest
        ]
        for field in count_fields:
            if field not in manifest:
                continue
            value = manifest[field]
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{field} must be a non-negative integer")
        if "whole_drawing_block" in manifest and not isinstance(
            manifest["whole_drawing_block"], bool
        ):
            raise ValueError("whole_drawing_block must be true or false")
        forbidden = {
            "whole_drawing_block": bool(manifest.get("whole_drawing_block")),
            **{field: manifest.get(field, 0) for field in count_fields},
        }
        bad = {key: value for key, value in forbidden.items() if value}
        add(
            "CN-SUBMIT-003",
            "FAIL" if bad else "SOURCE_REQUIRED" if missing_entities else "PASS",
            "Forbidden or non-flat entities were declared."
            if bad
            else "Entity facts are missing."
            if missing_entities
            else "No forbidden or non-flat entities were declared.",
            {"violations": bad, "missing": missing_entities},
        )

        precision = manifest.get("dimension_precision")
        expected_precision = 3 if expected_unit == "m" else 0 if expected_unit == "mm" else None
        dimension_ok = (
            manifest.get("dimension_entities_native") is True and precision == expected_precision
        )
        if expected_precision is None:
            add(
                "CN-SUBMIT-004",
                "MANUAL_REVIEW",
                "Dimension precision needs a drawing-type decision.",
            )
        else:
            add(
                "CN-SUBMIT-004",
                "PASS" if dimension_ok else "FAIL",
                "Native dimensions and precision match the mapped requirement."
                if dimension_ok
                else "Native dimensions or precision do not match the mapped requirement.",
                {
                    "native_dimensions": manifest.get("dimension_entities_native"),
                    "expected_precision": expected_precision,
                    "actual_precision": precision,
                },
            )

        layer_ok = manifest.get("layer_mapping_verified") is True and bool(
            manifest.get("layer_contract_version")
        )
        add(
            "CN-SUBMIT-005",
            "PASS" if layer_ok else "FAIL",
            "Layer mapping and its contract version are declared."
            if layer_ok
            else "Verified layer mapping or contract version is missing.",
            {
                "layer_mapping_verified": manifest.get("layer_mapping_verified"),
                "layer_contract_version": manifest.get("layer_contract_version"),
            },
        )

    statuses = {item["status"] for item in findings}
    overall = (
        "FAIL"
        if "FAIL" in statuses
        else "BLOCKED"
        if "SOURCE_REQUIRED" in statuses
        else "REVIEW_REQUIRED"
        if "MANUAL_REVIEW" in statuses
        else "PASS"
    )
    result = {
        "status": overall,
        "scope": "Manifest-level check of seven mapped rules; not full statutory or native-file conformance.",
        "facts_source": str(manifest_path),
        "standards_checked_on": load(PLUGIN / "references/standards/rules.json")["checked_on"],
        "findings": findings,
        "counts": {
            status: sum(item["status"] == status for item in findings)
            for status in ["PASS", "FAIL", "SOURCE_REQUIRED", "MANUAL_REVIEW", "NOT_APPLICABLE"]
        },
    }
    if args.output:
        if inside(root, args.output) == manifest_path:
            raise ValueError("Report output must not overwrite its input manifest")
        result["report"] = write_report(root, args.output, result)
    return result


def assess_run(root: Path, args: argparse.Namespace) -> dict:
    """Compare legacy saved receipts without launching applications."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", args.prefix):
        raise ValueError("Invalid run prefix")
    workflow = load(inside(root, f"runs/{args.prefix}_workflow/verification.json"))
    stage_names = {
        "rhino_baseline": f"{args.prefix}_rhino_baseline",
        "rhino_revised": f"{args.prefix}_rhino_revised",
        "grasshopper": f"{args.prefix}_gh",
        "qgis_baseline": f"{args.prefix}_qgis_baseline",
        "qgis_revised": f"{args.prefix}_qgis_revised",
        "cad_baseline": f"{args.prefix}_cad_baseline",
        "cad_revised": f"{args.prefix}_cad_revised",
    }
    missing_stages = [
        name for name in stage_names.values() if name not in workflow.get("stages", [])
    ]
    rhino = load(inside(root, f"runs/{stage_names['rhino_revised']}/verification.json"))
    qgis = load(inside(root, f"runs/{stage_names['qgis_revised']}/verification.json"))
    cad = load(inside(root, f"runs/{stage_names['cad_revised']}/verification.json"))
    gh = load(inside(root, f"runs/{stage_names['grasshopper']}/verification.json"))
    native = {"Rhino": rhino, "QGIS": qgis, "AutoCAD": cad, "Grasshopper": gh}
    checks = []

    def record(name: str, passed: bool, evidence: object) -> None:
        """Append a saved-run check."""
        checks.append({"check": name, "status": "PASS" if passed else "FAIL", "evidence": evidence})

    record(
        "workflow_receipt",
        workflow.get("status") == "QA_PASSED" and not missing_stages,
        {"status": workflow.get("status"), "missing_stages": missing_stages},
    )
    statuses = {name: data.get("status") for name, data in native.items()}
    record(
        "native_stage_receipts", all(value == "QA_PASSED" for value in statuses.values()), statuses
    )
    metrics = ["parcel_area_m2", "footprint_union_m2", "gfa_demo_m2"]
    metric_values = {
        metric: {name: data.get(metric) for name, data in native.items() if name != "Grasshopper"}
        for metric in metrics
    }
    metric_match = all(
        len({round(float(value), 6) for value in values.values()}) == 1
        for values in metric_values.values()
    )
    record("cross_application_metrics", metric_match, metric_values)

    geometry = load(inside(root, f"runs/{stage_names['rhino_revised']}/geometry_from_3dm.json"))
    expected_floors = {item["feature_id"]: int(item["floors"]) for item in geometry["buildings"]}
    qgis_floor_counts = {}
    for item in qgis["records"]["floors"]:
        feature = item.get("id") or item.get("feature_id")
        qgis_floor_counts[feature] = qgis_floor_counts.get(feature, 0) + 1
    cad_floor_counts = {}
    for item in cad["native_entities"].values():
        tags = item.get("tags", {})
        if tags.get("role") == "floor":
            feature = tags.get("feature_id")
            cad_floor_counts[feature] = cad_floor_counts.get(feature, 0) + 1
    gh_floors = {
        key: int(value["floors"]) for key, value in gh["results"]["revised"]["buildings"].items()
    }
    floor_evidence = {
        "Rhino_saved_3dm": expected_floors,
        "QGIS_saved_gpkg": qgis_floor_counts,
        "AutoCAD_saved_dwg": cad_floor_counts,
        "Grasshopper_reopen": gh_floors,
    }
    record(
        "stable_ids_and_floors",
        all(values == expected_floors for values in floor_evidence.values()),
        floor_evidence,
    )

    rhino_parcel = next(item["ring"] for item in rhino["records"] if item.get("role") == "parcel")
    qgis_parcel = qgis["records"]["parcel"][0]["ring"]
    cad_parcel = cad["native_entities"]["P001_parcel"]["ring"]
    max_error = max(
        math.dist(rhino_parcel[i], other[i])
        for other in [qgis_parcel, cad_parcel]
        for i in range(3)
    )
    record(
        "three_non_collinear_control_points",
        non_collinear(rhino_parcel[:3]) and max_error <= 0.01,
        {
            "frame": geometry.get("frame_id"),
            "maximum_xy_error_m": max_error,
            "real_crs_transform": False,
        },
    )

    native_files = {
        "3DM": f"runs/{stage_names['rhino_revised']}/design.3dm",
        "GH": f"runs/{stage_names['grasshopper']}/revised.gh",
        "QGZ": f"runs/{stage_names['qgis_revised']}/design.qgz",
        "GPKG": f"runs/{stage_names['qgis_revised']}/design.gpkg",
        "DWG": f"runs/{stage_names['cad_revised']}/design.dwg",
    }
    file_evidence = {
        name: {
            "path": path,
            "exists": inside(root, path).is_file(),
            "bytes": inside(root, path).stat().st_size if inside(root, path).is_file() else 0,
        }
        for name, path in native_files.items()
    }
    record(
        "editable_native_outputs",
        all(item["bytes"] > 0 for item in file_evidence.values()),
        file_evidence,
    )
    result = {
        "status": "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL",
        "prefix": args.prefix,
        "synthetic": workflow.get("synthetic"),
        "scope": "Read-only reassessment of saved native-file receipts; it does not reopen live applications.",
        "checks": checks,
    }
    if args.output:
        result["report"] = write_report(root, args.output, result)
    return result


def doctor(root: Path | None, binding: dict) -> dict:
    """Report configuration independently of native acceptance."""
    # No live connection is implied by a path or an open port.
    port_open = None
    qgis = binding.get("qgis", {})
    if qgis.get("port"):
        try:
            with socket.create_connection(
                (qgis.get("host", "127.0.0.1"), int(qgis["port"])), timeout=1
            ):
                port_open = True
        except OSError:
            port_open = False
    return {
        "status": "CONFIGURED" if root else "NEEDS_CONFIGURATION",
        "core_available": True,
        "project": str(root) if root else None,
        "next_step": "Use connected tools for the selected task"
        if root
        else "Run demo --output <new-directory> or init-project --output <new-directory>",
        "qgis_tcp_port_open": port_open,
        "live_mcp_authenticated": "NOT_CHECKED_BY_DOCTOR",
        "runtime_exists": bool(binding.get("mcp_python")) and Path(binding["mcp_python"]).is_file(),
        "applications": {
            name: bool(path) and Path(path).expanduser().exists()
            for name, path in binding.get("applications", {}).items()
        },
        "scope": "Configuration and optional port checks; no native application opened, no model acceptance",
    }


def run_synthetic(root: Path, binding: dict, args: argparse.Namespace) -> dict:
    """Invoke only a configured legacy runner with a fresh run ID."""
    if not args.execute:
        raise ValueError("Use --execute only when an actual native synthetic run is intended")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", args.prefix):
        raise ValueError("Invalid run prefix")
    if list((root / "runs").glob(args.prefix + "_*")):
        raise ValueError("Run prefix already exists; reconcile its state instead of replaying")
    snapshot = doctor(root, binding)
    if not snapshot["runtime_exists"]:
        raise ValueError(
            "Legacy native runner needs a configured mcp_python; use demo for the portable example"
        )
    runner = root / "scripts/run_mac_micro_workflow.py"
    if not runner.is_file():
        raise ValueError("Selected project has no native synthetic runner")
    result = subprocess.run(
        [binding["mcp_python"], str(runner), "--prefix", args.prefix], cwd=root, check=False
    )
    if result.returncode:
        raise RuntimeError(
            "Native run failed or is uncertain; inspect run receipts before retrying"
        )
    receipt = load(root / "runs" / (args.prefix + "_workflow") / "verification.json")
    if receipt.get("status") != "QA_PASSED":
        raise RuntimeError("Native acceptance receipt did not pass")
    return receipt


def main() -> int:
    """Execute a CLI operation and return its status code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", help="Explicit controlled project root")
    parser.add_argument(
        "--config",
        help="Private binding JSON; defaults to CITY_DESIGN_CONFIG or ignored local-binding.json",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Read-only dependency and recorded-evidence check")
    sub.add_parser("standards", help="Show dated standards catalog metadata")
    sub.add_parser("practices", help="Show verified practice cases and capability promotion")
    init = sub.add_parser(
        "init-project",
        help="Create a new controlled project without modifying existing directories",
    )
    init.add_argument("--output", required=True)
    demo = sub.add_parser("demo", help="Create and check an independent synthetic example")
    demo.add_argument("--output", required=True)
    demo.add_argument(
        "--with-rhino",
        action="store_true",
        help="Also write and independently read Rhino 8 files; requires rhino3dm",
    )
    export = sub.add_parser(
        "export-rhino8", help="Conservatively export a checked Rhino 8 exchange copy"
    )
    export.add_argument("source")
    export.add_argument("target")
    assess = sub.add_parser("assess-run", help="Reassess a saved cross-application run")
    assess.add_argument("--prefix", required=True)
    assess.add_argument("--output", help="Project-relative JSON report path")
    drawing = sub.add_parser(
        "check-drawing", help="Check a drawing manifest against mapped Chinese rules"
    )
    drawing.add_argument("--manifest", required=True, help="Project-relative JSON manifest")
    drawing.add_argument("--output", help="Project-relative JSON report path")
    run = sub.add_parser("run-synthetic", help="Run the existing native four-building example")
    run.add_argument("--prefix", required=True)
    run.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    try:
        if args.command in ("init-project", "demo"):
            result = create_project(
                args.output,
                demo=args.command == "demo",
                with_rhino=getattr(args, "with_rhino", False),
            )
        elif args.command == "export-rhino8":
            from rhino_export import export_rhino8

            result = export_rhino8(args.source, args.target)
        elif args.command == "standards":
            data = load(PLUGIN / "references/standards/catalog.json")
            result = {
                "checked_on": data["checked_on"],
                "count": len(data["standards"]),
                "standards": data["standards"],
            }
        elif args.command == "practices":
            result = load(PLUGIN / "references/practices/index.json")
        else:
            root, binding = project_path(
                args.project, args.config, required=args.command != "doctor"
            )
            if args.command == "doctor":
                result = doctor(root, binding)
            elif args.command == "assess-run":
                result = assess_run(root, args)
            elif args.command == "check-drawing":
                result = check_drawing(root, args)
            else:
                result = run_synthetic(root, binding, args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if args.command in {"check-drawing", "assess-run"}:
            return {"PASS": 0, "FAIL": 1, "BLOCKED": 2, "REVIEW_REQUIRED": 3}.get(
                result.get("status"), 2
            )
        return 0
    except (OSError, ValueError, RuntimeError, KeyError) as exc:
        print(
            json.dumps({"status": "BLOCKED_OR_UNCERTAIN", "reason": str(exc)}, ensure_ascii=False)
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
