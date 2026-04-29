"""
单元测试 - 消毒机核心模块
"""
import unittest
from pathlib import Path
from datetime import datetime
import sys

# 添加src和hardware到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'hardware'))

from machine_core.machine import DisinfectionMachine, DisinfectionRecord
from machine_core.config import MachineConfig
from hardware.machine_core.detector import StainDetector
from machine_core.predictor import DisinfectionPredictor


class TestDisinfectionMachine(unittest.TestCase):
    """测试消毒机类"""
    
    def setUp(self):
        """测试前准备"""
        self.machine = DisinfectionMachine(
            machine_id=999,
            name='测试消毒机',
            location='测试位置'
        )
    
    def test_machine_creation(self):
        """测试消毒机创建"""
        self.assertEqual(self.machine.machine_id, 999)
        self.assertEqual(self.machine.name, '测试消毒机')
        self.assertTrue(self.machine.enabled)
        self.assertEqual(self.machine.status, '正常')
    
    def test_session_management(self):
        """测试会话管理"""
        self.machine.start_session()
        self.assertIsNotNone(self.machine.current_session_start)
        
        self.machine.end_session()
        self.assertIsNone(self.machine.current_session_start)
        self.assertGreaterEqual(self.machine.total_runtime_seconds, 0)
    
    def test_add_record(self):
        """测试添加消毒记录"""
        record = DisinfectionRecord(
            timestamp=datetime.now(),
            scene_type=1,
            disinfection_object=1,
            bacteria_type='普通细菌(大肠杆菌等)',
            pollution_grayscale=128,
            colony_density=1000,
            pollution_type=1,
            pollution_level=2,
            severity_level=2,
            compliance_standard=1,
            disinfection_mode=1,
            operation_intensity=1,
            operation_method=1,
            disinfection_time=15,
            temperature=95,
            chemical_concentration=0.3,
            initial_energy=0.75,
            final_energy=0.60,
            energy_saving_rate=20,
            sterilization_rate=0.999,
            sterilization_achievement=0.0
        )
        
        self.machine.add_disinfection_record(record)
        self.assertEqual(len(self.machine.records), 1)
        self.assertEqual(self.machine.disinfected_count, 1)
    
    def test_statistics(self):
        """测试统计数据"""
        stats = self.machine.get_statistics()
        self.assertIn('total_disinfections', stats)
        self.assertIn('avg_energy_saving', stats)
        self.assertIn('avg_sterilization_rate', stats)


class TestMachineConfig(unittest.TestCase):
    """测试配置管理类"""
    
    def setUp(self):
        self.config = MachineConfig()
    
    def test_default_config(self):
        """测试默认配置"""
        modes = self.config.get('disinfection_modes')
        self.assertIsNotNone(modes)
        self.assertEqual(len(modes), 4)
    
    def test_config_set_get(self):
        """测试配置设置和获取"""
        self.config.set('test_key', 'test_value')
        self.assertEqual(self.config.get('test_key'), 'test_value')
    
    def test_config_save_load(self):
        """测试配置保存和加载"""
        self.config.set('test_key', 'test_value')
        self.config.save('test_config.json')
        
        new_config = MachineConfig()
        new_config.load('test_config.json')
        self.assertEqual(new_config.get('test_key'), 'test_value')


class TestStainDetector(unittest.TestCase):
    """测试污渍检测器"""
    
    def setUp(self):
        self.detector = StainDetector()
    
    def test_pollution_level_calculation(self):
        """测试污染等级计算"""
        # 轻度污染
        result = self.detector.get_pollution_level(80, 500)
        self.assertEqual(result['pollution_level'], 1)
        self.assertEqual(result['severity_level'], 1)
        
        # 中度污染
        result = self.detector.get_pollution_level(130, 2000)
        self.assertEqual(result['pollution_level'], 2)
        self.assertEqual(result['severity_level'], 2)
        
        # 重度污染
        result = self.detector.get_pollution_level(190, 4500)
        self.assertEqual(result['pollution_level'], 4)
        self.assertEqual(result['severity_level'], 3)
        
        # 极重污染
        result = self.detector.get_pollution_level(210, 5500)
        self.assertEqual(result['pollution_level'], 5)
        self.assertEqual(result['severity_level'], 4)


class TestDisinfectionPredictor(unittest.TestCase):
    """测试消毒预测器"""
    
    def setUp(self):
        self.predictor = DisinfectionPredictor()
    
    def test_prediction_output(self):
        """测试预测输出"""
        result = self.predictor.predict_disinfection_params(
            scene_type=1,
            disinfection_object=1,
            bacteria_type='普通细菌(大肠杆菌等)',
            pollution_grayscale=128,
            colony_density=1500,
            pollution_type=1,
            pollution_level=2,
            severity_level=2,
            compliance_standard=1
        )
        
        self.assertTrue(result['success'])
        self.assertIn('disinfection_mode', result)
        self.assertIn('disinfection_time', result)
        self.assertIn('temperature', result)
        self.assertIn('chemical_concentration', result)
        self.assertIn('energy_saving_rate', result)
        self.assertIn('sterilization_rate', result)
    
    def test_high_pollution_prediction(self):
        """测试高污染情况预测"""
        result = self.predictor.predict_disinfection_params(
            scene_type=1,
            disinfection_object=1,
            bacteria_type='耐药菌(MRSA等)',
            pollution_grayscale=210,
            colony_density=5500,
            pollution_type=1,
            pollution_level=5,
            severity_level=4,
            compliance_standard=3
        )
        
        # 高污染应使用更强的消毒模式
        self.assertGreaterEqual(result['disinfection_mode'], 3)
        self.assertGreater(result['disinfection_time'], 25)
        self.assertGreater(result['temperature'], 110)


if __name__ == '__main__':
    unittest.main()
