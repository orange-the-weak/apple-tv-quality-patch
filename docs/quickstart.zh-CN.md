[返回首页](../README.zh-CN.md) | [English](quickstart.md)

## 环境

源码检出目录运行，暂不作为PyPI包安装。需要 Python 3.10+、Node.js 20+（JS检查和测试）、JDK 17+、Android SDK Platform 34、Build Tools 34.0.0 和 ADB。已在 macOS 本地验证源码检查与 Android 构建；Linux/macOS 源码 CI 及 Linux HUD 构建 CI 已配置，尚未在远端运行。Linux 执行和 Windows 均未验证。

```sh
export ANDROID_SDK_ROOT=/path/to/android-sdk
export JAVA_HOME=/path/to/jdk-17
export PATH="$JAVA_HOME/bin:$ANDROID_SDK_ROOT/platform-tools:$PATH"
# 已装 sdkmanager 时：
sdkmanager 'platforms;android-34' 'build-tools;34.0.0' 'platform-tools'
```

先运行`python3 -m atvpatch doctor`只读检查环境；原包就绪后运行`python3 -m atvpatch inspect --input input`，提供`--sdk`可同时检查包名／版本。

## 1. 准备原包和自己的签名密钥

可将完整原版分包放在 `input/`，也可从已安装**官方原版**的设备提取。不要输入已打过补丁的包。网络ADB需先在电视开启调试，电脑执行 `adb connect TV_IP:5555`，并在电视确认授权；USB连接则用 `adb devices` 中的序列号。自定义ADB端口可给设备工具传入 `--port`。

```sh
python3 scripts/device.py --serial TV_IP:5555 pull --output input
mkdir -p keys
# 命令会交互询问密码；请妥善保管，不提交到Git。
keytool -genkeypair -keystore keys/local.p12 -storetype PKCS12 \
  -alias local -keyalg RSA -keysize 2048 -validity 10000 \
  -dname 'CN=Local TV Quality Patch'
# 在当前终端设置 ATV_KEYSTORE_PASSWORD 为上述密码；不要写入源码。
```

## 2. 构建补丁和浮窗

```sh
python3 -m atvpatch patch --input input --output build/apks \
  --keystore keys/local.p12
python3 -m atvpatch hud --output build/hud --keystore keys/local.p12
```

输出目录必须为空。每次实验用新目录，以保留可回退产物。可选 `--no-prefetch` 关闭预取、`--no-reclaim` 关闭已播视频回收。回收策略默认保留最近12秒的已播视频缓存，向后跳转较远可能需要重新下载；它的独立收益尚未证实。

新增`--video-buffer-mib N`可把视频池至少提高到N MiB（16–256），默认0保留平台上限，不降低已有更大上限，也不改变音频池。实测索尼配置在确认80MiB视频池配额受限后使用`--video-buffer-mib 128`，视频池上限增加48MiB；应核对整体进程内存并保留回退产物。60秒目标不代表字节容量一定能容纳60秒。

所有输入分包一起重签。构建检查版本、原始脚本SHA-256、替换位置唯一性、Node语法、ZIP对齐和签名，并核对DEX／原生库字节未改变。锁定三个播放器资产：worker、adopted HLS及PlayerPage。`verification.json` 记录输入输出哈希和功能开关，不记录密钥或密码。

## 3. 安装与启用

**官方版与本地签名不一致，不能直接覆盖。首次迁移通常需要用户自行卸载官方版并重新登录；卸载会清除应用数据。本项目不会自动卸载。请先备份原包、确认账号可登录，再决定是否迁移。** 已安装同一密钥签名的测试版时可覆盖更新；换密钥也不能保留原安装直接覆盖。

```sh
python3 scripts/device.py --serial TV_IP:5555 install --input build/apks
python3 scripts/device.py --serial TV_IP:5555 hud --apk build/hud/PlaybackPanel.apk
```

在电视“设置 → 无障碍”启用“播放信息面板”。日志权限授予后需关闭再启用一次该服务，确保进程重启；不要只把浮窗隐藏。服务用标准窗口切换事件判断前台，自动浮窗同时要求活动播放页心跳与原生控制栏可见状态，控制栏／页面关闭或心跳过期时隐藏；123手动模式单独开关。启用或覆盖安装面板后，请先返回桌面再打开Apple TV，让服务收到前台事件。若系统限制日志读取或按键过滤，对应功能可能不可用。

浮窗使用无障碍覆盖层；`DUMP`读取系统媒体状态，`READ_LOGS`读取播放器诊断标记，`INTERNET`只用于本机回环指标接收。服务不点击、不注入按键、不读取窗口文本。回环数据不是经过认证的安全来源。详见 [隐私与日志](privacy.zh-CN.md)。

## 日志与回退

```sh
python3 scripts/device.py --serial TV_IP:5555 logs --output diagnostic-logs
```

日志仅导出，稍后再离线分析。`adb shell dumpsys activity service local.tv.playbackpanel/.PanelService metrics`可轻量读取实时高低水位、配置上限、HLS估算字节、配额历史及已播缓存时长；估算峰值与曾触发配额不能单独当成当前硬上限。电视待机／服务停止期间无法记录；清理在写入或导出时执行，7天按分段最后写入时间计算。导出时仍在轮转可能产生少量重复或缺失，分析时按时间与记录内容去重。空字节或不完整记录不再中断整次导出，可恢复的记录保留，跳过行数会提示。

回退到上一测试版：用**相同密钥**构建的旧目录执行 `install`。回退官方版需要自行卸载本地签名版、安装保存的完整官方分包并重新登录，不能承诺保留数据。关闭浮窗／后台采集：在无障碍中关闭服务。原Apple TV签名不会被本项目恢复或伪造。


以上命令均在项目根目录运行。`--profile sony-x75j`显式选择已测128MiB配置，默认platform保留原生预算；显式`--video-buffer-mib`优先。安装单独执行，预检不改电视。
