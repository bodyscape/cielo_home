"""Temperature helpers for the Cielo Home integration."""

from math import floor


def quantize_temperature(
    temperature: float,
    minimum: float,
    maximum: float,
    step: float,
) -> float:
    """Clamp a temperature and round it to the appliance's supported grid."""
    clamped = min(max(temperature, minimum), maximum)
    if step <= 0:
        return clamped

    steps_from_minimum = floor(((clamped - minimum) / step) + 0.5)
    quantized = minimum + steps_from_minimum * step
    return min(max(quantized, minimum), maximum)
