from typing import List, Set
from app.models.schemas import Component, ComponentProduct

# Define the product_ids to keep for each as-built component.
DAI_80_A_KEEP_IDS: Set[str] = {"HO_108", "NA_402", "MI_601", "KU_111", "MI_204"}
DAI_01_A_KEEP_IDS: Set[str] = {"MI_602", "HO_109", "HO_208", "KU_111", "MI_205"}
DAI_81_A_KEEP_IDS: Set[str] = {"MI_602", "HO_109"}


def calculate_half_exchange_roof(
    as_built_component: Component, refurbishment_component: Component
) -> List[ComponentProduct]:
    """
    Calculates the final roof assembly for a "half-exchange" refurbishment.

    This function implements the specific logic for combining layers from an
    as-built roof component with a refurbishment component based on the
    as-built component's ID.

    Args:
        as_built_component: The Component object for the existing roof.
        refurbishment_component: The Component object for the new roof layers.

    Returns:
        A new list of ComponentProduct objects representing the combined roof.
    """
    if as_built_component.component_id == "DAI_80_a":
        bottom_layers = [
            p for p in as_built_component.products if p.product_id in DAI_80_A_KEEP_IDS
        ]
        return refurbishment_component.products + bottom_layers
    elif as_built_component.component_id == "DAI_01_a":
        bottom_layers = [
            p for p in as_built_component.products if p.product_id in DAI_01_A_KEEP_IDS
        ]
        return refurbishment_component.products + bottom_layers
    elif as_built_component.component_id == "DAI_81_a":
        bottom_layers = [
            p for p in as_built_component.products if p.product_id in DAI_81_A_KEEP_IDS
        ]
        return refurbishment_component.products + bottom_layers
    else:
        # Default: Return only the refurbishment component's products
        return refurbishment_component.products
