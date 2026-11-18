"""Local-only build CLI. All proprietary input and signed output stay outside source."""
import argparse
from io import BytesIO
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from zipfile import ZipFile
from .patches import PatchError, patch_assets, ADAPTER
from . import __version__, __version_code__
from .core import validate_video_budget
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ADAPTER["package"]


def run(args, **kwargs):
    return subprocess.run([str(a) for a in args], check=True, timeout=180, **kwargs)


def rewrite(data, replacements):
    out = BytesIO()
    with ZipFile(BytesIO(data)) as src, ZipFile(out, "w") as dst:
        for item in src.infolist():
            name = item.filename.upper()
            if name.startswith("META-INF/") and name.endswith((".SF", ".RSA", ".DSA", ".EC", "/MANIFEST.MF")):
                continue
            dst.writestr(item, replacements.get(item.filename, src.read(item.filename)))
    return out.getvalue()


def toolchain(args):
    value = args.sdk or os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
    if not value:
        raise ValueError("Set ANDROID_SDK_ROOT or --sdk")
    sdk = Path(value).resolve()
    tools = sdk / "build-tools" / args.build_tools
    for name in ("aapt", "d8", "zipalign", "apksigner"):
        if not (tools / name).is_file():
            raise ValueError("Missing SDK tool: " + str(tools / name))
    return sdk, tools


def signing(args):
    key = Path(args.keystore).resolve()
    if not key.is_file():
        raise ValueError("Keystore missing; generate your own key as described in README")
    if not os.environ.get(args.password_env):
        raise ValueError("Set keystore password environment variable: " + args.password_env)
    return key


def sign(tools, key, args, source, output, work):
    aligned = work / (source.name + ".aligned")
    run([tools / "zipalign", "-p", "-f", "4", source, aligned])
    command = [tools / "apksigner", "sign", "--ks", key, "--ks-pass", "env:" + args.password_env, "--out", output, aligned]
    run(command)
    run([tools / "apksigner", "verify", output], capture_output=True)
    run([tools / "zipalign", "-c", "-p", "4", output], capture_output=True)


def target_dir(args):
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise ValueError("Output directory must be empty (use a new directory)")
    return out


