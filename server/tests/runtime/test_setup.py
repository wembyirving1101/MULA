import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import setup_hermes


class SetupTests(unittest.TestCase):
    def test_private_matching_credentials_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = Path(directory) / "server"
            profile = Path(directory) / "profile"
            template = backend / "hermes" / "config.yaml"
            template.parent.mkdir(parents=True)
            template.write_text("platform_toolsets:\n  api_server: []\n", encoding="utf-8")
            output = io.StringIO()
            with patch.object(setup_hermes, "BACKEND", backend), patch.object(
                setup_hermes, "RUNTIME_HOME", profile
            ), contextlib.redirect_stdout(output):
                setup_hermes.main()
                backend_file = backend / ".env.hermes"
                gateway_file = profile / ".env"
                before = backend_file.read_text(encoding="utf-8")
                settings = dict(line.split("=", 1) for line in before.splitlines())
                gateway_settings = dict(
                    line.split("=", 1)
                    for line in gateway_file.read_text(encoding="utf-8").splitlines()
                )
                key = settings["HERMES_API_KEY"]
                self.assertGreaterEqual(len(key), 32)
                self.assertEqual(key, gateway_settings["API_SERVER_KEY"])
                self.assertNotIn(key, output.getvalue())
                self.assertEqual(backend_file.stat().st_mode & 0o777, 0o600)
                self.assertEqual(gateway_file.stat().st_mode & 0o777, 0o600)
                with self.assertRaises(SystemExit):
                    setup_hermes.main()
                self.assertEqual(backend_file.read_text(encoding="utf-8"), before)

    def test_existing_partial_setup_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = Path(directory) / "server"
            profile = Path(directory) / "profile"
            profile.mkdir()
            config = profile / "config.yaml"
            config.write_text("existing configuration", encoding="utf-8")
            with patch.object(setup_hermes, "BACKEND", backend), patch.object(
                setup_hermes, "RUNTIME_HOME", profile
            ), self.assertRaises(SystemExit):
                setup_hermes.main()
            self.assertEqual(config.read_text(encoding="utf-8"), "existing configuration")
            self.assertFalse((backend / ".env.hermes").exists())


if __name__ == "__main__":
    unittest.main()
