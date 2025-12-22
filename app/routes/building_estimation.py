"""
Building Estimation API Routes

Provides an endpoint to estimate building area, perimeter, and height from an address.
Includes standardized error handling and logging for maintainability.
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from app.utils.building_value_estimator import (
    estimate_building_values,
    BuildingEstimationError,
)
from app.routes.archetype_compute import resolve_country_code

logger = logging.getLogger(__name__)

router = APIRouter()


class BuildingEstimationRequest(BaseModel):
    """
    Request model for building estimation.
    """

    address: str = Field(..., example="Stephansplatz 1, 1010 Wien, Austria")


class BuildingEstimationResponse(BaseModel):
    """
    Response model for building estimation results.
    """

    grundflaeche: float
    gebaeudeumfang: float
    gebaeudehoehe: Optional[float]
    height_available: bool
    country_code: str
    message: Optional[str] = None


@router.post(
    "/estimate_building_values",
    response_model=BuildingEstimationResponse,
    tags=["Building Estimation"],
    summary="Estimate building area, perimeter, and height from address",
    description=(
        "Given an address, queries geospatial sources to approximate ground area (m²), "
        "perimeter (m), and building height (m, if available). Also resolves and returns "
        "the ISO country code."
    ),
    responses={
        200: {
            "description": "Estimation succeeded",
            "content": {
                "application/json": {
                    "examples": {
                        "ViennaExample": {
                            "summary": "Vienna address with height available",
                            "value": {
                                "grundflaeche": 850.0,
                                "gebaeudeumfang": 130.0,
                                "gebaeudehoehe": 18.5,
                                "height_available": True,
                                "country_code": "AT",
                                "message": "Estimated from OSM footprints and elevation data",
                            },
                        },
                        "BerlinNoHeight": {
                            "summary": "Berlin address without height",
                            "value": {
                                "grundflaeche": 540.0,
                                "gebaeudeumfang": 110.0,
                                "gebaeudehoehe": None,
                                "height_available": False,
                                "country_code": "DE",
                                "message": "Height not available for this area",
                            },
                        },
                    }
                }
            },
        },
        400: {
            "description": "Invalid address or geocoding failure",
            "content": {
                "application/json": {
                    "examples": {
                        "GeocodeFailure": {
                            "summary": "Could not resolve country from address",
                            "value": {
                                "detail": "Could not resolve country code: <geocoding error>"
                            },
                        }
                    }
                }
            },
        },
        404: {
            "description": "Building data not found for address",
            "content": {
                "application/json": {
                    "examples": {
                        "NotFound": {
                            "summary": "No building footprint found",
                            "value": {
                                "detail": "No building data found for the provided address"
                            },
                        }
                    }
                }
            },
        },
        500: {"description": "Internal server error"},
    },
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "examples": {
                        "Vienna": {
                            "summary": "Stephansplatz 1, Vienna",
                            "value": {"address": "Stephansplatz 1, 1010 Wien, Austria"},
                        },
                        "Berlin": {
                            "summary": "Alexanderplatz, Berlin",
                            "value": {"address": "Alexanderplatz, Berlin, Germany"},
                        },
                    }
                }
            },
        }
    },
)
def estimate_building_values_endpoint(request: BuildingEstimationRequest):
    """
    Estimate building area, perimeter, and height for a given address.
    Returns a standardized response or raises HTTPException on error.
    """
    try:
        result = estimate_building_values(request.address)
        try:
            country_code = resolve_country_code(request.address)
        except Exception as e:
            logger.error(f"Country code resolution failed: {e}")
            raise HTTPException(
                status_code=400, detail=f"Could not resolve country code: {e}"
            )
        result["country_code"] = country_code
        return result
    except BuildingEstimationError as e:
        logger.warning(f"Building estimation error: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error during building estimation")
        raise HTTPException(status_code=500, detail="Internal server error")


building_estimation_router = router
__all__ = ["building_estimation_router"]
