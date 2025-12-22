from collections import defaultdict
from typing import List, Tuple
from sqlalchemy.orm import Session

from app.models.models import (
    ArchetypeElement,
    ElementComponent,
    ComponentProduct,
)
from app.utils.refurbishment_rules import get_refurbishment_action
from app.utils.half_exchange_logic import calculate_half_exchange_roof

# Candidate refurbishment levels for which rules may exist.
REFURBISHMENT_LEVELS: List[str] = ["as-built", "light", "medium", "deep"]


def apply_refurbishment_logic(
    element_components: List[ElementComponent],
    archetype_elements: List[ArchetypeElement],
    refurbishment_level: str,
) -> List[Tuple[ComponentProduct, ArchetypeElement]]:
    """
    For each ArchetypeElement, select the correct ElementComponent(s) for the requested refurbishment_level,
    apply the correct material combination rule (add, exchange, half-exchange), and return the final list of (ComponentProduct, ArchetypeElement) tuples.

    Args:
        element_components: All ElementComponent objects for the archetype.
        archetype_elements: All ArchetypeElement objects for the archetype.
        refurbishment_level: The refurbishment level to apply ("as-built", "light", "medium", "deep").

    Returns:
        List of (ComponentProduct, ArchetypeElement) tuples representing the final material assembly.
    """
    final_layers: List[Tuple[ComponentProduct, ArchetypeElement]] = []
    # Group ElementComponents by their parent ArchetypeElement
    components_by_element_id: defaultdict[int, List[ElementComponent]] = defaultdict(
        list
    )
    for ec in element_components:
        components_by_element_id[ec.element_id].append(ec)

    element_map = {ae.id: ae for ae in archetype_elements}

    for element_id, components in components_by_element_id.items():
        archetype_element = element_map.get(element_id)
        if not archetype_element:
            continue

        # Always find the as-built component for this element
        as_built_ec = next(
            (c for c in components if c.refurbishment_level == "as-built"), None
        )
        # Find the refurbishment component for the requested level (may be None)
        refurbishment_ec = (
            None
            if refurbishment_level == "as-built"
            else next(
                (c for c in components if c.refurbishment_level == refurbishment_level),
                None,
            )
        )

        # If no as-built, skip (data error)
        if as_built_ec is None:
            continue

        # If no refurbishment component for this level, use as-built only
        if refurbishment_ec is None:
            for product in as_built_ec.component.products:
                final_layers.append((product, archetype_element))
            continue

        # Determine the rule to apply for this element/component
        action = get_refurbishment_action(
            archetype_element.element_type.name, refurbishment_ec.component.component_id
        )

        if action == "exchange":
            # Use only the refurbishment component's products
            for product in refurbishment_ec.component.products:
                final_layers.append((product, archetype_element))
        elif action == "add":
            # Combine as-built and refurbishment products (sum)
            for product in as_built_ec.component.products:
                final_layers.append((product, archetype_element))
            for product in refurbishment_ec.component.products:
                final_layers.append((product, archetype_element))
        elif action == "half-exchange":
            # Use the special half-exchange logic for roof
            combined_products = calculate_half_exchange_roof(
                as_built_ec.component, refurbishment_ec.component
            )
            for product in combined_products:
                final_layers.append((product, archetype_element))
        else:
            # If no rule found, fallback to as-built only (do NOT double-count)
            for product in as_built_ec.component.products:
                final_layers.append((product, archetype_element))

    return final_layers


def get_available_refurbishment_levels_for_archetype(
    db: Session,
    archetype_id: str,
) -> List[str]:
    """
    Inspect all components used by the given archetype and determine the set
    of refurbishment levels that actually have an effect according to the
    refurbishment rules.

    A level is considered "available" if, for at least one element:
      * an ElementComponent exists for that level, and
      * applying refurbishment_rules would change the resulting assembly
        compared to the as-built configuration.
    """
    # Load all elements and their components for the archetype
    archetype_elements: List[ArchetypeElement] = (
        db.query(ArchetypeElement)
        .filter(ArchetypeElement.archetype_id == archetype_id)
        .all()
    )
    if not archetype_elements:
        return []

    element_ids = [ae.id for ae in archetype_elements]
    element_components: List[ElementComponent] = (
        db.query(ElementComponent)
        .filter(ElementComponent.element_id.in_(element_ids))
        .all()
    )

    if not element_components:
        return []

    available_levels: List[str] = []

    # Group components by element for efficient comparison
    components_by_element_id: defaultdict[int, List[ElementComponent]] = defaultdict(
        list
    )
    for ec in element_components:
        components_by_element_id[ec.element_id].append(ec)

    element_map = {ae.id: ae for ae in archetype_elements}

    # Helper to build a simple "signature" of resulting products for comparison
    def _build_signature_for_level(level: str) -> set[tuple[str, int]]:
        signature: set[tuple[str, int]] = set()
        for element_id, components in components_by_element_id.items():
            archetype_element = element_map.get(element_id)
            if not archetype_element:
                continue

            as_built_ec = next(
                (c for c in components if c.refurbishment_level == "as-built"), None
            )
            if as_built_ec is None:
                continue

            if level == "as-built":
                # Only as-built products
                for product in as_built_ec.component.products:
                    signature.add((product.product_id, archetype_element.id))
                continue

            refurbishment_ec = next(
                (c for c in components if c.refurbishment_level == level), None
            )

            if refurbishment_ec is None:
                # Level has no effect for this element: fall back to as-built
                for product in as_built_ec.component.products:
                    signature.add((product.product_id, archetype_element.id))
                continue

            action = get_refurbishment_action(
                archetype_element.element_type.name,
                refurbishment_ec.component.component_id,
            )

            if action == "exchange":
                for product in refurbishment_ec.component.products:
                    signature.add((product.product_id, archetype_element.id))
            elif action == "add":
                for product in as_built_ec.component.products:
                    signature.add((product.product_id, archetype_element.id))
                for product in refurbishment_ec.component.products:
                    signature.add((product.product_id, archetype_element.id))
            elif action == "half-exchange":
                combined_products = calculate_half_exchange_roof(
                    as_built_ec.component, refurbishment_ec.component
                )
                for product in combined_products:
                    signature.add((product.product_id, archetype_element.id))
            else:
                # Unknown action -> fall back to as-built
                for product in as_built_ec.component.products:
                    signature.add((product.product_id, archetype_element.id))

        return signature

    # Baseline as-built signature
    as_built_signature = _build_signature_for_level("as-built")

    for level in REFURBISHMENT_LEVELS:
        level_signature = _build_signature_for_level(level)
        if level_signature != as_built_signature:
            available_levels.append(level)

    # Preserve order defined in REFURBISHMENT_LEVELS but ensure uniqueness
    seen = set()
    ordered_unique = []
    for level in available_levels:
        if level not in seen:
            seen.add(level)
            ordered_unique.append(level)
    return ordered_unique
