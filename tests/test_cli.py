import os
import unittest
from unittest.mock import patch

from blastradius import cli


class CliTests(unittest.TestCase):
    def test_help_exits_successfully(self):
        with self.assertRaises(SystemExit) as raised:
            cli.main(["--help"])

        self.assertEqual(raised.exception.code, 0)

    def test_serve_uses_the_selected_directory_and_address(self):
        with (
            patch.object(cli.os, "chdir") as chdir,
            patch.object(cli.app, "run") as run,
        ):
            cli.main(
                [
                    "--serve",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "5055",
                    os.curdir,
                ]
            )

        chdir.assert_called_once_with(os.curdir)
        run.assert_called_once_with(host="127.0.0.1", port=5055)


if __name__ == "__main__":
    unittest.main()
