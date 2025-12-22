import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db

from app.models.schemas import CSVUploadResponse
from app.utils.csv_reader import validate_csv_files
from app.utils.product_processor import process_product_list
from app.utils.component_processor import process_components_and_products
from app.utils.archetype_processor import (
    process_archetypes_elements_and_components,
    process_element_types,
)

router = APIRouter(tags=["CSV Upload"])
logger = logging.getLogger(__name__)


@router.post(
    "/upload_csvs",
    response_model=CSVUploadResponse,
    tags=["CSV Upload"],
    summary="Upload reference CSV datasets (products, components, archetypes)",
    responses={
        200: {
            "description": "CSV ingestion succeeded",
            "content": {
                "application/json": {
                    "examples": {
                        "Success": {
                            "summary": "Ingestion counts",
                            "value": {
                                "message": "CSVs uploaded and data ingested successfully",
                                "processed_archetypes": 124,
                                "processed_element_types": 8,
                                "processed_components": 42,
                                "processed_products": 215,
                                "processed_component_products": 380,
                                "processed_archetype_elements": 320,
                                "processed_element_components": 480,
                            },
                        }
                    }
                }
            },
        },
        400: {
            "description": "Invalid CSVs or missing required data",
            "content": {
                "application/json": {
                    "examples": {
                        "NoProducts": {
                            "summary": "Product CSV invalid",
                            "value": {
                                "detail": "No valid products found in product_list.csv. Aborting."
                            },
                        },
                        "NoArchetypes": {
                            "summary": "Archetype CSV invalid",
                            "value": {
                                "detail": "No valid Archetypes found in building_list.csv. Aborting."
                            },
                        },
                    }
                }
            },
        },
        500: {
            "description": "Database reset failed or unexpected ingestion error",
            "content": {
                "application/json": {
                    "examples": {
                        "DBResetFail": {
                            "summary": "Database reset failure",
                            "value": {
                                "detail": "Database reset failed: <error message>"
                            },
                        },
                        "Unexpected": {
                            "summary": "Unexpected error",
                            "value": {
                                "detail": "An unexpected error occurred during CSV processing: <error>. Check server logs."
                            },
                        },
                    }
                }
            },
        },
    },
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "product_list": {"type": "string", "format": "binary"},
                            "components_list": {"type": "string", "format": "binary"},
                            "building_list": {"type": "string", "format": "binary"},
                        },
                        "required": [
                            "product_list",
                            "components_list",
                            "building_list",
                        ],
                    },
                    "examples": {
                        "UploadExample": {
                            "summary": "Upload three CSV files",
                            "value": {
                                "product_list": "<binary: product_list.csv>",
                                "components_list": "<binary: components_list.csv>",
                                "building_list": "<binary: building_list.csv>",
                            },
                        }
                    },
                }
            },
        }
    },
)
async def upload_csvs(
    product_list: UploadFile = File(..., description="CSV file for Products"),
    components_list: UploadFile = File(
        ..., description="CSV file for Components and their Products"
    ),
    building_list: UploadFile = File(
        ..., description="CSV file for Archetypes, Elements, and their Components"
    ),
    db: Session = Depends(get_db),
):
    """
    Uploads Product, Component, and Building CSV files.
    Clears existing data and ingests the new data from the uploaded files.
    """
    logger.info("Starting CSV upload process...")
    try:
        product_df, components_df, building_df = await validate_csv_files(
            product_list, components_list, building_list
        )
        logger.info("CSV files validated successfully.")

        logger.info("Dropping and recreating database tables...")
        try:
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables recreated.")
        except Exception as e:
            logger.error(f"Database reset failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Database reset failed: {str(e)}"
            )

        # --- Ingestion Order ---
        # 1. Products
        logger.info("Processing Products...")
        products, valid_product_ids = process_product_list(product_df)
        if not products:
            raise HTTPException(
                status_code=400,
                detail="No valid products found in product_list.csv. Aborting.",
            )
        db.add_all(products)
        db.commit()
        logger.info(f"Committed {len(products)} Products.")

        # 2. Element Types (needs building_df)
        logger.info("Processing Element Types...")
        element_types_list, _ = process_element_types(building_df)  # Get list
        if not element_types_list:
            # Allow proceeding without element types, but log a strong warning
            logger.warning(
                "No Element Types found. ElementComponent links will likely fail."
            )
            element_type_map = {}
        else:
            db.add_all(element_types_list)
            db.commit()
            # Refresh objects to get generated IDs and build the map
            db.flush()  # Ensure objects are sent to DB
            element_type_map = {
                et.name: et.element_type_id for et in element_types_list
            }
            logger.info(f"Committed {len(element_types_list)} Element Types.")

        # 3. Components & Component Products (needs components_df and valid_product_ids)
        logger.info("Processing Components and Component Products...")
        components, component_products, valid_component_ids = (
            process_components_and_products(components_df, valid_product_ids)
        )
        if not components:
            # Allow proceeding without components, but log a strong warning
            logger.warning(
                "No valid Components found. ElementComponent links and estimations will likely fail."
            )
        else:
            db.add_all(components)
            db.commit()  # Commit components first
            logger.info(f"Committed {len(components)} Components.")

            if not component_products:
                logger.warning("No Component-Product links found.")
            else:
                db.add_all(component_products)
                db.commit()  # Commit component products
                logger.info(f"Committed {len(component_products)} Component Products.")

        # 4. Archetypes, ArchetypeElements, and ElementComponents
        logger.info(
            "Processing Archetypes, Archetype Elements, and Element Components..."
        )
        (
            archetypes,
            archetype_elements,
            element_components,
        ) = process_archetypes_elements_and_components(
            building_df, element_type_map, valid_component_ids
        )

        if not archetypes:
            raise HTTPException(
                status_code=400,
                detail="No valid Archetypes found in building_list.csv. Aborting.",
            )
        db.add_all(archetypes)
        db.commit()
        logger.info(f"Committed {len(archetypes)} Archetypes.")

        if not archetype_elements:
            logger.warning(
                "No Archetype Elements found. Estimations may not be possible."
            )
        else:
            db.add_all(archetype_elements)
            db.commit()
            logger.info(f"Committed {len(archetype_elements)} Archetype Elements.")

        if not element_components:
            logger.warning(
                "No Element-Component links found. Estimations may not be possible."
            )
        else:
            db.add_all(element_components)
            db.commit()
            logger.info(f"Committed {len(element_components)} Element Components.")

        logger.info("CSV processing and data ingestion completed successfully.")
        return CSVUploadResponse(
            message="CSVs uploaded and data ingested successfully",
            processed_archetypes=len(archetypes),
            processed_element_types=len(element_type_map),
            processed_components=len(components),
            processed_products=len(products),
            processed_component_products=len(component_products),
            processed_archetype_elements=len(archetype_elements),
            processed_element_components=len(element_components),
        )

    except HTTPException as e:
        logger.error(f"HTTP Exception during CSV upload: {e.detail}", exc_info=True)
        db.rollback()
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during CSV upload: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred during CSV processing: {str(e)}. Check server logs.",
        )
