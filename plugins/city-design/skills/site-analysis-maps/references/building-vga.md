# Building-only visibility graph analysis

The user may mean street angular-segment syntax or planar VGA. A request to treat only buildings as obstacles requires a **new building-only visibility graph**, not diffusion of an existing street score.

## Geometry and computation

- Inspect CAD units and layers. A Make2D visible-line drawing is not a building-footprint layer. Polygonization creates candidates; inspect multiple areas and distinguish roof outlines from paving, sports fields, landscape plinths, fences and open courts. Save selected/excluded IDs in diagnostics, but do not print them when the user requests no numbering.
- Preserve meaningful building holes, entrances and overhang distinctions when supported. Roof projections interpreted as fully opaque plan obstacles are an explicit simplification. Do not silently fill true courtyard holes just to make the graph easier.
- Place every obstacle and sampling point in one frame. Display rotation is not a georeference or proof of north. Keep the computational extent and display crop distinct, and retain context obstacles outside the visible crop.
- With a verified depthmapX CLI, retain engine version/hash, obstacle DXF and graph files. A tested 0.9.1 sequence is `IMPORT` → `VISPREP -pg <spacing> -pp <outside seed> -pm` → `VGA -vm visibility -vg -vr n` → `EXPORT -em pointmap-data-csv`. Inspect the installed CLI help before using version-sensitive options.
- A graph boundary limits results; a computational frame is not a physical site wall. Unconnected free spaces need additional seeds/components or an explicit uncomputed status. Do not paint unreachable or unsampled cells as zero integration.

## Readback

Check unique node references, uniform grid spacing, finite values, graph component sizes and zero calculated centers inside buildings. For at least three separated node centers, independently intersect sight lines with the actual obstacle geometry and compare visible neighbors with Connectivity.

For finite HH integration, independently check `RA = 2*(mean_depth-1)/(n-2)`, `Dn = 2*(n*(log2((n+2)/3)-1)+1)/((n-1)*(n-2))`, and `HH = Dn/RA`. Respect undefined cases rather than forcing n≤2 or mean_depth=1 through the formula. Global VGA within a finite frame is **Rn**, not the previous street-network R800.

## Drawing

Draw native analysis cells, white opaque buildings and a compact legend with metric/radius. A vivid red-blue palette and a lower alpha can be used without changing the metric table. Any display-only interpolation near building edges must be recorded; do not add metric records for interpolated display pixels. Retain NoData visibly distinct from white buildings and low scores. Cropping for composition must not change the saved graph or its normalization unless explicitly requested.

Visibility does not imply permission to walk through fences, private compounds or vegetation. Building-only VGA is a geometric scenario, not a measured pedestrian-flow prediction.
