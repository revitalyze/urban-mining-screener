# OSM ODbL Compliance

This document explains obligations under the Open Database License (ODbL) for OpenStreetMap (OSM) data used by Urban Mining Screener (UMS), with specific guidance for UI attribution, repository documentation, and dataset releases. It also clarifies the difference between Produced Works and Derivative Databases and provides example wording.

Key references:
- ODbL license: https://opendatacommons.org/licenses/odbl/1-0/
- OSM copyright: https://www.openstreetmap.org/copyright
- Project sources overview: [docs/sources.md](sources.md)

Scope:
- UMS uses OSM-derived data (e.g., building footprints, metrics) accessed via Overpass or other means.
- Any public interface showing or relying on OSM-derived data must include attribution and observe share-alike obligations where applicable.

## Obligations at a Glance

- Attribution: Display “© OpenStreetMap contributors” prominently on user-facing pages that show or depend on OSM-derived data.
- Notice: Provide links to ODbL 1.0 and OSM copyright pages.
- Share-alike for Derivative Databases: If you publicly use or distribute a derivative database based on OSM, you must offer it under ODbL and provide equivalent rights.
- Keep open: If you make public use of a derivative database, you must share the database (or a functionally equivalent form) under ODbL.

## Produced Works vs Derivative Databases

ODbL distinguishes:
- Produced Work: A work resulting from the database (e.g., images, charts, rendered maps). Attribution is required; share-alike generally applies to the database, not the image itself.
- Derivative Database: A database based on the original (e.g., exported tables that retain object-level data or structured attributes derived from OSM). Share-alike obligations apply.

UMS outputs and examples:
- Analytical dashboards displaying aggregate metrics without per-object datasets → usually Produced Works (attribution required).
- CSV exports that aggregate totals by product category or element type, without object-level geometry references → likely Produced Works (attribution required).
- Per-building CSV files containing object-level identifiers or direct attribute tables derived from OSM (e.g., per-building footprints/IDs) → likely Derivative Database (ODbL share-alike applies).

When in doubt, prefer compliance by treating exported datasets as Derivative Databases and offering an ODbL-compliant dump with attribution and license notice.

## Required Attribution in the UI

Every user-facing screen that displays or depends on OSM-derived data must show an attribution footer.

Recommended footer text (example):
“Data © OpenStreetMap contributors, licensed under ODbL 1.0. See the [OpenStreetMap Copyright](https://www.openstreetmap.org/copyright) and [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/).”

Implementation notes:
- Place the footer on all pages that visualize or rely on OSM footprints/metrics.
- Keep the text visible on mobile and desktop.
- If using map tiles or third-party renderers, also include their required attributions.
- See related guidance in [docs/sources.md](sources.md).

## Share-Alike: Practical Guidance

If you publish a derivative database (e.g., an exported table containing OSM-derived building objects), you must offer it as ODbL:
- Provide an accessible URL to download the dataset under ODbL 1.0.
- Include attribution and license notice with the dataset.
- Document transformation steps to enable contributors to reproduce the dataset.
- If you mix OSM with other sources, ensure licenses are compatible and the combined dataset remains ODbL-compliant.

For analytical outputs (charts/images/tables without object-level data):
- Provide attribution and license links.
- Share-alike typically does not apply to the image itself, but if you publish the underlying database, ODbL applies to that database.

## Example Wording

Short attribution for UI footer:
- “© OpenStreetMap contributors (ODbL 1.0)”
- Link “OpenStreetMap Copyright” and “ODbL 1.0”

Extended attribution for README:
- “This project uses geospatial data from OpenStreetMap (ODbL 1.0). Data © OpenStreetMap contributors. For licensing details, see docs/osm-odbl-compliance.md.”

Dataset release note (for derivative database):
- “This dataset is a derivative database based on OpenStreetMap. It is provided under ODbL 1.0 with attribution to OpenStreetMap contributors. Transformation steps and schema are documented in [docs/data-model.md](data-model.md).”

## Operational Checklist

For ongoing ODbL compliance in Urban Mining Screener:

- Ensure all user-facing screens that rely on OSM-derived data display an attribution footer in the SPA (UI).
- Ensure the top-level [README.md](../README.md) includes an OSM attribution section.
- When releasing derivative databases (e.g. per-building exports), publish an ODbL notice alongside the data and provide stable download URLs.

## Notes for Partners and Danube Region Extensions

- Regional datasets may have additional licensing requirements.
- Document provenance, version, and license for each dataset used.
- For Pulse archetype extensions, verify licensing terms before redistribution (see [docs/archetypes-pulse.md](archetypes-pulse.md)).

## Implementation Notes and Open Items

The following aspects should be maintained as the project evolves:

- UI footer: The SPA should consistently display the OSM attribution footer on all relevant views. Any major layout or design changes should re-check visibility and responsiveness of this footer.
- Repository attribution: The OSM attribution section in [README.md](../README.md) should be kept in sync with this document and with the actual data sources in use.
- Dataset publication: When derivative databases are published, they should be accompanied by:
  - a clear ODbL 1.0 notice,
  - attribution to OpenStreetMap contributors, and
  - public download URLs that remain stable over time.
- Overpass and caching: Overpass endpoint(s), replication policies, and any caching layer should be documented (e.g. in [docs/architecture.md](architecture.md) or [docs/configuration.md](configuration.md)), including how often data is refreshed.