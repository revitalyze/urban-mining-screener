# Archetypes and Pulse 2024 Integration

This document explains how building archetypes are represented in the Urban Mining Screener (UMS), how they are related to the Pulse 2024 archetype definitions, and how partners (especially in the Danube Region) can extend or replace archetypes for their countries using CSV imports.

It is intended for:

- Data providers and research partners preparing archetype tables.
- Developers integrating new archetype sources.
- Project owners who need to ensure licensing and provenance for archetype data.

For the underlying table and entity structure, see [`docs/data-model.md`](data-model.md). For data sources and licensing, see [`docs/sources.md`](sources.md) and [`docs/osm-odbl-compliance.md`](osm-odbl-compliance.md).


## 1. Background: Building Archetypes

### 1.1 Concept of archetypes

In UMS, a **building archetype** is a template describing a “typical” building in terms of:

- Country and climatic/market context.
- Construction period.
- Building type/usage.
- Reference ground floor area and reference volume.
- Composition of building elements (foundations, floors, walls, roofs, windows, etc.) into components and products.

Archetypes allow UMS to estimate material stocks and flows even when only limited building-specific data are available (e.g. address, footprint, and a small set of attributes). Instead of modeling each building from scratch, UMS scales archetypical reference metrics to the target building geometry.

This archetype approach is common in EU-wide projects. UMS follows this practice and structures archetypes in a normalized relational schema (see [`docs/data-model.md`](data-model.md)).


### 1.2 Relevance for the Urban Mining Screener

Archetypes drive:

- **Reference factors and scaling**:
  - `ref_bgf` (reference ground floor area) and `ref_volume` (reference building volume).
  - Element-level reference areas (e.g. external walls, roofs, internal walls) in `archetype_elements`.
  - Factors derived from reference areas, such as roof factors, retaining wall factors, and window factors (see [`app/utils/factor_calculator.py:calculate_reference_factors()`](../app/utils/factor_calculator.py:16)).

- **Element and component composition**:
  - Which components (assemblies) are used for each element type and refurbishment level.
  - Which products, thicknesses and percentage shares make up these components.

## 2. Pulse 2024 Baseline

### 2.1 Role of Pulse archetypes

The initial UMS configuration uses **Pulse 2024** archetype definitions for Austria (AT) as a baseline. These provide:

- Reference building-level metrics (BGF, volume).
- Element-level reference areas.
- Detailed component and product compositions for typical Austrian building types and periods.

Pulse-based archetype CSVs for Austria are bundled with this repository under `data/pulse/` and are ingested into the database schema described in [`docs/data-model.md`](data-model.md). They provide a concrete, working configuration that can be used as a reference for extending UMS to other regions.


### 2.2 Pulse data licensing

Pulse-derived CSVs are considered part of the Urban Mining Screener Software:

- Bundled CSVs: [`data/pulse/buildings_list.csv`](../data/pulse/buildings_list.csv), [`data/pulse/components_list.csv`](../data/pulse/components_list.csv), [`data/pulse/products_list.csv`](../data/pulse/products_list.csv)
- Data directory README: [`data/pulse/README.md`](../data/pulse/README.md)
- Software license text: [`../LICENSE`](../LICENSE)


## 3. UMS Archetype Schema

UMS stores archetypes and their element/component/product structure using the relational schema created in the initial migration:

- Migration: [`alembic/versions/c668fc8fc00d_init.py`](../alembic/versions/c668fc8fc00d_init.py:1)
- Schema description: [`docs/data-model.md`](data-model.md)

The key entities for archetypes are:

- `archetypes`
- `element_types`
- `archetype_elements`
- `components`
- `element_components`
- `component_products`
- `products`


### 3.1 Archetypes

**Table**: `archetypes`  
Defined in the migration and documented in [`docs/data-model.md`](data-model.md).

Key fields (simplified):

- `archetype_id`: string, primary key; recommended to encode country and type, e.g. `AT_RES_1960_1980`.
- `country`: ISO country code (e.g. `AT`, `DE`, `HU`, `BG`).
- Building descriptors (implementation may use `building_type`, `construction_period_start`, `construction_period_end`, etc.).
- `ref_bgf`: reference ground floor area (m²).
- `ref_volume`: reference building volume (m³).

Usage:

- `ref_bgf` and `ref_volume` are used in factor derivation and volume scaling (see [`app/utils/factor_calculator.py:calculate_reference_factors()`](../app/utils/factor_calculator.py:16)).
- `ref_volume` is particularly important for internal wall scaling (see [`app/utils/volume_calculator.py:calculate_material_volumes_weights()`](../app/utils/volume_calculator.py:16)).


### 3.2 Element types and archetype elements

**Element types**:

- **Table**: `element_types`
- Fields:
  - `element_type_id` (PK)
  - `name` (string, unique)
