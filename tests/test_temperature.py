"""Tests for Cielo Home temperature helpers."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest


_MODULE_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "cielo_home"
    / "temperature.py"
)
_SPEC = spec_from_file_location("cielo_home_temperature", _MODULE_PATH)
assert _SPEC and _SPEC.loader
_MODULE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
quantize_temperature = _MODULE.quantize_temperature


class QuantizeTemperatureTests(unittest.TestCase):
    """Test appliance-grid temperature quantization."""

    def test_fractional_fahrenheit_rounds_to_even_grid(self) -> None:
        """A HomeKit-converted 71.6 F request should become 72 F, not 71 F."""
        self.assertEqual(quantize_temperature(71.6, 64, 88, 2), 72)

    def test_rounds_to_nearest_supported_value(self) -> None:
        """Requests should use the closest value anchored at the minimum."""
        self.assertEqual(quantize_temperature(72.9, 64, 88, 2), 72)
        self.assertEqual(quantize_temperature(73.1, 64, 88, 2), 74)

    def test_midpoint_rounds_up(self) -> None:
        """An exact midpoint should use conventional half-up rounding."""
        self.assertEqual(quantize_temperature(73, 64, 88, 2), 74)

    def test_clamps_to_supported_range(self) -> None:
        """Requests outside the appliance range should be clamped."""
        self.assertEqual(quantize_temperature(60, 64, 88, 2), 64)
        self.assertEqual(quantize_temperature(90, 64, 88, 2), 88)

    def test_supports_celsius_grid(self) -> None:
        """The helper should work for a one-degree Celsius appliance grid."""
        self.assertEqual(quantize_temperature(22.2, 16, 30, 1), 22)

    def test_nonpositive_step_only_clamps(self) -> None:
        """An invalid step should not cause division by zero."""
        self.assertEqual(quantize_temperature(71.6, 64, 88, 0), 71.6)


if __name__ == "__main__":
    unittest.main()
