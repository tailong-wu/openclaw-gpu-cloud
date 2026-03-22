"""
AutoDL 云平台适配器
国内低价 GPU 云服务，支持 RTX 4090/H100 等
"""

import os
import time
import requests
from typing import Optional
from ..scheduler import CloudInstance
from ..estimator import ResourceEstimate


class AutoDLProvider:
    """AutoDL 云平台适配器"""
    
    BASE_URL = "https://nlp.aliyun.com/autodl-api/v1"
    
    def __init__(self):
        self.api_key = os.environ.get("AUTODL_API_KEY", "")
        self.headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
    
    def create_instance(self, requirements: ResourceEstimate) -> CloudInstance:
        """创建 AutoDL 实例"""
        if not self.api_key:
            raise ValueError("请设置 AUTODL_API_KEY 环境变量")
        
        # 搜索可用实例
        instance_info = self._find_available_gpu(requirements.gpu_type)
        
        # 创建实例
        response = requests.post(
            f"{self.BASE_URL}/instances",
            headers=self.headers,
            json={
                "gpu_type": instance_info["gpu_type"],
                "gpu_count": requirements.gpu_count,
                "image_id": "ubuntu20.04",
                "duration": int(requirements.estimated_hours * 3600),
            }
        )
        
        if response.status_code != 200:
            raise RuntimeError(f"创建实例失败: {response.text}")
        
        data = response.json()
        
        return CloudInstance(
            instance_id=data["instance_id"],
            platform="autodl",
            gpu_type=requirements.gpu_type,
            ip=data["public_ip"],
            ssh_user="root",
            ssh_key_path=os.path.expanduser("~/.ssh/id_rsa"),
        )
    
    def _find_available_gpu(self, gpu_type: str) -> dict:
        """查找可用 GPU"""
        # TODO: 调用 AutoDL API 查询可用实例
        # 这里简化处理
        gpu_type_map = {
            "RTX 4090": "GeForce RTX 4090",
            "RTX 3090": "GeForce RTX 3090",
            "A100": "A100",
            "H100": "H100",
        }
        return {"gpu_type": gpu_type_map.get(gpu_type, gpu_type)}
    
    def destroy_instance(self, instance_id: str):
        """销毁实例"""
        requests.delete(
            f"{self.BASE_URL}/instances/{instance_id}",
            headers=self.headers
        )
    
    def list_instances(self) -> list:
        """列出所有实例"""
        response = requests.get(
            f"{self.BASE_URL}/instances",
            headers=self.headers
        )
        return response.json().get("instances", [])
