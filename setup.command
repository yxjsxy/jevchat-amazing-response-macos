#!/bin/zsh
set -euo pipefail
cd "$(dirname "$0")"
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
if [[ "$(uname -m)" != arm64 ]]; then
  print "This build supports Apple Silicon (arm64) only."; exit 1
fi
if ! command -v uv >/dev/null 2>&1; then
  print "Install uv first: https://docs.astral.sh/uv/getting-started/installation/"; exit 1
fi
if ! xcrun --find clang >/dev/null 2>&1; then
  print "Install Xcode Command Line Tools: xcode-select --install"; exit 1
fi
if [[ "${1:-}" == --check ]]; then
  print "Prerequisites available (arm64, uv, clang)."; exit 0
fi
SUPPORT="$HOME/Library/Application Support/Jev Amazing"
RUNTIME="$SUPPORT/venv/bin/python"
umask 077
mkdir -p "$SUPPORT/config"
if [[ ! -e "$SUPPORT/config/env" ]]; then
  cp amazing.env.example "$SUPPORT/config/env"
fi
chmod 700 "$SUPPORT/config"
chmod 600 "$SUPPORT/config/env"
uv venv --python 3.12 --allow-existing "$SUPPORT/venv"
uv pip install --python "$RUNTIME" -r requirements-macos-cloud.txt
"$RUNTIME" packaging/build_amazing.py
"$RUNTIME" packaging/install_amazing.py
print "Installed: $HOME/Applications/Jev Amazing.app"
print "Configure your own keys in: $SUPPORT/config/env"
print "Then open Jev Amazing.app. No keys are printed or bundled."
