# Release preparation / 发布流程

本地准备不会自动初始化 Git、提交、推送或发布。仓库范围应为当前独立项目目录；Git 操作需要维护者明确执行。

1. Update `atvpatch/__init__.py` (version, version code, fixed release date), both changelogs, release notes and compatibility records. HUD metadata and source names derive from this version.
2. Run `bash scripts/test.sh`. With a local original APK, also run the optional native integration test using `ATV_TEST_APK` and run `inspect --sdk`. Never upload that input to CI.
3. Run `python3 scripts/release.py` then `python3 scripts/verify_release.py dist/apple-tv-quality-patch-0.2.0-source.zip`. Extract into a temporary directory and rerun source tests there. Check the included file list and metadata.
4. Before community launch, configure private vulnerability reporting/contact, issue access, repository description and license. Verify the English and Chinese homepage links and illustration label. Configure branch protection after the first successful remote CI run.
5. After review and explicit Git authorization, create the matching version tag. The manual Release draft workflow accepts only a matching clean tag and runs checks before `gh release create --draft --prerelease --verify-tag`. Review the draft before publishing.

## CI and signing / CI 与签名

Source checks run on Linux/macOS and Python 3.10/3.12. The Android job compiles and verifies the project-owned HUD with a disposable key, builds a source archive, verifies hashes and reruns tests from the extracted archive. CI does not establish physical playback compatibility. Android SDK setup accepts SDK licenses on the runner; the repository owner should review the Android SDK terms before enabling it.

Official HUD distribution is optional. Set repository secrets `HUD_RELEASE_KEYSTORE_B64` and `HUD_RELEASE_PASSWORD` only if distributing the project-owned HUD with a stable, maintainer-controlled key. The manual workflow defaults to source-only. Never ship a vendor APK, a patched Apple APK, signing keys or the disposable CI-signed HUD. Back up the stable key securely; losing it prevents in-place HUD updates.

SHA-256 sidecars and the internal file manifest detect corruption; they do not independently authenticate a publisher. Verify the trusted repository/tag and release provenance. Local archives without Git history explicitly report `source_commit: null` and must not be presented as a tagged release.

## v0.2.0 readiness / 当前状态

- Source preparation, modularization, documentation and local validation: see [release notes](releases/v0.2.0.md).
- Public source repository, initial remote CI and private vulnerability reporting are live: [repository](https://github.com/orange-the-weak/apple-tv-quality-patch), [first successful CI](https://github.com/orange-the-weak/apple-tv-quality-patch/actions/runs/44232924347).
- A version tag, draft/public Release, stable HUD release signing key and branch-protection rules are still separate maintainer steps. No formal Release was published by the source upload.
