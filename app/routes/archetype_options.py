"""
Archetype Options API Routes

Provides a static endpoint to retrieve valid options for Typologie, Konstruktionstyp, and Energieklasse.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

# Static options for archetype construction flow
TYPOLOGIES = [
    {"code": "SFH", "label": "Single Family Home", "description": "Einfamilienhaus"},
    {
        "code": "MFH",
        "label": "Multi Family Home",
        "description": "Mehrfamilienhaus mit 3 bis 11 Wohneinheiten, oft kompakt",
    },
    {
        "code": "ABL",
        "label": "Wohnblock",
        "description": "Mehrgeschoßige, großvolumige Wohnbauten ab 11 Wohneinheiten",
    },
    {
        "code": "EDU",
        "label": "Bildungseinrichtung",
        "description": "Schulen, Universitäten etc.",
    },
    {
        "code": "HEA",
        "label": "Gesundheitsgebäude",
        "description": "Krankenhäuser, Arztpraxen",
    },
    {
        "code": "HOR",
        "label": "Hotel und Restaurant",
        "description": "Gastgewerbliche Nutzung",
    },
    {"code": "OFF", "label": "Bürogebäude", "description": "Büroimmobilien"},
    {
        "code": "OTH",
        "label": "Sonstige Nicht-Wohngebäude",
        "description": "Alle sonstigen Sonderbauten (z. B. Kirchen, Hallen)",
    },
    {
        "code": "TRA",
        "label": "Gewerbe (Trade)",
        "description": "Handel, Verkaufsflächen",
    },
]

KONSTRUKTIONSTYPEN = [
    {"code": 1, "label": "Ziegel"},
    {"code": 1, "label": "Stahl"},
    {"code": 2, "label": "Betonbau"},
    {"code": 3, "label": "Holz"},
]

ENERGIEKLASSEN = [
    {"code": 1, "label": "Energieklasse 1"},
    {"code": 2, "label": "Energieklasse 2"},
    {"code": 3, "label": "Energieklasse 3"},
]


@router.get("/api/archetype_options", response_class=JSONResponse)
async def get_archetype_options():
    """
    Get valid options for Typologie, Konstruktionstyp, and Energieklasse.

    Returns:
        dict: Dictionary containing lists of valid options for each category.
    """
    # No authentication required; returns static data for frontend dropdowns.
    return {
        "typologie": TYPOLOGIES,
        "konstruktionstyp": KONSTRUKTIONSTYPEN,
        "energieklasse": ENERGIEKLASSEN,
    }
