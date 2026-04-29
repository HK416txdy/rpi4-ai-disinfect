"""
消毒机核心类
管理消毒机的状态、运行和数据处理
"""
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from dataclasses import dataclass, field

from .config import MachineConfig


@dataclass
class DisinfectionRecord:
    """消毒记录数据类"""
    timestamp: datetime
    scene_type: int
    disinfection_object: int
    bacteria_type: str
    pollution_grayscale: int
    colony_density: float  # CFU/cm²
    pollution_type: int
    pollution_level: int  # 1-5
    severity_level: int  # 1-4
    compliance_standard: int
    
    # 输出参数
    disinfection_mode: int
    operation_intensity: int
    operation_method: int
    disinfection_time: int  # 分钟
    temperature: int  # ℃
    chemical_concentration: float  # %
    
    # 能耗与效果
    initial_energy: float  # kW·h
    final_energy: float  # kW·h
    energy_saving_rate: float  # %
    sterilization_rate: float
    sterilization_achievement: float  # ‰


class DisinfectionMachine:
    """消毒机主类"""
    
    def __init__(self, machine_id: int, name: str, location: str = '', 
                 config: Optional[MachineConfig] = None):
        self.machine_id = machine_id
        self.name = name
        self.location = location
        self.config = config or MachineConfig()
        
        # 状态信息
        self.enabled = True
        self.status = '正常'
        self.disinfected_count = 0
        self.runtime_hours = 0.0
        
        # 数据存储
        self.records: List[DisinfectionRecord] = []
        self.data_dir = Path(__file__).parent.parent.parent / 'data' / f'machine_{machine_id}'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 运行时追踪
        self.current_session_start: Optional[datetime] = None
        self.total_runtime_seconds = 0
    
    def start_session(self):
        """开始消毒会话"""
        self.current_session_start = datetime.now()
        print(f"🟢 消毒机 {self.name} 开始运行会话")
    
    def end_session(self):
        """结束消毒会话"""
        if self.current_session_start:
            duration = (datetime.now() - self.current_session_start).total_seconds()
            self.total_runtime_seconds += duration
            self.runtime_hours = self.total_runtime_seconds / 3600
            self.current_session_start = None
            print(f"🔴 消毒机 {self.name} 结束运行会话，本次运行 {duration:.0f} 秒")
    
    def add_disinfection_record(self, record: DisinfectionRecord):
        """添加消毒记录"""
        self.records.append(record)
        self.disinfected_count += 1
        self._save_record(record)
    
    def _save_record(self, record: DisinfectionRecord):
        """保存单条记录到文件"""
        record_file = self.data_dir / f'record_{len(self.records)}.json'
        record_data = {
            'timestamp': record.timestamp.isoformat(),
            'scene_type': record.scene_type,
            'disinfection_object': record.disinfection_object,
            'bacteria_type': record.bacteria_type,
            'pollution_grayscale': record.pollution_grayscale,
            'colony_density': record.colony_density,
            'pollution_type': record.pollution_type,
            'pollution_level': record.pollution_level,
            'severity_level': record.severity_level,
            'compliance_standard': record.compliance_standard,
            'disinfection_mode': record.disinfection_mode,
            'operation_intensity': record.operation_intensity,
            'operation_method': record.operation_method,
            'disinfection_time': record.disinfection_time,
            'temperature': record.temperature,
            'chemical_concentration': record.chemical_concentration,
            'initial_energy': record.initial_energy,
            'final_energy': record.final_energy,
            'energy_saving_rate': record.energy_saving_rate,
            'sterilization_rate': record.sterilization_rate,
            'sterilization_achievement': record.sterilization_achievement
        }
        
        with open(record_file, 'w', encoding='utf-8') as f:
            json.dump(record_data, f, ensure_ascii=False, indent=2)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计数据"""
        if not self.records:
            return {
                'total_disinfections': 0,
                'avg_energy_saving': 0,
                'avg_sterilization_rate': 0,
                'total_runtime_hours': self.runtime_hours
            }
        
        total_energy_saving = sum(r.energy_saving_rate for r in self.records)
        total_sterilization = sum(r.sterilization_rate * 100 for r in self.records)
        
        return {
            'total_disinfections': len(self.records),
            'avg_energy_saving': total_energy_saving / len(self.records),
            'avg_sterilization_rate': total_sterilization / len(self.records),
            'total_runtime_hours': self.runtime_hours,
            'machine_status': self.status
        }
    
    def load_records(self):
        """加载历史消毒记录"""
        self.records = []
        for record_file in sorted(self.data_dir.glob('record_*.json')):
            try:
                with open(record_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    record = DisinfectionRecord(
                        timestamp=datetime.fromisoformat(data['timestamp']),
                        scene_type=data['scene_type'],
                        disinfection_object=data['disinfection_object'],
                        bacteria_type=data['bacteria_type'],
                        pollution_grayscale=data['pollution_grayscale'],
                        colony_density=data['colony_density'],
                        pollution_type=data['pollution_type'],
                        pollution_level=data['pollution_level'],
                        severity_level=data['severity_level'],
                        compliance_standard=data['compliance_standard'],
                        disinfection_mode=data['disinfection_mode'],
                        operation_intensity=data['operation_intensity'],
                        operation_method=data['operation_method'],
                        disinfection_time=data['disinfection_time'],
                        temperature=data['temperature'],
                        chemical_concentration=data['chemical_concentration'],
                        initial_energy=data['initial_energy'],
                        final_energy=data['final_energy'],
                        energy_saving_rate=data['energy_saving_rate'],
                        sterilization_rate=data['sterilization_rate'],
                        sterilization_achievement=data['sterilization_achievement']
                    )
                    self.records.append(record)
            except Exception as e:
                print(f"❌ 加载记录失败 {record_file}: {e}")
        
        self.disinfected_count = len(self.records)
        print(f"📖 加载了 {len(self.records)} 条消毒记录")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.machine_id,
            'name': self.name,
            'location': self.location,
            'enabled': self.enabled,
            'status': self.status,
            'disinfected_count': self.disinfected_count,
            'runtime_hours': round(self.runtime_hours, 2)
        }
