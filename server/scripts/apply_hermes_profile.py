"""Apply the version-checked, tool-free Mula context exception to pinned Hermes."""
from pathlib import Path
import subprocess

BACKEND = Path(__file__).resolve().parents[1]
SOURCE = BACKEND.parent / ".runtime" / "hermes-source"
ANCHOR = 'def _enforce_minimum_context(agent):\n'
REPLACEMENT = '''def _enforce_minimum_context(agent):
    # Mula's explicitly configured chat-only Operator has no tool schema budget.
    # Keep upstream's guard for other profiles, models, platforms and all tools.
    from hermes_cli.config import load_config
    compact_operator = (load_config().get("agent") or {}).get("mula_compact_operator") is True
    context = getattr(agent.context_compressor, "context_length", 0)
    if (
        compact_operator
        and agent.platform == "api_server"
        and agent.model == "huihui_ai/qwen3-abliterated:latest"
        and not agent.tools
        and isinstance(context, int)
        and 8192 <= context <= 40960
    ):
        return
'''


def main():
    expected = (BACKEND / "hermes/revision.txt").read_text(encoding="utf-8").strip()
    actual = subprocess.check_output(["git", "-C", str(SOURCE), "rev-parse", "HEAD"], text=True).strip()
    if actual != expected:
        raise SystemExit("Hermes revision differs; context patch was not applied.")
    path = SOURCE / "agent/agent_init.py"
    text = path.read_text(encoding="utf-8")
    pristine = subprocess.check_output(
        ["git", "-C", str(SOURCE), "show", "HEAD:agent/agent_init.py"], text=True
    )
    if pristine.count(ANCHOR) != 1:
        raise SystemExit("Hermes context guard changed; review the patch before applying.")
    patched = pristine.replace(ANCHOR, REPLACEMENT, 1)
    if text == patched:
        return
    if text != pristine:
        raise SystemExit("Hermes init file has other edits; existing changes were preserved.")
    path.write_text(patched, encoding="utf-8")
    print("Applied the tool-free Mula Operator context profile.")


if __name__ == "__main__":
    main()
