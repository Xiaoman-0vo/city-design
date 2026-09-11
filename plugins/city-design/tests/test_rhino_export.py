from pathlib import Path
import importlib.util
import json
import sys
import tempfile
import unittest

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))
from project_tools import create_project
from rhino_export import export_rhino8, sha, verify_models


@unittest.skipUnless(
    importlib.util.find_spec("rhino3dm"), "Optional rhino3dm dependency not installed"
)
class RhinoExchangeChecks(unittest.TestCase):
    def setUp(self) -> None:
        import rhino3dm as r

        self.r = r
        temp = tempfile.TemporaryDirectory(prefix="city-rhino-test-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        create_project(self.root / "example", demo=True, with_rhino=True)
        self.source = self.root / "example/outputs/revised.3dm"
        self.target = self.root / "copy.3dm"

    def test_example_native_readback(self) -> None:
        receipt = json.loads(
            (self.root / "example/outputs/demo_receipt.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(receipt["rhino_files"]), 2)
        self.assertTrue(all(x["sdk_readback"] == "PASSED" for x in receipt["rhino_files"]))

    def test_export_preserves_source(self) -> None:
        before = sha(self.source)
        result = export_rhino8(self.source, self.target)
        self.assertEqual(result["output_archive_version"], 80)
        self.assertEqual(result["top_objects"], 4)
        self.assertEqual(sha(self.source), before)
        self.assertFalse(result["rhino8_desktop_tested"])

    def test_repeat_reuses_verified_result(self) -> None:
        export_rhino8(self.source, self.target)
        before = sha(self.target)
        self.assertTrue(export_rhino8(self.source, self.target)["reused_verified_output"])
        self.assertEqual(sha(self.target), before)

    def test_source_cannot_be_destination(self) -> None:
        before = sha(self.source)
        with self.assertRaises(ValueError):
            export_rhino8(self.source, self.source)
        self.assertEqual(sha(self.source), before)

    def test_existing_target_preserved(self) -> None:
        self.target.write_bytes(b"user data")
        with self.assertRaises(ValueError):
            export_rhino8(self.source, self.target)
        self.assertEqual(self.target.read_bytes(), b"user data")

    def test_modified_output_rejected(self) -> None:
        export_rhino8(self.source, self.target)
        self.target.write_bytes(b"changed")
        with self.assertRaises(ValueError):
            export_rhino8(self.source, self.target)

    def test_unknown_pending_preserved(self) -> None:
        pending = self.root / "copy.pending.3dm"
        pending.write_bytes(b"unknown")
        with self.assertRaises(ValueError):
            export_rhino8(self.source, self.target)
        self.assertEqual(pending.read_bytes(), b"unknown")

    def test_matching_pending_resumes(self) -> None:
        pending = self.root / "copy.pending.3dm"
        pending.write_bytes(self.source.read_bytes())
        (self.root / "copy.pending.json").write_text(
            json.dumps(
                {
                    "source_sha256": sha(self.source),
                    "target_name": "copy.3dm",
                    "archive_version": 80,
                }
            ),
            encoding="utf-8",
        )
        self.assertEqual(export_rhino8(self.source, self.target)["status"], "PASSED")
        self.assertFalse(pending.exists())

    def test_changed_geometry_rejected(self) -> None:
        a = self.r.File3dm.Read(str(self.source))
        b = self.r.File3dm.Read(str(self.source))
        b.Objects[0].Geometry.Translate(self.r.Vector3d(1, 0, 0))
        with self.assertRaises(ValueError):
            verify_models(a, b, self.r)

    def test_changed_attributes_rejected(self) -> None:
        a = self.r.File3dm.Read(str(self.source))
        b = self.r.File3dm.Read(str(self.source))
        b.Objects[0].Attributes.Name = "different"
        with self.assertRaises(ValueError):
            verify_models(a, b, self.r)

    def test_document_frame_metadata_change_rejected(self) -> None:
        a = self.r.File3dm.Read(str(self.source))
        b = self.r.File3dm.Read(str(self.source))
        b.Strings["frame_id"] = "changed"
        with self.assertRaises(ValueError):
            verify_models(a, b, self.r)

    def test_completed_export_cleans_matching_journal(self) -> None:
        export_rhino8(self.source, self.target)
        journal = self.root / "copy.pending.json"
        journal.write_text(
            json.dumps(
                {
                    "source_sha256": sha(self.source),
                    "target_name": "copy.3dm",
                    "archive_version": 80,
                }
            ),
            encoding="utf-8",
        )
        self.assertTrue(export_rhino8(self.source, self.target)["reused_verified_output"])
        self.assertFalse(journal.exists())


if __name__ == "__main__":
    unittest.main()
