# app/utils/component_processor.py
import logging
from typing import List, Set, Tuple

import pandas as pd

from app.models.models import Component, ComponentProduct

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_components_and_products(
    components_df: pd.DataFrame, valid_product_ids: Set[str]
) -> Tuple[List[Component], List[ComponentProduct], Set[str]]:
    """Processes components and their associated products."""
    components = []
    component_products = []
    component_ids = set()
    processed_components = 0
    processed_comp_prods = 0
    skipped_comp_prods = 0

    # Forward fill the component ID
    components_df["ID"] = components_df["ID"].ffill()
    # Ensure required columns don't have NaNs where critical
    components_df.dropna(subset=["ID", "Product ID"], inplace=True)

    unique_ids = components_df["ID"].astype(str).str.strip().unique()
    for comp_id in unique_ids:
        if comp_id:
            components.append(Component(component_id=comp_id))
            component_ids.add(comp_id)
            processed_components += 1

    logger.info(f"Identified {processed_components} unique components.")

    thickness_col = "Thickness for layered (cm), unit for non-layered"
    percentage_col = "Percentage"

    # Convert relevant columns to numeric *before* iteration
    components_df[thickness_col] = pd.to_numeric(
        components_df[thickness_col], errors="coerce"
    )
    components_df[percentage_col] = pd.to_numeric(
        components_df[percentage_col], errors="coerce"
    )

    # Iterate through rows to create ComponentProduct links
    for index, row in components_df.iterrows():
        component_id = str(row["ID"]).strip()
        product_id = str(row["Product ID"]).strip()
        schichtstaerke_val = row[thickness_col]
        percentage_val = row[percentage_col]

        # Validate data for ComponentProduct - Percentage is always required
        if pd.isna(percentage_val):
            logger.warning(
                f"Skipping component product row {index + 2} for component '{component_id}': Invalid or missing percentage ('{row[percentage_col]}')."
            )
            skipped_comp_prods += 1
            continue

        # Handle potentially missing thickness (e.g., for non-layered/m2 items)
        thickness_to_store = None
        if pd.notna(schichtstaerke_val):
            thickness_to_store = float(schichtstaerke_val)
        else:
            logger.info(  # Use info level, as this might be expected
                f"Component product row {index + 2} (Comp: {component_id}, Prod: {product_id}): Missing or invalid thickness ('{row[thickness_col]}'). Storing as NULL"
            )

        if product_id not in valid_product_ids:
            logger.warning(
                f"Skipping component product row {index + 2}: Product ID '{product_id}' not found in valid products list."
            )
            skipped_comp_prods += 1
            continue

        if component_id not in component_ids:
            logger.warning(
                f"Skipping component product row {index + 2}: Component ID '{component_id}' was not identified as a unique component (likely missing its header row)."
            )
            skipped_comp_prods += 1
            continue

        component_product = ComponentProduct(
            component_id=component_id,
            product_id=product_id,
            schichtstaerke=thickness_to_store,  # Store handled thickness (can be None)
            percentage=float(percentage_val),
        )
        component_products.append(component_product)
        processed_comp_prods += 1

    logger.info(
        f"Processed {processed_comp_prods} component-product links, skipped {skipped_comp_prods} rows."
    )
    if not components:
        logger.warning("No valid components were processed.")
    if not component_products:
        logger.warning("No valid component-product links were processed.")

    return components, component_products, component_ids
