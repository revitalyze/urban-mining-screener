from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Archetype
from app.models.schemas import RefurbishmentOptionsResponse
from app.utils.refurbishment_service import (
    get_available_refurbishment_levels_for_archetype,
)

router = APIRouter(tags=["Material Estimation"])


@router.get(
    "/api/refurbishment_options/{archetype_id}",
    response_model=RefurbishmentOptionsResponse,
    summary="Get refurbishment options for an archetype",
    description=(
        "Inspect all components used by the given archetype and determine which "
        "refurbishment levels actually have an effect according to the refurbishment rules."
    ),
)
def get_refurbishment_options(
    archetype_id: str,
    db: Session = Depends(get_db),
) -> RefurbishmentOptionsResponse:
    """
    Return refurbishment options for the given archetype.

    Steps:
    1. Validate that the archetype exists.
    2. Determine which refurbishment levels have a material effect.
    3. Build a RefurbishmentOptionsResponse including default level and explanation.
    """
    # 1. Validate archetype exists
    archetype = (
        db.query(Archetype).filter(Archetype.archetype_id == archetype_id).first()
    )
    if archetype is None:
        raise HTTPException(status_code=404, detail="Archetype not found")

    # 2. Compute available refurbishment levels
    available_levels: List[str] = get_available_refurbishment_levels_for_archetype(
        db, archetype_id
    )

    refurbishment_required = bool(available_levels)
    default_level = "as-built" if "as-built" in available_levels else None

    explanation = (
        "Refurbishment options are available for this archetype."
        if refurbishment_required
        else None
    )

    return RefurbishmentOptionsResponse(
        archetype_id=str(archetype_id),
        refurbishment_required=refurbishment_required,
        available_levels=available_levels,
        default_level=default_level,
        explanation=explanation,
    )
