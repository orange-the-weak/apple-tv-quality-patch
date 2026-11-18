# Changelog

## 0.2.0 — 2026-11-18

- Fixed pending UP requests leaking into another playback page: ordered UI snapshots, lifecycle-bound requests, and cancellation on exit, hide, manual toggle or stale heartbeat. Added regression coverage for delayed keys, expiry and same-page controls.
- Source-first preview: bilingual homepage, read-only preflight, versioned adapter modules and explicit device profiles.
- Reproducible source packaging, HUD build checks, draft release CI and community templates.
- Eight feature combinations preserve the pre-refactor patched assets byte-for-byte; no new device compatibility claim.


English | [简体中文](CHANGELOG.zh-CN.md)

## 0.1.4 — 2026-11-16

- Fill toward the normal high watermark while paused instead of stopping at the low threshold; preserve explicit stop-streaming behavior.
- Add optional, validated video-only buffer budget configuration (`--video-buffer-mib`, default platform limits) and use 128 MiB on the tested Sony after observing pressure at 80 MiB. Audio remains unchanged.
- Record read-only watermarks, configured byte budgets, HLS-tracked occupancy/peaks, quota history, and behind-buffer duration; add a lightweight `metrics` diagnostic dump.
- Preserve highest-quality selection, two-video-request operation, remote handling, HUD behavior, and bounded log retention.

## 0.1.3 — 2026-11-15

- Restore native directional hold handling inside both player handlers when Android reader mode is active; the platform otherwise explicitly disables this path and falls back to ten-second skips.
- Preserve screen-reader state, focus navigation, short skips, and the 0.1.2 quality/HUD/logging changes.
- Add an optional integration test that executes both actual patched native handlers with reader mode enabled and native longpress support disabled. Vendor method fixtures are generated temporarily from a user-supplied APK and are never shipped.
- Physical Sony remote verification: the user confirmed that held fast-forward works again.

## 0.1.2 — 2026-11-15

- Restore the 123 manual toggle. Gate automatic UP activation on the actual player page and follow native controls visibility instead of an eight-second timer.
- Preserve the native longpress timer across repeat DOWN events in both directional seek handlers.
- Select the target as the manifest becomes ready and restore it after normal playback resumes from trickplay, using the existing seamless switch path.
- Add target/selected bitrate diagnostics and recover complete records from zero-filled/partial exports.
- Pin and patch PlayerPage in addition to the worker and adopted HLS. Keep DEX/native binaries unchanged.

## 0.1.1 — 2026-11-13

- Make English the default project documentation, retaining complete Simplified Chinese documentation and language links.
- Localize the HUD, app label, and accessibility description through Android resources: English by default, Chinese for Chinese system locales.
- Generate resource IDs during HUD builds and check translation coverage and formatting arguments.
- Preserve quality selection, prefetch, UP passthrough, log schemas, and retention limits.

## 0.1.0 — 2026-11-13

- Extract the version/asset-hash-pinned 14.3.1 patcher from the local workflow.
- Preserve highest-variant selection, the manual-mode abort guard, and one-ahead video prefetch; allow disabling prefetch and reclamation.
- Show the HUD with standard UP observation and eight-second hiding. The Sony X75J physical remote was confirmed to show the HUD without breaking original navigation.
- Include bounded local logging, explicit export, source-release tooling, and source tests.
- Exclude original/patched vendor APKs, player bundles, signing keys, and device logs from source releases.
