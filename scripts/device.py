"""Explicit device commands; never uninstall apps or alter accessibility settings."""
import argparse
import gzip
import json
import os
from pathlib import Path
import subprocess
import time

PACKAGE = "com.apple.atve.androidtv.appletv"
PANEL = "local.tv.playbackpanel"


def retain(folder, now=None):
    now = time.time() if now is None else now
    total = 0
    for path in sorted(folder.glob("playback-*.jsonl.gz"), key=lambda p: p.stat().st_mtime, reverse=True):
        size = path.stat().st_size
        if now - path.stat().st_mtime > 7 * 86400 or total + size > 64 * 1024 * 1024:
            path.unlink()
        else:
            total += size


def parse_diagnostic_dump(text):
    """Recover complete records from partial or zero-filled segment exports."""
    rows, skipped, active = [], 0, False
    for line in text.splitlines():
        line = line.strip()
        if line == "BEGIN_PLAYBACK_JSONL": active = True
        elif line == "END_PLAYBACK_JSONL": active = False
        elif active:
            clean = line.replace("\x00", "").strip()
            try:
                row = json.loads(clean)
            except ValueError:
                skipped += 1
                continue
            if isinstance(row, dict) and row.get("type") in {"runtime", "parallel", "sample", "quality"} and isinstance(row.get("data"), dict):
                rows.append(row)
            else:
                skipped += 1
    return rows, skipped


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adb", default="adb")
    parser.add_argument("--port", default="5037")
    parser.add_argument("--serial", required=True, help="ADB device serial or IP:port")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("pull"); p.add_argument("--output", required=True)
    p = sub.add_parser("install"); p.add_argument("--input", required=True)
    p = sub.add_parser("hud"); p.add_argument("--apk", required=True)
    p = sub.add_parser("logs"); p.add_argument("--output", default="diagnostic-logs")
    args = parser.parse_args()
    adb = [args.adb, "-P", args.port, "-s", args.serial]
    def call(*command, timeout=30):
        return subprocess.run(adb + list(command), check=True, text=True, capture_output=True, timeout=timeout).stdout
    if args.command == "pull":
        output = Path(args.output); output.mkdir(parents=True, exist_ok=True)
        if any(output.iterdir()):
            parser.error("Pull output must be empty")
        paths = [line.removeprefix("package:").strip() for line in call("shell", "pm", "path", PACKAGE).splitlines() if line.startswith("package:")]
        if not paths or len({Path(p).name for p in paths}) != len(paths):
            parser.error("No valid APK paths")
        for path in paths:
            call("pull", path, str(output / Path(path).name), timeout=120)
        print("Pulled", len(paths), "APK(s); the patcher will verify supported assets")
    elif args.command == "install":
        folder = Path(args.input)
        manifest = json.loads((folder / "verification.json").read_text())
        import hashlib
        files = []
        for row in manifest["files"]:
            name = row["file"]
            if Path(name).name != name or not name.endswith(".apk"):
                parser.error("Invalid APK filename")
            file = folder / name
            if hashlib.sha256(file.read_bytes()).hexdigest() != row["sha256"]:
                parser.error("APK hash mismatch")
            files.append(str(file))
        if not files:
            parser.error("No verified APKs")
        print(call("install-multiple", "-r", "--no-incremental", *files, timeout=180).strip())
    elif args.command == "hud":
        print(call("install", "-r", "--no-incremental", args.apk, timeout=120).strip())
        call("shell", "pm", "grant", PANEL, "android.permission.DUMP")
        call("shell", "pm", "grant", PANEL, "android.permission.READ_LOGS")
        print("Permissions granted. Disable/re-enable Playback Info Panel in TV accessibility settings to restart its process; UP remains passed through.")
    else:
        folder = Path(args.output); folder.mkdir(parents=True, exist_ok=True); retain(folder)
        rows = []; size = 0
        for index in range(7, -1, -1):
            text = call("shell", "dumpsys", "activity", "service", PANEL + "/.PanelService", "logs", str(index), timeout=12)
            parsed, skipped = parse_diagnostic_dump(text)
            if skipped:
                print(f"Skipped {skipped} malformed diagnostic line(s) in segment {index}")
            for row in parsed:
                encoded = json.dumps(row, separators=(",", ":")) + "\n"
                size += len(encoded.encode())
                if size > 9 * 1024 * 1024:
                    raise RuntimeError("Export exceeded size bound")
                rows.append(encoded)
        if not rows:
            parser.error("No stored diagnostics; check accessibility service")
        file = folder / ("playback-" + time.strftime("%Y%m%d-%H%M%S") + "-" + str(time.time_ns() % 1000000) + ".jsonl.gz")
        temp = file.with_suffix(file.suffix + ".partial")
        try:
            with gzip.open(temp, "wt", encoding="utf-8") as out:
                out.writelines(rows)
            temp.replace(file)
        finally:
            temp.unlink(missing_ok=True)
        retain(folder)
        print("Saved", len(rows), "records:", file)


if __name__ == "__main__":
    main()
