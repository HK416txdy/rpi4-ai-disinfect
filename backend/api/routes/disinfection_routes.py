"""
消毒参数预测路由模块
"""
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, session

from machine_core.machine import DisinfectionRecord


def register_disinfection_routes(app: Flask, base_dir: Path):
    """注册消毒相关路由"""
    
    @app.route('/api/predict_disinfection', methods=['POST'])
    def predict_disinfection():
        """预测消毒参数"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        
        app_context = app.config.get('APP_CONTEXT')
        if not app_context:
            return jsonify({'success': False, 'error': '应用上下文未初始化'}), 500
        
        data = request.json
        
        # 预测消毒参数
        result = app_context.predictor.predict_disinfection_params(
            scene_type=data.get('scene_type', 1),
            disinfection_object=data.get('disinfection_object', 1),
            bacteria_type=data.get('bacteria_type', '普通细菌(大肠杆菌等)'),
            pollution_grayscale=data.get('pollution_grayscale', 128),
            colony_density=data.get('colony_density', 1000),
            pollution_type=data.get('pollution_type', 1),
            pollution_level=data.get('pollution_level', 2),
            severity_level=data.get('severity_level', 2),
            compliance_standard=data.get('compliance_standard', 1)
        )
        
        return jsonify({'success': True, 'prediction': result})
    
    @app.route('/api/execute_disinfection', methods=['POST'])
    def execute_disinfection():
        """执行消毒并记录"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        
        app_context = app.config.get('APP_CONTEXT')
        if not app_context:
            return jsonify({'success': False, 'error': '应用上下文未初始化'}), 500
        
        data = request.json
        machine_id = data.get('machine_id')
        
        # 获取或创建消毒机实例
        machine = app_context.get_machine(
            machine_id=machine_id,
            machine_name=data.get('machine_name', f'消毒机{machine_id}')
        )
        
        # 创建消毒记录
        record = DisinfectionRecord(
            timestamp=datetime.now(),
            scene_type=data.get('scene_type', 1),
            disinfection_object=data.get('disinfection_object', 1),
            bacteria_type=data.get('bacteria_type', '普通细菌(大肠杆菌等)'),
            pollution_grayscale=data.get('pollution_grayscale', 128),
            colony_density=data.get('colony_density', 1000),
            pollution_type=data.get('pollution_type', 1),
            pollution_level=data.get('pollution_level', 2),
            severity_level=data.get('severity_level', 2),
            compliance_standard=data.get('compliance_standard', 1),
            disinfection_mode=data.get('disinfection_mode', 1),
            operation_intensity=data.get('operation_intensity', 1),
            operation_method=data.get('operation_method', 1),
            disinfection_time=data.get('disinfection_time', 20),
            temperature=data.get('temperature', 100),
            chemical_concentration=data.get('chemical_concentration', 0.3),
            initial_energy=data.get('initial_energy', 0.8),
            final_energy=data.get('final_energy', 0.6),
            energy_saving_rate=data.get('energy_saving_rate', 25),
            sterilization_rate=data.get('sterilization_rate', 0.999),
            sterilization_achievement=data.get('sterilization_achievement', 0.5)
        )
        
        # 添加记录
        machine.add_disinfection_record(record)
        
        # 生成报告
        report = app_context.report_generator.generate_disinfection_report(
            machine_id=machine_id,
            machine_name=machine.name,
            disinfection_params={
                'mode': data.get('disinfection_mode', 1),
                'time': data.get('disinfection_time', 20),
                'temperature': data.get('temperature', 100),
                'energy_saving_rate': data.get('energy_saving_rate', 25),
                'sterilization_rate': data.get('sterilization_rate', 0.999)
            },
            detection_result={
                'pollution_level': data.get('pollution_level', 2),
                'mean_grayscale': data.get('pollution_grayscale', 128)
            }
        )
        
        return jsonify({
            'success': True,
            'record_id': len(machine.records),
            'report': report
        })
    
    @app.route('/api/machine_stats/<int:machine_id>', methods=['GET'])
    def get_machine_stats(machine_id):
        """获取消毒机统计数据"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        
        app_context = app.config.get('APP_CONTEXT')
        if not app_context:
            return jsonify({'success': False, 'error': '应用上下文未初始化'}), 500
        
        machine = app_context.get_machine(machine_id)
        stats = machine.get_statistics()
        
        return jsonify({'success': True, 'statistics': stats})
