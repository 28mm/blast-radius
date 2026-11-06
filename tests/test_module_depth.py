import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from blastradius.handlers.dot import DotGraph, DotNode


ROOT = Path(__file__).resolve().parents[1]
GRAPH = """\
digraph {
    "[root] aws_vpc.root" -> "[root] module.child.aws_instance.one"
    "[root] aws_vpc.root" -> "[root] module.sibling.aws_instance.three"
    "[root] module.child.aws_instance.one" -> "[root] module.child.module.grandchild.aws_instance.two"
    "[root] module.child.aws_instance.one" -> "[root] module.sibling.aws_instance.three"
}
"""


class ModuleAddressTests(unittest.TestCase):
    def test_module_names_exclude_resource_address_segments(self):
        cases = {
            "[root] aws_vpc.root": ("root", ["root"]),
            "[root] module.child.aws_instance.one": (
                "module.child",
                ["child"],
            ),
            "[root] module.child.module.grandchild.aws_instance.two": (
                "module.child.module.grandchild",
                ["child", "grandchild"],
            ),
            "[root] module.child (close)": ("module.child", ["child"]),
            '[root] module.child["a.b"].aws_instance.one': (
                'module.child["a.b"]',
                ['child["a.b"]'],
            ),
        }

        for label, (module, modules) in cases.items():
            with self.subTest(label=label):
                self.assertEqual(DotNode._module(label), module)
                self.assertEqual(DotNode._label_to_modules(label), modules)


class ModuleDepthTests(unittest.TestCase):
    def make_graph(self, depth):
        graph = DotGraph("", file_contents=GRAPH)
        graph.set_module_depth(depth)
        return graph

    def test_depth_zero_collapses_each_top_level_module_once(self):
        graph = self.make_graph(0)

        self.assertEqual(
            [node.modules for node in graph.nodes if node.collapsed],
            [["child"], ["sibling"]],
        )
        self.assertEqual(len({node.label for node in graph.nodes}), len(graph.nodes))
        self.assertEqual(
            {(edge.source, edge.target) for edge in graph.edges},
            {
                ("[root] aws_vpc.root", "[root] module.child.collapsed.etc"),
                ("[root] aws_vpc.root", "[root] module.sibling.collapsed.etc"),
                (
                    "[root] module.child.collapsed.etc",
                    "[root] module.sibling.collapsed.etc",
                ),
            },
        )

    def test_depth_one_preserves_top_level_resources(self):
        graph = self.make_graph(1)

        self.assertEqual(
            [node.modules for node in graph.nodes if node.collapsed],
            [["child", "grandchild"]],
        )
        self.assertEqual(
            {(edge.source, edge.target) for edge in graph.edges},
            {
                (
                    "[root] aws_vpc.root",
                    "[root] module.child.aws_instance.one",
                ),
                (
                    "[root] aws_vpc.root",
                    "[root] module.sibling.aws_instance.three",
                ),
                (
                    "[root] module.child.aws_instance.one",
                    "[root] module.child.module.grandchild.collapsed.etc",
                ),
                (
                    "[root] module.child.aws_instance.one",
                    "[root] module.sibling.aws_instance.three",
                ),
            },
        )

    def test_cli_applies_module_depth_to_json_output(self):
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT)

        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "bin" / "blast-radius"),
                    "--json",
                    "--module-depth",
                    "0",
                ],
                input=GRAPH,
                text=True,
                capture_output=True,
                check=True,
                cwd=directory,
                env=environment,
            )

        payload = json.loads(result.stdout)
        collapsed = [node["modules"] for node in payload["nodes"] if node["type"] == "collapsed"]
        self.assertEqual(collapsed, [["child"], ["sibling"]])
        self.assertEqual(len(payload["edges"]), 3)


if __name__ == "__main__":
    unittest.main()
