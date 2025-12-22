# Data Sources and Licensing

This document summarizes geospatial and archetype data inputs used by Urban Mining Screener (UMS), highlights licensing obligations (especially ODbL for OpenStreetMap), and records placeholders for dataset versions/links to align with the Circular DigiBuild offer for the Danube Region.

- Primary geospatial source: OpenStreetMap (OSM) via Overpass API
- Archetype baseline: Pulse study (Austria, 2024) — extendable per region
- Elevation/height data: optional/region-dependent; placeholders included
- ODbL compliance is mandatory for any public output, website, or dataset derived from OSM. See [docs/osm-odbl-compliance.md](osm-odbl-compliance.md)

## OpenStreetMap (OSM) and Overpass

UMS retrieves or depends on building footprints and related attributes from OSM. Access typically occurs via Overpass API or cached derivatives.

- Source: OpenStreetMap contributors (ODbL 1.0)
- Access pattern:
  - Query building polygons/footprints
  - Compute ground area (m²) and perimeter (m)
  - Attempt to derive/approximate building height (m) where available
- Licensing: ODbL 1.0 requires attribution, notice, and share-alike for derivative databases. See [docs/osm-odbl-compliance.md](osm-odbl-compliance.md).

Attribution requirements (summary):
- Prominent “© OpenStreetMap contributors” statement
- Link to ODbL and OSM
- If publishing derivative databases, ensure ODbL compliance and share-alike


## Archetypes: Pulse Baseline (2024, Austria)

UMS uses archetype definitions that include reference ground area (BGF), volumes, element types, and component compositions. The current baseline references a 2024 Pulse study for Austria and can be extended per region.

Scope and use:
- Reference BGF and reference volume are used to scale to target building metrics.
- Element/component composition defines products, thickness (cm), and percentage shares.
- Factors such as roof, retaining walls, and window ratios are derived from reference element areas.

Bundled Pulse CSVs for the Austria baseline are provided under:

- [`data/pulse/buildings_list.csv`](../data/pulse/buildings_list.csv)
- [`data/pulse/components_list.csv`](../data/pulse/components_list.csv)
- [`data/pulse/products_list.csv`](../data/pulse/products_list.csv)

Documentation:
- Data model: [docs/data-model.md](data-model.md)
- Pulse relationship and extensibility: [docs/archetypes-pulse.md](archetypes-pulse.md)