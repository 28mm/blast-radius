import unittest
from unittest.mock import patch

from blastradius.handlers.dot import DotGraph
from blastradius.server import server

CYCLIC_DOT = """\
digraph {
    "[root] aws_instance.a" [label = "aws_instance.a"]
    "[root] aws_instance.b" [label = "aws_instance.b"]
    "[root] aws_instance.isolated" [label = "aws_instance.isolated"]
    "[root] aws_instance.a" -> "[root] aws_instance.b"
    "[root] aws_instance.b" -> "[root] aws_instance.a"
}
"""


class GraphPruningTests(unittest.TestCase):
    def test_center_is_cycle_safe(self):
        graph = DotGraph("", file_contents=CYCLIC_DOT)

        graph.center(graph.get_node_by_name("[root] aws_instance.a"))

        self.assertEqual(
            {node.label for node in graph.nodes},
            {
                "[root] aws_instance.a",
                "[root] aws_instance.b",
            },
        )
        self.assertEqual(len(graph.edges), 2)

    def test_center_preserves_an_isolated_selected_node(self):
        graph = DotGraph("", file_contents=CYCLIC_DOT)

        graph.center(graph.get_node_by_name("[root] aws_instance.isolated"))

        self.assertEqual(
            [node.label for node in graph.nodes],
            ["[root] aws_instance.isolated"],
        )
        self.assertEqual(graph.edges, [])

    @patch.object(server.DotGraph, "svg", return_value="<svg></svg>")
    def test_api_prunes_the_submitted_dot_source(self, _svg):
        response = server.app.test_client().post(
            "/api/graphs/render",
            json={
                "dot": CYCLIC_DOT,
                "refocus": "[root] aws_instance.a",
            },
        )

        self.assertEqual(response.status_code, 200)
        graph = response.get_json()["graph"]
        self.assertEqual(
            {node["label"] for node in graph["nodes"]},
            {
                "[root] aws_instance.a",
                "[root] aws_instance.b",
            },
        )
        self.assertEqual(len(graph["edges"]), 2)

    @patch.object(server.DotGraph, "svg", return_value="<svg></svg>")
    def test_api_preserves_isolated_selected_node(self, _svg):
        response = server.app.test_client().post(
            "/api/graphs/render",
            json={
                "dot": CYCLIC_DOT,
                "refocus": "[root] aws_instance.isolated",
            },
        )

        self.assertEqual(response.status_code, 200)
        graph = response.get_json()["graph"]
        self.assertEqual(
            [node["label"] for node in graph["nodes"]],
            ["[root] aws_instance.isolated"],
        )
        self.assertEqual(graph["edges"], [])


if __name__ == "__main__":
    unittest.main()
