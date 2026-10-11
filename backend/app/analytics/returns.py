
def calculate_simple_return(
    previous_price: float,
    current_price: float,
) -> float:
    """Calculate the simple return between two prices."""
    if previous_price <= 0 or current_price <= 0:
        raise ValueError("Prices must be positive")

    return (current_price / previous_price) - 1
