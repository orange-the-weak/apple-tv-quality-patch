# Privacy and logging

English | [简体中文](privacy.zh-CN.md)

The project does not collect accounts, passwords, cookies, subscription URLs, media URLs, DRM keys, or remote-control input content. It sends no remote telemetry. Building, installing, and exporting are explicit commands.

The HUD binds only to `127.0.0.1:18767`, not the LAN. Other local apps can send similarly shaped input, so it is not an authentication boundary. `DUMP` reads media diagnostics. Foreground detection uses package names from standard accessibility window events, without reading window text. `READ_LOGS` permits access to Luna output, but **raw logcat is never persisted**: only allowlisted numeric/boolean `LocalRuntime` fields and constrained `LocalParallel` events are saved. Audio-write warnings become counters; other lines are discarded.

Three-second samples contain bitrate, video dimensions/codecs, forward audio/video buffers, buffering state, and total TV download speed. Traffic includes other apps and ADB; it is not video bitrate. Timestamps may reveal viewing times, so inspect logs before sharing. Titles and playback URLs are not recorded. JSON field names stay unchanged across interface languages.

TV logs live in private `files/playback-diagnostics`: eight segments of at most 1 MiB each. Rotation deletes the oldest segment first. Writes and exports remove segments last modified more than seven days ago. Write errors do not interrupt playback. Desktop cleanup only touches `playback-*.jsonl.gz` in the chosen export folder, enforcing seven days / 64 MiB on each export. No desktop collector stays running. Disabling the accessibility service stops recording; uninstalling the HUD removes its private data.


Version 0.1.2 adds local `/ui` playback-page/control visibility signals to gate UP activation and synchronize hiding. It does not capture page text or titles. Quality-restore records contain only target/selected bitrate and boolean flags. Export recovers complete JSON from zero-filled/partial segments and reports skipped lines. Hidden or stale HUD display snapshots are not presented as current diagnostic readings.


Version 0.1.4 adds read-only buffer diagnostics: watermarks, configured byte budgets, tracked occupancy/peaks, quota history, behind-buffer duration, and prefetch readiness. No URLs or account fields are added. Existing TV (8 MiB/seven days) and desktop export (64 MiB/seven days) limits remain unchanged.
