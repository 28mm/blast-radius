import subprocess
import unittest
from unittest.mock import patch

from blastradius.server import server


class DiagnosticsTests(unittest.TestCase):
    def test_python_version_uses_the_running_interpreter(self):
        with patch.object(server.platform, "python_version", return_value="3.14.0"):
            with patch.object(server.subprocess, "run") as run:
                self.assertEqual(server.get_python_version(), "3.14.0")

        run.assert_not_called()

    def test_missing_terraform_is_reported_without_spawning_a_process(self):
        with patch.object(server, "which", return_value=None):
            with patch.object(server.subprocess, "run") as run:
                help_info = server.get_help()

        self.assertEqual(help_info["tf_version"], "Not installed")
        self.assertEqual(help_info["tf_exe"], "Not installed")
        run.assert_not_called()

    def test_windows_terraform_path_is_used_for_version_diagnostics(self):
        terraform_path = r"C:\Program Files\Terraform\terraform.exe"
        completed = subprocess.CompletedProcess(
            [terraform_path, "--version"],
            0,
            stdout=b"Terraform v1.15.8\r\n",
            stderr=b"",
        )

        def find_executable(name):
            if name == "terraform.exe":
                return terraform_path
            return None

        with patch.object(server, "which", side_effect=find_executable):
            with patch.object(server.subprocess, "run", return_value=completed) as run:
                help_info = server.get_help()

        self.assertEqual(help_info["tf_version"], "v1.15.8")
        self.assertEqual(help_info["tf_exe"], terraform_path)
        run.assert_called_once_with(
            [terraform_path, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def test_dot_only_project_renders_without_terraform_configuration(self):
        def find_executable(name):
            if name in {"dot", "dot.exe"}:
                return r"C:\Program Files\Graphviz\bin\dot.exe"
            return None

        with server.app.test_client() as client:
            with patch.object(server, "which", side_effect=find_executable):
                with patch.object(server.subprocess, "run") as run:
                    response = client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Blast Radius", response.data)
        self.assertIn(b"Not installed", response.data)
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
