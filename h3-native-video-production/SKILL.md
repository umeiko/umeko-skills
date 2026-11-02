---
name: h3-native-video-production
description: Produce and repair H3 native audiovisual storyboards and clips in ComfyUI, deploy the tested LightX2V 4-step FL2VA LoRA, and verify speakers, continuity, source audio, captions, and final edits. Use for AI short films and shot-level rework; ordinary screen recordings with external TTS belong to narrated-demo-video.
---

# H3 原生音画短片制作与返工

以用户当前剧本、角色参考和最新逐镜意见为准。把“首帧通过”“技术出片”“画面通过”“原生声音通过”“正式交付”分开记录。保留拒收版本与旧正式片；改镜头不覆盖历史请求和已交付母版。

## 按任务读取

- 上4步、从8步切换、排查模型兼容：读 [4步快速部署](references/turbo4-deployment.md)。附 CPU 工作流转换工具，不启动显卡。
- 设计分镜、提示词被念出、说错人、音色年龄错误：读 [对白与分镜契约](references/prompt-and-storyboard.md)。
- 原片自行生成台词字幕、黑字幕条或衣服/盒底文字：读 [原生字幕污染及去除](references/subtitle-contamination.md)，含实际失败、成功重生成配方和验收边界。
- 查看历次用户拒收以及最终修法：读 [奶龙短剧案例](references/grandpa-failure-cases.md)；涉及产品、热像、真人手或舞蹈参考时，再读 [其他短片案例](references/product-and-motion-cases.md)。
- 裁切救片、复用原音、字幕、剪辑与终审：读 [验收及后期](references/review-and-editing.md)。

## 执行原则

1. 先确定镜头要传达的唯一信息、真正说话人、听者、道具归属、左右位置和观众何时知道秘密。参考图要直接体现这些关系；不要靠长提示词扭转错误首帧。
2. 角色身份用简短正向描述和已检查参考图固定。负面清单在一次失败中同时提到触角、玩偶、相框，随后这些对象进入画面；因果未隔离，不能声称模型一定忽略否定词，也不要重复堆列这些概念。
3. H3 使用英文舞台描述、稳定说话人编号、`says:`，原文台词只放镜头正文的 `<d>[Chinese] …</d>`。环境声字段只写环境声。语法校验只能拦歧义，不能替代观看和声音验收。
4. 把首帧、完整请求、模型版本、配方、种子与 SHA 绑定到新镜头版本。排队快照不可被后续草稿暗改；逐镜步数变化只影响下一次明确提交，旧8步片继续显示实际8步。
5. 实际观看全景、细节和关键连续帧。说话者不对、身份突变、核心空间错误、提前泄底、串读指令、模型字幕属于本项目核心拒收项；轻微眨眼、布料和卡通手指变化按用户尺度记录接受。
6. 先选最小且保叙事的修法：同源真实动态近景、正确反应镜头、用户允许的原声替换，或重做首帧后新生成。裁掉核心动作、静帧顶时长、字幕掩盖错话，都不是修好。
7. 用户若只要求改声音，保住已接受画面；若要求重生成，就不以隐藏问题的裁切冒充新片。时长减半时先测完整台词能否原速放入，必要时经用户指定或允许改短句。

## 队列边界

沿用目标环境的调度和显卡约束，不从案例复制机器路径、GPU 数量或后台服务。区分用户内容返工、CPU 前置校验失败、主动暂停和真实 GPU 故障。

- 新准备好且已获授权的镜头可在现有安全队列继续，CPU 生图/后期不应人为阻塞采样。
- 不为等待验收空占显卡；有限批完成后正常退出。已提交请求先查原 queue/history，不盲目再次 POST。
- 用户暂停/睡眠后按其指定 drain 或中断，保留回执。继续时确认旧 worker 已退出，仅接证实未提交的项；不清掉故障 HOLD 来“恢复”。
- 本次部署案例环境禁止额外 CUDA/NVML/nvidia-smi 探针、驱动重置和 GPU 失败自动重试。其他环境先读其约束；不能把一次用户继续解释成永久自动恢复授权。

## 记录真实结果

每条返工保留：用户问题、具体失败时点、来源 SHA、原提示词、修改范围、实际看过的帧、原生 ASR/尾音依据、通过或未通过。原因标明是观察事实还是推测。交付只报告真实可播放文件和限制，不把分镜图、计数或成功日志说成成片。
