"""
This module centralizes the refurbishment logic based on element types and component IDs.
"""

REFURBISHMENT_RULES = {
    "External walls": {
        "add": {"REN_01_a", "REN_01_b"},
    },
    "Ground floor": {
        "add": {"REN_02_a", "REN_02_b"},
    },
    "Attic floor": {
        "add": {"REN_03_a", "REN_03_b", "REN_04_a", "REN_04_b"},
    },
    "Roof": {
        "add": {"REN_03_a", "REN_03_b"},
        "half-exchange": {"REN_07_a", "REN_07_b"},
        "exchange": {"REN_05_a", "REN_05_b", "REN_06_a", "REN_06_b"},
    },
    "Windows": {
        "exchange": {
            "Win_01_a",
            "Win_01_p",
            "Win_01_m",
            "Win_01_w",
            "Win_02_a",
            "Win_02_p",
            "Win_02_m",
            "Win_02_w",
        },
    },
    "Doors": {
        "exchange": {"Doo_01_r", "Doo_02_r", "Doo_03_r", "Doo_04_r", "Doo_05_r"},
    },
}


def get_refurbishment_action(element_type: str, component_id: str) -> str | None:
    """
    Determines the refurbishment action based on the element type and component ID.

    Args:
        element_type: The type of the building element.
        component_id: The ID of the refurbishment component.

    Returns:
        The refurbishment action as a string ("add", "exchange", "half-exchange").
        Defaults to "add" if no specific rule is found.
    """
    if element_type in REFURBISHMENT_RULES:
        rules_for_element = REFURBISHMENT_RULES[element_type]
        for action, component_ids in rules_for_element.items():
            if component_id in component_ids:
                return action

    return None
