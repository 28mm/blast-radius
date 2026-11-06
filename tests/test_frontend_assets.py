import unittest
from pathlib import Path

from blastradius.server import server


class FrontendAssetTests(unittest.TestCase):
    def test_dot_input_uses_api_and_reports_inline_errors(self):
        javascript = (
            Path(server.__file__).parent / "static" / "js" / "blast-radius.js"
        ).read_text(encoding="utf-8")

        self.assertIn('fetch("/api/graphs/render"', javascript)
        self.assertIn("showGraphMessage", javascript)
        self.assertNotIn('confirm("Invalid graph detected!', javascript)


if __name__ == "__main__":
    unittest.main()
