# Security policy

[简体中文](SECURITY.zh-CN.md)

Only the latest preview is maintained. A narrowly pinned patch does not guarantee the security of the vendor app, SDK or operating system. The project does not bypass account authorization or DRM.

Do not publish exploitable details, credentials, playback URLs, APKs or raw logs in public issues. After this repository is published, use **Security → Report a vulnerability** if private reporting is enabled. Until a private channel is configured, ask the maintainer to establish one without disclosing the vulnerability. There is currently no promised response SLA or configured private reporting address in this source bundle.

Include the affected project/app version, minimal reproduction, impact and a proposed mitigation using synthetic data. The local HUD loopback diagnostics endpoint is intended only for same-device read-only metrics; keep it on loopback and do not expose it through a network proxy. Review exported diagnostic data before sharing. See [privacy](docs/privacy.md).

Before publication, maintainers must enable private vulnerability reporting or document a verified private contact. Signing keys must stay outside the repository and source artifacts. CI uses a disposable build-test key; official HUD builds require a stable maintainer-controlled key.
