"""
应用上下文模块
管理应用的全局实例和共享资源
"""
from pathlib import Path
from typing import Dict, Any, Optional


class AppContext:
    """应用上下文，管理全局实例"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        
        # 延迟初始化
        self._detector = None
        self._predictor = None
        self._report_generator = None
        self._machines_cache = {}
    
    @property
    def detector(self):
        """获取污渍检测器实例"""
        if self._detector is None:
            from hardware.machine_core.detector import StainDetector
            self._detector = StainDetector()
        return self._detector
    
    @property
    def predictor(self):
        """获取消毒预测器实例"""
        if self._predictor is None:
            from machine_core.predictor import DisinfectionPredictor
            self._predictor = DisinfectionPredictor()
        return self._predictor
    
    @property
    def report_generator(self):
        """获取报告生成器实例"""
        if self._report_generator is None:
            from machine_core.report_generator import ReportGenerator
            self._report_generator = ReportGenerator()
        return self._report_generator
    
    def get_machine(self, machine_id: int, machine_name: str = ''):
        """获取或创建消毒机实例"""
        if machine_id not in self._machines_cache:
            from machine_core.machine import DisinfectionMachine
            self._machines_cache[machine_id] = DisinfectionMachine(
                machine_id=machine_id,
                name=machine_name or f'消毒机{machine_id}'
            )
            # 加载历史记录
            self._machines_cache[machine_id].load_records()
        return self._machines_cache[machine_id]
    
    def cleanup(self):
        """清理资源"""
        if self._detector:
            self._detector.release()
        self._machines_cache.clear()
