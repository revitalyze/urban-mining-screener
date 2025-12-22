import logging
from typing import Dict, List, Tuple

from app.models.models import ComponentProduct, Product
from app.models.schemas import MaterialByElementType

from app.utils.estimation_constants import (
    AREA_BASED_ELEMENTS,
    INTERNAL_WALL_ELEMENTS,
)
from app.utils.area_estimator import TargetAreaData

logger = logging.getLogger(__name__)


def calculate_material_volumes_weights(
    target_areas_data: List[TargetAreaData],
    ref_volume: float,
    target_volume: float,
) -> Tuple[List[MaterialByElementType], Dict[str, Dict]]:
    """
    Calculates volumes and weights for each product based on target areas or reference volume scaling.

    Args:
        db: SQLAlchemy session.
        target_areas_data: List of TargetAreaData (from area_estimator.py), each containing:
            - element_type_id: int
            - element_type_name: str
            - component_id: str
            - target_area: float
            - ref_area: float
        ref_volume: Reference building volume (for scaling internal wall elements).
        target_volume: Target building volume (for scaling internal wall elements).

    Returns:
        Tuple of:
            - List of MaterialByElementType (per product/element)
            - Dict of aggregated results by product category

    This function is compatible with the new refurbishment logic and expects TargetAreaData as produced by area_estimator.py.
    """
    results_by_element = []
    results_by_category_agg = {}

    components = list(
        set(item.component for item in target_areas_data)
    )
    if not components:
        logger.warning(
            "No components found in target_areas_data. Returning empty results."
        )
        return [], {}

    cp_lookup: Dict[str, List[ComponentProduct]] = {}
    for cp in components:
        component_product: ComponentProduct = cp[0]
        if component_product not in cp_lookup:
            cp_lookup[component_product.component_id] = []
        cp_lookup[component_product.component_id].extend(component_product.component.products)

    processed_count = 0
    skipped_count = 0
    for area_data in target_areas_data:
        try:
            component_id = str(
                area_data.component[0].component_id
            )
            target_area = float(area_data.target_area)
            element_type_name = str(area_data.element_type_name)
            ref_area = float(area_data.ref_area)
        except (AttributeError, ValueError, TypeError) as e:
            logger.error(f"Invalid TargetAreaData entry: {area_data} ({e}). Skipping.")
            skipped_count += 1
            continue

        component_products = cp_lookup.get(component_id, [])
        if not component_products:
            logger.debug(
                f"No component products found for component_id {component_id}. Skipping."
            )
            continue

        for cp in component_products:
            product = cp.product
            if not product or product.raw_density is None or product.raw_density <= 0:
                logger.warning(
                    f"Skipping calculation for ComponentProduct ID {getattr(cp, 'id', 'N/A')} (Component {component_id}, Product {getattr(cp, 'product_id', 'N/A')}): Missing Product data or invalid raw_density ({getattr(product, 'raw_density', 'N/A') if product else 'N/A'})."
                )
                skipped_count += 1
                continue

            # Convert thickness from cm to m
            thickness_m = (cp.schichtstaerke or 0) / 100.0
            if thickness_m <= 0:
                logger.debug(
                    f"Skipping product {cp.product_id} in component {component_id} due to zero or missing thickness."
                )
                skipped_count += 1
                continue

            percentage_factor = cp.percentage if cp.percentage is not None else 1.0
            if not (0 <= percentage_factor <= 1):
                logger.warning(
                    f"Percentage factor {percentage_factor} for product {cp.product_id} in component {component_id} is outside the expected 0-1 range. Clamping or check data."
                )
                percentage_factor = max(0.0, min(1.0, percentage_factor))

            volume = 0.0
            if element_type_name in INTERNAL_WALL_ELEMENTS:
                if ref_volume > 0:
                    volume = (
                        ref_area * thickness_m * percentage_factor / ref_volume
                    ) * target_volume
                    logger.debug(
                        f"Internal Wall Product {cp.product_id} in Comp {component_id}: "
                        f"Volume = ({ref_area} * {thickness_m} * {percentage_factor} / {ref_volume}) * {target_volume} = {volume}"
                    )
                else:
                    logger.warning(
                        f"Cannot calculate volume for internal wall product {cp.product_id} in component {component_id} because reference volume is zero."
                    )
                    volume = 0.0
            elif element_type_name in AREA_BASED_ELEMENTS:
                volume = target_area * thickness_m * percentage_factor
                logger.debug(
                    f"Area-Based Product {cp.product_id} in Comp {component_id} ({element_type_name}): "
                    f"Volume = {target_area} * {thickness_m} * {percentage_factor} = {volume}"
                )
            else:
                logger.warning(
                    f"Element type '{element_type_name}' for component {component_id} is neither explicitly Area-Based nor Internal Wall. Volume calculation skipped."
                )
                volume = 0.0

            weight = volume * product.raw_density

            if volume > 1e-9:
                volume = round(volume, 6)
                weight = round(weight, 4)

                results_by_element.append(
                    MaterialByElementType(
                        product_id=product.product_id,
                        product_designation=product.designation_en or "N/A",
                        element_type=element_type_name,
                        volume=volume,
                        weight=weight,
                    )
                )

                category_name = (
                    product.category_en if product.category_en else "Unknown Category"
                )
                designation_name = (
                    product.designation_en
                    if product.designation_en
                    else "Unknown Designation"
                )
                category_key = f"{category_name}|{product.product_id}"

                if category_key not in results_by_category_agg:
                    results_by_category_agg[category_key] = {
                        "product_id": product.product_id,
                        "product_designation": designation_name,
                        "category": category_name,
                        "total_volume": 0.0,
                        "total_weight": 0.0,
                    }
                results_by_category_agg[category_key]["total_volume"] += volume
                results_by_category_agg[category_key]["total_weight"] += weight
                processed_count += 1
            else:
                logger.debug(
                    f"Calculated volume for {cp.product_id} in {component_id} is near zero ({volume}). Skipping addition."
                )
                skipped_count += 1

    logger.info(
        f"Calculated volumes/weights for {processed_count} material instances. Skipped {skipped_count} due to missing data or near-zero volume."
    )
    return results_by_element, results_by_category_agg
