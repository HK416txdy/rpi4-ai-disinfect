"""
消毒预测器模块
根据污染情况预测消毒参数和能耗
基于消毒数据.json的业务逻辑
"""
from typing import Dict, Any, Optional
import numpy as np


class DisinfectionPredictor:
    """消毒参数预测器"""
    
    def __init__(self):
        # 基于消毒数据.json的规则
        self.mode_mapping = {
            1: '模式1（常规消毒）',
            2: '模式2（强化消毒）',
            3: '模式3（深度消毒）',
            4: '模式4（特殊消毒）'
        }
    
    def predict_disinfection_params(
        self,
        scene_type: int,
        disinfection_object: int,
        bacteria_type: str,
        pollution_grayscale: int,
        colony_density: float,
        pollution_type: int,
        pollution_level: int,
        severity_level: int,
        compliance_standard: int
    ) -> Dict[str, Any]:
        """
        预测消毒参数
        基于消毒数据.json的100条数据训练的经验规则
        """
        
        # 计算消毒模式
        disinfection_mode = self._calculate_mode(
            pollution_level, severity_level, compliance_standard, bacteria_type
        )
        
        # 计算操作力度
        operation_intensity = self._calculate_intensity(
            pollution_level, severity_level, bacteria_type
        )
        
        # 计算操作手法
        operation_method = self._calculate_method(
            disinfection_object, pollution_type
        )
        
        # 计算消毒时间
        disinfection_time = self._calculate_time(
            pollution_level, bacteria_type, compliance_standard
        )
        
        # 计算温度
        temperature = self._calculate_temperature(
            pollution_level, bacteria_type, disinfection_mode
        )
        
        # 计算药剂浓度
        chemical_concentration = self._calculate_concentration(
            pollution_level, bacteria_type, disinfection_mode
        )
        
        # 计算能耗
        initial_energy = self._calculate_initial_energy(
            disinfection_time, temperature, chemical_concentration
        )
        
        final_energy = self._calculate_final_energy(
            initial_energy, pollution_level, bacteria_type
        )
        
        energy_saving_rate = self._calculate_energy_saving(
            initial_energy, final_energy
        )
        
        # 计算灭菌率
        sterilization_rate = self._calculate_sterilization_rate(
            bacteria_type, disinfection_mode, compliance_standard
        )
        
        sterilization_achievement = self._calculate_sterilization_achievement(
            sterilization_rate, compliance_standard
        )
        
        return {
            'disinfection_mode': disinfection_mode,
            'mode_name': self.mode_mapping.get(disinfection_mode, '未知模式'),
            'operation_intensity': operation_intensity,
            'operation_method': operation_method,
            'disinfection_time': disinfection_time,
            'temperature': temperature,
            'chemical_concentration': round(chemical_concentration, 2),
            'initial_energy': round(initial_energy, 2),
            'final_energy': round(final_energy, 2),
            'energy_saving_rate': round(energy_saving_rate, 0),
            'sterilization_rate': round(sterilization_rate, 6),
            'sterilization_achievement': round(sterilization_achievement, 3),
            'success': True
        }
    
    def _calculate_mode(self, pollution_level, severity_level, compliance_standard, bacteria_type) -> int:
        """计算消毒模式"""
        # 基于数据的经验规则
        if pollution_level >= 5 or severity_level >= 4:
            return 4  # 特殊消毒
        elif pollution_level >= 4 or severity_level >= 3:
            return 3  # 深度消毒
        elif pollution_level >= 3 or compliance_standard >= 2:
            return 2  # 强化消毒
        else:
            return 1  # 常规消毒
    
    def _calculate_intensity(self, pollution_level, severity_level, bacteria_type) -> int:
        """计算操作力度"""
        risk_factor = 0
        
        if '耐药菌' in bacteria_type or '特殊病原体' in bacteria_type:
            risk_factor += 1
        
        intensity = pollution_level + severity_level + risk_factor
        
        if intensity <= 3:
            return 1
        elif intensity <= 5:
            return 2
        elif intensity <= 7:
            return 3
        else:
            return 4
    
    def _calculate_method(self, disinfection_object, pollution_type) -> int:
        """计算操作手法"""
        # 简化逻辑
        if disinfection_object in [1, 2]:  # 器械类
            return 2
        else:
            return 1
    
    def _calculate_time(self, pollution_level, bacteria_type, compliance_standard) -> int:
        """计算消毒时间"""
        base_time = 10
        
        # 根据污染等级调整
        time_multiplier = {
            1: 0.8,
            2: 1.0,
            3: 1.3,
            4: 1.6,
            5: 2.0
        }
        
        base_time *= time_multiplier.get(pollution_level, 1.0)
        
        # 根据菌种调整
        if '耐药菌' in bacteria_type:
            base_time *= 1.3
        elif '特殊病原体' in bacteria_type:
            base_time *= 1.5
        elif '致病菌' in bacteria_type:
            base_time *= 1.1
        
        # 根据合规标准调整
        if compliance_standard >= 3:
            base_time *= 1.2
        
        return int(round(base_time))
    
    def _calculate_temperature(self, pollution_level, bacteria_type, disinfection_mode) -> int:
        """计算温度参数"""
        base_temp = 85
        
        # 根据污染等级
        temp_add = {
            1: 5,
            2: 10,
            3: 15,
            4: 20,
            5: 30
        }
        
        base_temp += temp_add.get(pollution_level, 10)
        
        # 根据菌种
        if '耐药菌' in bacteria_type:
            base_temp += 15
        elif '特殊病原体' in bacteria_type:
            base_temp += 25
        elif '致病菌' in bacteria_type:
            base_temp += 10
        
        # 根据消毒模式
        base_temp += (disinfection_mode - 1) * 5
        
        return int(round(base_temp))
    
    def _calculate_concentration(self, pollution_level, bacteria_type, disinfection_mode) -> float:
        """计算药剂浓度"""
        base_conc = 0.25
        
        # 根据污染等级
        conc_add = {
            1: 0.05,
            2: 0.10,
            3: 0.15,
            4: 0.20,
            5: 0.30
        }
        
        base_conc += conc_add.get(pollution_level, 0.10)
        
        # 根据菌种
        if '耐药菌' in bacteria_type:
            base_conc += 0.20
        elif '特殊病原体' in bacteria_type:
            base_conc += 0.30
        elif '致病菌' in bacteria_type:
            base_conc += 0.10
        
        # 根据消毒模式
        base_conc += (disinfection_mode - 1) * 0.08
        
        return round(base_conc, 2)
    
    def _calculate_initial_energy(self, disinfection_time, temperature, chemical_concentration) -> float:
        """计算初始能耗"""
        # 简化能耗模型
        energy = 0.5
        energy += (disinfection_time / 20.0) * 0.3
        energy += ((temperature - 80) / 50.0) * 0.2
        energy += (chemical_concentration / 1.0) * 0.1
        
        return round(energy, 2)
    
    def _calculate_final_energy(self, initial_energy, pollution_level, bacteria_type) -> float:
        """计算最终能耗"""
        # 根据优化程度调整
        optimization_factor = 0.85 - (pollution_level * 0.03)
        
        if '耐药菌' in bacteria_type or '特殊病原体' in bacteria_type:
            optimization_factor += 0.05
        
        final_energy = initial_energy * optimization_factor
        
        return round(final_energy, 2)
    
    def _calculate_energy_saving(self, initial_energy, final_energy) -> float:
        """计算节能率"""
        if initial_energy == 0:
            return 0
        
        saving = ((initial_energy - final_energy) / initial_energy) * 100
        return round(saving, 0)
    
    def _calculate_sterilization_rate(self, bacteria_type, disinfection_mode, compliance_standard) -> float:
        """计算灭菌率"""
        base_rate = 0.999
        
        # 根据菌种调整
        if '耐药菌' in bacteria_type:
            base_rate += 0.0009
        elif '特殊病原体' in bacteria_type:
            base_rate += 0.00099
        
        # 根据消毒模式
        mode_bonus = {
            1: 0,
            2: 0.00001,
            3: 0.00005,
            4: 0.00009
        }
        
        base_rate += mode_bonus.get(disinfection_mode, 0)
        
        # 确保不超过1.0
        return min(base_rate, 0.9999999)
    
    def _calculate_sterilization_achievement(self, sterilization_rate, compliance_standard) -> float:
        """计算灭菌达标程度（‰）"""
        # 合规标准对应的最低要求
        min_requirements = {
            1: 0.999,      # 99.9%
            2: 0.9999,     # 99.99%
            3: 0.99999     # 99.999%
        }
        
        min_rate = min_requirements.get(compliance_standard, 0.999)
        
        # 计算超出部分（‰）
        achievement = (sterilization_rate - min_rate) * 1000
        
        return round(max(achievement, 0), 3)
