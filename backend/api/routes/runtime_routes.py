
"""
运行时管理路由模块
管理消毒机的运行状态和计时器
"""
import json
from pathlib import Path
from flask import Flask, request, jsonify, session
from datetime import datetime
class RuntimeManager:
    """运行时状态管理器"""
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.runtime_file = data_dir / 'runtime_status.json'
        self._load_status()
    def _load_status(self):
        """加载运行状态"""
        self.status = {}
        if self.runtime_file.exists():
            try:
                with open(self.runtime_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for machine_id, status in data.items():
                        self.status[int(machine_id)] = {
                            'is_running': status.get('is_running', False),
                            'start_time': datetime.fromisoformat(status['start_time']) if status.get('start_time') else None,
                            'total_seconds': status.get('total_seconds', 0),
                            'machine_name': status.get('machine_name', f'消毒机{machine_id}')
                        }
            except Exception as e:
                print(f"❌ 加载运行状态失败: {e}")
    def _save_status(self):
        """保存运行状态"""
        data = {}
        for machine_id, status in self.status.items():
            data[str(machine_id)] = {
                'is_running': status['is_running'],
                'start_time': status['start_time'].isoformat() if status['start_time'] else None,
                'total_seconds': status['total_seconds'],
                'machine_name': status['machine_name']
            }
        with open(self.runtime_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    def start_runtime(self, machine_id: int, machine_name: str):
        """开始运行"""
        if machine_id not in self.status:
            self.status[machine_id] = {
                'is_running': False,
                'start_time': None,
                'total_seconds': 0,
                'machine_name': machine_name
            }
        if not self.status[machine_id]['is_running']:
            self.status[machine_id]['is_running'] = True
            self.status[machine_id]['start_time'] = datetime.now()
            self.status[machine_id]['machine_name'] = machine_name
            self._save_status()
            return True
        return False
    def stop_runtime(self, machine_id: int):
        """停止运行"""
        if machine_id in self.status and self.status[machine_id]['is_running']:
            start_time = self.status[machine_id]['start_time']
            if start_time:
                duration = (datetime.now() - start_time).total_seconds()
                self.status[machine_id]['total_seconds'] += duration
            self.status[machine_id]['is_running'] = False
            self.status[machine_id]['start_time'] = None
            self._save_status()
            return True
        return False
    def get_status(self, machine_id: int):
        """获取机器状态"""
        if machine_id not in self.status:
            return {
                'machine_id': machine_id,
                'is_running': False,
                'total_hours': 0,
                'lifetime_status': self._calculate_lifetime_status(0)
            }
        status = self.status[machine_id]
        total_seconds = status['total_seconds']
        # 如果正在运行，计算当前运行时间
        if status['is_running'] and status['start_time']:
            current_duration = (datetime.now() - status['start_time']).total_seconds()
            total_seconds += current_duration
        total_hours = total_seconds / 3600
        return {
            'machine_id': machine_id,
            'is_running': status['is_running'],
            'total_hours': total_hours,
            'lifetime_status': self._calculate_lifetime_status(total_hours)
        }
    def get_all_status(self):
        """获取所有机器状态"""
        machines = []
        for machine_id in self.status.keys():
            machines.append(self.get_status(machine_id))
        return machines
    def _calculate_lifetime_status(self, total_hours: float):
        """计算寿命状态"""
        # 假设设计寿命为1000小时
        design_hours = 1000
        percentage = (total_hours / design_hours) * 100
        if percentage < 50:
            level = 'good'
            status = '良好'
            message = f'设备运行正常，使用率 {percentage:.1f}%'
        elif percentage < 75:
            level = 'normal'
            status = '一般'
            message = f'设备需要注意维护，使用率 {percentage:.1f}%'
        elif percentage < 90:
            level = 'warning'
            status = '警告'
            message = f'设备即将达到使用寿命，使用率 {percentage:.1f}%'
        else:
            level = 'danger'
            status = '危险'
            message = f'设备已超期使用，使用率 {percentage:.1f}%'
        remaining_hours = max(0, design_hours - total_hours)
        return {
            'level': level,
            'status': status,
            'percentage': round(percentage, 1),
            'remaining_hours': remaining_hours,
            'message': message
        }
def register_runtime_routes(app: Flask, base_dir: Path):
    """注册运行时管理路由"""
    runtime_manager = RuntimeManager(base_dir / 'data')
    @app.route('/api/runtime/start', methods=['POST'])
    def start_runtime():
        """开始运行计时器"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        data = request.json
        machine_id = data.get('machine_id')
        machine_name = data.get('machine_name', f'消毒机{machine_id}')
        if not machine_id:
            return jsonify({'success': False, 'error': '缺少机器ID'})
        success = runtime_manager.start_runtime(machine_id, machine_name)
        if success:
            return jsonify({'success': True, 'message': f'开始运行 {machine_name}'})
        else:
            return jsonify({'success': False, 'error': '机器已在运行中'})
    @app.route('/api/runtime/stop', methods=['POST'])
    def stop_runtime():
        """停止运行计时器"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        data = request.json
        machine_id = data.get('machine_id')
        if not machine_id:
            return jsonify({'success': False, 'error': '缺少机器ID'})
        success = runtime_manager.stop_runtime(machine_id)
        if success:
            return jsonify({'success': True, 'message': '停止运行'})
        else:
            return jsonify({'success': False, 'error': '机器未在运行'})
    @app.route('/api/runtime/status/<int:machine_id>', methods=['GET'])
    def get_runtime_status(machine_id):
        """获取单个机器运行状态"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        status = runtime_manager.get_status(machine_id)
        return jsonify({'success': True, **status})
    @app.route('/api/runtime/all_status', methods=['GET'])
    def get_all_runtime_status():
        """获取所有机器运行状态"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        machines = runtime_manager.get_all_status()
        return jsonify({'success': True, 'machines': machines})
