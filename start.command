#!/bin/zsh
set -euo pipefail
APP="$HOME/Applications/Jev Amazing.app"
if [[ ! -d "$APP" ]]; then
  print "Run ./setup.command first."; exit 1
fi
exec open "$APP"