- Examples: `"Ground floor"`, `"External walls"`, `"Roof"`, `"Windows"`, `"Internal walls, load-bearing"`.

Element types drive algorithmic branching via constants defined in [`app/utils/estimation_constants.py`](../app/utils/estimation_constants.py:1), e.g.:

- `EL_TYPE_GROUND_FLOOR`
- `EL_TYPE_EXTERNAL_WALLS`
- `EL_TYPE_WINDOWS`
- `HORIZONTAL_ELEMENTS`
- `INTERNAL_WALL_ELEMENTS`
- `AREA_BASED_ELEMENTS`

**Archetype elements**:

- **Table**: `archetype_elements`
- Fields:
  - `id` (PK)
  - `archetype_id` → `archetypes.archetype_id`
  - `element_type_id` → `element_types.element_type_id`
  - `ref_area` (float, m²)

Usage:

- Reference areas per element type are used to compute proportions and factors, for example:
  - Roof and retaining wall factors \(\text{faktor\_dach}\), \(\text{faktor\_sm}\).
  - Window factor \(\text{faktor\_w}\).
- Summation and factor derivation are implemented in [`app/utils/factor_calculator.py`](../app/utils/factor_calculator.py:1).
- Proportions per component within an element are used when deriving target areas in [`app/utils/area_estimator.py:estimate_target_areas()`](../app/utils/area_estimator.py:36) and [`app/utils/area_aggregator.py:calculate_all_as_built_areas()`](../app/utils/area_aggregator.py:33).


### 3.3 Components and element components

**Components**:

- **Table**: `components`
- `component_id`: string (PK)
- Represents a logical assembly: e.g. a specific external wall, roof buildup, or ground floor buildup.

Components are typically populated from CSV via [`app/utils/component_processor.py:process_components_and_products()`](../app/utils/component_processor.py:14), which:

- Reads component IDs and associated product rows.
- Creates `Component` instances and `ComponentProduct` links.
- Ensures numeric parsing of thickness and percentage and basic validation.

**Element components**:

- **Table**: `element_components`
- Fields:
  - `id` (PK)
  - `element_id` → `archetype_elements.id`
  - `component_id` → `components.component_id`
  - `refurbishment_level` (string, default `"as-built"`)

Usage:

- Connect a given `archetype_elements` entry with one or more components.
- Support multiple `refurbishment_level`s (e.g. `"as-built"`, `"partial"`, `"exchange"`, `"medium"`, etc.).
- Used by refurbishment logic and window logic; see:
  - Refurbishment rules: [`app/utils/refurbishment_rules.py`](../app/utils/refurbishment_rules.py:1)
  - Half-exchange roof logic: [`app/utils/half_exchange_logic.py`](../app/utils/half_exchange_logic.py:10)
  - Window data: [`app/utils/window_calculator.py:calculate_window_data()`](../app/utils/window_calculator.py:68)


### 3.4 Component products and products

**Component products**:

- **Table**: `component_products`
- Fields:
  - `id` (PK)
  - `component_id` → `components.component_id`
  - `product_id` → `products.product_id`
  - `schichtstaerke` (float; layer thickness in cm or other scaling quantity)
  - `percentage` (float; share factor, generally in [0,1])

Usage:

- Define the **composition** of each component in terms of products, thicknesses, and shares.
- Used in [`app/utils/volume_calculator.py:calculate_material_volumes_weights()`](../app/utils/volume_calculator.py:16) to compute volumes and weights.

**Products**:

- **Table**: `products`
- Fields:
  - `product_id` (PK)
  - `designation_en` (string)
  - `category_en` (string)
  - `raw_density` (float, kg/m³)
  - `unit` (string)

Usage:

- `raw_density` converts volumes from m³ to weights in kg.
- `category_en` supports aggregation by product category.
- `unit` provides semantic context (e.g. m³, m², pieces).


### 3.5 How one archetype is defined

Putting it together, one archetype is defined by:

- **Metadata**:
  - Country (`country`), construction period, building type, etc.
- **Reference metrics**:
  - `ref_bgf` and `ref_volume` for scaling.
- **Element set**:
  - `archetype_elements` records for each `element_type_id`, with `ref_area`s.
- **Components and refurbishment**:
  - `element_components` mapping each element to one or more `components` per refurbishment level.
- **Component composition**:
  - `component_products` mapping components to `products` with `schichtstaerke` and `percentage`.


## 4. CSV Import and Pulse Mapping

UMS supports ingestion of archetype, component and product data via CSV to simplify integration of external sources such as Pulse.

Relevant code:

