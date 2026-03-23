"""
云平台适配器
"""

from .autodl import AutoDLProvider
from .autodl_playwright import AutoDLPlaywrightProvider
from .lambda_lab import LambdaLabProvider
from .vastai import VastAIProvider
from .runpod import RunPodProvider

__all__ = [
    "AutoDLProvider",
    "AutoDLPlaywrightProvider",
    "LambdaLabProvider",
    "VastAIProvider",
    "RunPodProvider",
]
