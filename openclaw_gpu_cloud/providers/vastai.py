"""
Vast.ai 云平台适配器
全球竞价 GPU 实例，价格较低
"""

import os
import requests
from ..scheduler import CloudInstance
from ..estimator import ResourceEstimate


class VastAIProvider:
    """Vast.ai 云平台适配器"""
    
    BASE_URL = "https://vast.ai/api/v0"
    
    def __init__(self):
        self.api_key = os.environ.get("VAST_API_KEY", "")
    
    def create_instance(self, requirements: ResourceEstimate) -> CloudInstance:
        """创建 Vast.ai 实例"""
        if not self.api_key:
            raise ValueError("请设置 VAST_API_KEY 环境变量")
        
        # 搜索可用实例
        offers = self._search_offers(requirements.gpu_type, requirements.gpu_count)
        
        if not offers:
            raise RuntimeError("没有找到可用的 GPU 实例")
        
        # 选择最便宜的
        offer = offers[0]
        
        # 创建实例
        response = requests.post(
            f"{self.BASE_URL}/instances",
            params={"api_key": self.api_key},
            json={
                "offer_id": offer["id"],
                "template_id": "default",
                "env": {},
                "bid_mode": "standard",
            }
        )
        
        if response.status_code != 200:
            raise RuntimeError(f"创建实例失败: {response.text}")
        
        data = response.json()["instance"]
        
        return CloudInstance(
            instance_id=str(data["id"]),
            platform="vastai",
            gpu_type=requirements.gpu_type,
            ip=data["inet"],
            port=data["port"],
            ssh_user="root",
        )
    
    def _search_offers(self, gpu_type: str, count: int) -> list:
        """搜索可用 GPU 实例"""
        gpu_name_map = {
            "RTX 4090": "RTX 4090",
            "RTX 3090": "RTX 3090",
            "A100": "A100",
            "H100": "H100",
            "V100 32GB": "V100",
        }
        
        response = requests.get(
            f"{self.BASE_URL}/offers",
            params={
                "api_key": self.api_key,
                "gpu_name": gpu_name_map.get(gpu_type, gpu_type),
                "num_gpus": count,
                "order_by": "price",
                "availability": "true",
            }
        )
        
        if response.status_code != 200:
            return []
        
        return response.json().get("offers", [])[:5]
    
    def destroy_instance(self, instance_id: str):
        """销毁实例"""
        requests.delete(
            f"{self.BASE_URL}/instances/{instance_id}",
            params={"api_key": self.api_key}
        )
