# OpenClaw GPU Cloud Skill

云 GPU 调度插件，让 OpenClaw 可以在没有 GPU 的情况下自动使用云平台资源。

## 功能

- 🔍 **智能预估** - 根据模型自动预估 GPU 需求
- ☁️ **多平台** - AutoDL / Lambda Lab / Vast.ai / RunPod
- 🚀 **一键启动** - 自动创建云实例
- 🛡️ **自动释放** - 任务结束自动销毁

## 使用方式

### 命令行

```bash
# 预估资源
openclaw gpu estimate --model llama-7b --task inference

# 启动云 GPU
openclaw gpu launch --model llama-7b --budget 5

# 列出当前实例
openclaw gpu list

# 销毁实例
openclaw gpu destroy <instance-id>
```

### Python API

```python
from openclaw_gpu_cloud import CloudScheduler

scheduler = CloudScheduler(budget=5.0)

# 预估
est = scheduler.estimate(model="llama-7b", task_type="inference")

# 启动
instance = scheduler.launch(requirements=est, workdir="./task", on_done="destroy")
```

## 配置

设置云平台 API Key：

```bash
# AutoDL (推荐国内用户)
export AUTODL_API_KEY="your-key"

# Lambda Lab
export LAMBDA_API_KEY="your-key"

# Vast.ai
export VAST_API_KEY="your-key"

# RunPod
export RUNPOD_API_KEY="your-key"
```

## 预估模型

| 模型 | 任务 | 推荐 GPU | 预计费用 |
|------|------|----------|----------|
| LLaMA-7B | 推理 | RTX 4090 | $0.25/h |
| LLaMA-13B | 推理 | RTX 4090 | $0.50/h |
| LLaMA-70B | 推理 | A100 80GB | $1.50/h |
| SD v1.5 | 推理 | RTX 3090 | $0.40/h |
