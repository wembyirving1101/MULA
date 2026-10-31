"""Behavior checks for the scoped context exception, including tool protection."""
import ast
from pathlib import Path
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

from scripts.apply_hermes_profile import SOURCE


class ContextProfileTests(unittest.TestCase):
    def test_only_configured_tool_free_operator_can_use_smaller_context(self):
        source = SOURCE / "agent/agent_init.py"
        if not source.exists():
            self.skipTest("Pinned Hermes source is not installed")
        tree = ast.parse(source.read_text(encoding="utf-8"))
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_enforce_minimum_context")
        namespace = {"MINIMUM_CONTEXT_LENGTH": 64000}
        config_module = ModuleType("hermes_cli.config")
        config_module.load_config = lambda: {"agent": {"mula_compact_operator": True}}
        package = ModuleType("hermes_cli")
        with patch.dict("sys.modules", {"hermes_cli": package, "hermes_cli.config": config_module}):
            exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), "exec"), namespace)
            guard = namespace["_enforce_minimum_context"]
            agent = SimpleNamespace(
                platform="api_server", model="huihui_ai/qwen3-abliterated:latest", tools=[],
                context_compressor=SimpleNamespace(context_length=40960),
                _ollama_num_ctx=40960, base_url="", provider="custom", _config_context_length=40960,
            )
            guard(agent)
            for attribute, value in [("tools", ["terminal"]), ("platform", "cli"), ("model", "different-model")]:
                old = getattr(agent, attribute)
                setattr(agent, attribute, value)
                with self.subTest(attribute=attribute), self.assertRaises(ValueError):
                    guard(agent)
                setattr(agent, attribute, old)
            config_module.load_config = lambda: {"agent": {}}
            with self.assertRaises(ValueError):
                guard(agent)
