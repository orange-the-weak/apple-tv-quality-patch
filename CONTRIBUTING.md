# Contributing

[简体中文](CONTRIBUTING.zh-CN.md)

Start with [compatibility](docs/compatibility.md) and [architecture](docs/architecture.md). This preview deliberately supports one original app version. Describe the device, app version, profile and expected behavior before proposing support for another version.

## Development

Use Python 3.10+, Node 20+ and JDK 17+. Run `bash scripts/test.sh` from the checkout root. `ATV_TEST_APK` may point to a legally obtained original base APK for local native-event integration tests; CI does not receive this proprietary fixture and reports the skip. Run `python3 -m atvpatch doctor --sdk "$ANDROID_SDK_ROOT"` before Android builds.

Keep changes scoped to a reproducible problem. Update English and Chinese user documentation, focused tests and the changelog together. Use the [adapter guide](docs/adapting.md) for new app versions. Never relax hash or anchor checks to make an unknown version pass. Separate platform defaults from opt-in device profiles.

## Evidence and privacy

Use synthetic fixtures. Do not commit vendor APKs, decompiled vendor code, media, keys, account details, subscription URLs, signed playback URLs or raw device logs. Review even sanitized logs before sharing. Include a short reproduction and relevant counters rather than a full capture. Screenshots must be your own and redact personal data.

For runtime changes, record the physical device, Android/app versions, profile, quality, HDR/audio output and navigation behavior. A passing source test is not proof of device playback or DRM compatibility. Keep tests short; longer sessions should have a reason and a stop condition.

Maintainers review behavior, compatibility, privacy and rollback before accepting a change. See [security reporting](SECURITY.md) and the [code of conduct](CODE_OF_CONDUCT.md).
