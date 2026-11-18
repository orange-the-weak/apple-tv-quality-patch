# Validation record

English | [简体中文](validation.zh-CN.md)

Baseline: 2026-11-13, version 0.1.0.

- Local source tests checked unsupported-input rejection, preservation of binary ZIP payloads/removal of old signatures, and UP-event passthrough. JVM tests covered key/action/repeat/foreground/freshness combinations.
- A macOS build used the original Apple TV 14.3.1 set of 20 APK splits. Version and original asset hashes, JavaScript syntax, alignment, signatures, and unchanged DEX/native bytes passed.
- All generated player assets matched the previously working quality/prefetch patch byte-for-byte. The source cleanup did not require reinstalling or repeating long playback tests.
- The HUD compiled with JDK 17 / SDK 34 and was installed on Sony X75J.
- An earlier Dark Matter short test held about 25.02 Mbps in 4K Dolby Vision. Logs showed overlapping segment downloads, 21 completed prefetches, and no fallbacks. End-of-sample forward buffers were 22.5 seconds video / 30.6 seconds audio. Startup audio warnings remained; this does not establish long-term stability.
- Background sample/parallel/runtime recording and export worked with the HUD hidden. Desktop cleanup tests covered size, age, scope, and idempotence. Logs do not establish soundbar-side Atmos reception.
- Foreground window events, HUD display, and eight-second hiding were verified on the TV. The user then confirmed that a physical remote UP press showed the HUD and original navigation worked. ADB injection did not exercise this physical input path; low-level sendevent was denied.
- Optional prefetch/reclamation combinations passed JavaScript syntax checks using local original assets. Source archives use an allowlist and file-hash manifest.

Version 0.1.1 adds English/Chinese resources and documentation.

- Eight Python source tests and the JVM key-policy matrix pass locally. Localization tests verify matching resource keys, nonempty translations, matching typed format arguments, resource references, bilingual document links, and inclusion of both resource sets in the release.
- The localized HUD builds with SDK 34 / JDK 17. Alignment and signature checks pass. APK metadata contains the English default label “Playback Info Panel” and Chinese label “播放信息面板”, with default and `zh` resources.
- Quality/prefetch patches, key policy, log schemas, and retention limits were not changed. The existing physical-remote result applies to the unchanged key-handling behavior; it is not a new language-specific device test.
- English resource rendering on an English-system TV has not been visually tested. A device update was attempted, but ADB reconnection returned “No route to host”; the localized APK was not installed. The TV system language was not changed.

Other TV brands, OS versions, and ABIs remain unverified. Remote CI has not run. Source CI does not test DRM playback or server-side authorization.


## 0.1.2 — 2026-11-15

Existing device APKs and bounded logs were backed up before changes. The exported old logs contained 4,717 recoverable records, including low-bitrate entries with manual mode enabled. Source inspection identified repeated DOWN events restarting the native one-second hold timer and a native post-trickplay path choosing lower variants without clearing manual mode. A zero-filled log record also broke the original exporter.

- Nine Python tests, the JVM key/route/control matrix, and Node payload tests pass. The payload tests exercise held-key timer preservation, direction changes/lost-UP recovery, UI ownership/disposal, early highest-variant selection, post-trickplay restoration, and suppression during seeking, abnormal rates, or item changes.
- Builds validate three pinned assets and unchanged DEX/native payloads. The final Apple TV APK set and localized HUD were installed without uninstalling or changing login/routing.
- A first 60-second experiment with native immediate/user-initiated switching produced video-buffer loss and PTS discontinuity. That path was removed. The final build keeps seamless switching; it does not forcibly purge buffered media.
- A second, same-title 60-second round included a ten-second short skip. Runtime samples held 25.429813 Mbps; the last three samples had forward video buffers 7.35 / 13.36 / 19.93 seconds, with audio reaching 31.71 seconds. Playback positions advanced 123.37 → 145.85 → 160.96 seconds. This is a bounded check, not proof of long-term stability or adverse-network behavior.
- On the paused player, a diagnostic UP request was blocked on the launcher; manual mode toggled independently. On returning to Apple TV, automatic mode was visible while native controls were visible and was hidden when their callback became false. These checks validate the policy/display path, not physical button delivery.
- Hidden/stale display text was found to remain in dumpsys output and could be mistaken for live samples. It now carries age and is omitted when hidden/stale; continuous JSON samples remain the source for playback analysis.
- The final exporter saved 5,249 records without the old zero-filled-record failure. TV retention remains eight 1-MiB segments and seven-day cleanup; desktop export retention remains 64 MiB/seven days.
- Physical 123 and held-direction behavior on this build still await user confirmation. The earlier physical UP/navigation confirmation applied to 0.1.0, not these new behaviors. Remote CI and other TV models remain unverified.


## 0.1.3 — 2026-11-15: physical held-key fix

The user reported that 0.1.2 still performed only short skips. A bounded hardware capture showed a genuine approximately 3.3-second right-key hold, excluding a short physical press. The Android platform override sets `supportsScreenReaderDirectionalLongPress` to false. With reader mode active, both native player handlers therefore bypass their hold timers and use the short-skip compatibility path.

