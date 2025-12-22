"""
Area Calculations Utility

Provides functions to calculate target areas for area-based building components.
"""

import logging

logger = logging.getLogger(__name__)


def calculate_component_proportion(
    ref_area: float, total_ref_area_for_type: float
) -> float:
    """
    Calculate the proportion of a component's reference area to the total reference area for its type.
    """
    if total_ref_area_for_type > 0:
        return ref_area / total_ref_area_for_type
    return 0.0


def calculate_horizontal_area(
    target_grundflaeche: float, component_proportion: float
) -> float:
    """
    Calculate area for horizontal elements (e.g., ground floor).
    """
    return target_grundflaeche * component_proportion


def calculate_retaining_wall_area(
    faktor_sm: float, target_grundflaeche: float, component_proportion: float
) -> float:
    """
    Calculate area for retaining walls.
    """
    return faktor_sm * target_grundflaeche * component_proportion


def calculate_roof_area(
    faktor_dach: float, target_grundflaeche: float, component_proportion: float
) -> float:
    """
    Calculate area for roof elements.
    """
    return faktor_dach * target_grundflaeche * component_proportion


def calculate_external_wall_area(
    target_gebaeudeumrisse: float,
    target_gebaeudehoehe: float,
    faktor_w: float,
    component_proportion: float,
) -> float:
    """
    Calculate area for external walls.
    """
    total_envelope_area = target_gebaeudeumrisse * target_gebaeudehoehe
    denominator = 1.0 + faktor_w
    proportion_external = 1.0 / denominator if denominator != 0 else 1.0
    base_target_area = total_envelope_area * proportion_external
    return base_target_area * component_proportion


def calculate_window_area(
    target_gebaeudeumrisse: float,
    target_gebaeudehoehe: float,
    faktor_w: float,
    component_proportion: float,
) -> float:
    """
    Calculate area for windows.
    """
    total_envelope_area = target_gebaeudeumrisse * target_gebaeudehoehe
    denominator = 1.0 + faktor_w
    proportion_window = faktor_w / denominator if denominator != 0 else 0.0
    base_target_area = total_envelope_area * proportion_window
    return base_target_area * component_proportion


def calculate_default_area(
    ref_area: float,
    target_grundflaeche: float,
    ref_grundflaeche: float,
    element_type_name: str,
) -> float:
    """
    Fallback calculation for unhandled area-based element types.
    """
    logger.warning(
        f"Unhandled area-based element type: {element_type_name}. Using ground floor scaling."
    )
    scale_factor = (
        (target_grundflaeche / ref_grundflaeche) if ref_grundflaeche > 0 else 0
    )
    return ref_area * scale_factor
