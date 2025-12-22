"""
Area Aggregator Utility

Provides functions to aggregate and calculate as-built areas for all element types.
Ensures modular, maintainable, and well-documented code for use in material estimation workflows.
"""

import logging
from typing import Dict, List

from app.models.schemas import MaterialEstimationRequest
from app.utils.area_calculations import (
    calculate_component_proportion,
    calculate_horizontal_area,
    calculate_retaining_wall_area,
    calculate_roof_area,
    calculate_external_wall_area,
    calculate_window_area,
    calculate_default_area,
)
from app.utils.estimation_constants import (
    EL_TYPE_RETAINING_WALLS,
    EL_TYPE_ROOF,
    EL_TYPE_EXTERNAL_WALLS,
    EL_TYPE_WINDOWS,
    AREA_BASED_ELEMENTS,
    HORIZONTAL_ELEMENTS,
)

logger = logging.getLogger(__name__)


def calculate_all_as_built_areas(
    archetype_elements: List,
    element_type_map: Dict[int, str],
    request: MaterialEstimationRequest,
    factors: Dict[str, float],
) -> Dict[int, float]:
    """
    Calculate the original as-built areas for all element types from archetype data.
    This ensures that even when components are exchanged, we know the original area.
    """
    target_grundflaeche = request.target_grundflaeche
    target_gebaeudeumrisse = request.target_gebaeudeumrisse
    target_gebaeudehoehe = request.target_gebaeudehoehe

    ref_grundflaeche = factors["ref_grundflaeche"]
    faktor_sm = factors["faktor_sm"]
    faktor_dach = factors["faktor_dach"]
    faktor_w = factors["faktor_w"]

    all_as_built_areas_by_type: Dict[int, float] = {}

    # Calculate total reference areas per element type from all archetype elements
    total_ref_areas_per_type: Dict[int, float] = {}
    for ae in archetype_elements:
        element_type_id = getattr(ae, "element_type_id", None)
        ref_area = getattr(ae, "ref_area", 0.0)
        if element_type_id is not None:
            total_ref_areas_per_type[element_type_id] = total_ref_areas_per_type.get(
                element_type_id, 0.0
            ) + (ref_area or 0.0)

    # Calculate as-built area for each archetype element
    for ae in archetype_elements:
        element_type_id = getattr(ae, "element_type_id", None)
        element_type_name = element_type_map.get(element_type_id, "Unknown")
        ref_area = getattr(ae, "ref_area", 0.0)
        target_area = 0.0

        # Calculate target area ONLY for area-based elements
        if element_type_name in AREA_BASED_ELEMENTS:
            total_ref_area_for_type = total_ref_areas_per_type.get(element_type_id, 0.0)
            component_proportion = calculate_component_proportion(
                ref_area, total_ref_area_for_type
            )

            if element_type_name in HORIZONTAL_ELEMENTS:
                target_area = calculate_horizontal_area(
                    target_grundflaeche, component_proportion
                )
            elif element_type_name == EL_TYPE_RETAINING_WALLS:
                target_area = calculate_retaining_wall_area(
                    faktor_sm, target_grundflaeche, component_proportion
                )
            elif element_type_name == EL_TYPE_ROOF:
                target_area = calculate_roof_area(
                    faktor_dach, target_grundflaeche, component_proportion
                )
            elif element_type_name == EL_TYPE_EXTERNAL_WALLS:
                target_area = calculate_external_wall_area(
                    target_gebaeudeumrisse,
                    target_gebaeudehoehe,
                    faktor_w,
                    component_proportion,
                )
            elif element_type_name == EL_TYPE_WINDOWS:
                target_area = calculate_window_area(
                    target_gebaeudeumrisse,
                    target_gebaeudehoehe,
                    faktor_w,
                    component_proportion,
                )
            else:
                target_area = calculate_default_area(
                    ref_area, target_grundflaeche, ref_grundflaeche, element_type_name
                )

        # Accumulate as-built area by element type
        if element_type_id is not None:
            all_as_built_areas_by_type[element_type_id] = (
                all_as_built_areas_by_type.get(element_type_id, 0.0)
                + round(target_area, 4)
            )

    logger.debug(f"All as-built areas by type: {all_as_built_areas_by_type}")
    return all_as_built_areas_by_type
