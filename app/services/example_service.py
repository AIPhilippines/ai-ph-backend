from typing import Dict, Any

def get_hello_world(number: int) -> Dict[str, str]:
    
    return {"message": f"Naibog ko sa akong crush. Iyang favorite number kay {number}."}

def compute_flames(name_1: str, name_2: str) -> dict[str, Any]:
    set_name_1 = set(name_1)
    set_name_2 = set(name_2)

    different_letters = set_name_1.difference(set_name_2)
    int_diff = len(different_letters)

    """
    F - Friends
    L - Love
    A - Affection
    M - Marriage
    E - Enemies
    S - Sweethearts
    """

    if int_diff%6 == 0:
        return {"result": "Sweethearts"}
    elif int_diff%6 == 1:
        return {"result": "Friends"}
    elif int_diff%6 == 2:
        return {"result": "Love"}
    elif int_diff%6 == 3:
        return {"result": "Affection"}
    elif int_diff%6 == 4:
        return {"result": "Marriage"}
    elif int_diff%6 == 5:
        return {"result": "Enemies"}
