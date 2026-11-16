import unittest

from custom_components.cielo_home.cielohomedevice import CieloHomeDevice


class GetActionTest(unittest.TestCase):
    def test_swing_is_optional(self):
        latest_action = {
            "power": "on",
            "mode": "cool",
            "fanspeed": "auto",
            "temp": "21",
            "light": "off",
        }
        device = object.__new__(CieloHomeDevice)
        device._device = {"latestAction": latest_action}

        action = device._get_action()
        self.assertNotIn("swing", action)
        self.assertEqual(action["swinginternal"], "")

        latest_action["swing"] = "pos3"
        action = device._get_action()
        self.assertEqual(action["swing"], "pos3")


if __name__ == "__main__":
    unittest.main()
