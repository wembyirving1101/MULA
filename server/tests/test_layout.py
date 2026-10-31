"""Protect persistent-state paths and the public HTTP boundary during moves."""
from pathlib import Path
import unittest

from src.common.paths import PROJECT_ROOT
from src.main import app


class LayoutTests(unittest.TestCase):
    def test_persistent_state_stays_at_repository_root(self):
        self.assertEqual(PROJECT_ROOT, Path(__file__).resolve().parents[2])
        self.assertTrue((PROJECT_ROOT / "run.sh").is_file())

    def test_feature_routers_keep_existing_public_endpoints(self):
        # OpenAPI expands included feature routers, including lazy routers in
        # newer FastAPI versions; app.routes may contain router placeholders.
        routes = {(path, method.upper()) for path, operations in app.openapi()["paths"].items()
                  for method in operations}
        expected = {
            ("/health", "GET"), ("/ready", "GET"),
            ("/api/auth/signup", "POST"), ("/api/auth/login", "POST"),
            ("/api/auth/logout", "POST"), ("/api/auth/me", "GET"),
            ("/api/conversation", "GET"),
            ("/api/agents/operator/chat", "POST"), ("/api/speech", "POST"),
        }
        self.assertTrue(expected.issubset(routes))
