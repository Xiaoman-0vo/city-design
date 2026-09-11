# Editable delivery, version compatibility and recovery

Read this when handing off a model, exporting an older version, resuming uncertain saves or changing a model the user may have edited.

## Preserve the active authority

Identify the actual file path, document identity, units, source hash and current revision. A delivery copy the user has edited may supersede the last generated project snapshot. Compare them before rerunning an older generator. Preserve user-frozen objects and intentional deletions; update the owning parameters/registry when a requested change is meant to persist. Do not restore deleted objects merely because a historical source still contains them.

Keep shape parameters separate from absolute placement transforms. A repeated operation must not accumulate rotations or translations. Where a partial model replaces part of a site, check its frame and replace the corresponding objects/definitions rather than importing a duplicate on top.

## Save, reopen and compare

On an uncertain save, inspect the existing file and live documents first. Preserve an unsaved/recovery copy before resolving conflicts. With multiple Rhino windows, check each target's path, document identifier and modified state. Close only requested windows after preserving necessary edits; avoid overwriting a newer file with an older window.

Record source/output hashes, stable IDs, units, visibility, material assignments and named views. Independently reopen or read the saved model and inspect the changed geometry. A successful save, valid geometry, internal circulation, photo agreement and physical metric accuracy are separate checks. A floor opening must remain cut in the saved ground geometry; moving an underground space also requires checking covering surfaces and the perimeter connection.

## Match the recipient's Rhino version

Determine the receiver's target version and create a separate exchange file. Keep the editable original. Use native Save As when a connected Rhino can perform the conversion; verify the resulting archive and reopen it. The optional `scripts/city_design.py export-rhino8` command supports conservative SDK export for readable geometry and records exactly what was checked. It does not certify all Rhino 9-only features or third-party plugin data.

Do not replace an editable 3DM with STL/OBJ by default. Confirm geometry, object identity, layer/block structure, colors, units and camera views after conversion. Preserve the source if any check fails. Report whether acceptance used an SDK or the actual recipient application. Native Rhino 8 opening and display remain unverified until performed there.

For delivery, provide one clearly named current file and optional local/compatibility copies, with their purpose and coordinate relationship. Only share the files the user has authorized; internal logs, private configuration and raw photo metadata do not belong in a public plugin package.
