import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INIT_SCRIPT = ROOT / "docker-terraform-init.sh"


@unittest.skipIf(os.name == "nt", "the container initialization script is POSIX shell")
class DockerTerraformInitTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        self.log = self.root / "terraform.log"

        mock_bin = self.root / "bin"
        mock_bin.mkdir()
        terraform = mock_bin / "terraform"
        terraform.write_text(
            '#!/bin/sh\nprintf "%s\\n" "$*" >> "$MOCK_TERRAFORM_LOG"\n',
            encoding="utf-8",
        )
        terraform.chmod(0o755)

        self.environment = os.environ.copy()
        self.environment["PATH"] = (
            str(mock_bin) + os.pathsep + self.environment["PATH"]
        )
        self.environment["MOCK_TERRAFORM_LOG"] = str(self.log)
        for name in (
            "BLAST_RADIUS_TERRAFORM_INIT",
            "CHDIR",
            "TF_DATA_DIR",
        ):
            self.environment.pop(name, None)

    def run_init(self, **environment):
        process_environment = self.environment.copy()
        process_environment.update(environment)
        return subprocess.run(
            ["/bin/sh", str(INIT_SCRIPT), str(self.workspace)],
            text=True,
            capture_output=True,
            check=False,
            env=process_environment,
        )

    def terraform_calls(self):
        if not self.log.exists():
            return []
        return self.log.read_text(encoding="utf-8").splitlines()

    def add_configuration(self, directory=None):
        config_dir = directory or self.workspace
        (config_dir / "main.tf").write_text(
            'resource "terraform_data" "example" {}\n',
            encoding="utf-8",
        )

    def test_auto_initializes_an_uncached_configuration(self):
        self.add_configuration()

        result = self.run_init()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.terraform_calls(),
            [
                f"-chdir={self.workspace} init -backend=false -input=false",
            ],
        )
        self.assertNotIn("terraform get", result.stdout)

    def test_auto_reuses_a_nonempty_private_module_cache(self):
        self.add_configuration()
        cached_module = self.workspace / ".terraform" / "modules" / "private"
        cached_module.mkdir(parents=True)
        (cached_module / "main.tf").write_text("", encoding="utf-8")

        result = self.run_init()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.terraform_calls(), [])
        self.assertIn("cached Terraform data exists", result.stdout)

    def test_auto_skips_dot_only_startup(self):
        result = self.run_init()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.terraform_calls(), [])
        self.assertIn("no .tf files were found", result.stdout)

    def test_auto_respects_chdir_and_relative_tf_data_dir(self):
        config_dir = self.workspace / "stacks" / "application"
        config_dir.mkdir(parents=True)
        self.add_configuration(config_dir)
        cache_dir = config_dir / ".tfdata"
        cache_dir.mkdir()
        (cache_dir / "environment").write_text("default", encoding="utf-8")

        result = self.run_init(
            CHDIR="stacks/application",
            TF_DATA_DIR=".tfdata",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.terraform_calls(), [])
        self.assertIn(str(cache_dir), result.stdout)

    def test_explicit_always_and_never_modes(self):
        with self.subTest(mode="always"):
            result = self.run_init(BLAST_RADIUS_TERRAFORM_INIT="always")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                self.terraform_calls(),
                [
                    f"-chdir={self.workspace} init -backend=false -input=false",
                ],
            )

        self.log.unlink()
        self.add_configuration()
        with self.subTest(mode="never"):
            result = self.run_init(BLAST_RADIUS_TERRAFORM_INIT="never")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(self.terraform_calls(), [])
            self.assertIn("BLAST_RADIUS_TERRAFORM_INIT=never", result.stdout)

    def test_invalid_mode_fails_with_a_clear_error(self):
        result = self.run_init(BLAST_RADIUS_TERRAFORM_INIT="sometimes")

        self.assertEqual(result.returncode, 64)
        self.assertEqual(self.terraform_calls(), [])
        self.assertIn("expected auto, always, or never", result.stderr)

    def test_missing_chdir_fails_before_running_terraform(self):
        result = self.run_init(CHDIR="missing")

        self.assertEqual(result.returncode, 66)
        self.assertEqual(self.terraform_calls(), [])
        self.assertIn("does not exist", result.stderr)


if __name__ == "__main__":
    unittest.main()
