# app/utils/csv_reader.py
import io
import logging
from typing import List, Tuple

import pandas as pd
from fastapi import HTTPException, UploadFile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EXPECTED_ENCODING = "latin1"


async def read_csv_to_dataframe(file: UploadFile, filename: str) -> pd.DataFrame:
    """Reads an uploaded CSV file into a pandas DataFrame with error handling."""
    try:
        content = await file.read()
        decoded_content = content.decode(EXPECTED_ENCODING)
        df = pd.read_csv(
            io.StringIO(decoded_content), sep=None, engine="python"
        )
        logger.info(f"Successfully read {filename} with shape {df.shape}")
        # Basic cleaning: remove leading/trailing whitespace from column names
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        logger.error(
            f"Error reading or decoding CSV file {filename}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=400, detail=f"Error reading CSV file {filename}: {str(e)}"
        )


def validate_dataframe_columns(
    df: pd.DataFrame, required_columns: List[str], filename: str
):
    """Validates the presence of required columns in a DataFrame."""
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logger.error(f"Missing columns in {filename}: {missing_columns}")
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns in {filename}: {', '.join(missing_columns)}",
        )
    logger.info(f"Validated columns for {filename}.")


async def validate_csv_files(
    product_list_file: UploadFile,
    components_list_file: UploadFile,
    building_list_file: UploadFile,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Validates uploaded CSV files and returns pandas DataFrames."""

    product_df = await read_csv_to_dataframe(product_list_file, "product_list.csv")
    components_df = await read_csv_to_dataframe(
        components_list_file, "components_list.csv"
    )
    building_df = await read_csv_to_dataframe(building_list_file, "building_list.csv")

    required_product_columns = [
        "ID",
        "Designation (EN)",
        "Category (EN)",
        "Raw density",
        "Unit",
    ]
    validate_dataframe_columns(product_df, required_product_columns, "product_list.csv")

    required_component_columns = [
        "ID",
        "Product ID",
        "Thickness for layered (cm), unit for non-layered",
        "Percentage",
    ]
    validate_dataframe_columns(
        components_df, required_component_columns, "components_list.csv"
    )

    required_building_columns = [
        "ID",
        "Country",
        "Use",
        "Typology",
        "From (year)",
        "To (year)",
        "Construction type",
        "Gross floor area (m2)",
        "Volume (m3)",
        "Element type",
        "Area (m2)",
        "ID component (as-built)",
        "ID component (light refurbishment)",
        "ID component (medium refurbishment)",
        "ID component (deep refurbishment)",
    ]
    validate_dataframe_columns(
        building_df, required_building_columns, "building_list.csv"
    )

    return product_df, components_df, building_df
