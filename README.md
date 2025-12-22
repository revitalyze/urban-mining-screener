# Urban Mining Screener (UMS)

The Urban Mining Screener (UMS) estimates material quantities in existing buildings based on archetypes and reference data. The system consists of a FastAPI backend, a React/Vite single-page application, and a PostgreSQL database, and can be run either via Docker or in a local development setup.

UMS is made publicly available as source code and archetype CSV data under a dedicated Software License Agreement held by Graz University of Technology and revitalyze FlexCo. The Software is intended for research, testing and evaluation by the scientific community and project partners, and is **not** licensed for commercial exploitation or redistribution without prior and explicit consent from the rights holders.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Quickstart](#quickstart)
   - [Docker (recommended)](#docker-recommended)
   - [Local Development](#local-development)
4. [API Overview](#api-overview)
5. [Usage](#usage)
6. [CSV Inputs](#csv-inputs)
7. [Documentation](#documentation)
8. [Attribution and Licensing](#attribution-and-licensing)
9. [Funding / Acknowledgements](#funding--acknowledgements)

---

## Project Overview

The Urban Mining Screener (UMS) estimates the materials used in existing buildings by combining user inputs with archetype-based reference data:

- Users provide a building address.
- The system derives basic building metrics (e.g. ground area, perimeter, height) from OSM-derived data.
- Users refine the estimation by selecting archetype parameters (typology, construction year, construction type, energy class).
- Optionally, users choose a refurbishment level that affects material quantities.
- The system computes estimated material quantities by element and product category and allows CSV export.

The project has been developed in the context of the Circular DigiBuild initiative for the Danube Region (final wording to be confirmed).

For detailed technical documentation, see:

- Architecture: [`docs/architecture.md`](docs/architecture.md)
- Algorithms and estimation logic: [`docs/algorithms.md`](docs/algorithms.md)
- Data model: [`docs/data-model.md`](docs/data-model.md)

---

## Features

1. **CSV Upload and Database Management**
   - Upload three CSV files: `product_list.csv`, `components_list.csv`, and `building_list.csv`.
   - Parse the CSVs and extract necessary columns.
   - Ingest the parsed data into the PostgreSQL database.

2. **Building and Material Estimation UI**
   - Step 1: Enter a building address to estimate ground area, perimeter, and height from OSM-derived data.
   - Step 2: Provide archetype parameters (typology, construction year, construction type, energy class) to compute an archetype.
   - Step 3 (if applicable): Select a refurbishment level (including **“As-built (no refurbishment)”** as the baseline) when refurbishment options exist for the archetype.
   - Step 4: View estimated materials grouped by element type and product category, and export results as CSV.

3. **Calculation Logic**
   - Estimate materials for a target building by scaling reference data from the selected archetype.
   - Calculate factors for retaining walls, roof, and windows.
   - Estimate target areas for different element types.
   - Calculate product volumes and weights.

For in-depth behavior, see:

- User-facing workflow: [`docs/user-guide.md`](docs/user-guide.md)
- Data structures and relationships: [`docs/data-model.md`](docs/data-model.md)
- Estimation pipeline and formulas: [`docs/algorithms.md`](docs/algorithms.md)

---

## Quickstart

### Docker (recommended)

Run the full stack (backend, frontend, and database) via Docker:

```bash
git clone <repository_url>
cd <repository_directory>
docker build -t ums:local .
docker compose up -d
```

- Backend and SPA are served at: http://localhost:8000 by default.
- PostgreSQL is started and managed via `docker-compose`.
- Alembic migrations are executed automatically on container start (see [`entrypoint.sh`](entrypoint.sh:1)).

See [`docs/installation.md`](docs/installation.md) for full details, environment variables, and troubleshooting.

### Local Development

You can also run backend and frontend separately for development.

#### Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --port 8000
```

Notes:

- Ensure a PostgreSQL instance is available and configured via environment variables or [`app/config.py`](app/config.py:1). Local DB name and connection details are documented in [`docs/installation.md`](docs/installation.md).
- When using the Docker-based workflow, migrations are handled automatically on startup via [`entrypoint.sh`](entrypoint.sh:1).

#### Frontend

From the `frontend/` directory:

```bash
cd frontend
npm install
npm run dev
```

- The Vite dev server runs at: http://localhost:5173.
- Configure CORS and authentication domains as described in:
  - Installation: [`docs/installation.md`](docs/installation.md)
  - Configuration: [`docs/configuration.md`](docs/configuration.md)

---

## Usage

1. Open the application in your web browser:
   - Docker / production: http://localhost:8000
   - Local dev (separate frontend): http://localhost:5173
2. Log in using the configured `APP_PASSWORD` (via the login view).
3. Navigate to the “Building Estimation” page.
4. Enter a building address to estimate ground area, perimeter, and height.
5. Provide archetype parameters (typology, construction year, construction type, energy class) and compute the archetype.
6. If prompted, select a refurbishment level (e.g. **“As-built (no refurbishment)”**, “light”, “medium”, “deep”).
7. Click “Estimate Materials” to view estimated materials and use the CSV export functionality if needed.

Screenshots and a more detailed walkthrough are available in [`docs/user-guide.md`](docs/user-guide.md).

---

## CSV Inputs

The application relies on three main CSV inputs:

- `product_list.csv`
  Contains product details (ID, category, raw density, and related attributes).

- `components_list.csv`
  Lists components with associated products, layer thickness, and percentage contributions.

- `building_list.csv`
  Contains archetype data (archetype ID, reference areas, component IDs, and related metadata).

The exact schema and constraints for these files are described in:

- Data Model: [`docs/data-model.md`](docs/data-model.md)
- Archetypes and Pulse relationship: [`docs/archetypes-pulse.md`](docs/archetypes-pulse.md)

---

## Documentation

For full documentation, see:

- Documentation index: [`docs/README.md`](docs/README.md)
- Installation: [`docs/installation.md`](docs/installation.md)
- Configuration: [`docs/configuration.md`](docs/configuration.md)
- User Guide: [`docs/user-guide.md`](docs/user-guide.md)
- Architecture: [`docs/architecture.md`](docs/architecture.md)
- Data Model: [`docs/data-model.md`](docs/data-model.md)
- Sources and data provenance: [`docs/sources.md`](docs/sources.md)
- OSM ODbL compliance details: [`docs/osm-odbl-compliance.md`](docs/osm-odbl-compliance.md)
- Archetypes and Pulse integration: [`docs/archetypes-pulse.md`](docs/archetypes-pulse.md)

---

## Attribution and Licensing

### OpenStreetMap (OSM)

Data © OpenStreetMap contributors — ODbL 1.0.
Usage of OSM-derived building metrics follows ODbL obligations described in:

- [`docs/osm-odbl-compliance.md`](docs/osm-odbl-compliance.md)
- [`docs/sources.md`](docs/sources.md)

### Urban Mining Screener Software License

The UMS source code and bundled archetype CSVs (including Pulse-based archetypes) are licensed under the **Urban Mining Screener Software License Agreement**:

- See [`LICENSE`](LICENSE) for the full license text.

Key points (informal summary — the full license prevails):

- Graz University of Technology and revitalyze FlexCo hold all ownership rights on the Software.
- The Software is made public as part of the Circular DigiBuild project to be used by the scientific community and project partners for testing and evaluation.
- Further developments of the Software must be made accessible under the same license.
- The user **cannot commercially exploit or distribute the Software** without prior and explicit consent of Graz University of Technology and revitalyze FlexCo (see contact addresses in [`LICENSE`](LICENSE)).
- The Software is provided “as is” without any warranties of any nature.

If you use UMS for a publication or publish results obtained through the use of the Software, please cite it as:

```bibtex
@software
  title={Urban Mining Screener},
  author={Ritonja Schauer, Sasa and Lang-Raudaschl, Matthias and Hiemesch, Rebekka and Streif, Michael and Plaseller, David and Alaux, Nicolas and Schwark, Benedict and Hörmann, Marius and Ruschi Mendes Saade, Marcella and Passer, Alexander},
  year={2025},
  organization={Institute of Architecture Technology (IAT) and Working Group Sustainable Construction, Institute of Structural Design (ITE-NHB) and revitalyze FlexCo}
```

---

## Funding / Acknowledgements

Developed in the context of the Circular DigiBuild project for the Danube Region.
