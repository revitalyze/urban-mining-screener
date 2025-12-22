"""
Area Estimator Utility

Provides functions to estimate target areas for area-based and volume-based building components.
Ensures modular, maintainable, and well-documented code for use in material estimation workflows.
"""

import logging
from typing import Any, Dict, List, Tuple

from app.models.models import ComponentProduct, ArchetypeElement
from app.models.schemas import MaterialEstimationRequest, TargetAreaData
from app.utils.area_calculations import (
    calculate_component_proportion,
    calculate_horizontal_area,
    calculate_retaining_wall_area,
    calculate_roof_area,
    calculate_external_wall_area,
    calculate_window_area,
    calculate_default_area,
)
from app.utils.area_aggregator import calculate_all_as_built_areas
from app.utils.estimation_constants import (
    EL_TYPE_RETAINING_WALLS,
    EL_TYPE_ROOF,
    EL_TYPE_EXTERNAL_WALLS,
    EL_TYPE_WINDOWS,
    AREA_BASED_ELEMENTS,
    HORIZONTAL_ELEMENTS,
)
from app.utils.refurbishment_rules import get_refurbishment_action

logger = logging.getLogger(__name__)


def estimate_target_areas(
    request: MaterialEstimationRequest,
    final_component_products: List[Tuple[ComponentProduct, ArchetypeElement]],
    archetype_elements: List,
    element_type_map: Dict[int, str],
    factors: Dict[str, float],
) -> List[TargetAreaData]:
    """
    Estimates target areas for area-based components with proper handling of refurbishment actions.
    For volume-based components (internal walls), it passes necessary info.
    Returns a list of Pydantic models containing data by (element_type_id, element_type_name, component_id).
    """
    target_grundflaeche = request.target_grundflaeche
    target_gebaeudeumrisse = request.target_gebaeudeumrisse
    target_gebaeudehoehe = request.target_gebaeudehoehe

    ref_grundflaeche = factors["ref_grundflaeche"]
    faktor_sm = factors["faktor_sm"]
    faktor_dach = factors["faktor_dach"]
    faktor_w = factors["faktor_w"]

    # Calculate all as-built areas from archetype data first
    all_as_built_areas_by_type = calculate_all_as_built_areas(
        archetype_elements, element_type_map, request, factors
    )

    # Separate as-built and refurbishment components for proportion calculation
    as_built_components: List[Tuple[ComponentProduct, ArchetypeElement]] = []
    refurbishment_components: List[
        Tuple[ComponentProduct, ArchetypeElement, str | None]
    ] = []

    for cp, ae in final_component_products:
        component_id = getattr(cp, "component_id", None)
        element_type_name = element_type_map.get(
            getattr(ae, "element_type_id", None), "Unknown"
        )
        action: str | None = get_refurbishment_action(element_type_name, component_id)

        if action is None:
            as_built_components.append((cp, ae))
        else:
            refurbishment_components.append((cp, ae, action))

    # Pre-calculate total reference areas per element type using ONLY as-built components
    total_ref_areas_per_type: Dict[int, float] = {}
    for cp, ae in as_built_components:
        element_type_id = getattr(ae, "element_type_id", None)
        ref_area = getattr(ae, "ref_area", 0.0)
        if element_type_id is not None:
            total_ref_areas_per_type[element_type_id] = total_ref_areas_per_type.get(
                element_type_id, 0.0
            ) + (ref_area or 0.0)

    logger.debug(
        f"Total reference areas per type (as-built only): {total_ref_areas_per_type}"
    )

    # Dictionary to aggregate results by (element_type_id, element_type_name, component_id)
    aggregated_data: Dict[Tuple[int, str, str], Dict[str, Any]] = {}

    # First pass: calculate as-built areas per element_type_id
    as_built_areas_by_type = {}

    # Process as-built components first
    for cp, ae in as_built_components:
        element_type_id = getattr(ae, "element_type_id", None)
        element_type_name = element_type_map.get(element_type_id, "Unknown")
        ref_area = getattr(ae, "ref_area", 0.0)
        component_id = getattr(cp, "component_id", None)
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

        # Aggregation key
        key = (element_type_id, element_type_name, component_id)

        # Initialize aggregated entry for as-built component
        if key not in aggregated_data:
            aggregated_data[key] = {
                "element_type_id": element_type_id,
                "element_type_name": element_type_name,
                "component": (cp, ae),
                "target_area": round(target_area, 4),
                "ref_area": ref_area,
                "is_refurbishment": False,
                "action": None,
            }
        else:
            # For multiple as-built components with same key, add target_area
            aggregated_data[key]["target_area"] += round(target_area, 4)

        # Track as-built areas by element_type
        rounded_target_area = round(target_area, 4)
        if element_type_id is not None:
            as_built_areas_by_type[element_type_id] = (
                as_built_areas_by_type.get(element_type_id, 0.0) + rounded_target_area
            )

        logger.debug(
            f"Processed as-built component {component_id} ({element_type_name}): ref_area={ref_area}, calculated target_area={target_area:.4f}"
        )

    # Process refurbishment components
    for cp, ae, action in refurbishment_components:
        element_type_id = getattr(ae, "element_type_id", None)
        element_type_name = element_type_map.get(element_type_id, "Unknown")
        ref_area = getattr(ae, "ref_area", 0.0)
        component_id = getattr(cp, "component_id", None)

        # Aggregation key
        key = (element_type_id, element_type_name, component_id)

        # Initialize aggregated entry for refurbishment component
        if key not in aggregated_data:
            aggregated_data[key] = {
                "element_type_id": element_type_id,
                "element_type_name": element_type_name,
                "component": (cp, ae),
                "target_area": 0.0,  # Will be set in second pass
                "ref_area": ref_area,
                "is_refurbishment": True,
                "action": action,
            }

        logger.debug(
            f"Processed refurbishment component {component_id} ({element_type_name}): action={action}, ref_area={ref_area}"
        )

    # Second pass: assign correct area to refurbishment components based on action
    for key, entry in aggregated_data.items():
        if entry["is_refurbishment"]:
            element_type_id = entry["element_type_id"]
            # Use the complete as-built areas calculated from archetype data
            as_built_area = all_as_built_areas_by_type.get(element_type_id, 0.0)
            entry["target_area"] = as_built_area

    # Convert aggregated data to TargetAreaData objects
    target_areas_data_list = [
        TargetAreaData(
            element_type_id=entry["element_type_id"],
            element_type_name=entry["element_type_name"],
            component=entry["component"],
            target_area=round(entry["target_area"], 4),
            ref_area=entry["ref_area"],
        )
        for entry in aggregated_data.values()
    ]
    replacement_element_types = {
        item.element_type_name
        for item in target_areas_data_list
        if item.component[0].component_id in {"REN_07_a", "REN_07_b"}
    }

    if replacement_element_types:
        target_areas_data_list = [
            item
            for item in target_areas_data_list
            if item.element_type_name not in replacement_element_types
               or item.component[0].component_id in {"REN_07_a", "REN_07_b"}
        ]

    logger.info(
        f"Prepared {len(target_areas_data_list)} component data entries for volume calculation."
    )
    return target_areas_data_list
