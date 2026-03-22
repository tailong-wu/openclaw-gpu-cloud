"""
GPU 需求预估模块
根据任务参数智能估算需要的 GPU 规格和运行时长
"""

from dataclasses import dataclass
from typing import Optional, Literal
import re

TaskType = Literal["training", "fine-tuning", "inference", "embedding"]


@dataclass
class ResourceEstimate:
    """资源预估结果"""
    gpu_type: str          # 如 "RTX 4090", "A100", "H100"
    gpu_count: int         # GPU 数量
    memory_per_gpu: int    # 每卡显存需求 (GB)
    estimated_hours: float # 预估运行时长
    estimated_cost: float  # 预估费用 (美元)
    recommended_platform: str  # 推荐平台
    confidence: float      # 预估置信度 0-1


# GPU 规格数据库
GPU_CATALOG = {
    "RTX 4090": {"vram": 24, "price_per_hour": 0.5, "platform": "autodl"},
    "RTX 3090": {"vram": 24, "price_per_hour": 0.4, "platform": "autodl"},
    "RTX A6000": {"vram": 48, "price_per_hour": 0.8, "platform": "lambda"},
    "A100 40GB": {"vram": 40, "price_per_hour": 1.0, "platform": "lambda"},
    "A100 80GB": {"vram": 80, "price_per_hour": 1.5, "platform": "lambda"},
    "H100": {"vram": 80, "price_per_hour": 3.0, "platform": "lambda"},
    "V100 32GB": {"vram": 32, "price_per_hour": 0.6, "platform": "vastai"},
}


MODEL_MEMORY_MAP = {
    ("7b", "fp16"): 14, ("7b", "fp32"): 28,
    ("13b", "fp16"): 26, ("13b", "fp32"): 52,
    ("30b", "fp16"): 60, ("30b", "int8"): 35,
    ("70b", "fp16"): 140, ("70b", "int8"): 80, ("70b", "int4"): 50,
}


class GPUEstimator:
    """GPU 资源预估器"""
    
    def __init__(self, budget: Optional[float] = None):
        self.budget = budget
    
    def estimate(
        self,
        model: str,
        task_type: TaskType = "inference",
        dataset_size: str = "1GB",
        batch_size: int = 1,
        precision: str = "fp16",
        **kwargs
    ) -> ResourceEstimate:
        """预估 GPU 资源需求"""
        param_count = self._parse_model_params(model)
        base_memory = self._estimate_base_memory(param_count, precision)
        
        if task_type in ("training", "fine-tuning"):
            base_memory *= 4
            estimated_hours = self._estimate_training_time(param_count, dataset_size)
        else:
            estimated_hours = 0.5
        
        gpu_type, gpu_count, memory_per_gpu = self._select_gpu(base_memory)
        gpu_info = GPU_CATALOG[gpu_type]
        estimated_cost = gpu_info["price_per_hour"] * estimated_hours * gpu_count
        
        return ResourceEstimate(
            gpu_type=gpu_type,
            gpu_count=gpu_count,
            memory_per_gpu=memory_per_gpu,
            estimated_hours=estimated_hours,
            estimated_cost=estimated_cost,
            recommended_platform=gpu_info["platform"],
            confidence=0.7
        )
    
    def _parse_model_params(self, model: str) -> int:
        """从模型名称解析参数量（单位：B）"""
        model_lower = model.lower()
        match = re.search(r'(\d+)[bB]', model_lower)
        if match:
            return int(match.group(1))
        
        known = {
            "llama-2-7b": 7, "llama-2-13b": 13, "llama-2-70b": 70,
            "llama-3-8b": 8, "llama-3-70b": 70,
            "mistral-7b": 7, "mixtral-8x7b": 47,
            "qwen-7b": 7, "qwen-14b": 14, "qwen-72b": 72,
        }
        for name, params in known.items():
            if name in model_lower:
                return params
        return 7  # 默认 7B
    
    def _estimate_base_memory(self, param_count: int, precision: str) -> int:
        """估算基础显存需求 (GB)"""
        key = (f"{param_count}b", precision)
        if key in MODEL_MEMORY_MAP:
            return MODEL_MEMORY_MAP[key]
        mult = {"fp32": 4, "fp16": 2, "bf16": 2, "int8": 1, "int4": 0.5}
        return int(param_count * mult.get(precision, 2))
    
    def _estimate_training_time(self, param_count: int, dataset_size: str) -> float:
        """估算训练时间（小时）"""
        size_map = {"kb": 0.001, "mb": 0.001, "gb": 1, "tb": 1000}
        match = re.match(r'(\d+\.?\d*)\s*([kmgt]b)', dataset_size.lower())
        size_gb = float(match.group(1)) * size_map.get(match.group(2), 1) if match else 1
        return max(0.5, size_gb * 0.5 * (param_count / 7))
    
    def _select_gpu(self, required_memory: int) -> tuple:
        """选择合适的 GPU, 返回 (gpu_type, gpu_count, memory_per_gpu)"""
        for gpu_name, specs in GPU_CATALOG.items():
            if specs["vram"] >= required_memory:
                return (gpu_name, 1, specs["vram"])
        
        # 需要多卡
        for gpu_name, specs in GPU_CATALOG.items():
            if specs["vram"] >= required_memory / 4:
                needed = (required_memory + specs["vram"] - 1) // specs["vram"]
                return (gpu_name, needed, specs["vram"])
        
        # fallback 到最大的
        return ("H100", 1, 80)
    
    def _fit_budget(self, required_memory: int, budget: float, task_type: str) -> tuple:
        """根据预算选择最优 GPU"""
        for gpu_name, specs in sorted(GPU_CATALOG.items(), key=lambda x: x[1]["price_per_hour"]):
            if specs["vram"] >= required_memory:
                hours = budget / specs["price_per_hour"]
                if hours >= 0.5:
                    return (gpu_name, 1, specs["vram"], hours)
        return self._select_gpu(required_memory)
