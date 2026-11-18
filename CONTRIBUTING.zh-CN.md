# 参与贡献

[English](CONTRIBUTING.md)

先阅读[兼容性](docs/compatibility.zh-CN.md)与[架构](docs/architecture.zh-CN.md)。当前预览版只适配一个原始 App 版本；新增支持前请说明设备、App 版本、配置及预期行为。

## 开发与验证

需要 Python 3.10+、Node 20+、JDK 17+。在项目根目录运行 `bash scripts/test.sh`。本地可用 `ATV_TEST_APK` 指向合法获取的原始 base APK，运行原生按键集成检查；CI 不持有该文件，明确记录跳过。Android 构建前运行 `python3 -m atvpatch doctor --sdk "$ANDROID_SDK_ROOT"`。

每次改动围绕一个可复现问题，同步中英文使用文档、必要测试和变更记录。新增版本遵循[适配指南](docs/adapting.zh-CN.md)，不要放宽哈希或锚点检查。通用默认值与设备专用配置分开维护。

## 证据与隐私

测试使用合成样本。不要提交原厂 APK、反编译原厂源码、媒体、密钥、账号、订阅地址、带签名播放链接或原始设备日志。分享前人工复核脱敏结果，用简短复现与相关指标替代整份日志。截图使用自己的素材并去除个人信息。

涉及运行行为时记录实机、Android/App 版本、配置、画质、HDR/音频输出和遥控导航。源码测试通过不代表播放或 DRM 兼容。默认采用短测，长测需要明确目标及停止条件。

维护者结合行为、兼容性、隐私和回退方式审查。另见[安全报告](SECURITY.zh-CN.md)及[社区行为规范](CODE_OF_CONDUCT.md)。
