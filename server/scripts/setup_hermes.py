"""Create a dedicated local Hermes home and matching backend credentials."""

import os
from pathlib import Path
import secrets


BACKEND = Path(__file__).resolve().parents[1]
RUNTIME_HOME = BACKEND.parent / ".runtime" / "hermes"


def write_private(path: Path, content: str) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as file:
        file.write(content)


def main() -> None:
    backend_env = BACKEND / ".env.hermes"
    gateway_env = RUNTIME_HOME / ".env"
    config = RUNTIME_HOME / "config.yaml"
    if any(path.exists() for path in (backend_env, gateway_env, config)):
        raise SystemExit(
            "Hermes configuration already exists. Existing files were preserved. "
            "See server/README.md to start or edit this profile."
        )
    RUNTIME_HOME.mkdir(parents=True, exist_ok=True, mode=0o700)
    key = secrets.token_urlsafe(32)
    write_private(backend_env, (
        "HERMES_BASE_URL=http://127.0.0.1:8642\n"
        f"HERMES_API_KEY={key}\n"
        "HERMES_MODEL=hermes-agent\n"
        "HERMES_TIMEOUT_SECONDS=120\n"
    ))
    write_private(gateway_env, (
        "API_SERVER_ENABLED=true\n"
        f"API_SERVER_KEY={key}\n"
        "API_SERVER_HOST=127.0.0.1\n"
        "API_SERVER_PORT=8642\n"
    ))
    write_private(config, (BACKEND / "hermes" / "config.yaml").read_text(encoding="utf-8"))
    print("Created the private Hermes profile and server/.env.hermes; no credentials were printed.")


if __name__ == "__main__":
    main()
