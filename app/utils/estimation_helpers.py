import logging
from typing import Dict, List, Tuple

from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException

from app.models.models import (
    Archetype,
    ElementComponent,
    ArchetypeElement,
    Component,
    ComponentProduct,
)
from app.models.schemas import (
    MaterialByProductCategory,
    MaterialEstimationRequest,
)
from app.utils.estimation_constants import INTERNAL_WALL_ELEMENTS
from app.utils.area_estimator import TargetAreaData

logger = logging.getLogger(__name__)


def _fetch_archetype_from_db(db: Session, archetype_id: str) -> Archetype:
    """Fetch archetype from database with all necessary joins."""
    archetype = (
        db.query(Archetype)
        .filter(Archetype.archetype_id == archetype_id)
        .options(
            joinedload(Archetype.elements).joinedload(ArchetypeElement.element_type),
            joinedload(Archetype.elements)
            .joinedload(ArchetypeElement.components)
            .joinedload(ElementComponent.component)
            .joinedload(Component.products)
            .joinedload(ComponentProduct.product),
        )
        .first()
    )
    if not archetype:
        logger.error(f"Archetype with ID {archetype_id} not found in database.")
        raise HTTPException(
            status_code=404, detail=f"Archetype '{archetype_id}' not found"
        )
    return archetype


def _build_element_type_map_and_components(
    archetype: Archetype, archetype_id: str
) -> Tuple[Dict[int, str], List[ElementComponent]]:
    """Build element type map and collect all components from archetype elements."""
    element_type_map = {}
    all_components = []

    if not archetype.elements:
        logger.warning(
            f"Archetype '{archetype_id}' found, but has no associated elements. Estimation might yield zero results."
        )
        return element_type_map, all_components

    for archetype_element in archetype.elements:
        if archetype_element.element_type:
            element_type_map[archetype_element.element_type.element_type_id] = (
                archetype_element.element_type.name
            )
            all_components.extend(archetype_element.components)
        else:
            logger.warning(
                f"ArchetypeElement ID {archetype_element.id} for Archetype {archetype_id} "
                "is missing ElementType link. Skipping."
            )

    if not all_components:
        logger.warning(
            f"Archetype '{archetype_id}' has elements, but they have no associated components. "
            "Estimation might yield zero results."
        )

    if not element_type_map:
        logger.warning(
            f"No valid Element Types associated with components for Archetype '{archetype_id}'."
        )

    return element_type_map, all_components


def get_reference_data(
    db: Session, archetype_id: str
) -> Tuple[Archetype, List[ArchetypeElement], List[ElementComponent], Dict[int, str]]:
    """Retrieves archetype, its elements, components, and element type map from DB."""
    archetype = _fetch_archetype_from_db(db, archetype_id)
    element_type_map, all_components = _build_element_type_map_and_components(
        archetype, archetype_id
    )

    logger.info(f"Retrieved reference data for Archetype: {archetype_id}")
    return archetype, archetype.elements, all_components, element_type_map


def _validate_request_dimensions(request: MaterialEstimationRequest) -> None:
    """Validate that target dimensions are positive values."""
    if (
        request.target_grundflaeche <= 0
        or request.target_gebaeudeumrisse <= 0
        or request.target_gebaeudehoehe <= 0
    ):
        raise HTTPException(
            status_code=400,
            detail="Target dimensions (ground floor area, perimeter, height) must be positive.",
        )


def _validate_internal_walls_requirements(
    target_areas_data: List[TargetAreaData],
    ref_volume: float,
    archetype_id: str,
) -> None:
    """Validate that internal walls requirements are met."""
    has_internal_walls = any(
        item.element_type_name in INTERNAL_WALL_ELEMENTS for item in target_areas_data
    )
    if has_internal_walls and ref_volume <= 0:
        logger.error(
            f"Cannot estimate internal walls for Archetype {archetype_id} because "
            "reference volume (ref_volume) is missing or zero in the archetype data."
        )
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot estimate internal walls for Archetype {archetype_id}: "
                "Missing or zero reference volume in archetype data."
            ),
        )


def _format_category_results(
    results_by_category_agg: Dict[str, Dict[str, any]],
) -> List[MaterialByProductCategory]:
    """Format category results into response schema objects."""
    return [
        MaterialByProductCategory(
            product_id=data["product_id"],
            product_designation=data["product_designation"],
            category=data["category"],
            total_volume=round(data["total_volume"], 6),
            total_weight=round(data["total_weight"], 4),
        )
        for data in results_by_category_agg.values()
    ]