def patch_apks(args):
    profile = json.loads((ROOT / "atvpatch/profiles" / (args.profile + ".json")).read_text())
    args.video_buffer_mib = validate_video_budget(profile["video_buffer_mib"] if args.video_buffer_mib is None else args.video_buffer_mib)
    _, tools = toolchain(args)
    key = signing(args)
    source = Path(args.input).resolve()
    out = target_dir(args)
    if out == source or source in out.parents or out in source.parents:
        raise ValueError("Input and output must be separate non-nested directories")
    files = sorted(source.glob("*.apk"))
    if not files:
        raise ValueError("No APKs in input directory")
    bases = []
    for path in files:
        badging = run([tools / "aapt", "dump", "badging", path], capture_output=True, text=True).stdout.splitlines()[0]
        if not re.search(r"package: name='" + re.escape(PACKAGE) + r"'", badging) or ("versionCode='" + ADAPTER["version_code"] + "'") not in badging:
            raise PatchError("Unsupported package/version; run python3 -m atvpatch inspect --input INPUT")
        with ZipFile(path) as apk:
            if "assets/app.zip" in apk.namelist():
                bases.append(path)
    if len(bases) != 1:
        raise PatchError("Expected exactly one base APK containing assets/app.zip")
    base = bases[0]
    with ZipFile(base) as apk:
        original = apk.read("assets/app.zip")
    with ZipFile(BytesIO(original)) as assets:
        patched = patch_assets(assets, prefetch=not args.no_prefetch, reclaim_video=not args.no_reclaim, video_buffer_mib=args.video_buffer_mib)
    patched_zip = rewrite(original, patched)
    with ZipFile(BytesIO(original)) as before, ZipFile(BytesIO(patched_zip)) as after:
        changed = [n for n in before.namelist() if before.read(n) != after.read(n)]
        if sorted(changed) != sorted(patched):
            raise PatchError("Unexpected asset changes")
    records = []
    with tempfile.TemporaryDirectory(prefix="atv-build-") as folder:
        work = Path(folder)
        for name, data in patched.items():
            script = work / name
            script.write_bytes(data)
            run(["node", "--check", script], capture_output=True)
        for path in files:
            unsigned = work / ("unsigned-" + path.name)
            signed = work / path.name
            unsigned.write_bytes(rewrite(path.read_bytes(), {"assets/app.zip": patched_zip} if path == base else {}))
            sign(tools, key, args, unsigned, signed, work)
            with ZipFile(path) as before, ZipFile(signed) as after:
                for name in before.namelist():
                    if name.endswith(".dex") or name.startswith("lib/"):
                        if before.read(name) != after.read(name):
                            raise PatchError("DEX/native payload changed")
            records.append({"file": path.name, "input_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "sha256": hashlib.sha256(signed.read_bytes()).hexdigest()})
        for path in files:
            shutil.copyfile(work / path.name, out / path.name)
    manifest = {"project_version": __version__, "apple_tv_version": ADAPTER["version"], "adapter": ADAPTER["id"], "profile": args.profile, "changed_assets": changed, "prefetch": not args.no_prefetch, "reclaim_video": not args.no_reclaim, "video_buffer_mib": args.video_buffer_mib, "files": records}
    (out / "verification.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("Built and verified", len(records), "APK(s):", out)


def build_hud(args):
    sdk, tools = toolchain(args)
    key = signing(args)
    out = target_dir(args)
    platform = sdk / "platforms/android-34/android.jar"
    if not platform.is_file():
        raise ValueError("Install SDK platforms;android-34")
    javac = Path(os.environ["JAVA_HOME"]) / "bin/javac" if os.environ.get("JAVA_HOME") else "javac"
    with tempfile.TemporaryDirectory(prefix="atv-hud-") as folder:
        work = Path(folder)
        classes, dex, generated = work / "classes", work / "dex", work / "generated"
        classes.mkdir(); dex.mkdir(); generated.mkdir()
        unsigned, signed = work / "hud-unsigned.apk", work / "PlaybackPanel.apk"
        ET.register_namespace("android", "http://schemas.android.com/apk/res/android")
        manifest = ET.parse(ROOT / "hud/AndroidManifest.xml")
        manifest.getroot().set("{http://schemas.android.com/apk/res/android}versionName", __version__)
        manifest.getroot().set("{http://schemas.android.com/apk/res/android}versionCode", str(__version_code__))
        generated_manifest = work / "AndroidManifest.xml"
        manifest.write(generated_manifest, encoding="utf-8", xml_declaration=True)
        run([tools / "aapt", "package", "-f", "-m", "-J", generated, "-M", generated_manifest, "-S", ROOT / "hud/res", "-I", platform, "-F", unsigned])
        sources = sorted((ROOT / "hud/src").rglob("*.java")) + sorted(generated.rglob("*.java"))
        run([javac, "-source", "8", "-target", "8", "-bootclasspath", str(platform) + os.pathsep + str(tools / "core-lambda-stubs.jar"), "-d", classes, *sources])
        run([tools / "d8", "--lib", platform, "--output", dex, *sorted(classes.rglob("*.class"))])
        run([tools / "aapt", "add", unsigned, "classes.dex"], cwd=dex)
        sign(tools, key, args, unsigned, signed, work)
        shutil.copyfile(signed, out / signed.name)
    print("Built and verified HUD:", out / "PlaybackPanel.apk")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("patch", "hud"):
        p = sub.add_parser(name)
        p.add_argument("--sdk")
        p.add_argument("--build-tools", default="34.0.0")
        p.add_argument("--keystore", required=True)
        p.add_argument("--password-env", default="ATV_KEYSTORE_PASSWORD")
        p.add_argument("--output", required=True)
        if name == "patch":
            p.add_argument("--input", required=True)
            p.add_argument("--no-prefetch", action="store_true")
            p.add_argument("--no-reclaim", action="store_true")
            p.add_argument("--profile", choices=["platform", "sony-x75j"], default="platform")
            p.add_argument("--video-buffer-mib", type=int, default=None, help="Raise only the video SourceBuffer budget; 0 keeps the platform default, otherwise 16..256 MiB")
    from .preflight import doctor, inspect_input
    p = sub.add_parser("doctor", help="Read-only environment checks; installs nothing")
    p.add_argument("--sdk"); p.add_argument("--build-tools", default="34.0.0")
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("inspect", help="Read-only asset/anchor validation; no signing or output APK")
    p.add_argument("--input", required=True); p.add_argument("--json", action="store_true")
    p.add_argument("--sdk"); p.add_argument("--build-tools", default="34.0.0")
    args = parser.parse_args()
    try:
        if args.command in {"doctor", "inspect"}:
            result = doctor(args) if args.command == "doctor" else inspect_input(args)
            print(json.dumps(result, indent=2) if args.json else result["summary"] + "\n" + "\n".join(result.get("messages", [])))
            if not result["ok"]: parser.exit(1)
        else:
            (patch_apks if args.command == "patch" else build_hud)(args)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        parser.exit(1, "Build failed: " + str(error) + "\n")


if __name__ == "__main__":
    main()
