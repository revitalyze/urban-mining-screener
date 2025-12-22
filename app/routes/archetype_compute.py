"""
Archetype Compute API Routes

Provides an endpoint to compute the archetype for a building based on address and parameters.
Includes modular filtering logic, improved docstrings, and standardized logging.
"""

import logging
import requests
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import Archetype

logger = logging.getLogger(__name__)

router = APIRouter()


def resolve_country_code(address: str) -> str:
    """
    Use Nominatim geocoding API to resolve the country code from the address.
    Returns a 2-letter country code (ISO 3166-1 alpha-2) or raises ValueError if not found.
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "addressdetails": 1,
        "limit": 1,
    }
    headers = {"User-Agent": "material-estimation-app/1.0"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if not data or "address" not in data[0]:
            raise ValueError("No geocoding result")
        address_info = data[0]["address"]
        country_code = address_info.get("country_code")
        if not country_code:
            raise ValueError("Country code not found")
        return country_code.upper()
    except Exception as e:
        logger.error("Failed to resolve country code for address: %s", e)
        raise ValueError(f"Could not resolve country code: {e}")


class ArchetypeComputeRequest(BaseModel):
    """
    Request model for archetype computation.
    """

    address: str = Field(..., example="Stephansplatz 3, 1010 Wien, Austria")
    typologie: str = Field(..., example="SFH")
    baujahr: int = Field(..., example=1910)
    konstruktionstyp: int = Field(..., example=2)
    energieklasse: int = Field(..., example=1)


class ArchetypeComputeResponse(BaseModel):
    """
    Response model for archetype computation.
    """

    archetype_id: str


class ArchetypeNotFoundResponse(BaseModel):
    """
    Error response model for archetype not found.
    """

    error: str


def _parse_archetype_id(archetype_id: str):
    """
    Parse the archetype_id into its components.
    Returns (country_code, typ_code, start_period, end_period, konstruktionstyp, energieklasse)
    or None if parsing fails.
    """
    parts = archetype_id.split("-")
    if len(parts) != 5:
        return None
    country_code, typ_code, start_period, end_period, last = parts
    if len(last) < 2:
        return None
    try:
        a_konstr = int(last[0])
        a_energie = int(last[1])
    except ValueError:
        return None
    return country_code, typ_code, start_period, end_period, a_konstr, a_energie


def _filter_archetypes(
    archetypes: List[Archetype],
    land_code: str,
    typologie: str,
    konstruktionstyp: int,
    energieklasse: int,
) -> List[Archetype]:
    """
    Filter archetypes by country, typologie, konstruktionstyp, and energieklasse.
    """
    filtered = []
    for a in archetypes:
        parsed = _parse_archetype_id(a.archetype_id)
        if not parsed:
            continue
        country_code, typ_code, _, _, a_konstr, a_energie = parsed
        if (
            country_code.strip().upper() == land_code.strip().upper()
            and typ_code.strip() == typologie.strip()
            and a_konstr == konstruktionstyp
            and a_energie == energieklasse
        ):
            filtered.append(a)
    return filtered


@router.post(
    "/compute_archetype",
    response_model=ArchetypeComputeResponse,
    tags=["archetype"],
    summary="Compute archetype ID from address and parameters",
    description=(
        "Resolves the country code from the given address, finds archetypes whose construction period "
        "covers the provided 'baujahr', and filters by typology, construction type, and energy class. "
        "If exactly one archetype matches, returns its ID; otherwise, returns 404."
    ),
    responses={
        200: {
            "description": "Archetype successfully resolved",
            "content": {
                "application/json": {
                    "examples": {
                        "Austria_SFH_Example": {
                            "summary": "Austrian Single Family Home, built ~1910",
                            "value": {"archetype_id": "AT-SFH-1900-1930-21"},
                        },
                        "Germany_MFH_Example": {
                            "summary": "German Multi Family Home, built ~1975",
                            "value": {"archetype_id": "DE-MFH-1970-1980-21"},
                        },
                    }
                }
            },
        },
        404: {
            "model": ArchetypeNotFoundResponse,
            "description": "No matching archetype found for the given parameters",
            "content": {
                "application/json": {
                    "examples": {
                        "NoMatch": {
                            "summary": "No archetype found",
                            "value": {"error": "Archetype not found"},
                        }
                    }
                }
            },
        },
        400: {
            "description": "Bad request due to address geocoding failure",
            "content": {
                "application/json": {
                    "examples": {
                        "GeocodeFailure": {
                            "summary": "Could not determine country from address",
                            "value": {
                                "detail": "Could not determine country from address: geocoding error"
                            },
                        }
                    }
                }
            },
        },
    },
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "examples": {
                        "SFH_Example": {
                            "summary": "Single Family Home in Vienna",
                            "value": {
                                "address": "Stephansplatz 3, 1010 Wien, Austria",
                                "typologie": "SFH",
                                "baujahr": 1910,
                                "konstruktionstyp": 2,
                                "energieklasse": 1,
                            },
                        },
                        "MFH_Example": {
                            "summary": "Multi Family Home in Berlin",
                            "value": {
                                "address": "Alexanderplatz, Berlin, Germany",
                                "typologie": "MFH",
                                "baujahr": 1975,
                                "konstruktionstyp": 2,
                                "energieklasse": 1,
                            },
                        },
                    }
                }
            },
        }
    },
)
def compute_archetype(req: ArchetypeComputeRequest, db: Session = Depends(get_db)):
    """
    Compute the archetype by dynamically querying for overlapping construction periods.
    Steps:
    1. Resolve the land_code from the address.
    2. Query all archetypes where baujahr is between construction_period_start and construction_period_end.
    3. Filter by typologie, konstruktionstyp, energieklasse, and land_code.
    4. If exactly one archetype remains, return its archetype_id. Otherwise, return 404.
    """
    try:
        land_code = resolve_country_code(req.address)
    except ValueError as e:
        logger.error(f"Country code resolution failed: {e}")
        raise HTTPException(
            status_code=400, detail=f"Could not determine country from address: {e}"
        )

    # Query for archetypes with overlapping construction period
    archetypes = (
        db.query(Archetype)
        .filter(
            Archetype.construction_period_start <= req.baujahr,
            Archetype.construction_period_end >= req.baujahr,
        )
        .all()
    )

    filtered = _filter_archetypes(
        archetypes,
        land_code,
        req.typologie,
        req.konstruktionstyp,
        req.energieklasse,
    )

    logger.debug(
        f"Archetype filter debug: land_code={land_code}, typologie={req.typologie}, "
        f"baujahr={req.baujahr}, konstruktionstyp={req.konstruktionstyp}, "
        f"energieklasse={req.energieklasse}, filtered_count={len(filtered)}"
    )

    if len(filtered) == 1:
        return {"archetype_id": filtered[0].archetype_id}
    logger.warning(
        f"Archetype not found for params: land_code={land_code}, typologie={req.typologie}, "
        f"baujahr={req.baujahr}, konstruktionstyp={req.konstruktionstyp}, "
        f"energieklasse={req.energieklasse}"
    )
    raise HTTPException(status_code=404, detail="Archetype not found")
