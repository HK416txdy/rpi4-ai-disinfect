"""
CSV数据管理模块
管理消毒机的CSV数据存储
"""
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional


class CSVManager:
    """CSV文件管理器"""
    
    def __init__(self, csv_path: Path):
        self.csv_path = csv_path
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    def load_machines(self) -> List[Dict[str, Any]]:
        """从CSV加载消毒机数据"""
        machines = []
        
        if not self.csv_path.exists():
            print(f"⚠️ CSV文件不存在: {self.csv_path}")
            return machines
        
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    machine = {
                        'id': int(row['id']),
                        'name': row['name'],
                        'location': row['location'],
                        'enabled': row['enabled'].lower() == 'true',
                        'status': row['status'],
                        'disinfected_count': int(row['disinfected_count']),
                        'runtime_hours': float(row.get('runtime_hours', 0))
                    }
                    machines.append(machine)
            
            print(f"📖 从CSV加载了 {len(machines)} 台消毒机")
            
        except Exception as e:
            print(f"❌ 读取CSV文件失败: {e}")
        
        return machines
    
    def save_machines(self, machines: List[Dict[str, Any]]):
        """保存消毒机数据到CSV"""
        print(f"💾 保存 {len(machines)} 台消毒机到: {self.csv_path}")
        
        try:
            with open(self.csv_path, 'w', encoding='utf-8', newline='') as file:
                fieldnames = ['id', 'name', 'location', 'enabled', 'status', 
                            'disinfected_count', 'runtime_hours']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                
                for machine in machines:
                    writer.writerow({
                        'id': machine['id'],
                        'name': machine['name'],
                        'location': machine['location'],
                        'enabled': str(machine['enabled']),
                        'status': machine['status'],
                        'disinfected_count': machine['disinfected_count'],
                        'runtime_hours': f"{machine.get('runtime_hours', 0):.2f}"
                    })
            
            print("✅ CSV文件保存成功")
            
        except Exception as e:
            print(f"❌ 保存CSV文件失败: {e}")
    
    def get_next_id(self) -> int:
        """获取下一个可用的ID"""
        machines = self.load_machines()
        if not machines:
            return 1
        return max(machine['id'] for machine in machines) + 1
    
    def create_default_data(self):
        """创建默认的初始数据"""
        if self.csv_path.exists():
            print("⚠️ CSV文件已存在，跳过创建")
            return
        
        print("📝 创建默认消毒机数据...")
        
        default_machines = [
            {
                'id': 1,
                'name': '消毒机A',
                'location': '北京市海淀区',
                'enabled': True,
                'status': '正常',
                'disinfected_count': 1250,
                'runtime_hours': 125.5
            },
            {
                'id': 2,
                'name': '消毒机B',
                'location': '上海市浦东新区',
                'enabled': True,
                'status': '警告',
                'disinfected_count': 890,
                'runtime_hours': 89.0
            }
        ]
        
        self.save_machines(default_machines)
        print("✅ 默认数据创建完成")
