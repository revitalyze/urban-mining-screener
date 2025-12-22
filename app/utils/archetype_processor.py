# app/utils/archetype_processor.py
import logging
from typing import Dict, List, Set, Tuple

import pandas as pd

from app.models.models import (
    Archetype,
    ArchetypeElement,
    ElementComponent,
    ElementType,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_element_types(
    building_df: pd.DataFrame,
) -> Tuple[List[ElementType], Dict[str, int]]:
    """Extracts unique element types from the building list DataFrame."""
    element_types = []
    element_type_map = {}
    building_df["ID"] = building_df["ID"].ffill()
    unique_element_type_names = (
        building_df["Element type"].dropna().astype(str).str.strip().unique()
    )

    for i, name in enumerate(unique_element_type_names, start=1):
        if name:
            element_type = ElementType(name=name)
            element_types.append(element_type)


    logger.info(f"Identified {len(element_types)} unique element types.")
    if not element_types:
        logger.warning("No element types found in building_list.csv.")
    return element_types, {}


def process_archetypes_elements_and_components(
    building_df: pd.DataFrame,
    element_type_map: Dict[str, int],
    valid_component_ids: Set[str],
) -> Tuple[List[Archetype], List[ArchetypeElement], List[ElementComponent]]:
    """Processes archetypes, their elements, and component links."""
    archetypes: List[Archetype] = []
    archetype_elements: List[ArchetypeElement] = []
    element_components: List[ElementComponent] = []

    processed_archetypes = 0
    processed_elements = 0
    processed_elem_comps = 0
    skipped_rows = 0

    # Ensure ID is forward filled for grouping
    building_df["ID"] = building_df["ID"].ffill()
    building_df.dropna(
        subset=["ID"], inplace=True
    )  # Remove rows where ID could not be filled

    # Convert numeric columns, coercing errors
    building_df["Gross floor area (m2)"] = pd.to_numeric(
        building_df["Gross floor area (m2)"], errors="coerce"
    )
    building_df["Volume (m3)"] = pd.to_numeric(
        building_df["Volume (m3)"], errors="coerce"
    )
    building_df["From (year)"] = pd.to_numeric(
        building_df["From (year)"], errors="coerce"
    )
    building_df["To (year)"] = pd.to_numeric(building_df["To (year)"], errors="coerce")
    building_df["Area (m2)"] = pd.to_numeric(building_df["Area (m2)"], errors="coerce")

    archetype_groups = building_df.groupby("ID")

    for archetype_id_str, group in archetype_groups:
        archetype_id = str(archetype_id_str).strip()
        if not archetype_id:
            logger.warning("Skipping group with empty Archetype ID.")
            continue

        # Get archetype details from the first row of the group
        # Use .first_valid_index() in case the first row has NaNs in metadata columns
        first_valid_idx = group["Country"].first_valid_index()  # Use a common column
        if first_valid_idx is None:
            logger.warning(
                f"Skipping Archetype '{archetype_id}': No valid rows found for metadata."
            )
            continue
        first_row = group.loc[first_valid_idx]

        # Basic validation for essential archetype data
        ref_bgf_val = first_row["Gross floor area (m2)"]
        ref_volume_val = first_row["Volume (m3)"]

        if pd.isna(ref_bgf_val) or pd.isna(ref_volume_val):
            logger.warning(
                f"Skipping Archetype '{archetype_id}': Missing critical numeric data (Gross floor area: '{first_row['Gross floor area (m2)']}', Volume: '{first_row['Volume (m3)']}')"
            )
            continue

        archetype = Archetype(
            archetype_id=archetype_id,
            country=(
                str(first_row["Country"]).strip()
                if pd.notna(first_row["Country"])
                else None
            ),
            building_type=(
                str(first_row["Typology"]).strip()
                if pd.notna(first_row["Typology"])
                else None
            ),
            construction_period_start=(
                int(first_row["From (year)"])
                if pd.notna(first_row["From (year)"])
                else None
            ),
            construction_period_end=(
                int(first_row["To (year)"])
                if pd.notna(first_row["To (year)"])
                else None
            ),
            main_material=(
                str(first_row["Construction type"]).strip()
                if pd.notna(first_row["Construction type"])
                else None
            ),
            ref_bgf=float(ref_bgf_val),
            ref_volume=float(ref_volume_val),
        )
        archetypes.append(archetype)
        processed_archetypes += 1

        # Process elements and their components for this archetype
        for index, row in group.iterrows():
            element_type_name = (
                str(row["Element type"]).strip()
                if pd.notna(row["Element type"])
                else None
            )
            ref_area_val = row["Area (m2)"]

            # A row must have an element type and an area to be processed.
            if not element_type_name or pd.isna(ref_area_val):
                if element_type_name or pd.notna(ref_area_val):
                    logger.debug(
                        f"Skipping row {index + 2} for archetype '{archetype_id}': Missing Element Type ('{element_type_name}') or Area ('{ref_area_val}')."
                    )
                skipped_rows += 1
                continue

            element_type_id = element_type_map.get(element_type_name)
            if not element_type_id:
                logger.warning(
                    f"Skipping element row {index + 2}: Element Type '{element_type_name}' not found in the database map."
                )
                skipped_rows += 1
                continue

            # Create one ArchetypeElement per valid row
            archetype_element = ArchetypeElement(
                archetype_id=archetype_id,
                element_type_id=element_type_id,
                ref_area=float(ref_area_val),
            )
            archetype_elements.append(archetype_element)
            processed_elements += 1

            # Define the mapping of CSV columns to refurbishment levels
            refurbishment_map = {
                "ID component (as-built)": "as-built",
                "ID component (light refurbishment)": "light",
                "ID component (medium refurbishment)": "medium",
                "ID component (deep refurbishment)": "deep",
            }

            # Create ElementComponents for the various refurbishment levels
            for column, level in refurbishment_map.items():
                if column in row and pd.notna(row[column]):
                    component_id = str(row[column]).strip()
                    if component_id in valid_component_ids:
                        element_component = ElementComponent(
                            element=archetype_element,  # Link to the parent element
                            component_id=component_id,
                            refurbishment_level=level,
                        )
                        element_components.append(element_component)
                        processed_elem_comps += 1
                    else:
                        logger.warning(
                            f"Skipping component link in row {index + 2}: Component ID '{component_id}' for level '{level}' is not a valid component."
                        )

    logger.info(f"Processed {processed_archetypes} archetypes.")
    logger.info(f"Processed {processed_elements} archetype elements.")
    logger.info(f"Processed {processed_elem_comps} element-component links.")
    logger.info(f"Skipped {skipped_rows} rows due to missing data.")

    if not archetypes:
        logger.warning("No valid archetypes were processed.")
    if not archetype_elements:
        logger.warning("No valid archetype elements were processed.")
    if not element_components:
        logger.warning("No valid element-component links were processed.")

    return archetypes, archetype_elements, element_components
