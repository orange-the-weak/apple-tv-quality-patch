# Compatibility / 兼容性

| Component / 项目 | Supported / 支持范围 |
| --- | --- |
| Vendor app | Apple TV Android TV 14.3.1, versionCode 143100; three original asset SHA-256 values must match |
| Host / 构建主机 | Python 3.10+, Node 20+, JDK 17+, Android SDK platform 34 / build-tools 34.0.0 |
| Physical validation / 实机记录 | Sony X75J, Android 12, armeabi-v7a; see validation record |
| Default profile | `platform`: retain native video memory budget |
| Device opt-in | `sony-x75j`: video pool 128 MiB; audio budget unchanged |
| Other devices / 其他设备 | Not yet physically verified / 尚未实机验证 |

哈希与锚点验证不等于完整 split 集合、设备 ABI、账号或 DRM 验证。没有适配的新版本应直接拒绝，不能强行安装。检查工具不会自动切换设备配置。

[实机验证记录](validation.zh-CN.md) · [快速开始](quickstart.zh-CN.md)
