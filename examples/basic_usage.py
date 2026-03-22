"""
基础使用示例
"""

from openclaw_gpu_cloud import CloudScheduler


def main():
    # 创建调度器，预算 5 美元
    scheduler = CloudScheduler(budget=5.0)
    
    # 预估 LLaMA-7B 推理需要的资源
    estimate = scheduler.estimate(
        model="llama-7b",
        task_type="inference",
        precision="fp16"
    )
    
    print(f"预估结果:")
    print(f"  GPU: {estimate.gpu_type} x {estimate.gpu_count}")
    print(f"  显存: {estimate.memory_per_gpu} GB/卡")
    print(f"  预计运行时长: {estimate.estimated_hours}h")
    print(f"  预计费用: ${estimate.estimated_cost:.2f}")
    print(f"  推荐平台: {estimate.recommended_platform}")
    print()
    
    # 启动云实例
    print("启动云 GPU 实例...")
    instance = scheduler.launch(
        requirements=estimate,
        workdir="./my-task",
        on_done="destroy"  # 任务结束后自动销毁
    )
    
    print(f"实例已启动: {instance.ip}")
    print(f"实例 ID: {instance.instance_id}")
    print(f"平台: {instance.platform}")
    
    # 等待用户完成工作
    input("按 Enter 键手动销毁实例...")
    
    # 手动销毁
    scheduler.destroy(instance.instance_id)
    print("实例已销毁")


if __name__ == "__main__":
    main()
