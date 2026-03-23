# openclaw-gpu-cloud

> OpenClaw 云GPU调度插件 — 无本地GPU时，自动调度云资源，智能预估需求，任务结束自动释放

## 🎯 功能特性

- 🔍 **智能预估** - 根据任务类型/模型大小自动预估 GPU 规格和运行时长
- ☁️ **多平台支持** - AutoDL / Lambda Lab / Vast.ai / RunPod
- 🚀 **一键启动** - 自动创建云实例、配置环境、启动任务
- 🛡️ **自动释放** - 任务完成后自动销毁实例，不浪费资源
- 🔄 **OpenClaw 原生集成** - 作为 skill 插件无缝接入

## 📦 支持的云平台

| 平台 | 特点 | 地区 |
|------|------|------|
| **AutoDL** | 国内低价 RTX4090/H100，按量计费 | 中国 |
| Lambda Lab | 欧美主流，Tesla/V100/A100/H100 | 美国/欧洲 |
| Vast.ai | 竞价实例，价格低 | 全球 |
| RunPod | Serverless GPU，按秒计费 | 美国/欧洲 |

## 🛠️ 快速开始

### 安装

```bash
pip install openclaw-gpu-cloud
```

### 配置云平台

#### AutoDL（推荐国内用户）

AutoDL 使用 Playwright 模拟浏览器操作，需要设置用户名密码：

```bash
export AUTODL_USERNAME="your-username"
export AUTODL_PASSWORD="your-password"

# 安装 Playwright 浏览器（仅首次）
playwright install chromium
```

首次登录时建议使用非无头模式，方便输入验证码。

详细说明见 [docs/AUTODL_SETUP.md](docs/AUTODL_SETUP.md)

#### 其他平台（有 API）

```bash
# Lambda Lab
export LAMBDA_API_KEY="your-lambda-key"

# Vast.ai
export VAST_API_KEY="your-vast-key"

# RunPod
export RUNPOD_API_KEY="your-runpod-key"
```

### 使用示例

#### AutoDL（Playwright 模拟）

```python
from openclaw_gpu_cloud import CloudScheduler

# 创建调度器，指定 AutoDL
scheduler = CloudScheduler(preferred_platform="autodl")

# 预估资源
预估 = scheduler.estimate(model="llama-7b", task_type="inference")
print(f"建议: {预估.gpu_type} x {预估.gpu_count}")

# 启动任务
instance = scheduler.launch(requirements=预估, workdir="./my-task")
print(f"实例已创建: {instance.ip}")
```

#### 其他平台（API）

```python
from openclaw_gpu_cloud import CloudScheduler

# 创建调度器，指定平台
scheduler = CloudScheduler(preferred_platform="vastai")

# 预估资源
预估 = scheduler.estimate(
    model="llama-7b",
    dataset_size="10GB",
    batch_size=16
)
print(f"建议: {预估.gpu_type} x {预估.gpu_count}, 预计 {预估.estimated_hours}h")

# 启动任务
instance = scheduler.launch(
    requirements=预估,
    workdir="./my-task",
    on_done="destroy"  # 或 "notify"
)

# SSH 到实例
instance.connect()
```

## 📁 项目结构

```
openclaw-gpu-cloud/
├── openclaw_gpu_cloud/
│   ├── __init__.py
│   ├── scheduler.py      # 核心调度器
│   ├── estimator.py      # GPU 需求预估
│   ├── providers/        # 云平台适配器
│   │   ├── __init__.py
│   │   ├── autodl.py
│   │   ├── lambda_lab.py
│   │   ├── vastai.py
│   │   └── runpod.py
│   └── skills/          # OpenClaw skill 接口
│       └── SKILL.md
├── tests/
├── examples/
├── README.md
└── pyproject.toml
```

## 🔧 接入 OpenClaw

将此仓库克隆到 OpenClaw 的 skills 目录：

```bash
git clone https://github.com/tailong-wu/openclaw-gpu-cloud \
  ~/.openclaw/skills/gpu-cloud
```

## 📊 GPU 需求预估模型

预估基于以下因素：

- 模型参数量 (7B, 13B, 70B...)
- 序列长度 (128, 512, 2048...)
- Batch size
- 训练/推理模式
- 数据集大小

## ⚠️ 注意事项

- 请确保云平台账户余额充足
- 建议设置预算上限 (budget parameter)
- 敏感操作请自行验证

## 📄 License

MIT

## 🤝 Contributing

Issues 和 PRs 欢迎！
