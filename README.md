# Umeko Embedded AI Skills

[中文说明](README_CN.md)

Reusable Codex skills for embedded AI, model engineering, and media production. Each top-level skill directory is self-contained and can be installed independently.

## Skills

| Skill | Purpose |
|---|---|
| [`ascend-llm-training`](ascend-llm-training/) | Prepare, pack, launch, monitor, evaluate, and debug LLM training on Huawei Ascend NPUs with CANN, `torch_npu`, MindSpeed-LLM, or Megatron-LM. Includes field-tested guidance for document-isolated packing, HCCL jobs, `safetensors` transfer hangs, same-hardware evaluation, and activation-quantization diagnostics. |
| [`narrated-demo-video`](narrated-demo-video/) | Build reproducible narrated demo videos from real UI recording, segmented TTS, subtitles, music, effects, and FFmpeg timelines. |
| [`h3-native-video-production`](h3-native-video-production/) | Produce and repair H3 native audiovisual shorts: tested 4-step LoRA deployment, speaker and continuity checks, user-rejected shot case studies, source-preserving edits, subtitles, and delivery verification. |

## Install

Clone the repository and copy or symlink the skill you need into your Codex skills directory:

```bash
git clone https://github.com/umeiko/umeko-skills.git
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R umeko-skills/h3-native-video-production "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Restart or reload Codex if the new skill is not discovered immediately. You can then invoke it explicitly:

```text
Use $h3-native-video-production to deploy the tested 4-step LoRA and review these native-dialogue shots.
```

## Repository conventions

- `SKILL.md`: required entry point and workflow.
- `agents/openai.yaml`: optional UI metadata.
- `references/`: details loaded only when relevant.
- `scripts/`: reusable helpers that can be run without copying large code blocks.

Public content intentionally excludes private hosts, credentials, internal paths, proprietary model or dataset names, and unpublished metrics.
