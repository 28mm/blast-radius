import io
import unittest
from unittest.mock import patch

from blastradius.server import server

ROOTLESS_DOT = """\
digraph {
    "[root] aws_vpc.main" [label = "aws_vpc.main"]
    "[root] aws_instance.web" [label = "aws_instance.web"]
    "[root] aws_instance.web" -> "[root] aws_vpc.main"
}
"""


class RenderApiTests(unittest.TestCase):
    def setUp(self):
        self.client = server.app.test_client()

    @patch.object(server.DotGraph, "svg", return_value="<svg id='graph0'></svg>")
    def test_renders_modern_terraform_graph_without_synthetic_root(self, _svg):
        response = self.client.post(
            "/api/graphs/render",
            json={"dot": ROOTLESS_DOT},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["svg"], "<svg id='graph0'></svg>")
        self.assertEqual(payload["warnings"], [])
        self.assertEqual(len(payload["graph"]["nodes"]), 2)
        self.assertEqual(len(payload["graph"]["edges"]), 1)
        self.assertNotIn(
            "[root] root",
            {node["label"] for node in payload["graph"]["nodes"]},
        )

    @patch.object(server.DotGraph, "svg", return_value="<svg></svg>")
    def test_legacy_input_and_upload_routes_remain_compatible(self, _svg):
        input_response = self.client.post("/input", data={"input": ROOTLESS_DOT})
        upload_response = self.client.post(
            "/upload",
            data={"file": (io.BytesIO(ROOTLESS_DOT.encode()), "graph.dot")},
            content_type="multipart/form-data",
        )

        for response in (input_response, upload_response):
            with self.subTest(path=response.request.path):
                self.assertEqual(response.status_code, 200)
                payload = response.get_json()
                self.assertIn("SVG", payload)
                self.assertIn("JSON", payload)

    def test_rejects_non_json_and_missing_dot_requests(self):
        not_json = self.client.post(
            "/api/graphs/render",
            data="not json",
            content_type="text/plain",
        )
        missing_dot = self.client.post("/api/graphs/render", json={})

        self.assertEqual(not_json.status_code, 400)
        self.assertEqual(
            not_json.get_json()["error"]["code"],
            "invalid_request",
        )
        self.assertEqual(missing_dot.status_code, 400)
        self.assertEqual(
            missing_dot.get_json()["error"]["code"],
            "missing_dot",
        )

    def test_rejects_unparseable_and_invalid_options(self):
        unparseable = self.client.post(
            "/api/graphs/render",
            json={"dot": "digraph { this is not a Terraform graph }"},
        )
        invalid_depth = self.client.post(
            "/api/graphs/render",
            json={"dot": ROOTLESS_DOT, "module_depth": -1},
        )

        self.assertEqual(unparseable.status_code, 422)
        self.assertEqual(
            unparseable.get_json()["error"]["code"],
            "invalid_graph",
        )
        self.assertEqual(invalid_depth.status_code, 400)
        self.assertEqual(
            invalid_depth.get_json()["error"]["code"],
            "invalid_module_depth",
        )

    def test_rejects_oversized_dot_documents(self):
        with patch.object(server, "MAX_DOT_BYTES", 32):
            response = self.client.post(
                "/api/graphs/render",
                json={"dot": ROOTLESS_DOT},
            )

        self.assertEqual(response.status_code, 413)
        self.assertEqual(
            response.get_json()["error"]["code"],
            "payload_too_large",
        )

    @patch.object(server.DotGraph, "svg", return_value="<svg></svg>")
    def test_missing_refocus_node_returns_a_warning(self, _svg):
        response = self.client.post(
            "/api/graphs/render",
            json={"dot": ROOTLESS_DOT, "refocus": "missing.resource"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("not found", response.get_json()["warnings"][0])

if __name__ == "__main__":
    unittest.main()
