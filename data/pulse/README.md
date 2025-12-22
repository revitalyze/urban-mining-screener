# Pulse Archetype CSVs (Austria, 2024)

This directory contains Pulse-based archetype CSVs for Austria (2024) used by the Urban Mining Screener (UMS). These tables provide the default building, component, and product definitions that the backend ingests into the archetype schema described in:

- [`docs/data-model.md`](../../docs/data-model.md)
- [`docs/archetypes-pulse.md`](../../docs/archetypes-pulse.md)

The files are intended as a concrete, working Pulse-based configuration for Austria that can be used as a reference when extending UMS to other regions.

## Files

### `buildings_list.csv`

High-level building archetypes for Austria:

- Defines archetype identifiers, country, construction period, and key metadata.
- Links each archetype to its element composition (e.g. external walls, roofs, floors) via element and component references.
- Provides the reference metrics (e.g. ground floor area, volume) that are used for scaling to target buildings.

### `components_list.csv`

Component definitions and their layer stacks:

- Defines components (assemblies) such as specific wall, roof, or floor build-ups.
- Maps each component to one or more products with layer thicknesses and share factors.
- Serves as the bridge between element-level areas and product-level material quantities.

### `products_list.csv`

Product catalog for materials:

- Defines products with identifiers, categories, and raw densities.
- Provides the basic material properties that are used to convert volumes to masses and to aggregate results by product category.
- Forms the basis for the material breakdown reported by UMS.

For detailed schema descriptions and how these CSVs are mapped into the database tables, see:

- [`docs/data-model.md`](../../docs/data-model.md)
- [`docs/archetypes-pulse.md`](../../docs/archetypes-pulse.md)

## License and usage

These CSVs are part of the Urban Mining Screener Software and are governed by the same **Urban Mining Screener Software License Agreement** as the rest of the repository:

- See [`../../LICENSE`](../../LICENSE) for the full license text.

In particular:

- The CSVs are made available together with the source code for **research, testing, and evaluation** by the community and project partners.
- **Commercial exploitation or redistribution** of these CSVs, in whole or in part, is **not permitted** without prior and explicit consent from Graz University of Technology and revitalyze FlexCo.
- The CSVs are considered bundled archetype data of the Software; they are not licensed under a permissive open-source data license.

The archetype definitions in this directory are derived from Pulse 2024 / Austria work.

## Citation

If you use the Urban Mining Screener and the bundled Pulse-based archetypes for scientific work, please cite the Software as described in the main project README:

- [`../../README.md`](../../README.md)