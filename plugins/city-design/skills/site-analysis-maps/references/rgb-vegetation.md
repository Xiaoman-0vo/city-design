# RGB vegetation grids

Use original RGB pixels to classify. A grayscale basemap is display only. An ordinary satellite-map screenshot supports **green-pixel fraction**, not NDVI, physical canopy cover or measured green-space area without separate validation.

1. Preserve screenshot and hash. Record imagery date if available; capture date is not imagery date. Exclude UI, labels and other occlusions with a valid-data mask. If the user asks for a central unobstructed square, crop both image and masks with identical native coordinates.
2. Reuse verified masks if only the style changes. In a new case, inspect hue/saturation/value and relative green-channel thresholds against visible vegetation and artificial green surfaces. One tested starting rule was hue 60–160°, saturation ≥0.16, value ≥0.105, G ≥1.04R and G ≥1.07B; it is not a universal classifier. Keep artificial-surface exclusions separate and test uncertain sports surfaces as sensitivity scenarios.
3. For every cell, fraction = green valid pixels / all valid pixels. Artificial non-vegetation remains in the denominator. No valid observations means NoData, never 0. Partition native pixels exactly once; increasing export pixels adds no evidence.
4. `scripts/rgb_grid.py` partitions saved masks and writes a CSV, NPZ and receipt. Check cell sums against the whole crop and independently recompute three cells.
5. Suggested green legend edges are 0, 5, 10, 20, 30, 50, 100%. These are configurable, not measurement thresholds. A tested design plate uses 30×30 cells, neutral grayscale context and 0.42 overlay alpha. Do not make this screenshot-specific resolution a universal rule.

A smaller crop changes the denominator and its reported percentage. Retain both extents and do not describe their difference as vegetation change. In an analytical comparison, use matched extents, thresholds and missing-data treatment.
