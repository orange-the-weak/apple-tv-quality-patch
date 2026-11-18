# 实现与维护边界

[English](architecture.md) | 简体中文

`atvpatch/patches.py` 是14.3.1专用的字节锚点和原创注入代码。只匹配已验证的 worker、adopted HLS及PlayerPage的SHA-256。不存在跨版本稳定API的承诺，新版本需重新定位、增加独立版本适配和实际验证，不能仅修改版本号或删除哈希检查。

播放清单包含不同尺寸、码率与编码的variants。清单初始化完成后的下一轮事件循环检查播放器实例和内容仍一致，再调用 `hls.ol.setManualMode` 和 `setEnabledMediaOptionByType`。选择异常时释放手动模式。最高档按宽×高优先、同尺寸按码率比较；它是清单声明值，不是逐帧测量。不修改音轨过滤。每3秒的守护检查会在快进恢复正常播放后纠正较低档位，并使用已有无缝切档路径；已缓存的低清片段可能先播放完，不使用会造成视频时间戳缺口的强制立即清除。跳过iframe、非正常速率、seeking及内容变化，目标档已匹配时不重复切换。

adopted HLS的片段中止路径增加manualMode判断，避免绕过手动选择降档。该策略会牺牲网络不足时的自动降档能力，因此高档卡顿仍可能发生；手动模式不是无限带宽。

媒体库在加载当前VOD视频片段时启动下一完整片段预取。通过现有observable缓存接续已经完成或进行中的下载，只允许一个额外预取槽；限制片段时长≤8秒、已知byte range≤32MiB。没有byte range时不做硬字节上限承诺；其内存占用与片段体积有关。清理／变更请求时取消闲置预取，失败返回原下载路径。`_localPrefetchOnly`隔离加载状态与in-flight range通知，避免把未来片段当作当前加载片段。没有修改HTTP、认证、解密或DRM原生库。

默认回收已播视频缓存，保留12秒后向窗口，每次至少间隔6秒，跳过seeking/updating。SourceBuffer上限保持平台默认（实测视频80MiB、音频5MiB），并发缓存另计；不宣称各设备都采用这两个上限。回收收益未单独验证，可用 `--no-reclaim` 做对照。

每3秒worker通过127.0.0.1:18767发送有界JSON。面板服务限制请求体、请求头和读取超时，网络折线图保留120秒／最多90点。前向缓冲由combined buffer与各轨water level读取，不能使用包含已播部分的bufferedDuration冒充前向缓冲。

PlayerPage通过本机`/ui`报告活动播放页和原生控制栏显隐，每秒心跳、销毁时清理，覆盖／退出时发送失活。旧页面不能覆盖当前页面状态。上键要求Apple TV前台且活动播放页；浮窗跟随实际控制栏回调隐藏，包括原生5／8／20秒不同模式，不再用固定八秒代替。页面退出或心跳过期时自动模式隐藏。123保留为独立手动开关，可在播放页以外使用。方向键按下和抬起继续透传，仅消费123键。

两处方向键长按处理忽略同一次按住期间重复的Down，避免不断重置原生一秒计时器；Up保持原来的短按跳转／释放行为。方向变化会取消旧方向计时器，丢失Up后也可在间隔后恢复新手势。

界面使用默认英文／中文Android资源；协议字段及日志字段不随语言改变。

构建的ZIP重写修改三个assets；重新对齐并统一签名全部分包。签名变化会影响覆盖安装与可能的完整性校验，不能保证所有账号或后续服务端政策可用。


0.1.3还处理Android平台的额外兼容条件：reader开启且原生supportsScreenReaderDirectionalLongPress为false时，旧处理器会直接执行短跳转而不启动计时器。仅在两处播放方向处理器启用原生长按分支，不修改全局读屏、焦点或其他界面。限量方向诊断只记录动作阶段和兼容布尔值，每个处理器最多40条，不进入电视滚动日志白名单。


0.1.4修正Gg停止水位选择：暂停使用正常高水位，显式stopStreaming仍使用原来的停止水位。默认保留平台字节预算，可显式通过video_buffer_mib参数提高视频池，音频和较大的原生预算保持不变。缓冲诊断为只读，记录高低水位、总秒数目标、HLS估算字节／观测峰值、配额曾触发标记及单独的配置字节上限，不把时间目标与字节容量混为一谈。


## v0.2.0 module boundaries

`atvpatch/patches.py` validates and composes the pinned adapter. The adapter manifest stores identity/hashes, while `adapters/v14_3_1/{player,hls,worker}.py` owns each transformation. `profiles/*.json` contains explicit device policy; `preflight.py` provides read-only checks. The CLI, generated HUD manifest and release archive use `atvpatch/__init__.py` as their version source. See the version adapter and release guides for extension and distribution contracts.