- CSV upload endpoint: [`app/routes/csv_upload.py`](../app/routes/csv_upload.py:1)
- CSV reader utility: [`app/utils/csv_reader.py`](../app/utils/csv_reader.py:1)
- Archetype processing: [`app/utils/archetype_processor.py`](../app/utils/archetype_processor.py:1)
- Component processing: [`app/utils/component_processor.py`](../app/utils/component_processor.py:1)


### 4.1 CSV upload flow

The typical ingestion flow is:

1. **Upload CSV(s)** via the API endpoint in [`app/routes/csv_upload.py`](../app/routes/csv_upload.py:1). The endpoint:
   - Accepts CSV files for products, components, archetypes, and archetype-element mappings (exact file set depends on the configuration).
   - Passes them to the CSV utilities.

2. **Parse CSVs** using [`app/utils/csv_reader.py`](../app/utils/csv_reader.py:1), which:
   - Normalizes column names and types.
   - Converts numeric columns where appropriate.
   - Provides structured dataframes.

3. **Create or update entities** using [`app/utils/archetype_processor.py`](../app/utils/archetype_processor.py:1) and [`app/utils/component_processor.py`](../app/utils/component_processor.py:1):
   - `archetype_processor`:
     - Reads archetype-level information and populates the `archetypes` table.
     - Creates `archetype_elements` for each element type.
     - Creates `element_components` for each element and refurbishment level.
   - `component_processor`:
     - Processes component and component-product relations:
       - Ensures consistent `component_id`s.
       - Validates `Product ID`s against the `products` table.
       - Converts thickness and percentage to numeric values and sets `schichtstaerke` and `percentage`.

4. **Commit to the database**:
   - The processed records are stored in the database defined by [`alembic/versions/c668fc8fc00d_init.py`](../alembic/versions/c668fc8fc00d_init.py:1).


### 4.2 Mapping Pulse archetypes to UMS schema

A single Pulse archetype (conceptually one row in the original Pulse tables) is mapped as follows:

- **Archetype row → `archetypes` record**:
  - Country, building type, construction period, etc. populate the `archetypes` row.
  - Reference ground area and volume from Pulse become `ref_bgf` and `ref_volume`.

- **Pulse element rows → `archetype_elements` records**:
  - For each element type (e.g. external walls, roof, internal walls) represented in Pulse, create an `archetype_elements` entry with `ref_area`.

- **Pulse element–component mapping → `element_components` records**:
  - For each combination of element and component in Pulse (and for each refurbishment level where applicable), create `element_components` rows.

- **Component compositions → `components` and `component_products` records**:
  - Each Pulse component becomes a `components` row (`component_id`).
  - For each product in that component, create a `component_products` row with:
    - `product_id`
    - `schichtstaerke` (thickness or similar scaling)
    - `percentage` (share factor).

**Important**: For the Austria baseline, a Pulse-derived CSV export is bundled under `data/pulse/` and governed by the Urban Mining Screener Software License Agreement (see [`../LICENSE`](../LICENSE)). For any additional Pulse or non-Pulse archetype datasets, project owners and partners must:

- Verify that redistribution in this repository is allowed under the source data license.
- Ensure that bundling is compatible with the Urban Mining Screener Software License Agreement.
- Keep non-redistributable datasets in separate, non-public data locations and configure deployments accordingly.

See Section 7 for general licensing guidance.


## 5. Extending Archetypes for Danube Region Partners

UMS is designed to be extended beyond Austria. Partners in the Danube Region can define archetypes for their own countries using the same schema and CSV processes.

### 5.1 Recommended workflow

A recommended step-by-step workflow for partners:

1. **Start from the reference Pulse mapping for Austria (AT)**:
   - Use the existing AT archetype CSV templates as a **structural template** (columns, type names, component IDs, etc.).
   - Do **not** reuse Austrian numeric values without checking applicability.

2. **Create a country-specific CSV template**:
   - Duplicate the AT CSV templates into a new set for your country (e.g. `DE_*`, `HU_*`, `BG_*`).
   - Adjust:
     - `archetype_id` naming to include country code (e.g. `DE_RES_1960_1980`).
     - Element types to match UMS constants in [`app/utils/estimation_constants.py`](../app/utils/estimation_constants.py:1) where possible (e.g. `"Ground floor"`, `"External walls"`).

3. **Populate reference metrics and compositions**:
   - Replace Austrian numeric values with your **own** study or dataset values:
     - `ref_bgf`, `ref_volume`.
     - `ref_area` per element type in `archetype_elements`.
     - Component compositions (layer thicknesses and percentage shares) in `component_products`.
   - Ensure all product IDs used are defined in your `products` CSV and compatible with UMS (density, category, etc.).

