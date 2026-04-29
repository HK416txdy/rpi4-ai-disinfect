"""
AI消毒机核心模块
基于消毒数据.json的业务逻辑实现
"""
from .machine import DisinfectionMachine
from .config import MachineConfig
from .detector import StainDetector
from .predictor import DisinfectionPredictor
from .report_generator import ReportGenerator

__all__ = [
    'DisinfectionMachine',
    'MachineConfig', 
    'StainDetector',
    'DisinfectionPredictor',
    'ReportGenerator'
]
