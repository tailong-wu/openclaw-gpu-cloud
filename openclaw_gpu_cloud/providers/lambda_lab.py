"""
Lambda Lab 云平台适配器
欧美主流 GPU 云服务
"""

import os
import requests
from ..scheduler import CloudInstance
from ..estimator import ResourceEstimate


class LambdaLabProvider:
    """Lambda Lab 云平台适配器"""
    
    BASE_URL = "https://cloud.lambdalabs.com/api/v1"
    
    def __init__(self):
        self.api_key = os.environ.get("LAMBDA_API_KEY", "")
        self.headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
    
    def create_instance(self, requirements: ResourceEstimate) -> CloudInstance:
        """创建 Lambda Lab 实例"""
        if not self.api_key:
            raise ValueError("请设置 LAMBDA_API_KEY 环境变量")
        
        # 查找可用区
        region = self._find_available_region(requirements.gpu_type)
        
        # 创建实例
        response = requests.post(
            f"{self.BASE_URL}/instance-operations/instances",
            headers=self.headers,
            json={
                "region_name": region,
                "instance_type_name": self._map_gpu_type(requirements.gpu_type),
                "ssh_key_names": ["default"],
                "file_system_names": [],
            }
        )
        
        if response.status_code != 201:
            raise RuntimeError(f"创建实例失败: {response.text}")
        
        data = response.json()["data"]
        
        return CloudInstance(
            instance_id=data["id"],
            platform="lambda",
            gpu_type=requirements.gpu_type,
            ip=data["ip"]["public"]["ip_address"],
            ssh_user="ubuntu",
            ssh_key_path=os.path.expanduser("~/.ssh/id_rsa"),
        )
    
    def _find_available_region(self, gpu_type: str) -> str:
        """查找有可用 GPU 的区域"""
        # TODO: 调用 API 查询
        return "us-west-1"
    
    def _map_gpu_type(self, gpu_type: str) -> str:
        """映射 GPU 类型到 Lambda 规格"""
        mapping = {
            "RTX A6000": "gpu_1x_rtx6000",
            "A100 40GB": "gpu_1x_a100_40gb",
            "A100 80GB": "gpu_1x_a100_80gb",
            "H100": "gpu_1x_h100",
        }
        return mapping.get(gpu_type, "gpu_1x_a100_40gb")
    
    def destroy_instance(self, instance_id: str):
        """销毁实例"""
        requests.post(
            f"{self.BASE_URL}/instance-operations/terminate",
            headers=self.headers,
            json={"instances": [instance_id]}
        )