4. **Define country-specific archetypes**:
   - For each archetype, set:
     - `country` = your country’s ISO code (e.g. `DE`, `HU`, `BG`).
     - Consistent naming for `archetype_id`, such as `<COUNTRY>_<USE>_<PERIOD>`:
       - Example: `DE_RES_1945_1970`, `HU_NONRES_1980_2000`.
   - This naming scheme:
     - Helps filtering by country and typology.
     - Simplifies country-based selection in archetype compute routes (see [`app/routes/archetype_compute.py`](../app/routes/archetype_compute.py:1)).

5. **Import via CSV upload**:
   - Use the CSV upload API in [`app/routes/csv_upload.py`](../app/routes/csv_upload.py:1) to ingest the new archetypes.
   - Verify:
     - No missing product IDs.
     - All essential reference metrics (`ref_bgf`, `ref_volume`) are set.
     - Element type names match the constants used in UMS where needed (for correct factor and area calculations).

6. **Test the new archetypes**:
   - Use the building estimation endpoint [`app/routes/building_estimation.py:estimate_building_values_endpoint()`](../app/routes/building_estimation.py:139) to obtain geometry for addresses in your country.
   - Run material estimation via [`app/routes/estimation.py:estimate_building_materials()`](../app/routes/estimation.py:211) and confirm:
     - Results are numerically plausible.
     - Element and product breakdowns match expectations from your reference studies.

### 5.2 Naming conventions and filtering

To keep archetypes manageable and filterable across regions:

- Use ISO country codes as a prefix in `archetype_id`.
- Include key attributes in the ID:
  - `<COUNTRY>_<SEGMENT>_<PERIOD>[_<VARIANT>]`
  - Example: `AT_RES_1945_1970`, `AT_RES_1945_1970_HIGHINS`, `HU_NONRES_1980_2000`.

- Store classification attributes like building type, period, and main material in dedicated columns where supported by the schema, as described in [`docs/data-model.md`](data-model.md).


### 5.3 Partner responsibilities

Each partner is responsible for:

- Ensuring that the source study or dataset for archetypes:
  - Allows use within the project.
  - Allows or restricts redistribution; this influences whether CSVs can be committed here.
- Providing documentation for:
  - Study name, year, geographic scope.
  - Methodology assumptions (e.g. typical ratios, sample size).
  - Coverage and limitations.

UMS does not enforce licensing rules at runtime. Project owners must review and manage data licensing at deployment and publication time.


## 6. Versioning and Provenance

Archetype definitions should be treated as versioned datasets, not as immutable constants. For each country or partner dataset, we recommend tracking:

- **Source study and year**:
  - e.g. “Study XYZ on residential building stock in HU, 2022”.

- **Archetype CSV version**:
  - e.g. `HU_archetypes_v1.0.csv`.
  - Keep a changelog when values are updated.

- **Contact institution and maintainer**:
  - Name of institution providing the archetype definitions.
  - Contact person or email for technical questions.

## 7. Licensing and Data-Sharing Considerations

Archetype data may inherit licenses and restrictions from external sources. UMS also relies on geospatial data such as OSM under ODbL, which further constrains downstream data products.

Relevant docs:

- Data sources and licensing overview: [`docs/sources.md`](sources.md)
- OSM/ODbL compliance: [`docs/osm-odbl-compliance.md`](osm-odbl-compliance.md)
- Software license and bundled data terms: [`../LICENSE`](../LICENSE)


### 7.1 Pulse data licensing

Pulse-derived archetypes bundled with this repository are governed by the **Urban Mining Screener Software License Agreement**:

- The Austria Pulse CSV export under `data/pulse/` is bundled as part of the Software.
- Public access to these CSVs is provided to enable research, testing, and evaluation of UMS.
- Commercial exploitation or redistribution of these CSVs, in whole or in part, is not permitted without prior and explicit consent from Graz University of Technology and revitalyze FlexCo.
- The CSVs are not open data; they are subject to the same restrictions as the rest of the Software.

When creating additional Pulse-based or other archetype datasets, treat licensing explicitly:

- Only commit CSVs whose licenses allow redistribution and that are compatible with the Urban Mining Screener Software License Agreement.
- Keep non-redistributable datasets in separate, non-public data repositories or deployment-specific storage.
- Document the source study, year, and license for each dataset in project-level documentation (e.g. in [`docs/sources.md`](sources.md) or per-directory READMEs).


### 7.2 OSM and other geospatial sources

UMS uses OpenStreetMap (OSM) via Overpass to derive building footprints and, where possible, heights. OSM data is licensed under ODbL 1.0 and requires:

- Attribution (“© OpenStreetMap contributors”).
- Notice and share-alike for derived databases.

See:

- [`docs/osm-odbl-compliance.md`](osm-odbl-compliance.md)
- [`docs/sources.md`](sources.md)

Although archetype tables themselves may not be OSM-derived, **outputs that combine archetypes with OSM-based geometry** (e.g. building-level material stock estimates) can fall under ODbL obligations, especially if exported as object-level databases.
