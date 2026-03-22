"""
GPU 预估示例 - 展示不同模型的预估结果
"""

from openclaw_gpu_cloud import GPUEstimator


def main():
    estimator = GPUEstimator(budget=10.0)
    
    models = [
        ("llama-7b", "inference"),
        ("llama-13b", "inference"),
        ("llama-7b", "fine-tuning"),
        ("qwen-14b", "fine-tuning"),
        ("stable-diffusion", "inference"),
    ]
    
    print("=" * 60)
    print("GPU 资源预估对比")
    print("=" * 60)
    
    for model, task_type in models:
        est = estimator.estimate(model=model, task_type=task_type)
        
        print(f"\n{model} ({task_type}):")
        print(f"  ├─ GPU: {est.gpu_type} x {est.gpu_count}")
        print(f"  ├─ 显存/卡: {est.memory_per_gpu} GB")
        print(f"  ├─ 预计时长: {est.estimated_hours:.1f}h")
        print(f"  ├─ 预计费用: ${est.estimated_cost:.2f}")
        print(f"  └─ 平台: {est.recommended_platform}")


if __name__ == "__main__":
    main()
