"""
数据导入模块
导入消毒数据.json等外部数据
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional


class DataImporter:
    """数据导入器"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent
    
    def import_disinfection_data(self, json_path: Optional[Path] = None) -> List[Dict[str, Any]]:
        """导入消毒数据.json"""
        
        json_path = json_path or self.data_dir / '消毒数据.json'
        
        if not json_path.exists():
            print(f"❌ 数据文件不存在: {json_path}")
            return []
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取消毒数据明细
            disinfection_records = data.get('消毒数据明细', [])
            
            print(f"✅ 成功导入 {len(disinfection_records)} 条消毒数据")
            
            return disinfection_records
            
        except Exception as e:
            print(f"❌ 导入数据失败: {e}")
            return []
    
    def get_data_info(self, json_path: Optional[Path] = None) -> Dict[str, Any]:
        """获取数据基本信息"""
        
        json_path = json_path or self.data_dir / '消毒数据.json'
        
        if not json_path.exists():
            return {'error': '数据文件不存在'}
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return data.get('数据基本信息', {})
            
        except Exception as e:
            return {'error': f'读取数据失败: {e}'}
    
    def export_training_data(self, output_path: Path, json_path: Optional[Path] = None):
        """导出训练数据格式"""
        
        records = self.import_disinfection_data(json_path)
        
        if not records:
            print("❌ 没有可导出的数据")
            return
        
        # 转换为训练格式
        training_data = []
        for record in records:
            training_sample = {
                'input': {
                    'scene_type': record['场景类型（输入）'],
                    'disinfection_object': record['消毒对象（输入）'],
                    'pollution_grayscale': record['污染物灰度值（输入）'],
                    'colony_density': record['菌落密度（CFU/cm²，输入）'],
                    'pollution_type': record['污染物类型（输入）'],
                    'pollution_level': record['污染等级（1-5，输入）'],
                    'compliance_standard': record['合规标准（输入）']
                },
                'output': {
                    'disinfection_mode': record['消杀模式（输出）'],
                    'operation_intensity': record['操作力度（输出）'],
                    'operation_method': record['操作手法（输出）'],
                    'disinfection_time': record['消毒时间（分钟，输出）'],
                    'temperature': record['温度参数（℃，输出）'],
                    'chemical_concentration': record['药剂浓度（%，输出）'],
                    'final_energy': record['最终能耗（kW·h，输出）'],
                    'sterilization_rate': record['灭菌达标率（输出）']
                }
            }
            training_data.append(training_sample)
        
        # 保存
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(training_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 训练数据已导出到: {output_path}")
        print(f"📊 共导出 {len(training_data)} 条样本")
