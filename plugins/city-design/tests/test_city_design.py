import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))
import city_design as app
from project_tools import create_project, read_binding


class PortableChecks(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory(prefix="city-design-test-")
        self.addCleanup(temp.cleanup)
        self.temp = Path(temp.name).resolve()
        self.root = self.temp / "example with spaces"
        create_project(self.root, demo=True)
        self.config = self.temp / "config.json"
        self.config.write_text('{"project_root": null, "applications": {}}', encoding="utf-8")

    def drawing(self, name: str) -> dict:
        return app.check_drawing(
            self.root, types.SimpleNamespace(manifest="drawings/" + name + ".json", output=None)
        )

    def manifest(self, data: dict) -> dict:
        (self.root / "drawings/custom.json").write_text(json.dumps(data), encoding="utf-8")
        return self.drawing("custom")

    def valid_submission(self) -> dict:
        return {
            "drawing_type": "site_plan",
            "electronic_submission": True,
            "receiving_authority_adoption": True,
            "synthetic": False,
            "plane_coordinate_system": "EXAMPLE_FRAME",
            "elevation_system": "EXAMPLE_HEIGHT",
            "coordinate_system_source": "receiving_authority",
            "control_points": [[0, 0], [10, 0], [0, 10]],
            "export_unit": "m",
            "whole_drawing_block": False,
            "external_references": 0,
            "duplicate_lines": 0,
            "zero_length_lines": 0,
            "elevated_lines": 0,
            "anonymous_blocks": 0,
            "dimension_precision": 3,
            "dimension_entities_native": True,
            "layer_mapping_verified": True,
            "layer_contract_version": "EXAMPLE_ONLY",
        }

    def cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.pop("CITY_DESIGN_PROJECT", None)
        env.pop("CITY_DESIGN_CONFIG", None)
        return subprocess.run(
            [
                sys.executable,
                str(PLUGIN / "scripts/city_design.py"),
                "--config",
                str(self.config),
                *args,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
        )

    def test_master_plan(self) -> None:
        result = self.drawing("master_plan_complete")
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["counts"]["PASS"], 2)

    def test_invalid_submission(self) -> None:
        result = self.drawing("electronic_submission_invalid")
        failed = {x["rule"] for x in result["findings"] if x["status"] == "FAIL"}
        self.assertTrue(
            {"CN-SUBMIT-001", "CN-SUBMIT-003", "CN-SUBMIT-004", "CN-SUBMIT-005"}.issubset(failed)
        )

    def test_unconfirmed_adoption_blocks(self) -> None:
        self.assertEqual(
            self.drawing("electronic_submission_unconfirmed")["counts"]["SOURCE_REQUIRED"], 5
        )

    def test_missing_entity_facts_do_not_pass(self) -> None:
        data = self.valid_submission()
        del data["elevated_lines"]
        self.assertEqual(self.manifest(data)["status"], "BLOCKED")

    def test_explicit_entity_facts(self) -> None:
        self.assertEqual(self.manifest(self.valid_submission())["status"], "PASS")

    def test_synthetic_coordinates_cannot_be_accepted(self) -> None:
        data = self.valid_submission()
        data["synthetic"] = True
        self.assertEqual(self.manifest(data)["status"], "FAIL")

    def test_invalid_counts_and_boolean(self) -> None:
        for field, value in (
            ("elevated_lines", -1),
            ("elevated_lines", True),
            ("elevated_lines", "0"),
            ("whole_drawing_block", "false"),
        ):
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                data = self.valid_submission()
                data[field] = value
                self.manifest(data)

    def test_unknown_drawing_type(self) -> None:
        with self.assertRaises(ValueError):
            self.manifest({"drawing_type": "invented", "electronic_submission": False})

    def test_path_escape(self) -> None:
        with self.assertRaises(ValueError):
            app.inside(self.root, "../../outside.json")

    def test_report_cannot_overwrite_input(self) -> None:
        path = self.root / "drawings/master_plan_complete.json"
        before = path.read_bytes()
        with self.assertRaises(ValueError):
            app.check_drawing(
                self.root,
                types.SimpleNamespace(
                    manifest="drawings/master_plan_complete.json",
                    output="drawings/master_plan_complete.json",
                ),
            )
        self.assertEqual(path.read_bytes(), before)

    def test_control_points(self) -> None:
        self.assertTrue(app.non_collinear([[0, 0], [0, 0], [10, 0], [0, 10]]))
        self.assertTrue(app.non_collinear([["0", "0"], ["10", "0"], ["0", "10"]]))
        for points in (
            [[0, 0], [1, 0], [2, 0]],
            [[0, 0], [float("nan"), 0], [0, 2]],
            [[False, 0], [1, 0], [0, 1]],
            [["bad", 0], [1, 0], [0, 1]],
        ):
            self.assertFalse(app.non_collinear(points))

    def test_demo_area_and_identity(self) -> None:
        data = json.loads((self.root / "outputs/demo_receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(data["baseline_demo_floor_area_m2"], 20000)
        self.assertEqual(data["revised_demo_floor_area_m2"], 20000)
        scene = json.loads((self.root / "inputs/scene.json").read_text(encoding="utf-8"))
        self.assertEqual(
            [b["feature_id"] for b in scene["buildings"]], ["B001", "B002", "B003", "B004"]
        )
        self.assertTrue((self.root / "outputs/plan.svg").is_file())

    def test_repeat_demo_preserves_files(self) -> None:
        path = self.root / "inputs/scene.json"
        before = path.read_bytes()
        with self.assertRaises(ValueError):
            create_project(self.root, demo=True)
        self.assertEqual(path.read_bytes(), before)

    def test_doctor_without_private_project(self) -> None:
        result = self.cli("doctor")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["status"], "NEEDS_CONFIGURATION")
        self.assertTrue(data["core_available"])

    def test_relative_binding(self) -> None:
        self.config.write_text(json.dumps({"project_root": self.root.name}), encoding="utf-8")
        self.assertEqual(Path(read_binding(self.config)[0]["project_root"]), self.root)

    def test_missing_explicit_config_is_actionable(self) -> None:
        with self.assertRaisesRegex(ValueError, "does not exist"):
            read_binding(self.temp / "absent.json")

    def test_configured_project_cli(self) -> None:
        result = self.cli(
            "--project",
            str(self.root),
            "check-drawing",
            "--manifest",
            "drawings/master_plan_complete.json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "PASS")

    def test_unconfirmed_new_project(self) -> None:
        path = self.temp / "new project"
        create_project(path)
        state = json.loads((path / "state/PROJECT_STATE.json").read_text(encoding="utf-8"))
        self.assertEqual(state["frame_id"], "UNCONFIRMED")
        self.assertEqual(state["units"], "unconfirmed")

    def test_cli_failed_check_has_failure_exit_code(self) -> None:
        result = self.cli(
            "--project",
            str(self.root),
            "check-drawing",
            "--manifest",
            "drawings/electronic_submission_invalid.json",
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
