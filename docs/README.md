# Urban Mining Screener (UMS) — Documentation Index

This directory contains the technical documentation for the Urban Mining Screener (UMS) prepared within the Circular DigiBuild context.

_Back to project overview: [`README.md`](../README.md)_

## Overview

These documents assume you are already familiar with the high-level goals and user workflow described in the project [`README.md`](../README.md). The docs here focus on:

- Installation and runtime environments (local, Docker, deployment).
- Configuration and environment variables.
- User-facing workflows in more depth (with screenshots).
- System architecture and request lifecycle.
- Data model and data sources.
- Licensing and ODbL/OSM compliance.
- Extending archetypes, including integration with Pulse data.

## Getting Started

For local and Docker workflows, see the installation guide:

- Installation: [`installation.md`](installation.md)

## Configuration

Environment variables and configuration details:

- Configuration: [`configuration.md`](configuration.md)

## User Guide

Step-by-step usage, including screenshots of the UI and expected outputs:

- User Guide: [`user-guide.md`](user-guide.md)

## Architecture

End-to-end system overview and request lifecycle:

- Architecture: [`architecture.md`](architecture.md)

## Data Model

Entities, relationships, and conversion factors used in estimations:

- Data Model: [`data-model.md`](data-model.md)

## Sources & Licensing

Data sources and attribution requirements:

- Sources: [`sources.md`](sources.md)

## OSM ODbL Compliance

Obligations and example attribution text for OSM-derived data:

- OSM ODbL Compliance: [`osm-odbl-compliance.md`](osm-odbl-compliance.md)

## Extending Archetypes (Pulse)

Relationship to Pulse archetypes and regional extensions:

- Archetypes & Pulse: [`archetypes-pulse.md`](archetypes-pulse.md)

## Quick Links

- Installation: [`installation.md`](installation.md)
- Configuration: [`configuration.md`](configuration.md)
- User Guide: [`user-guide.md`](user-guide.md)
- Architecture: [`architecture.md`](architecture.md)
- Data Model: [`data-model.md`](data-model.md)
- Sources & Licensing: [`sources.md`](sources.md)
- OSM Compliance: [`osm-odbl-compliance.md`](osm-odbl-compliance.md)
- Archetypes (Pulse): [`archetypes-pulse.md`](archetypes-pulse.md)

## Compatibility

- Python 3.11, Node 18+ (recommended 20), Docker 24+, Compose v2.

## Licensing

The Urban Mining Screener source code and bundled archetype CSVs (including Pulse-based archetypes) are licensed under the **Urban Mining Screener Software License Agreement** held by Graz University of Technology and revitalyze FlexCo.

- See [`LICENSE`](../LICENSE) for the full license text.
- Informal summary (the full license prevails):
  - The Software is made public for research, testing, and evaluation by the scientific community and project partners.
  - The Software, including bundled archetype CSVs, is **not licensed for commercial exploitation or redistribution** without prior and explicit consent from the rights holders.
  - Further developments of the Software must be made accessible under the same license where they are derived works.

Attribution requirements and obligations for OSM-derived data are documented in [`osm-odbl-compliance.md`](osm-odbl-compliance.md).