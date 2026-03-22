"""
RunPod 云平台适配器
Serverless GPU，按秒计费
"""

import os
import requests
from ..scheduler import CloudInstance
from ..estimator import ResourceEstimate


class RunPodProvider:
    """RunPod 云平台适配器"""
    
    BASE_URL = "https://api.runpod.io/graphql"
    
    def __init__(self):
        self.api_key = os.environ.get("RUNPOD_API_KEY", "")
    
    def create_instance(self, requirements: ResourceEstimate) -> CloudInstance:
        """创建 RunPod Serverless GPU 实例"""
        if not self.api_key:
            raise ValueError("请设置 RUNPOD_API_KEY 环境变量")
        
        # 查找 GPU 类型 ID
        gpu_type_id = self._find_gpu_type(requirements.gpu_type)
        
        # 提交 Serverless 任务
        query = """
        mutation createServerlessEndpoint($input: CreateServerlessEndpointInput!) {
            createServerlessEndpoint(input: $input) {
                id
            }
        }
        """
        
        response = requests.post(
            self.BASE_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "query": query,
                "variables": {
                    "input": {
                        "gpuTypeId": gpu_type_id,
                        "networkVolumeId": None,
                        "flashBoot": True,
                    }
                }
            }
        )
        
        if response.status_code != 200:
            raise RuntimeError(f"创建端点失败: {response.text}")
        
        data = response.json()
        endpoint_id = data["data"]["createServerlessEndpoint"]["id"]
        
        return CloudInstance(
            instance_id=endpoint_id,
            platform="runpod",
            gpu_type=requirements.gpu_type,
            ip=f"{endpoint_id}.onrender.com",  # RunPod 提供公共 URL
        )
    
    def _find_gpu_type(self, gpu_type: str) -> str:
        """查找 GPU 类型 ID"""
        mapping = {
            "RTX 4090": "RTX 4090",
            "RTX A6000": "RTX A6000",
            "A100 40GB": "A100 40GB",
            "A100 80GB": "A100 80GB",
            "H100": "H100",
        }
        return mapping.get(gpu_type, "A100 40GB")
    
    def destroy_instance(self, instance_id: str):
        """销毁端点"""
        query = """
        mutation deleteServerlessEndpoint($endpointId: String!) {
            deleteServerlessEndpoint(endpointId: $endpointId)
        }
        """
        
        requests.post(
            self.BASE_URL,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "query": query,
                "variables": {"endpointId": instance_id}
            }
        )
