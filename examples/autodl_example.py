"""
AutoDL Playwright 使用示例
"""

import os
from openclaw_gpu_cloud.providers import AutoDLPlaywrightProvider


def main():
    # 方式 1: 通过环境变量设置
    # export AUTODL_USERNAME="your-username"
    # export AUTODL_PASSWORD="your-password"
    
    # 方式 2: 直接传参
    username = os.environ.get("AUTODL_USERNAME")
    password = os.environ.get("AUTODL_PASSWORD")
    
    if not username or not password:
        print("请设置环境变量:")
        print("  export AUTODL_USERNAME='your-username'")
        print("  export AUTODL_PASSWORD='your-password'")
        return
    
    print("=" * 60)
    print("AutoDL Playwright 自动化示例")
    print("=" * 60)
    
    with AutoDLPlaywrightProvider(username, password) as provider:
        # 1. 登录
        print("\n[1/3] 登录 AutoDL...")
        if not provider.login(headless=False):  # 首次建议用非无头模式
            print("登录失败，请检查账号密码")
            return
        print("✓ 登录成功")
        
        # 2. 列出当前实例
        print("\n[2/3] 获取实例列表...")
        instances = provider.list_instances()
        print(f"当前有 {len(instances)} 个实例:")
        for inst in instances:
            print(f"  - {inst.get('name', 'N/A')}: {inst.get('status', 'N/A')} ({inst.get('ip', 'N/A')})")
        
        # 3. 创建新实例（示例，需要取消注释）
        # print("\n[3/3] 创建新实例...")
        # from openclaw_gpu_cloud import CloudScheduler
        # scheduler = CloudScheduler()
        # estimate = scheduler.estimate(model="llama-7b", task_type="inference")
        # instance = provider.create_instance(requirements=estimate)
        # print(f"✓ 实例已创建: {instance.instance_id}")
        # print(f"  IP: {instance.ip}")
        # print(f"  GPU: {instance.gpu_type}")
        
        # 4. 释放实例（示例，需要取消注释）
        # input("\n按 Enter 键释放实例...")
        # provider.destroy_instance(instance.instance_id)
    
    print("\n✓ 完成")


if __name__ == "__main__":
    main()
