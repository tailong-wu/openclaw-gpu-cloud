# AutoDL Playwright 集成说明

AutoDL 目前没有公开的 REST API，我们使用 Playwright 通过模拟浏览器操作来实现自动化。

## 前置要求

### 安装 Playwright 浏览器

```bash
pip install playwright
playwright install chromium
```

### 设置环境变量

```bash
export AUTODL_USERNAME="your-username"
export AUTODL_PASSWORD="your-password"
```

## 使用方式

### 基本使用

```python
from openclaw_gpu_cloud.providers import AutoDLPlaywrightProvider

with AutoDLPlaywrightProvider() as provider:
    # 登录（首次建议 headless=False，方便输入验证码）
    provider.login(headless=False)
    
    # 列出实例
    instances = provider.list_instances()
    
    # 创建实例
    instance = provider.create_instance(requirements=estimate)
    
    # 释放实例
    provider.destroy_instance(instance.instance_id)
```

### 通过 Scheduler 使用

```python
from openclaw_gpu_cloud import CloudScheduler

scheduler = CloudScheduler(preferred_platform="autodl")
estimate = scheduler.estimate(model="llama-7b", task_type="inference")
instance = scheduler.launch(requirements=estimate, on_done="destroy")
```

## 注意事项

1. **首次登录** - 建议使用 `headless=False`，AutoDL 可能需要验证码
2. **Cookie 保存** - 登录成功后 Cookie 会保存到 `~/.autodl_cookies.json`，后续可以无头模式登录
3. **页面变化** - AutoDL 页面结构可能变化，需要更新选择器
4. **速率限制** - 不要频繁操作，避免账号被限制

## 调试技巧

### 查看页面快照

```python
page.screenshot(path="screenshot.png")
```

### 慢速模式

```python
page.goto(url, timeout=60000)
```

### 等待特定元素

```python
page.wait_for_selector('.instance-card', timeout=60000)
```

## 故障排查

### 登录失败
- 检查用户名密码是否正确
- 是否需要验证码（使用非无头模式）
- 账号是否被限制

### 找不到元素
- AutoDL 页面结构可能变化，需要更新选择器
- 使用浏览器开发者工具检查元素

### Cookie 失效
- 删除 `~/.autodl_cookies.json` 重新登录
