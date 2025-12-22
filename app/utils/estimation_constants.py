# app/utils/estimation_constants.py
from typing import Set

EL_TYPE_FOUNDATION = "Foundation"
EL_TYPE_GROUND_FLOOR = "Ground floor"
EL_TYPE_UPPER_FLOORS = "Upper floors"
EL_TYPE_ATTIC_FLOOR = "Attic floor"
EL_TYPE_RETAINING_WALLS = "Retaining walls"
EL_TYPE_ROOF = "Roof"
EL_TYPE_EXTERNAL_WALLS = "External walls"
EL_TYPE_WINDOWS = "Windows"
EL_TYPE_INTERNAL_WALLS_LOAD = "Internal walls, load-bearing"
EL_TYPE_INTERNAL_WALLS_NON_LOAD = "Internal walls, non load-bearing"

HORIZONTAL_ELEMENTS: Set[str] = {
    EL_TYPE_FOUNDATION,
    EL_TYPE_GROUND_FLOOR,
    EL_TYPE_UPPER_FLOORS,
    EL_TYPE_ATTIC_FLOOR,
}
INTERNAL_WALL_ELEMENTS: Set[str] = {
    EL_TYPE_INTERNAL_WALLS_LOAD,
    EL_TYPE_INTERNAL_WALLS_NON_LOAD,
}
AREA_BASED_ELEMENTS: Set[str] = (
    {
        EL_TYPE_FOUNDATION,
        EL_TYPE_GROUND_FLOOR,
        EL_TYPE_UPPER_FLOORS,
        EL_TYPE_ATTIC_FLOOR,
        EL_TYPE_RETAINING_WALLS,
        EL_TYPE_ROOF,
        EL_TYPE_EXTERNAL_WALLS,
        EL_TYPE_WINDOWS,
    }
)
