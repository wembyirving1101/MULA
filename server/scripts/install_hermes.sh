#!/usr/bin/env bash
set -euo pipefail

backend_dir="$(cd "$(dirname "$0")/.." && pwd)"
source_dir="$backend_dir/../.runtime/hermes-source"
profile_dir="$backend_dir/../.runtime/hermes"
revision="$(cat "$backend_dir/hermes/revision.txt")"

if [ ! -e "$source_dir" ]; then
  mkdir -p "$source_dir"
  git -C "$source_dir" init --quiet
  git -C "$source_dir" remote add origin https://github.com/NousResearch/hermes-agent.git
fi

if [ ! -d "$source_dir/.git" ]; then
  echo "Unexpected Hermes source directory; existing files were preserved." >&2
  exit 1
fi
case "$(git -C "$source_dir" remote get-url origin)" in
  https://github.com/NousResearch/hermes-agent.git|https://github.com/nousresearch/hermes-agent.git) ;;
  *) echo "Unexpected Hermes origin; existing files were preserved." >&2; exit 1 ;;
esac

# An interrupted first fetch leaves a valid empty repository. Resume it without
# resetting or overwriting an existing checkout.
if ! git -C "$source_dir" rev-parse --verify HEAD >/dev/null 2>&1; then
  git -C "$source_dir" fetch --depth 1 origin "$revision"
  git -C "$source_dir" checkout --detach FETCH_HEAD
fi

if [ "$(git -C "$source_dir" rev-parse HEAD)" != "$revision" ]; then
  echo "Hermes checkout differs from the pinned revision; existing files were preserved." >&2
  exit 1
fi

# Use upstream's locked dependency installer, without publishing a global
# launcher, changing shell profiles, installing a browser, or starting services.
python3 "$backend_dir/scripts/apply_hermes_profile.py"
bash "$source_dir/scripts/install.sh" --stage python-deps \
  --dir "$source_dir" --hermes-home "$profile_dir" \
  --skip-browser --skip-computer-use --non-interactive
