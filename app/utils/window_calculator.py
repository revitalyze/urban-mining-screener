import logging
from typing import Dict, List, Tuple, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import (
    ArchetypeElement,
    ElementComponent,
    Component,
    ComponentProduct,
    Product,
)

logger = logging.getLogger(__name__)


def _get_window_element_type_id(
    element_type_map: Dict[int, str], archetype_id: str
) -> Optional[int]:
    """Find the element type ID for 'Windows' from the element type map."""
    for element_type_id, element_name in element_type_map.items():
        if element_name.lower() == "windows":
            return element_type_id

    logger.warning(f"Element type 'Windows' not found for Archetype {archetype_id}")
    return None


def _execute_window_query(
    db: Session,
    archetype_id: str,
    window_element_type_id: int,
    total_window_area: float,
    refurbishment_level: str,
) -> List[Tuple[str, str, float]]:
    """Execute database query to calculate window product areas."""
    result = (
        db.query(
            ComponentProduct.product_id,
            Product.designation_en,
            func.sum(
                total_window_area
                * ComponentProduct.schichtstaerke
                * ComponentProduct.percentage
            ).label("total_product_area"),
        )
        .select_from(ElementComponent)
        .join(Component, ElementComponent.component_id == Component.component_id)
        .join(ComponentProduct, Component.component_id == ComponentProduct.component_id)
        .join(Product, ComponentProduct.product_id == Product.product_id)
        .join(ArchetypeElement, ElementComponent.element_id == ArchetypeElement.id)
        .filter(
            ArchetypeElement.archetype_id == archetype_id,
            ArchetypeElement.element_type_id == window_element_type_id,
            ElementComponent.refurbishment_level == refurbishment_level,
        )
        .group_by(ComponentProduct.product_id, Product.designation_en)
        .all()
    )

    return [
        (str(product_id), designation_en, total_product_area)
        for product_id, designation_en, total_product_area in result
    ]


def calculate_window_data(
    db: Session,
    archetype_id: str,
    element_type_map: Dict[int, str],
    external_wall_area: float,
    factor_window: float,
    refurbishment_level: str,
) -> List[Tuple[str, str, float]]:
    """
    Calculates the total area for each product used in windows of the archetype.

    The total product area is calculated as the sum over all window components of
    (external_wall_area * factor_window * schichtstaerke * (percentage / 100)) for each product.
    Assumes schichtstaerke is a dimensionless factor, as multiplying by a thickness would yield volume, not area.

    Includes fallback logic: if no components are found for the specified refurbishment level,
    defaults to "as-built" components.

    Args:
        db (Session): The database session.
        archetype_id (str): The ID of the archetype.
        element_type_map (Dict[int, str]): A map of element type IDs to their names.
        external_wall_area (float): The external wall area in square meters.
        factor_window (float): The factor representing the proportion of wall area occupied by windows.
        refurbishment_level (str): The refurbishment level to filter components by.

    Returns:
        List[Tuple[str, str, float]]: A list of tuples containing product ID, designation_en, and total product area.
    """
    window_element_type_id = _get_window_element_type_id(element_type_map, archetype_id)
    if window_element_type_id is None:
        return []

    try:
        total_window_area = external_wall_area * factor_window

        # Try with original refurbishment level
        result = _execute_window_query(
            db,
            archetype_id,
            window_element_type_id,
            total_window_area,
            refurbishment_level,
        )

        # Fallback to "as-built" if no results and not already using it
        if not result and refurbishment_level.lower() != "as-built":
            logger.info(
                f"No window components found for refurbishment level '{refurbishment_level}' "
                f"for Archetype {archetype_id}. Falling back to 'as-built' components."
            )
            result = _execute_window_query(
                db, archetype_id, window_element_type_id, total_window_area, "as-built"
            )

        return result
    except Exception as e:
        logger.error(
            f"Error calculating window data for Archetype {archetype_id}: {e}",
            exc_info=True,
        )
        return []
