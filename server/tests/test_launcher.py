import importlib.util
import unittest
from unittest.mock import patch

from src.common.paths import PROJECT_ROOT

spec = importlib.util.spec_from_file_location("mula_launcher", PROJECT_ROOT / "scripts/run.py")
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


class LauncherTests(unittest.TestCase):
    def test_stopped_server_can_be_started(self):
        with patch.object(launcher, "responds", return_value=False):
            self.assertFalse(launcher.server_ready())

    def test_old_server_is_not_silently_reused(self):
        with patch.object(launcher, "responds", side_effect=[True, False]):
            with self.assertRaisesRegex(RuntimeError, "older or incompatible server"):
                launcher.server_ready()

    def test_current_server_is_reused_without_generating_audio(self):
        with patch.object(launcher, "responds", return_value=True) as responds:
            self.assertTrue(launcher.server_ready())
        self.assertEqual(responds.call_args_list[1].args, ("http://127.0.0.1:8000/api/speech",))
        self.assertEqual(responds.call_args_list[1].kwargs, {"statuses": (405,)})
