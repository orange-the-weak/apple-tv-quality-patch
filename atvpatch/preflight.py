"""Read-only preflight. No network requests, installs, signing, or device changes."""
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from zipfile import ZipFile, BadZipFile
from .patches import ADAPTER, patch_assets


def executable(name):
    home = os.environ.get("JAVA_HOME") if name in {"java", "javac", "keytool"} else None
    return str(Path(home) / "bin" / name) if home else shutil.which(name)


def version(name, args):
    command = executable(name)
    if not command:
        return None
    try:
        result = subprocess.run([command, *args], capture_output=True, text=True, timeout=10)
        if result.returncode: return None
        return (result.stdout + result.stderr).strip().splitlines()[0]
    except (OSError, subprocess.SubprocessError):
        return None


def doctor(args):
    checks = []
    def add(name, ok, detail, remedy):
        checks.append({"name": name, "ok": bool(ok), "detail": detail, "remedy": "" if ok else remedy})
    add("python", sys.version_info >= (3,10), sys.version.split()[0], "Use Python 3.10 or newer")
    for tool, flag, minimum in [("node","--version",20),("javac","-version",17),("java","-version",17)]:
        text = version(tool,[flag]); match = re.search(r'(?:^v|javac |version ")(\d+)', text or '')
        add(tool, match and int(match.group(1)) >= minimum, text or "unavailable", f"Install {tool} {minimum}+; check PATH/JAVA_HOME")
    add("keytool", executable("keytool") and Path(executable("keytool")).is_file(), "available" if executable("keytool") else "unavailable", "Install JDK 17 and set JAVA_HOME")
    sdk_value = args.sdk or os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
    sdk = Path(sdk_value) if sdk_value else None
    for name in ["aapt","d8","zipalign","apksigner","core-lambda-stubs.jar"]:
        relative = Path("build-tools") / args.build_tools / name
        add("sdk:"+name, sdk and (sdk / relative).is_file(), relative.as_posix(), "Install SDK build-tools;"+args.build_tools)
    add("sdk:platform", sdk and (sdk / "platforms/android-34/android.jar").is_file(), "platforms/android-34/android.jar", "Install SDK platforms;android-34")
    adb = shutil.which("adb") or (str(sdk / "platform-tools/adb") if sdk else None)
    add("adb", adb and Path(adb).is_file(), "available" if adb and Path(adb).is_file() else "unavailable", "Install platform-tools and add it to PATH")
    ok = all(check["ok"] for check in checks)
    return {"ok":ok,"summary":"Environment ready" if ok else "Environment incomplete; nothing was changed", "checks":checks, "messages":[("OK " if c["ok"] else "MISSING ")+c["name"]+": "+(c["detail"] if c["ok"] else c["remedy"]) for c in checks]}


def inspect_input(args):
    source = Path(args.input)
    paths = sorted(source.glob("*.apk")) if source.is_dir() else [source]
    bases = []; files = []
    try:
        if not paths: raise ValueError("No APKs found; provide the complete original APK directory")
        for path in paths:
            with ZipFile(path) as apk:
                if "assets/app.zip" in apk.namelist(): bases.append(path)
            files.append({"file":path.name,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
        if len(bases) != 1: raise ValueError("Expected exactly one base APK with assets/app.zip")
        with ZipFile(bases[0]) as apk, ZipFile(BytesIO(apk.read("assets/app.zip"))) as assets:
            patch_assets(assets)  # Checks all hashes and unique transformation anchors; writes nothing.
        sdk_value = args.sdk or os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
        aapt = Path(sdk_value) / "build-tools" / args.build_tools / "aapt" if sdk_value else None
        verified = bool(aapt and aapt.is_file())
        if verified:
            for path in paths:
                result = subprocess.run([str(aapt),"dump","badging",str(path)],check=True,capture_output=True,text=True,timeout=15)
                first = result.stdout.splitlines()[0]
                if "name='"+ADAPTER["package"]+"'" not in first or "versionCode='"+ADAPTER["version_code"]+"'" not in first:
                    raise ValueError("Unsupported package/version in APK set")
        messages = ["Original asset hashes and all patch anchors match.", "Manifest package/version checked for supplied APKs." if verified else "Manifest not checked: provide --sdk for aapt validation. Build always checks manifests.", "Split completeness, device ABI and account authorization still require installation/device validation."]
        return {"ok":True,"summary":"Supported assets verified", "adapter":ADAPTER["id"],"manifest_verified":verified,"files":files,"transforms":ADAPTER["transforms"],"messages":messages}
    except (OSError, ValueError, KeyError, IndexError, BadZipFile, subprocess.SubprocessError):
        return {"ok":False,"summary":"Input is unsupported, incomplete, unreadable, or already patched", "messages":["Use unmodified Apple TV Android TV 14.3.1 (143100) with matching assets. See docs/compatibility.md."]}
