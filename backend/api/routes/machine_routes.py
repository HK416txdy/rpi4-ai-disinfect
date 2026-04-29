"""
消毒机管理路由模块
"""
import re
import shutil
from pathlib import Path
from flask import Flask, request, jsonify, session

from data_management.csv_manager import CSVManager
from machine_core.machine import DisinfectionMachine


def register_machine_routes(app: Flask, base_dir: Path):
    """注册消毒机管理路由"""
    
    # 从 app.config 获取 CSVManager 实例
    csv_manager = app.config.get('CSV_MANAGER')
    if not csv_manager:
        from data_management.csv_manager import CSVManager
        csv_manager = CSVManager(base_dir / 'data' / 'machines.csv')
    
    @app.route('/api/machines', methods=['GET'])
    def get_machines():
        """获取所有消毒机列表"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        
        machines = csv_manager.load_machines()
        return jsonify({'success': True, 'machines': machines})
    
    @app.route('/api/add_machine', methods=['POST'])
    def add_machine():
        """添加新消毒机"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        
        data = request.json
        machines = csv_manager.load_machines()
        
        new_machine = {
            'id': csv_manager.get_next_id(),
            'name': data['name'],
            'location': data['location'],
            'enabled': data.get('enabled', True),
            'status': data.get('status', '正常'),
            'disinfected_count': 0,
            'runtime_hours': 0.0
        }
        
        machines.append(new_machine)
        csv_manager.save_machines(machines)
        
        # 创建目录结构
        _create_machine_directories(new_machine['id'], new_machine['name'], base_dir)
        
        return jsonify({'success': True, 'machine': new_machine})
    
    @app.route('/api/delete_machine/<int:machine_id>', methods=['DELETE'])
    def delete_machine(machine_id):
        """删除消毒机"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        
        machines = csv_manager.load_machines()
        machine = next((m for m in machines if m['id'] == machine_id), None)
        
        if not machine:
            return jsonify({'success': False, 'error': '消毒机不存在'})
        
        # 删除目录
        _delete_machine_directories(machine_id, machine['name'], base_dir)
        
        # 从CSV中删除
        machines = [m for m in machines if m['id'] != machine_id]
        csv_manager.save_machines(machines)
        
        return jsonify({'success': True, 'message': '消毒机已删除'})
    
    @app.route('/api/machine/<int:machine_id>', methods=['GET'])
    def get_machine(machine_id):
        """获取单个消毒机详情"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        
        machines = csv_manager.load_machines()
        machine = next((m for m in machines if m['id'] == machine_id), None)
        
        if not machine:
            return jsonify({'success': False, 'error': '消毒机不存在'})
        
        return jsonify({'success': True, 'machine': machine})
    
    def _create_machine_directories(machine_id: int, machine_name: str, base_dir: Path):
        """创建消毒机目录结构"""
        clean_name = re.sub(r'[^\w\u4e00-\u9fff]', '', machine_name)
        machine_folder = f"{machine_id}_{clean_name}"
        machine_dir = base_dir / 'update' / machine_folder
        
        directory_structure = [
            'dirt/images/default',
            'dirt/result',
            'fabric/images/default',
            'fabric/result',
            'equipment/images/default',
            'equipment/result',
            'agor/data/default',
            'agor/result'
        ]
        
        for dir_path in directory_structure:
            (machine_dir / dir_path).mkdir(parents=True, exist_ok=True)
        
        print(f"✅ 创建消毒机目录: {machine_folder}")
    
    def _delete_machine_directories(machine_id: int, machine_name: str, base_dir: Path):
        """删除消毒机目录"""
        clean_name = re.sub(r'[^\w\u4e00-\u9fff]', '', machine_name)
        machine_folder = f"{machine_id}_{clean_name}"
        machine_dir = base_dir / 'update' / machine_folder
        
        if machine_dir.exists():
            shutil.rmtree(machine_dir)
            print(f"🗑️ 删除消毒机目录: {machine_folder}")
