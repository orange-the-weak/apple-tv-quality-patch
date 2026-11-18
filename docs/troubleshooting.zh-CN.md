# Troubleshooting / 故障排查

| Symptom / 现象 | Check / 检查 |
| --- | --- |
| `doctor` fails | Read each remedy; use JDK 17+, Node 20+, SDK platform 34 / build-tools 34.0.0; set JAVA_HOME and ANDROID_SDK_ROOT |
| `inspect` rejects input | Supply unmodified 14.3.1 assets and original APK set; already-patched files are rejected |
| Manifest not checked | Pass `--sdk`; this warning is not full compatibility approval |
| Install signature mismatch | Original and locally signed packages have different signing identities; back up first, uninstalling can erase login and data |
| Low buffer / 偶发卡顿 | Compare active video and audio buffer, measured download rate and route; video buffer alone does not prove playable headroom |
| Low quality / 画质低 | Check available variants, selected track and actual HDR; a manifest maximum is not measured throughput or a playback guarantee |
| HUD missing | Check overlay/accessibility setup and playback state; UP is playback-only, 123 is manual |
| Long-press broken | Record real remote events; injected ADB keys do not exercise the same accessibility path |

默认保留最高画质策略；不要把降画质当成缓冲问题的修复。测试线路要显式选择，不硬编码私有代理。先导出有界日志再比较，避免重复长测。分享日志前检查账号、链接与设备信息。

[日志与回退](quickstart.zh-CN.md#日志与回退)