- The 0.1.3 change enables the original hold branch only inside those two player handlers. It does not disable accessibility, modify global reader state, or alter quality/HUD behavior.
- Runtime diagnostics from the physical test contained 40 bounded records with `reader=true` and `nativeLongAllowed=false`. Repeated events had a separate action phase (not repeated DOWN), so timer reset alone did not explain this TV's failure.
- The user then confirmed: “held press has recovered.” This is physical-remote confirmation of the corrected path; no additional source/title endurance test was run.
- Ten local Python tests passed with a user-supplied original APK, including execution of both actual patched native handlers in reader mode with native longpress disabled. Short release, repeated DOWN, and the observed separate-repeat action were covered. The synthetic fixtures were temporary and are not distributed. The source-only CI skips this one vendor-dependent test unless `ATV_TEST_APK` is supplied.
- Player patch build, JavaScript syntax, signatures, alignment, and unchanged DEX/native payload checks passed. The Apple TV patch was installed in place; the unchanged HUD remains at component version 0.1.2.


## 0.1.4 — 2026-11-16: pause fill and video byte budget

The user observed that a paused player stopped downloading around 12.1 seconds despite available concurrency. Source inspection confirmed that the native Gg selector used the low watermark when paused. The corrected selector uses the ordinary high watermark and still respects explicit stopStreaming.

Read-only device counters showed low/high/max targets of 6/54/60 seconds, an 80-MiB configured video pool, a tracked byte peak around 78.8 MiB, and quota history during the current session. After the pause-selector fix alone, paused video reached about 22.28 seconds before capacity pressure. HLS occupancy is an estimate (including proportional partial-segment accounting), and quotaSeen is latched history; the separately reported configured byte limit establishes the budget.

- The device had about 1.09 GiB available before the video-budget experiment. Only the video pool was raised from 80 to 128 MiB using `--video-buffer-mib 128`; audio stayed at 5 MiB. Request concurrency and the selected route were not changed. Highest variant selection remained enabled.
- A cold-start readiness probe timed out after 30 seconds and stopped without repeating or changing title. Once the current title was ready, one bounded 60-second comparison paused for 30 seconds and resumed for 30 seconds.
- The paused video buffer reached 43.41497 seconds; audio reached 46.94231 seconds. During resumed samples, video remained 31.21575–41.71126 seconds and buffering was false throughout. Bitrate stayed 25.367923 Mbps at 3840×1920 Dolby Vision.
- Paused position held at 1988.4063 seconds. The resumed position progressed 1990.1100→2016.9552 across roughly 27 seconds. This is a short check, not a guarantee for all titles or sustained network outages.
- Application PSS was about 290 MiB after the test, versus about 254 MiB in the earlier baseline snapshot. Available system memory remained about 1.05 GiB. These are whole-process/system snapshots, not a claim that every change in PSS is caused by the byte budget.
- There were audio-write warnings during pause/resume transition (605 in the whole window); resumed samples after 36 seconds had none. Warning counts alone were not treated as evidence of playback stalls.
- PlayerPage bytes matched the physically verified 0.1.3 build, preserving the reader-mode hold fix and HUD/remote behavior. Original APKs, source, logs, measurements, and memory snapshots were retained locally for rollback and later analysis.
- Eleven local Python tests (including the optional original-asset integration test), JVM key/route tests, Node payload tests, and read-only metric tests passed. Actual patched native pause and video-allocation expressions were executed; audio budgets and larger native video budgets remained unchanged. Build signatures/alignment and DEX/native payload checks passed.

The open-source default remains the platform video budget (`0`); the 128-MiB setting is an explicit tested device profile. English-system visual verification, remote CI, and other devices remain unverified. Logs remain bounded at 8 MiB/seven days on TV and 64 MiB/seven days per export directory.


## v0.2.0 local release-preparation checks — 2026-11-18

- macOS: Python 3.14.6, Node 24.4.1, JDK 17.0.21, Android SDK platform 34 / build-tools 34.0.0.
- All 16 Python checks passed with a locally supplied original APK, including native seek/reader-mode integration; Java HUD policy and JavaScript payload/buffer suites passed.
- Eight prefetch/reclaim/video-budget combinations match all three pre-refactor asset outputs byte-for-byte.
- Read-only `doctor` passes with the configured JDK/SDK. `inspect` validates original assets/anchors and package/version through aapt. Missing-tool and unsupported-input tests verify actionable refusal without writing input files.
- Five original APK splits were locally patched with the explicit Sony profile, signed and verified; unchanged DEX/native payload checks passed. These local-only artifacts are not distributed or installed by this task.
- Own HUD compiles, signs, aligns and reports version 0.2.0 / 200. The disposable build-test key and HUD artifact are deleted after the smoke test.
- Source-only archive hashes and file allowlist pass. An extracted source archive reruns all source checks: 15 Python checks pass, one proprietary-fixture integration check is explicitly skipped, Java/JavaScript suites pass.
- Workflow/template YAML parses locally. Linux/macOS CI matrix and draft-release execution still require a published Git repository and actual remote runs.

No new TV installation or physical playback session was performed for this packaging refactor. Earlier physical results above remain deployment-specific historical evidence, not fresh v0.2.0 playback validation.

Follow-up UP lifecycle fix: pending requests and queued key callbacks are invalidated across page exits. Java regression cases cover page changes, delayed callbacks, single-use requests, expiry, cancellation and delayed same-page controls. Source suites and HUD build verification pass; no TV installation was performed.
