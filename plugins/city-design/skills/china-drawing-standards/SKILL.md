---
name: china-drawing-standards
description: Select and check Chinese urban planning, architectural, landscape, municipal and GIS drawing standards for City Design deliverables, keeping current standards, drafts, local requirements and project conventions distinct.
---

# Chinese drawing standards

Read `../../references/standards/catalog.json` to locate sources and `../../references/standards/rules.json` for the initial rule mappings. The catalog is dated evidence, not an automatically refreshed legal database. Verify status at the issuing authority or authoritative catalog before a new formal issue; use available public text or the user's authorized copy for exact clauses.

Determine the deliverable first: planning master plan, site plan, architectural plan/section/elevation, landscape, municipal discipline, topographic map, analytical map, presentation or electronic submission. Identify jurisdiction, project stage, scale and the school's or client's requirements. Do not apply a single symbol/color/unit profile to every category.

Keep four distinctions explicit:

- A standard's current status versus possession of its full text. A catalog entry permits selection, not invented clause-level checks.
- A issued standard versus a draft or standardization plan. GB/T 18112-2000 is recorded as repealed; plan 20221187-T-334 was awaiting approval at this collection date. Neither is an active drawing default.
- A national/industry standard versus an association or local rule. T/UPSC 0002-2018 is an electronic-submission reference; confirm adoption by the receiving authority before treating it as the submission contract.
- Model units versus paper dimensions and annotation conventions. Architectural drawings can require millimetres while a site model uses metres; preserve source geometry and use an explicit export transform.

For an applicable rule, record standard ID, edition, clause, jurisdiction, drawing type, extracted requirement, implementation/check and evidence. Mark each check `PASS`, `FAIL`, `NOT_APPLICABLE`, `MANUAL_REVIEW` or `SOURCE_REQUIRED`; never equate missing information with passing. Store custom aesthetics as project conventions without claiming they are national requirements.

The initial mappings cover a small set of verified clauses. They do not implement every standard in the catalog. In particular, the existing synthetic CAD model includes height-bearing geometry and custom layers; it is not a T/UPSC-compliant electronic-submission file. Prepare a dedicated flat export and the adopted layer/attribute mapping before evaluating that contract.

Create a project-relative facts manifest using `../../references/standards/drawing-manifest.schema.json`, then run `../../scripts/city_design.py --project <project-directory> check-drawing --manifest <project-relative.json>`. The command evaluates seven mapped rules and can write a JSON report with `--output`. Inputs are declared facts; until native scanning exists, verify them against the drawing rather than treating the report as full conformance. Missing entity counts are missing evidence, not zero. Electronic submission coordinates pass only when their source is the receiving authority, the file is not synthetic and at least three control points are non-collinear.

Downloaded standards remain in the controlled project standards library with source URL and checksum. The distributable plugin carries references and original rule mappings, not a blanket redistribution license for third-party PDFs.
