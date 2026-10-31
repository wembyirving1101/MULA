"""Start the local Mula stack and stop only the processes this launcher owns."""
import argparse
from contextlib import ExitStack
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import webbrowser

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / ".runtime" / "logs"


def responds(url, statuses=(200,), headers=None):
    try:
        with urlopen(Request(url, headers=headers or {}), timeout=2) as response:
            return response.status in statuses
    except HTTPError as error:
        return error.code in statuses
    except (URLError, TimeoutError, OSError):
        return False


def stop_children(children):
    for name, process in reversed(children):
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
    deadline = time.monotonic() + 8
    for name, process in reversed(children):
        remaining = max(0, deadline - time.monotonic())
        try:
            process.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()


def launch(name, command, cwd, ready, stack, children, timeout=90):
    if ready():
        print(f"{name} is already running.", flush=True)
        return
    log_path = LOGS / f"{name.lower()}.log"
    log = stack.enter_context(log_path.open("w", encoding="utf-8"))
    process = subprocess.Popen(command, cwd=cwd, stdout=log, stderr=subprocess.STDOUT,
                               start_new_session=True)
    children.append((name, process))
    print(f"Starting {name}…", flush=True)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"{name} stopped during startup. See {log_path}")
        if ready():
            print(f"{name} is ready.", flush=True)
            return
        time.sleep(0.5)
    raise RuntimeError(f"{name} did not become ready. See {log_path}")


def main():
    parser = argparse.ArgumentParser(description="Run Mula with one command.")
    parser.add_argument("--no-open", action="store_true", help="Do not open a browser")
    args = parser.parse_args()
    env_file = ROOT / "server/.env.hermes"
    required = [env_file, ROOT / "server/.venv/bin/python",
                ROOT / ".runtime/hermes-source/.hermes/bin/hermes",
                ROOT / "client/node_modules/next/dist/bin/next"]
    for path in required:
        if not path.exists():
            raise RuntimeError(f"Setup is missing: {path}. Follow server/README.md first.")
    for executable in ("node", "ollama"):
        if shutil.which(executable) is None:
            raise RuntimeError(f"{executable} is not available in this Terminal's PATH.")
    settings = dict(dotenv_values(env_file))
    settings.update(os.environ)
    hermes = (settings.get("HERMES_BASE_URL") or "http://127.0.0.1:8642").rstrip("/")
    key = settings.get("HERMES_API_KEY")
    if not key:
        raise RuntimeError("Hermes API key is missing. Follow server/README.md.")
    headers = {"Authorization": f"Bearer {key}"}
    LOGS.mkdir(parents=True, exist_ok=True)
    children = []
    try:
        with ExitStack() as stack:
            launch("Ollama", ["ollama", "serve"], ROOT,
                   lambda: responds("http://127.0.0.1:11434/api/tags"), stack, children)
            launch("Hermes", ["bash", str(ROOT / "server/scripts/start_hermes.sh")], ROOT,
                   lambda: responds(f"{hermes}/v1/capabilities", headers=headers), stack, children)
            launch("Server", [str(ROOT / "server/.venv/bin/python"), "-m", "uvicorn", "src.main:app",
                   "--host", "127.0.0.1", "--port", "8000", "--env-file", str(env_file)],
                   ROOT / "server", lambda: responds("http://127.0.0.1:8000/health")
                   and responds("http://127.0.0.1:8000/api/auth/me", statuses=(401,)), stack, children)
            launch("Client", ["node", str(ROOT / "client/node_modules/next/dist/bin/next"),
                   "dev", "--hostname", "127.0.0.1", "--port", "3000"], ROOT / "client",
                   lambda: responds("http://127.0.0.1:3000/") and
                   responds("http://127.0.0.1:3000/api/auth/me", statuses=(401,)), stack, children)
            print("\nMula is ready: http://127.0.0.1:3000\nPress Ctrl+C to stop services started by this command.", flush=True)
            if not args.no_open:
                webbrowser.open("http://127.0.0.1:3000")
            while True:
                for name, process in children:
                    if process.poll() is not None:
                        raise RuntimeError(f"{name} stopped. See {LOGS / (name.lower() + '.log')}")
                time.sleep(1)
    finally:
        stop_children(children)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    try:
        main()
    except KeyboardInterrupt:
        print("\nMula stopped.")
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
