import logging
from typing import List, Set, Tuple

import pandas as pd

from app.models.models import Product

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_product_list(product_df: pd.DataFrame) -> Tuple[List[Product], Set[str]]:
    """Processes the product list DataFrame into Product objects."""
    products = []
    product_ids = set()
    processed_count = 0
    skipped_count = 0

    for index, row in product_df.iterrows():
        product_id = str(row["ID"]).strip() if pd.notna(row["ID"]) else None
        unit = (
            str(row["Unit"]).strip() if pd.notna(row["Unit"]) else None
        )
        raw_density_val = pd.to_numeric(row["Raw density"], errors="coerce")

        if not product_id:
            logger.warning(f"Skipping product row {index + 2}: Missing Product ID.")
            skipped_count += 1
            continue

        # Handle potentially missing density (e.g., for 'm2' items)
        density_to_store = None
        if pd.notna(raw_density_val):
            density_to_store = float(raw_density_val)
        elif unit != "m2":
            logger.warning(
                f"Product row {index + 2} (ID: {product_id}): Missing or invalid Raw density ('{row['Raw density']}') for unit '{unit}'. Storing as NULL."
            )
        # NA_402 is air and still is included in the default products
        if product_id != "NA_402":
            product = Product(
                product_id=product_id,
                designation_en=(
                    str(row["Designation (EN)"]).strip()
                    if pd.notna(row["Designation (EN)"])
                    else "N/A"
                ),
                category_en=(
                    str(row["Category (EN)"]).strip()
                    if pd.notna(row["Category (EN)"])
                    else "N/A"
                ),
                raw_density=density_to_store,
                unit=unit,
            )
            products.append(product)
            product_ids.add(product_id)
            processed_count += 1

    logger.info(f"Processed {processed_count} products, skipped {skipped_count} rows.")
    if not products:
        logger.warning("No valid products were processed from product_list.csv.")
    return products, product_ids
