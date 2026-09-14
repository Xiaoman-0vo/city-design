# Winter/summer sunlight on model ground

This is geometric direct-sun duration, not irradiance, brightness, weather-observed sunshine or a regulatory daylight certificate. Select the analysis year and verify the solstice dates in the site's local time zone. The day can differ from the UTC date.

## Preserve the model frame

Read the current saved model, not an older massing generator. Check units, geographic origin, the model-to-projected transform and the relation between projected grid north and true north. Check at least three non-collinear retained placements against their recorded transforms. This validates model-frame consistency, not survey registration.

For a Rhino model, resolve instance definitions recursively, compose each instance transform exactly once, and exclude definition objects from the top-level scene. Honor hidden/history/superseded object status. Use native mesh geometry or cached render meshes from the saved Breps. If a major surface lacks a mesh, obtain a controlled native mesh rather than substituting its bounding box. Record any deliberately omitted sub-grid detail; do not silently omit missing buildings or floors.

Define occluders and receiving surfaces separately. A downwards ray can locate the uppermost ground or paving surface at each grid center; an exposed lower courtyard must retain its negative elevation. Building interior/roof projections are a separate display mask. Missing ground is NoData. Raise test rays slightly above the sampled surface to avoid numerical self-intersection and record that offset.

## Calculate and compare

Use a verified solar-position implementation, for example pvlib's NREL SPA, with time-zone-aware timestamps. Solar azimuth is relative to true north; transform the horizontal direction into the model frame before intersecting geometry. For each daylight time interval, accumulate its duration only where the ray toward the sun is unobstructed. Keep all known context occluders even when the display crop is smaller.

Use the same receiver grid, model and hour scale for both dates. A case used 5 m cells, 5-minute midpoint sampling and a 0–15 h legend; these are adjustable analysis settings, not guaranteed accuracy. Keep the blue/red hour legend continuous and consistent. Vegetation requires explicit evergreen/deciduous/transmission assumptions; do not silently treat an opaque summer crown model as known winter vegetation. A building-only comparison may exclude crowns if that scenario is documented.

## Checks

- A box of height H must cast a horizontal shadow of length H/tan(solar altitude) on level ground.
- Spot-check rays with a second triangle-intersection implementation and verify several solar positions with an independent ephemeris.
- Halve the time step on spatially distributed receivers and record median/max duration differences. Refine if the difference matters for the intended decision.
- Durations lie between zero and the sampled unobstructed daylight interval. Dates use the same limits, missing-data mask, building display and plot rectangle.
- Preserve source model hash, geometry counts, excluded objects, true-north basis, surface elevations, dates/time zone, solar algorithm/version, raw grid CSV/NPZ and checks.

The project case supports an approximate model-based comparison; uncertain building heights, absent context beyond the model and unknown tree seasonality remain physical limitations even when the computation checks pass.
