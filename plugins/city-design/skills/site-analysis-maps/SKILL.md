---
name: site-analysis-maps
description: Create reproducible static urban-analysis maps from RGB vegetation masks, building-only visibility graphs or model sunlight calculations. Use for vegetation coverage grids, space-syntax VGA plates, winter/summer sunlight maps and transparent figure exports.
---

# Site Analysis Maps

Separate calculation from drawing. Preserve the source image/CAD/model, the full analysis domain, native metric values, and a record of every display crop, rotation, color scale and opacity. Reducing the visible extent normally changes only the plate; reducing the computational graph requires a distinct analysis run.

Read only the applicable method:

- [RGB vegetation grids](references/rgb-vegetation.md): ordinary RGB screenshots, native-pixel masks, exact valid-pixel denominators, grayscale basemap and green grid overlay.
- [Building-only VGA](references/building-vga.md): interpreted or semantic building outlines, real depthmapX visibility calculations, saved metric validation and white-building heatmaps.
- [Model sunlight](references/model-sunlight.md): native model frames and surfaces, solstice dates, direct-sun hours, ray checks and comparable seasonal legends.

## Figure contract

For a design analysis plate, a square map with a small right legend is a useful starting point. The user's format governs: transparent PNG, no title/IDs and no web page are valid explicit choices. Do not add a north arrow without a verified true-north relation. Keep source, units, inference limits and parameters in the companion receipt when the user requests a minimal canvas.

Use `scripts/map_plate.py` for a regular grid already calculated in one coordinate frame. It exports RGBA PNG, PDF/SVG for inspection and a metadata receipt. Values must remain in native units; NoData stays separate from zero. A supplied building layer must be in the grid's display coordinates. Never align unrelated CAD, Rhino and screenshot frames by visual resemblance alone.

Install the optional packages in [requirements-maps.txt](../../requirements-maps.txt) into the chosen analysis environment before using these helpers. Native VGA and solar calculation engines have separate requirements described in their method references; loading this skill does not install them.

For red-blue plates, blue=low and red=high unless specified otherwise. The helper's vivid blue/red anchors draw on the user's selected Nature-style palette; this is a color choice, not journal certification. Keep identical limits for winter/summer or other comparable date series. Do not use per-panel quantiles to make every date equally red. Saturation and opacity are separate settings; match legend alpha to map alpha and inspect the final image composited on white as well as with transparency.

Example Python API:

```python
from map_plate import render_plate
render_plate(values, extent=[xmin, xmax, ymin, ymax], output=png_path,
             label="Visual integration\nHH · Rn", vmin=lo, vmax=hi,
             buildings=building_gdf, alpha=0.74, crop=display_extent)
```

`values` is a 2D numeric array. The default origin is lower left; image grids can pass `origin="upper"`. Export resolution is not observation or calculation resolution. Choose a new output path for a changed style; read back dimensions, alpha and source hashes, then inspect the image. When the user requests a root delivery folder, synchronize only accepted final images and verify copy hashes; keep intermediate outputs elsewhere.

## Verification boundary

The project case demonstrates native-pixel aggregation and a real saved VGA with independent visibility and HH formula checks. It does not establish universal automatic building recognition, measured vegetation cover, survey accuracy, or actual pedestrian accessibility. Dependencies are optional Python analysis packages; an installed skill alone does not prove native application connectivity.
