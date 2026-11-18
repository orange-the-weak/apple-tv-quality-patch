#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m unittest discover -s tests -v
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
javac -d "$work" hud/src/local/tv/playbackpanel/HudKeyPolicy.java tests/HudKeyPolicyTest.java
java -cp "$work" HudKeyPolicyTest

node tests/payloads.test.js

node tests/buffer-metrics.test.js
