"""Optional numerical/export checks using only synthetic scene data."""

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

OPTIONAL_READY = all(
    importlib.util.find_spec(name) is not None for name in ("numpy", "pandas", "PIL", "matplotlib")
)
SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "site-analysis-maps" / "scripts"


@unittest.skipUnless(OPTIONAL_READY, "Optional requirements-maps.txt packages not installed")
class AnalysisMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sys.path.insert(0, str(SCRIPTS))
        import numpy
        from PIL import Image
        import rgb_grid
        import map_plate

        cls.np = numpy
        cls.Image = Image
        cls.rgb = rgb_grid
        cls.plate = map_plate

    @classmethod
    def tearDownClass(cls) -> None:
        sys.path.remove(str(SCRIPTS))

    def test_native_partition_preserves_zero_and_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            valid = self.np.zeros((4, 4), dtype="uint8")
            valid[:2] = 255
            green = self.np.zeros_like(valid)
            green[:2, 2:] = 255
            green[2:] = 255  # Invalid pixels must never enter the numerator.
            self.Image.fromarray(valid).save(folder / "valid.png")
            self.Image.fromarray(green).save(folder / "green.png")
            args = [
                "rgb_grid",
                "--valid-mask",
                str(folder / "valid.png"),
                "--green-mask",
                str(folder / "green.png"),
                "--crop",
                "0",
                "0",
                "4",
                "4",
                "--cells",
                "2",
                "--output",
                str(folder / "result"),
            ]
            with patch.object(sys, "argv", args), patch("builtins.print"):
                self.rgb.main()
            receipt = json.loads((folder / "result.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["valid_pixels"], 8)
            self.assertEqual(receipt["green_pixels"], 4)
            self.assertEqual(receipt["green_percent"], 50)
            with self.np.load(folder / "result.npz") as archive:
                grid = archive["values"]
                self.assertEqual(grid[0, 0], 0)
                self.assertEqual(grid[0, 1], 100)
                self.assertTrue(self.np.isnan(grid[1]).all())

    def test_invalid_grid_is_rejected_before_export(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "invalid.png"
            for grid in ([], [[float("nan")]], [0, 1]):
                with self.subTest(grid=grid), self.assertRaises(ValueError):
                    self.plate.render_plate(grid, [0, 2, 0, 2], path, "test", 0, 1)
            self.assertFalse(path.exists())

    def test_saved_plate_retains_values_and_transparency(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "plate.png"
            values = self.np.array([[0.0, 1.0], [self.np.nan, 0.5]])
            original = values.copy()
            receipt = self.plate.render_plate(
                values,
                [0, 2, 0, 2],
                path,
                "Synthetic hours",
                0,
                1,
                ticks=self.np.array([0, 0.5, 1]),
                nodata_label=False,
            )
            self.np.testing.assert_equal(values, original)
            self.assertEqual(receipt["finite_count"], 3)
            self.assertEqual(receipt["missing_count"], 1)
            self.assertEqual(receipt["legend_limits"], [0, 1])
            with self.Image.open(path) as image:
                self.assertEqual(image.size, (5600, 5000))
                self.assertEqual(image.getpixel((0, 0))[3], 0)
            self.assertTrue(path.with_suffix(".pdf").is_file())
            self.assertTrue(path.with_suffix(".svg").is_file())


if __name__ == "__main__":
    unittest.main()
