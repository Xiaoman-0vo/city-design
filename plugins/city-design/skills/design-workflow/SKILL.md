---
name: design-workflow
description: Coordinate City Design projects across QGIS, Rhino/Grasshopper and AutoCAD, using controlled copies, native file verification and evidence from design practice. Use for urban or architectural design work that needs these connected applications.
---

# City Design

Translate the user's design intention into editable native deliverables and checked changes. Read the selected project's AGENTS.md and state first; a plugin installation does not itself authorize unrelated projects or external publication.

## Find the connected project

Use `../../scripts/city_design.py doctor` to inspect configuration. A fresh install may report `NEEDS_CONFIGURATION`; the independent `demo --output <new-directory>` still works without native applications. Pass `--project <project-directory>` before commands for real work. Use `init-project` only for a new directory, and read `../../docs/USAGE.md` for optional private bindings. Read `../../references/mac-runtime.md` for the historical Mac adapter, not as a current connection snapshot.

When asked to install or supplement native connections, first read `../../docs/CONNECTIONS.md` and `../../references/connections.json`. Use `../../scripts/connections.py` for staged QGIS acquisition and configuration; preserve existing MCP entries and private tokens. Rhino uses McNeel official components; QGIS MCP is community maintained. Autodesk Help only searches documentation. The documented AutoCAD native MCP route is Windows/Autodesk Assistant, not a supported Mac/Codex shortcut. Verify live native responses separately from registration.

Historical cross-application verification covers a synthetic four-building workflow with private adapters. The public package includes a separate portable example and optional Rhino SDK output; it does not include those private adapters. Photo site reconstruction is a developing capability. `../../references/capabilities.json` records evidence and limits. Recheck live tools and document identity when resuming. Native wrappers may report transport success around an internal error: require native receipts and reopened output files.

Use `../../scripts/city_design.py assess-run --prefix <run-id>` to re-evaluate saved cross-application receipts, stable IDs, floor counts, metrics, control points and editable native outputs. This is a read-only evidence check; it does not replace reopening the applications for a fresh acceptance.

## Execute a design revision

1. Establish source files, units, coordinate frame, stable feature IDs, frozen objects and the requested changes. Keep original files; make a new run or controlled working copy. Unknown coordinates, legal floor-area rules and green area remain unknown.
2. Discover actual tool schemas. Use Rhino for scheme geometry, QGIS for spatial checks, and AutoCAD for controlled drawings. Serialize writes to each native document. Preserve document identity across Mac windows.
3. Save native geometry, then derive exchange data from the saved file. Reopen QGIS, Rhino/GH and CAD outputs separately to compare IDs, geometry, floors and declared metrics. Include at least three non-collinear control points when checking a coordinate transformation.
4. Use the Chinese drawing standards skill for a standards-dependent drawing. Determine discipline, stage and jurisdiction before selecting a profile. Keep model geometry separate from a submission drawing that requires flat lines, a particular layer table or different units.
5. Review the exported page for scale, Chinese glyphs, clipping, line weights, legend and source/date. Preserve the editable native project alongside the PDF.
6. Report the actual changes, failed checks and evidence paths; update the project status. A test model does not establish statutory or construction compliance.

On a write timeout, record `TIMEOUT_UNCERTAIN`, inspect the file/process state and reconcile before retrying. Do not replay a possibly completed mutation under a fresh name merely to avoid the check.

Before handoff, compatibility export, uncertain recovery or updating a user-edited file, read `../../references/delivery-and-recovery.md`. Determine the recipient's Rhino version, preserve the editable original, and verify the exported copy. Check frozen objects and intentional deletions before rerunning an old generator. SDK acceptance and native application acceptance must be reported separately.

## Establish ground layout before placing site objects

For existing-site and urban-base-model work, follow **先确定地面格局，再放置建筑与附属构件，最后细化**. Read `../../references/ground-layout-and-placement.md` when placing buildings, entrances, fences or trees, or correcting objects that are misaligned with roads.

Establish a versioned ground layout and coordinate basis first: roads and curbs, pedestrian space, parcel boundaries, green areas, openings and levels. Mark unresolved parts provisional. Derive placement frames for the relevant street or parcel; preserve photo-supported building angles. Move dependent entrance paving, fences and trees with their parent placement. Before further detail, inspect the actual saved plan and check carriageway conflicts, setbacks, supporting ground and entrance connections. Ground-layout changes invalidate affected placement checks.

This is an agent workflow requirement with case-supported project checks; the plugin does not yet provide a universal automatic alignment or collision engine.

## Reconstruct a photographed site

Read `../../references/photo-site-reconstruction.md` when photographs constrain an existing site's geometry or camera views. Preserve original metadata through image transformations, keep each exposure's pose independent, and judge acceptance using the user's requested photo/model comparison. A saved, valid 3DM and a low feature reprojection error are intermediate evidence, not proof that the photographed space has been reproduced.

## Reproduce an example

For a portable first run, use `../../scripts/city_design.py demo --output <new-directory>`. Add `--with-rhino` when the optional rhino3dm dependency is installed. This creates its own synthetic inputs, preview and checked SDK files; it does not open design applications or establish cross-application acceptance.

For an explicitly requested legacy adapter check in a project that supplies the native runner, run:

```
python3 <plugin>/scripts/city_design.py run-synthetic --prefix <new-run-id> --execute
```

This invokes the pinned project runtime; it does not install packages. Check `doctor` first. It opens native applications through the existing adapters and writes a new synthetic run. A repeated run ID is rejected. AutoCAD PDF publication currently uses the verified main-window route separately; the example runner does not automate that print dialog.

## Improve the plugin through practice

Use `../../references/practice-loop.md` after a useful design exercise or a demonstrated failure. Promote only behavior supported by retained inputs, native outputs and checks. Keep new design methods experimental until tested on the relevant geometry and stage; avoid making one project's drawing preferences universal.

Run `../../scripts/city_design.py practices` to inspect the promoted capability cases and their explicit exclusions.
