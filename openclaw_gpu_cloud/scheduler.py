"""
云 GPU 调度器
负责选择平台、启动实例、管理生命周期
"""

import os
import time
import subprocess
from typing import Optional, Callable
from dataclasses import dataclass
from .estimator import GPUEstimator, ResourceEstimate, TaskType


@dataclass
class CloudInstance:
    """云端实例"""
    instance_id: str
    platform: str
    gpu_type: str
    ip: str
    port: int = 22
    ssh_user: str = "root"
    ssh_key_path: Optional[str] = None
    
    def connect(self, local_port: int = 2222):
        """通过 SSH 隧道连接"""
        cmd = [
            "ssh", "-L", f"{local_port}:localhost:22",
            "-o", "StrictHostKeyChecking=no",
            "-i", self.ssh_key_path or "",
            f"{self.ssh_user}@{self.ip}",
            "-p", str(self.port)
        ]
        subprocess.run(cmd)
    
    def wait_ready(self, timeout: int = 300) -> bool:
        """等待实例就绪"""
        print(f"等待实例 {self.instance_id} 启动...")
        for _ in range(timeout // 10):
            if self._check_ssh():
                print(f"实例已就绪: {self.ip}")
                return True
            time.sleep(10)
        return False
    
    def _check_ssh(self) -> bool:
        """检查 SSH 是否可用"""
        try:
            result = subprocess.run(
                ["ssh", "-o", "StrictHostKeyChecking=no", 
                 "-o", f"PasswordAuthentication=no",
                 "-o", "ConnectTimeout=5",
                 f"{self.ssh_user}@{self.ip}", "echo ok"],
                capture_output=True, timeout=10
            )
            return result.returncode == 0
        except:
            return False


class CloudScheduler:
    """云 GPU 调度器"""
    
    def __init__(self, budget: Optional[float] = None, preferred_platform: Optional[str] = None):
        self.estimator = GPUEstimator(budget)
        self.preferred_platform = preferred_platform
        self._instances = []
        self._providers = {}
        self._init_providers()
    
    def _init_providers(self):
        """初始化云平台适配器"""
        from .providers import autodl, lambda_lab, vastai, runpod
        
        self._providers = {
            "autodl": autodl.AutoDLProvider(),
            "lambda": lambda_lab.LambdaLabProvider(),
            "vastai": vastai.VastAIProvider(),
            "runpod": runpod.RunPodProvider(),
        }
    
    def estimate(
        self,
        model: str,
        task_type: TaskType = "inference",
        **kwargs
    ) -> ResourceEstimate:
        """预估资源需求"""
        return self.estimator.estimate(model, task_type, **kwargs)
    
    def launch(
        self,
        requirements: ResourceEstimate,
        workdir: str,
        on_done: str = "destroy",  # "destroy", "notify", "keep"
        notify_webhook: Optional[str] = None,
    ) -> CloudInstance:
        """启动云 GPU 实例"""
        platform = self.preferred_platform or requirements.recommended_platform
        
        if platform not in self._providers:
            raise ValueError(f"不支持的平台: {platform}")
        
        provider = self._providers[platform]
        instance = provider.create_instance(requirements)
        
        if not instance.wait_ready():
            raise RuntimeError(f"实例 {instance.instance_id} 启动超时")
        
        self._instances.append(instance)
        
        # 设置完成回调
        if on_done == "destroy":
            self._setup_auto_destroy(instance)
        
        return instance
    
    def _setup_auto_destroy(self, instance: CloudInstance):
        """设置自动销毁"""
        # TODO: 实现任务监控和自动销毁逻辑
        pass
    
    def destroy_all(self):
        """销毁所有实例"""
        for instance in self._instances:
            try:
                platform = instance.platform
                if platform in self._providers:
                    self._providers[platform].destroy_instance(instance.instance_id)
            except Exception as e:
                print(f"销毁实例 {instance.instance_id} 失败: {e}")
        self._instances.clear()
    
    def destroy(self, instance_id: str):
        """销毁指定实例"""
        for i, inst in enumerate(self._instances):
            if inst.instance_id == instance_id:
                platform = inst.platform
                if platform in self._providers:
                    self._providers[platform].destroy_instance(inst.instance_id)
                self._instances.pop(i)
                break
    
    def list_instances(self) -> list:
        """列出当前所有实例"""
        return self._instances.copy()
