# Version adapters / 版本适配

当前适配器明确拆成播放器界面、HLS 选流与 worker 缓冲三个模块：

- `atvpatch/adapters/apple_tv_14_3_1.json`: package/version, original hashes, transformations.
- `atvpatch/adapters/v14_3_1/player.py`: player UI and controls.
- `atvpatch/adapters/v14_3_1/hls.py`: quality and bounded prefetch.
- `atvpatch/adapters/v14_3_1/worker.py`: buffer metrics and memory policy.
- `atvpatch/patches.py`: validation and composition.
- `atvpatch/profiles/*.json`: explicit device policy; no automatic device inference.

新增版本时建立新的版本模块与清单，保留旧版验证路径。使用本地合法原始文件记录哈希，分别审查每个锚点且保证唯一；不要提交原厂源码或 APK。新增合成输入测试及不支持版本拒绝测试。当前 CLI 只选择已注册的 14.3.1 适配器；新增版本还需显式注册选择逻辑并测试冲突，不会仅靠复制 JSON 自动生效。

实机检查需覆盖登录、同片同轨、HDR/音频、字幕/选集、长按、暂停下载、内存及回退。先做一分钟短测；不同硬件上的成功必须单独记录。
