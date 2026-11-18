# 安全策略

[English](SECURITY.md)

只维护最新预览版。版本锁定补丁不能保证原厂 App、SDK 或系统的安全，也不绕过账号授权或 DRM。

不要在公开 Issue 发布可利用细节、凭据、播放链接、APK 或原始日志。[项目主仓库](https://github.com/orange-the-weak/apple-tv-quality-patch) 已启用私密漏洞报告，请使用 [Security → Report a vulnerability](https://github.com/orange-the-weak/apple-tv-quality-patch/security/advisories/new)。若使用尚未开启该功能的分支仓库，只请求维护者建立私密渠道，不披露漏洞。目前不承诺响应时限，也没有单独配置私密联系邮箱。

报告应包含项目/App 版本、最小复现、影响及可能的缓解措施，使用合成数据。HUD 的本机回环诊断接口仅供同设备读取指标，不应通过代理暴露到局域网或公网。分享诊断数据前人工检查，另见[隐私说明](docs/privacy.zh-CN.md)。

维护者应保持私密漏洞报告功能可用。签名密钥不能进入仓库及源码包。CI 仅使用一次性构建测试密钥；正式 HUD 构建需要维护者保管的稳定密钥。
