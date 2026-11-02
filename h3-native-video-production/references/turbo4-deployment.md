# 当前实测4步 LoRA：快速部署

本页固定的是一次本地实际跑通的 **FL2VA 首帧生成**配方，不代表作者后续版本，也不适用于名字相似的所有模型。部署前查看目标 ComfyUI 实际节点与模型类型；不要为追“最新”顺手升级整套生产环境。

## 1. 文件和配方必须成套

| 项目 | 已验证配置 |
|---|---|
| 底模 | `minimax_h3_fl2va_pruned_int8_convrot.safetensors` |
| LoRA 仓库 | [lightx2v/Minimax-h3-Turbo](https://huggingface.co/lightx2v/Minimax-h3-Turbo/tree/30f485ed874aa44c8183348ad361c5eabad318da) |
| 固定 revision | `30f485ed874aa44c8183348ad361c5eabad318da` |
| LoRA | `minimax_h3_fl2v_turbo_4step_v1.2_768p_comfyui_bf16.safetensors` |
| 文件大小 | `1956193000` bytes |
| SHA256 | `c8168ebc17bbacc4296103dda2fec1ba85b24392fa08cf2bfbcef0cff0dc3cc8` |
| 采样 | `4` steps，`euler`，`simple`，denoise `1.0` |
| 强度与 shift | strength_model `1.0`，video `6.0`，audio `3.0` |
| 本地验证形式 | 576×1024、24fps、158真实帧、首帧条件、H3原生音轨；不是768p质量全面认证 |

本地 CPU 头检查有624个张量键，运行时加载208组矩阵 patch；数量只作辅助诊断，完整 SHA 才锁定本文件。`768p` 是该权重版本名，不要求把原576×1024分镜偷偷改分辨率。

已有8步版本是 `minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors`，SHA `2339acdf19bfe123f46b971ea35d367a84adb85de43627e1eceafa5a5b2b111e`，配方8/euler/simple/video12/audio3/strength1。**切4步同时更换 LoRA 和 video shift；只把8改成4不能冒充4步蒸馏版本。**

## 2. 下载一次，完整校验后采用

以下是已有可运行 FL2VA 环境的增量部署；底模、VAE、文本编码器和自定义节点沿用原已跑通工作流。`COMFY_MODELS` 指实际模型目录，`SKILL_DIR` 指本 skill 的安装目录。

```bash
export COMFY_MODELS='/path/to/ComfyUI/models'
export SKILL_DIR='/path/to/h3-native-video-production'
mkdir -p "$COMFY_MODELS/loras"
export H3_TURBO_FILE='minimax_h3_fl2v_turbo_4step_v1.2_768p_comfyui_bf16.safetensors'
curl --fail --location --continue-at - \
  'https://huggingface.co/lightx2v/Minimax-h3-Turbo/resolve/30f485ed874aa44c8183348ad361c5eabad318da/minimax_h3_fl2v_turbo_4step_v1.2_768p_comfyui_bf16.safetensors' \
  --output "$COMFY_MODELS/loras/$H3_TURBO_FILE.partial"
python3 "$SKILL_DIR/scripts/prepare_turbo4.py" \
  --lora "$COMFY_MODELS/loras/$H3_TURBO_FILE.partial" --verify-only
```

仅校验成功后将 `.partial` 改为正式文件名。若正式文件已存在，先核其 SHA；相同就复用，不重新下载或覆盖。不完整文件不载入。文件系统不支持 hardlink/symlink 时采用 exclusive copy 后再核 SHA；这属于 CPU 安装修复，不是 GPU 重试理由。网络失败保留断点，重下不应触发视频提交。

```bash
test ! -e "$COMFY_MODELS/loras/$H3_TURBO_FILE" && \
  mv -n "$COMFY_MODELS/loras/$H3_TURBO_FILE.partial" "$COMFY_MODELS/loras/$H3_TURBO_FILE"
```

## 3. 接对 MODEL 链

```text
FL2VA UNET → 原工作流必需的 MODEL 包装节点
           → LoraLoaderModelOnly (4step v1.2, strength1)
           → MiniMaxH3SigmaShift (video6, audio3)
           ├→ BasicGuider.model
           └→ BasicScheduler.model (4, simple, denoise1)
KSamplerSelect = euler
```

Guider 和 scheduler 都必须指向 **同一个 shift 后 MODEL**。仅接 guider、scheduler 仍走原底模，会形成不一致配方。原环境的 `UmekoH3FP16DenseAttention` 是本地包装节点，别要求别的安装凭空也有该节点。

可用附带工具转换 **API-format JSON**（每节点含 `class_type`/`inputs`；不是前端可视化 workflow 格式）：

```bash
CUDA_VISIBLE_DEVICES=-1 python3 "$SKILL_DIR/scripts/prepare_turbo4.py" \
  --lora "$COMFY_MODELS/loras/$H3_TURBO_FILE" \
  --input existing_fl2va_api.json --output new_fl2va_turbo4_api.json
```

工具先完整 SHA 校验，保留原文件，拒绝覆盖输出；保留首帧、种子、台词、分辨率、帧长及其他节点。它只支持单个 FL2VA/单个 guider/scheduler/sampler 的已知链，拒绝 Ref2VA、未知底模、额外未知 LoRA、歧义分支。转换不安装节点、不打开端口、不提交 GPU；输出仍需目标环境前置校验。

## 4. 一镜试跑后再扩

先按用户范围选一个已知镜头，保存原8步源，使用相同首帧 bytes、台词、种子、画幅、fps和帧长。记录作者配方差异；不能为了“公平”把4步推荐 shift 改回8步设置。采样成功后实际核圆头/身份、唯一说话人、口型、音色、台词和尾音，再决定是否采用。

- 历史8步与新4步耗时会受到缓存、并发、版本和 shift 影响，不能称纯步数受控跑分。
- 单镜像样不意味着全部镜头自动通过；不要因加速批准而省掉内容验收。
- 本配方不适用于独立 Ref2VA 动作参考底模，也不与 FastH3 Omni、Turbo-SLA 混用。
- Omni 案例曾在模型检测中误读 PDD 头维度：只在隔离 runtime 用作者匹配代码做 CPU header/meta 几何预检；没有据此修改生产 ComfyUI。这个问题不要求给正常 FL2VA4步环境打 Omni 补丁。

本页参数依据固定 revision 文件及实际部署回执。后续作者指南变化时先核原始模型卡并记录新版本，保留本配方作为可回退的独立预设。
