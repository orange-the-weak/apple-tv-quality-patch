[Back to project](../README.md) | [简体中文](quickstart.zh-CN.md)

## Requirements

Run from a source checkout; installation as a PyPI package is not supported. Requirements: Python 3.10+, Node.js 20+ (JavaScript checks and tests), JDK 17+, Android SDK Platform 34, Build Tools 34.0.0, and ADB.

Local source and Android builds were checked on macOS. Linux/macOS source CI and Linux HUD build CI are configured but have not run remotely; Linux execution and Windows remain unverified.

```sh
export ANDROID_SDK_ROOT=/path/to/android-sdk
export JAVA_HOME=/path/to/jdk-17
export PATH="$JAVA_HOME/bin:$ANDROID_SDK_ROOT/platform-tools:$PATH"
# If sdkmanager is available:
sdkmanager 'platforms;android-34' 'build-tools;34.0.0' 'platform-tools'
```

Run `python3 -m atvpatch doctor` to check tools without changing the machine. Then run `python3 -m atvpatch inspect --input input` before building. Add `--sdk` to inspect APK manifests as well.

## 1. Prepare original APKs and a signing key

Put the complete original APK set in `input/`, or pull it from a device running the **official, unmodified** app. Already patched APKs are rejected.

For network ADB, enable debugging on the TV, run `adb connect TV_IP:5555`, and approve the connection on the TV. For USB, use the serial shown by `adb devices`. The device tool accepts `--port` for a custom ADB server port.

```sh
python3 scripts/device.py --serial TV_IP:5555 pull --output input
mkdir -p keys
# This prompts for a password. Keep the key private and out of Git.
keytool -genkeypair -keystore keys/local.p12 -storetype PKCS12 \
  -alias local -keyalg RSA -keysize 2048 -validity 10000 \
  -dname 'CN=Local TV Quality Patch'
# Set ATV_KEYSTORE_PASSWORD in your terminal to that password.
# Do not put it in source files.
```

## 2. Build the patch and HUD

```sh
python3 -m atvpatch patch --input input --output build/apks \
  --keystore keys/local.p12
python3 -m atvpatch hud --output build/hud --keystore keys/local.p12
```

Output directories must be empty. Use a new directory for each experiment to retain rollback artifacts. Optional flags: `--no-prefetch` disables prefetching; `--no-reclaim` disables played-video buffer reclamation. Reclamation retains roughly 12 seconds behind the playhead; seeking further back may require downloading again. Its independent benefit has not been established.

`--video-buffer-mib N` optionally raises only the video SourceBuffer budget to at least N MiB (16–256); the default `0` preserves platform limits and never lowers a larger native budget. Audio limits are unchanged. The tested Sony profile uses `--video-buffer-mib 128` after diagnostics showed pressure against its 80-MiB video pool. This increases the configured video ceiling by 48 MiB on that TV; measure total process memory and keep rollback artifacts. A 60-second target does not guarantee 60 seconds fit in the byte budget.

All supplied APK splits are re-signed together. The build verifies the version, original asset SHA-256 hashes, unique patch anchors, JavaScript syntax, ZIP alignment, signatures, and unchanged DEX/native payloads. Three player assets are version-pinned: the worker, adopted HLS, and PlayerPage. `verification.json` records hashes and feature flags, never passwords or keys.

## 3. Install and enable

**A locally signed build cannot update the official app because the signatures differ. First migration usually requires manually uninstalling the official app and signing in again. Uninstalling clears app data. This project never uninstalls automatically.** Save the original APKs and confirm you can sign in before migrating. Builds signed with the same local key can update each other; changing keys also prevents an in-place update.

```sh
python3 scripts/device.py --serial TV_IP:5555 install --input build/apks
python3 scripts/device.py --serial TV_IP:5555 hud --apk build/hud/PlaybackPanel.apk
```

Enable **Playback Info Panel** in the TV's accessibility settings. After granting log permissions, disable and re-enable the accessibility service to restart its process; hiding the HUD is insufficient. After enabling or updating the service, return to the home screen, then open Apple TV so it receives a foreground-window event. The automatic HUD also requires a live, topmost player-page heartbeat and native controls visibility. It hides when the controls/page disappear or the bridge becomes stale; manually opened 123 mode remains a separate toggle. OS restrictions may prevent log reading or key observation on some devices.

The HUD uses an accessibility overlay. `DUMP` reads system media diagnostics, `READ_LOGS` reads player diagnostic markers, and `INTERNET` receives local loopback metrics. It does not click, inject keys, or read window text. Loopback input is not authenticated. See [Privacy and logging](privacy.md).

## Logs and rollback

```sh
python3 scripts/device.py --serial TV_IP:5555 logs --output diagnostic-logs
```

This exports logs for later offline analysis. `adb shell dumpsys activity service local.tv.playbackpanel/.PanelService metrics` also exposes a lightweight live snapshot with low/high watermarks, configured limits, HLS-tracked byte estimates, quota history, and behind-buffer duration. Observed peak bytes and quota history are not current-limit measurements by themselves. Recording pauses while the TV or service is stopped. Cleanup runs during writes or exports; segment age is based on its last modification time. Exporting during rotation may duplicate or omit a few records; deduplicate by timestamp and content. Zero-filled or partial records no longer abort export; recoverable records are retained and skipped lines are reported.

To restore an older local build, run `install` against its saved output directory, using APKs signed with the **same key**. Returning to the official app requires manually uninstalling the local build, installing the saved complete official set, and signing in again; data preservation is not guaranteed. Disable the accessibility service to stop the HUD and logging. The project neither restores nor impersonates Apple's original signature.


Run all commands from the checkout root. `--profile sony-x75j` explicitly selects the tested 128-MiB profile; the default `platform` profile preserves native budgets. An explicit `--video-buffer-mib` overrides the profile. Installation remains a separate command; preflight never changes a device.
