import logging
from typing import List, Tuple

from sqlalchemy.orm import Session

from app.models.models import ArchetypeElement, ComponentProduct
from app.models.schemas import MaterialEstimationRequest, MaterialEstimationResponse
from app.utils.factor_calculator import calculate_reference_factors
from app.utils.area_estimator import estimate_target_areas, TargetAreaData
from app.utils.volume_calculator import calculate_material_volumes_weights
from app.utils.refurbishment_service import apply_refurbishment_logic
from app.utils.window_calculator import calculate_window_data
from app.utils.estimation_helpers import (
    get_reference_data,
    _validate_request_dimensions,
    _validate_internal_walls_requirements,
    _format_category_results,
)

logger = logging.getLogger(__name__)


def estimate_materials(
    db: Session, request: MaterialEstimationRequest
) -> MaterialEstimationResponse:
    """
    Orchestrates the material estimation process using separated logic functions.

    The refurbishment logic now returns a list of (ComponentProduct, ArchetypeElement) tuples,
    which is passed through the estimation pipeline.
    """
    logger.info(
        f"Starting material estimation for Archetype: {request.archetype_id} and "
        f"refurbishment level: {request.refurbishment_level}"
    )

    # Validate input parameters
    _validate_request_dimensions(request)

    # Retrieve reference data
    archetype, archetype_elements, archetype_components, element_type_map = (
        get_reference_data(db, request.archetype_id)
    )

    # Handle case where archetype exists but has no valid components/element types
    if not archetype_components or not element_type_map:
        logger.warning(
            f"No valid component or element type data for Archetype {request.archetype_id}. "
            "Returning empty estimation."
        )
        return MaterialEstimationResponse(
            by_element_type=[],
            by_product_category=[],
            calculation_factors={},
            window_data=[],
        )

    # Apply refurbishment logic to get the final list of component products
    final_component_products: List[Tuple[ComponentProduct, ArchetypeElement]] = (
        apply_refurbishment_logic(
            archetype_components, archetype_elements, request.refurbishment_level
        )
    )

    # Calculate reference factors
    factors = calculate_reference_factors(
        archetype, archetype_elements, element_type_map
    )

    # Estimate target areas for area-based components
    target_areas_data: List[TargetAreaData] = estimate_target_areas(
        request, final_component_products, archetype_elements, element_type_map, factors
    )

    if not target_areas_data:
        logger.warning(
            f"No target areas or component data could be prepared for Archetype {request.archetype_id}."
        )
        return MaterialEstimationResponse(
            by_element_type=[], by_product_category=[], calculation_factors=factors
        )

    # Calculate volumes and validate requirements
    target_volume = request.target_grundflaeche * request.target_gebaeudehoehe
    ref_volume = factors.get("ref_volume", 0)
    _validate_internal_walls_requirements(
        target_areas_data, ref_volume, request.archetype_id
    )

    # Calculate final material volumes and weights
    results_by_element, results_by_category_agg = calculate_material_volumes_weights(
        target_areas_data, ref_volume, target_volume
    )

    # Calculate window data
    external_wall_area = request.target_gebaeudeumrisse * request.target_gebaeudehoehe
    window_data = calculate_window_data(
        db,
        request.archetype_id,
        element_type_map,
        external_wall_area,
        factors["faktor_w"],
        request.refurbishment_level,
    )

    # Format and return results
    results_by_category_list = _format_category_results(results_by_category_agg)

    logger.info(
        f"Material estimation completed successfully for Archetype: {request.archetype_id}"
    )

    return MaterialEstimationResponse(
        by_element_type=results_by_element,
        by_product_category=results_by_category_list,
        calculation_factors=factors,
        window_data=window_data,
    )
