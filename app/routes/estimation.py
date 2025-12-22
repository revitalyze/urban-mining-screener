# app/routers/estimation.py
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Archetype
from app.models.schemas import (
    ArchetypeList,
    MaterialEstimationRequest,
    MaterialEstimationResponse,
)

from app.utils.estimation_service import estimate_materials

router = APIRouter(tags=["Material Estimation"])
logger = logging.getLogger(__name__)


@router.get(
    "/archetypes",
    response_model=ArchetypeList,
    tags=["Material Estimation"],
    summary="List available archetype IDs",
    description="Retrieve all archetype identifiers sorted for selection in estimation requests.",
    responses={
        200: {
            "description": "List of archetype IDs",
            "content": {
                "application/json": {
                    "examples": {
                        "Example": {
                            "summary": "Sample archetype list",
                            "value": {
                                "archetypes": [
                                    "AT-SFH-1900-1930-21",
                                    "DE-MFH-1970-1980-21",
                                ]
                            },
                        }
                    }
                }
            },
        },
        500: {
            "description": "Database query failed",
            "content": {
                "application/json": {
                    "examples": {
                        "DBFailure": {
                            "summary": "Could not fetch archetype list",
                            "value": {
                                "detail": "Could not fetch archetype list from database."
                            },
                        }
                    }
                }
            },
        },
    },
)
async def get_archetypes(db: Session = Depends(get_db)):
    """
    Retrieves a list of available Archetype IDs from the database.
    """
    logger.info("Request received for fetching archetype list.")
    try:
        archetypes = (
            db.query(Archetype.archetype_id).order_by(Archetype.archetype_id).all()
        )
        archetype_ids = [a[0] for a in archetypes]
        logger.info(f"Found {len(archetype_ids)} archetypes.")
        return ArchetypeList(archetypes=archetype_ids)
    except Exception as e:
        logger.error(
            f"Error fetching archetypes from database: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail="Could not fetch archetype list from database."
        )


@router.post(
    "/estimate_materials",
    response_model=MaterialEstimationResponse,
    tags=["Material Estimation"],
    summary="Estimate building materials based on archetype and target dimensions",
    description=(
        "Estimates material quantities for a target building using a reference archetype and target building "
        "dimensions (ground area, perimeter, height). Returns breakdown by element type and product category, "
        "including calculation factors for transparency and window data."
    ),
    responses={
        200: {
            "description": "Material estimation succeeded",
            "content": {
                "application/json": {
                    "examples": {
                        "SFH_Vienna": {
                            "summary": "Single Family Home estimation example",
                            "value": {
                                "by_element_type": [
                                    {
                                        "product_id": "BRICK-001",
                                        "product_designation": "Clay Brick",
                                        "element_type": "Wall",
                                        "volume": 120.5,
                                        "weight": 216900.0,
                                    },
                                    {
                                        "product_id": "CONC-002",
                                        "product_designation": "Concrete C25/30",
                                        "element_type": "Foundation",
                                        "volume": 45.0,
                                        "weight": 101250.0,
                                    },
                                ],
                                "by_product_category": [
                                    {
                                        "product_id": "BRICK-001",
                                        "product_designation": "Clay Brick",
                                        "category": "Masonry",
                                        "total_volume": 120.5,
                                        "total_weight": 216900.0,
                                    },
                                    {
                                        "product_id": "CONC-002",
                                        "product_designation": "Concrete C25/30",
                                        "category": "Concrete",
                                        "total_volume": 45.0,
                                        "total_weight": 101250.0,
                                    },
                                ],
                                "calculation_factors": {
                                    "height_factor": 1.1,
                                    "perimeter_factor": 0.95,
                                    "density_overrides": {"CONC-002": 2250.0},
                                },
                                "window_data": [
                                    ["Window", "Double glazing", 32.0],
                                    ["Door", "Wood", 12.0],
                                ],
                            },
                        }
                    }
                }
            },
        },
        400: {
            "description": "Invalid request parameters",
            "content": {
                "application/json": {
                    "examples": {
                        "BadRequest": {
                            "summary": "Missing or invalid fields",
                            "value": {"detail": "target_grundflaeche must be > 0"},
                        }
                    }
                }
            },
        },
        500: {
            "description": "Internal server error during estimation",
            "content": {
                "application/json": {
                    "examples": {
                        "ServerError": {
                            "summary": "Unexpected error",
                            "value": {
                                "detail": "An unexpected error occurred during material estimation: internal error"
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
                        "SFH_Request": {
                            "summary": "Estimate materials for SFH archetype",
                            "value": {
                                "archetype_id": "AT-SFH-1900-1930-21",
                                "target_grundflaeche": 120.0,
                                "target_gebaeudeumrisse": 44.0,
                                "target_gebaeudehoehe": 9.5,
                                "refurbishment_level": "as-built",
                            },
                        },
                        "MFH_Request": {
                            "summary": "Estimate materials for MFH archetype",
                            "value": {
                                "archetype_id": "DE-MFH-1970-1980-21",
                                "target_grundflaeche": 540.0,
                                "target_gebaeudeumrisse": 110.0,
                                "target_gebaeudehoehe": 18.0,
                                "refurbishment_level": "light",
                            },
                        },
                    }
                }
            },
        }
    },
)
async def estimate_building_materials(
    request: MaterialEstimationRequest, db: Session = Depends(get_db)
):
    """
    Estimates material quantities for a target building based on a reference archetype
    and target building dimensions (ground floor area, perimeter, height).
    """
    logger.info(
        f"Received material estimation request for archetype: {request.archetype_id}"
    )
    try:
        response = estimate_materials(db, request)
        logger.info(
            f"Successfully generated estimation for archetype: {request.archetype_id}"
        )
        return response
    except HTTPException as e:
        logger.warning(
            f"HTTP Exception during estimation for {request.archetype_id}: {e.detail}"
        )
        raise e
    except ValueError as e:
        logger.error(
            f"Value error during estimation for {request.archetype_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            f"Unexpected error during estimation for {request.archetype_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred during material estimation: {str(e)}",
        )
