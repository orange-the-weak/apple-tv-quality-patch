# Architecture and maintenance

English | [简体中文](architecture.zh-CN.md)

`atvpatch/patches.py` contains version-specific byte anchors and original injected code for 14.3.1. Worker, adopted-HLS, and PlayerPage SHA-256 hashes must match. Supporting another version requires a separately checked adapter and device validation; changing a version string or removing hash checks is insufficient.

On the next event-loop turn after playlist initialization, the worker verifies that the player instance and item are unchanged, then calls `hls.ol.setManualMode` and `setEnabledMediaOptionByType`. Selection exceptions release manual mode. Resolution takes priority, followed by bitrate at equal resolution. Bitrates are manifest declarations, not per-frame measurements. Audio filtering remains unchanged. A guarded three-second check restores the target after exiting trickplay, whose native path can choose a lower variant while manual mode remains enabled. Switches use the existing seamless path. Already buffered low-quality segments may play before the higher variant; forced immediate purges were rejected after producing a video-buffer gap on the tested TV. The check skips iframe mode, non-normal rates, seeking, and changed items; matching selections do not trigger repeated buffer switches.

The fragment-abort path respects manual mode, preventing an independent downgrade. This sacrifices normal network-driven downshifting, so stalls can still occur when bandwidth is insufficient.

While loading the current VOD video segment, the media library prefetches the next complete segment. Existing observable caches let playback reuse completed or ongoing requests. There is one additional prefetch slot; segment duration is limited to eight seconds and known byte ranges to 32 MiB. Without a byte range, there is no hard byte-size guarantee. Unused prefetches are canceled on cleanup/request changes; errors return to the original download path. `_localPrefetchOnly` prevents prefetch from replacing the current in-flight range/load state. HTTP, authentication, native decryption, and DRM libraries are not modified.

Played-video reclamation keeps a 12-second backward window, runs at least six seconds apart, and skips seeking/updating. Platform SourceBuffer limits remain unchanged (80 MiB video / 5 MiB audio on the tested TV); prefetch memory is additional. Other platforms may differ. Reclamation's independent benefit is unverified; disable it with `--no-reclaim` for comparison.

Every three seconds, the worker sends bounded JSON to `127.0.0.1:18767`. The receiver limits headers, body size, and read time. Network history retains at most 90 points / 120 seconds. Forward buffers come from combined-buffer and per-track water levels; total `bufferedDuration` includes already-played media and is not forward buffer.

PlayerPage posts topmost playback-page and actual controls visibility to the same loopback receiver via `/ui`. Its one-second heartbeat stops on disposal; covered/removed pages send inactive state. An old page cannot override the current page owner. Standard accessibility foreground events gate the automatic HUD as well. UP only requests it on an active playback page; it follows the native controls callback (including the native 5/8/20-second modes), and hides on page exit or a stale UI heartbeat. No fixed HUD timeout substitutes for the controls timer. 123 remains a separate manually toggled HUD, usable outside playback. Directional key actions always pass through; only the configured 123 keys are consumed.

Two native directional handlers now ignore repeat DOWN events while the same key remains held, so the native one-second longpress timer is not continually restarted. UP still reaches the original short-skip/release behavior. Changing direction cancels the previous pending hold; a stale held state resets after a gap so a lost UP cannot permanently suppress later gestures.

Android string resources provide English by default and Chinese for `zh` locales. App labels, service descriptions, graph labels, status/error messages, and formatted metrics use the same resource system. Protocol identifiers, codec names, and JSON schemas are language-independent. The HUD build generates `R.java` before compilation.

ZIP rewriting changes three player assets. All supplied splits are realigned and signed together. Signature changes may affect installation or integrity checks; future service behavior is not guaranteed.


Version 0.1.3 also handles the Android capability gate: reader mode plus `supportsScreenReaderDirectionalLongPress=false` previously bypassed the hold timer entirely. Only the two player directional handlers enable the native hold branch; global reader state and focus navigation are untouched. Bounded runtime direction diagnostics contain action phase/capability booleans, at most 40 lines per handler, and are not included in the TV rolling-log allowlist.


Version 0.1.4 changes the Gg watermark selector so a paused player uses the normal high watermark; explicit stopStreaming still uses its original stop threshold. Platform byte budgets remain the default. An explicit video_buffer_mib setting raises only the video pool and preserves audio and any larger native budget. Read-only diagnostics separate time targets, HLS-tracked byte estimates/observed peaks, historical quota flags, and configured byte limits. They do not equate a time target with available memory.


## v0.2.0 module boundaries

`atvpatch/patches.py` validates and composes the pinned adapter. The adapter manifest stores identity/hashes, while `adapters/v14_3_1/{player,hls,worker}.py` owns each transformation. `profiles/*.json` contains explicit device policy; `preflight.py` provides read-only checks. The CLI, generated HUD manifest and release archive use `atvpatch/__init__.py` as their version source. See the version adapter and release guides for extension and distribution contracts.
