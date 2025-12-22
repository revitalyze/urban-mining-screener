import logging
from typing import Dict, List

from app.models.models import Archetype, ArchetypeElement
from app.utils.estimation_constants import (
    EL_TYPE_RETAINING_WALLS,
    EL_TYPE_ROOF,
    EL_TYPE_EXTERNAL_WALLS,
    EL_TYPE_WINDOWS,
    EL_TYPE_GROUND_FLOOR,
)

logger = logging.getLogger(__name__)


def calculate_reference_factors(
    archetype: Archetype,
    archetype_elements: List[ArchetypeElement],
    element_type_map: Dict[int, str],
) -> Dict[str, float]:
    """Calculates reference factors (SM, Dach, W) based on archetype data."""
    ref_bgf = archetype.ref_bgf or 0
    ref_volume = archetype.ref_volume or 0  # Needed for internal walls

    if ref_bgf <= 0:
        logger.warning(
            f"Archetype '{archetype.archetype_id}' has zero or missing reference ground floor area (ref_bgf). Factors involving it will be zero."
        )
    if ref_volume <= 0:
        logger.warning(
            f"Archetype '{archetype.archetype_id}' has zero or missing reference volume (ref_volume). Internal wall calculations will fail or be zero."
        )

    # Map names to IDs needed for factors
    element_ids = {name: id for id, name in element_type_map.items()}
    retaining_walls_id = element_ids.get(EL_TYPE_RETAINING_WALLS)
    roof_id = element_ids.get(EL_TYPE_ROOF)
    external_walls_id = element_ids.get(EL_TYPE_EXTERNAL_WALLS)
    windows_id = element_ids.get(EL_TYPE_WINDOWS)
    ref_grundflaeche_id = element_ids.get(EL_TYPE_GROUND_FLOOR)

    # Sum reference areas for specific element types from the valid archetype_components
    ref_areas = {}
    for ae in archetype_elements:
        element_type_id = ae.element_type_id
        ref_area = ae.ref_area or 0
        ref_areas[element_type_id] = ref_areas.get(element_type_id, 0) + ref_area

    ref_retaining_walls_area = (
        ref_areas.get(retaining_walls_id, 0) if retaining_walls_id else 0
    )
    ref_roof_area = ref_areas.get(roof_id, 0) if roof_id else 0
    ref_external_walls_area = (
        ref_areas.get(external_walls_id, 0) if external_walls_id else 0
    )
    ref_windows_area = ref_areas.get(windows_id, 0) if windows_id else 0
    ref_gruendflaeche = (
        ref_areas.get(ref_grundflaeche_id, 0) if ref_grundflaeche_id else 0
    )
    # --- Calculate factors ---
    faktor_sm = (
        ref_retaining_walls_area / ref_gruendflaeche if ref_gruendflaeche > 0 else 0
    )
    faktor_dach = ref_roof_area / ref_gruendflaeche if ref_gruendflaeche > 0 else 0

    faktor_w = (
        ref_windows_area / (ref_external_walls_area + ref_windows_area)
        if (ref_external_walls_area + ref_windows_area) > 0
        else 0
    )

    factors = {
        "faktor_sm": round(faktor_sm, 6),
        "faktor_dach": round(faktor_dach, 6),
        "faktor_w": round(faktor_w, 6),
        "ref_bgf": ref_bgf,
        "ref_grundflaeche": ref_gruendflaeche,
        "ref_volume": ref_volume,
        "ref_retaining_walls_area": ref_retaining_walls_area,
        "ref_roof_area": ref_roof_area,
        "ref_external_walls_area": ref_external_walls_area,
        "ref_windows_area": ref_windows_area,
    }
    logger.info(
        f"Calculated factors for Archetype '{archetype.archetype_id}': {factors}"
    )
    return factors
