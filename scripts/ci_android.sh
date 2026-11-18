#!/usr/bin/env bash
# Compile/sign/verify our own HUD using a disposable key; never distribute this APK.
set -euo pipefail
cd "$(dirname "$0")/.."
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
export ATV_CI_PASSWORD
ATV_CI_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_hex(24))')
keytool -genkeypair -noprompt -alias ci -keyalg RSA -keysize 2048 -validity 1   -storetype PKCS12 -keystore "$work/ci.p12" -storepass:env ATV_CI_PASSWORD   -keypass:env ATV_CI_PASSWORD -dname 'CN=Disposable CI Build'
python3 -m atvpatch hud --keystore "$work/ci.p12" --password-env ATV_CI_PASSWORD --output "$work/hud"
python3 - "$work/hud/PlaybackPanel.apk" <<'PYCODE'
import os, subprocess, sys
from pathlib import Path
from atvpatch import __version__, __version_code__
sdk=Path(os.environ.get('ANDROID_SDK_ROOT') or os.environ['ANDROID_HOME'])
data=subprocess.check_output([str(sdk/'build-tools/34.0.0/aapt'),'dump','badging',sys.argv[1]],text=True)
assert "versionCode='"+str(__version_code__)+"'" in data
assert "versionName='"+__version__+"'" in data
print('HUD compiled, signed, aligned and version verified; disposable artifact is not distributed')
PYCODE
python3 scripts/release.py
archive=$(python3 -c 'from atvpatch import __version__;print("dist/apple-tv-quality-patch-"+__version__+"-source.zip")')
python3 scripts/verify_release.py "$archive"
python3 - "$archive" "$work" <<'PYCODE'
import sys, zipfile
with zipfile.ZipFile(sys.argv[1]) as archive: archive.extractall(sys.argv[2])
PYCODE
source_root=$(python3 -c 'from atvpatch import __version__;print("apple-tv-quality-patch-"+__version__)')
(cd "$work/$source_root" && unset ATV_TEST_APK && bash scripts/test.sh)
