# Photograph-constrained site reconstruction

Use this guidance for an existing site reconstructed from ground photographs. It records failures observed in the September 2026 City Design site exercise, not a general claim of survey accuracy.

## Preserve what the camera recorded

- Keep immutable originals and a source-to-derived manifest with hashes, exposure ID, paired video, timestamps, orientation, native dimensions, physical lens, focal length, 35 mm equivalent, digital zoom, GPS accuracy and heading. Inventory all supplied angles before choosing computational subsets. Reuse completed features and matches when only calibration or pose solving changes.
- Resizing and EXIF transposition can strip metadata. Supply the original calibration explicitly to the reconstruction database. Rotate or resize image coordinates and intrinsics consistently; verify landscape and portrait examples independently.
- Group camera intrinsics by physical lens and effective crop/zoom, with the transformed image dimensions. Equal 35 mm equivalents do not identify the same physical lens. Do not multiply a digital-zoom factor again when the recorded equivalent focal already includes the crop. Check the adopted field of view against the actual camera's metadata conventions.
- Equal GPS locations, rounded coordinates, or adjacent capture times do not identify the same pose. Keep separate rotations for every exposure. Adjacent images from one position provide rotation/visibility information but may provide almost no triangulation baseline.
- GPS, altitude, compass heading and their reported errors are soft evidence unless independently controlled. Identify outliers before site registration. Focus-distance metadata is not automatically a building range or metric scale control.

Apple maker-note acceleration was usable as an orientation check in this exercise. ExifTool identifies tag 8 as `AccelerationVector`; inspect the decoded coordinate convention before applying it. For the native metadata here, swapping the first two components and applying the image's EXIF rotation brought it into the displayed camera frame. The reconstructed up vector was then `R_camera_from_world.T @ a_camera`. This convention was checked across multiple poses; do not assume another extractor has identical axis order. Acceleration during movement also perturbs this gravity prior. Source: [ExifTool Apple maker-note definitions](https://github.com/exiftool/exiftool/blob/master/lib/Image/ExifTool/Apple.pm).

## For an editable urban analysis base

When the requested deliverable is an editable urban analysis base, follow [ground layout and placement](ground-layout-and-placement.md) before adding facade detail. Existing drafts and photo evidence can support provisional geometry without completing global photogrammetry. Keep point clouds in their own frame until a supported transform exists. Organize placement by stable site objects and their dependencies, not reconstruction component IDs. A local entrance can be internally connected yet misplaced relative to the street; check both relationships.

## Make the geometry explain several views

Use photographs as the form evidence when the user specifies this priority; maps assist footprint context and coordinate placement. Record contradictions, for example a map's construction parcel that photographs show as occupied. Identify the object before adding detail: a metro pavilion, residential gate and school gate have different circulation geometry.

Maintain exposure-level states such as inventoried, matched, registered in a local component, orientation checked, site aligned and photo/model checked. A large registered count can hide several disconnected scenes or repeated-facade mismatches. Report component sizes and the evidence needed to connect them, rather than silently treating all components as one site frame.

Repetitive windows, wall tiles and paving can produce convincing but incorrect correspondences. Check positive depth, triangulation angle, track distribution, gravity consistency, plausible baselines and withheld fixed edges. Fit visible corners, parallel/orthogonal wall directions and level changes where the photographs support them. Label dimensions based on nominal railing or eye height as assumptions. A low fitting error on the wall used to solve the cameras does not independently validate another wall, the ground or the entire scene.

Model storefront depth, awnings, open fences, guardhouses, pedestrian/vehicle entries, stairs and terrain openings as geometry where visible. A downward stair below an uncut ground surface is not an entrance. Trees contribute real occlusion and spatial structure: model their visible trunks/crowns and use other angles to infer hidden construction. Distinguish observed and continued surfaces; do not fill an unseen facade with invented detail and call it verified.

For same-view acceptance, save the source photo ID, image dimensions, intrinsics and extrinsics with each named view. Render the model at the corresponding aspect and field of view, compare fixed architectural outlines in multiple directions, and retain residuals and unresolved differences. Keep fit observations distinct from withheld checks. Texture, season, illumination and transient people/vehicles should not conceal a geometric mismatch.

## Rhino Mac failures that changed the workflow

- Inspect the MCP slot's injected document, its path, units and object count. `ActiveDoc`, a newly opened window, and the tool-bound document can differ. Opening a file does not prove the slot changed documents; `UpdateDocumentPath` did not resolve this in the observed Mac session.
- Read nested execution errors even when the tool wrapper reports success. On an uncertain save or import, inspect the file and document before retrying. Preserve recovery/autosave content in a controlled copy first.
- Verify metre units after import and after reopening. An unset unit system cannot be declared correct merely because numerical dimensions look plausible.
- Importing an updated model into a document with old, same-named block definitions can retain stale geometry. Reconcile definitions or use a new revision identifier, then compare changed parts in the actual document.
- `ViewInfo.Viewport` behaved as a copy in the observed API. Set a `ViewportInfo` on the live viewport, add the named view from that viewport, and read it back. Reset stale clipping/projection before comparison captures.
- Normalize near-duplicate polygon closure vertices to the model tolerance before extrusion. Check positive extrusion direction, caps, zero-area slivers and all block-definition geometry. Account for polygons that collapse during precision reduction; native validity and lost-area accounting are separate checks.

These are case-supported operating precautions. They do not establish arbitrary reconstruction accuracy, current connection availability or statutory drawing compliance.
