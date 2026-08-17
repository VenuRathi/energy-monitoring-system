import unittest
from unittest.mock import patch

from app.api import server as api_server
from app.api.service import _demo_hourly_energy_history


class HourlyEnergyHistoryTests(unittest.TestCase):
    def test_demo_history_returns_ordered_72_hour_energy_points(self) -> None:
        points = _demo_hourly_energy_history("MTR-DEMO-001", 72)

        self.assertEqual(len(points), 72)
        self.assertLess(points[0]["hour"], points[-1]["hour"])
        self.assertEqual(
            set(points[0]),
            {"hour", "activeEnergy", "reactiveEnergy", "apparentEnergy"},
        )
        self.assertIsInstance(points[0]["activeEnergy"], float)

    def test_demo_history_caps_requested_hours_and_handles_unknown_meter(self) -> None:
        self.assertEqual(len(_demo_hourly_energy_history("MTR-DEMO-001", 120)), 72)
        self.assertEqual(_demo_hourly_energy_history("MTR-UNKNOWN", 72), [])

    def test_demo_history_route_returns_expected_payload(self) -> None:
        with patch("app.api.service._demo_mode_enabled", return_value=True):
            response = api_server.app.test_client().get("/api/meters/MTR-DEMO-001/hourly-energy?hours=72")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(len(payload), 72)
        self.assertEqual(set(payload[0]), {"hour", "activeEnergy", "reactiveEnergy", "apparentEnergy"})


if __name__ == "__main__":
    unittest.main()
