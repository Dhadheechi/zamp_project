import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.data.presets import PRESETS

class TestVendorOnboarding(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_root_html(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("zamp", response.text.lower())
        self.assertIn("Live Stage Execution Pipeline", response.text)

    def test_api_presets(self):
        response = self.client.get("/api/presets")
        self.assertEqual(response.status_code, 200)
        presets = response.json()
        self.assertGreaterEqual(len(presets), 4)

    def test_api_evaluate_happy_path(self):
        payload = PRESETS["happy_path"]["data"]
        response = self.client.post("/api/evaluate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["decision"]["status"], "APPROVED")
        self.assertLess(data["decision"]["risk_score"], 25)
        self.assertEqual(len(data["decision"]["stages"]), 3)
        self.assertIsNone(data["decision"]["vendor_communication"])

    def test_api_evaluate_name_mismatch(self):
        payload = PRESETS["name_mismatch"]["data"]
        response = self.client.post("/api/evaluate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["decision"]["status"], "REJECTED")
        self.assertGreaterEqual(data["decision"]["risk_score"], 70)
        self.assertIsNotNone(data["decision"]["vendor_communication"])

    def test_api_evaluate_tax_mismatch(self):
        payload = PRESETS["tax_country_mismatch"]["data"]
        response = self.client.post("/api/evaluate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["decision"]["status"], "PENDING_ACTION")
        self.assertIsNotNone(data["decision"]["vendor_communication"])
        self.assertTrue(any("tax identifier" in a.lower() for a in data["decision"]["vendor_communication"]["action_items"]))

    def test_metrics_and_history(self):
        res = self.client.get("/api/metrics")
        self.assertEqual(res.status_code, 200)
        metrics = res.json()
        self.assertGreaterEqual(metrics["total_runs"], 3)

        hist_res = self.client.get("/api/history")
        self.assertEqual(hist_res.status_code, 200)
        history = hist_res.json()
        self.assertGreaterEqual(len(history), 3)

if __name__ == "__main__":
    unittest.main()
