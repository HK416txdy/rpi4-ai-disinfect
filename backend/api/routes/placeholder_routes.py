"""
临时占位路由模块
为尚未实现的功能提供友好提示
"""
from pathlib import Path
from flask import Flask, request, jsonify, session


def register_placeholder_routes(app: Flask, base_dir: Path):
    """注册占位路由"""
    
    # ========== 器械识别相关 ==========
    @app.route('/api/detect_equipment', methods=['POST'])
    def detect_equipment():
        """器械识别（开发中）"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        return jsonify({
            'success': False, 
            'error': '器械识别功能正在开发中，敬请期待'
        })
    
    @app.route('/api/train_equipment_model', methods=['POST'])
    def train_equipment_model():
        """训练器械识别模型（开发中）"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        return jsonify({
            'success': False, 
            'error': '模型训练功能正在开发中'
        })
    
    @app.route('/api/download_equipment_results/<int:machine_id>', methods=['GET'])
    def download_equipment_results(machine_id):
        """下载器械识别结果（开发中）"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        return jsonify({
            'success': False, 
            'error': '此功能正在开发中'
        })
    
    @app.route('/api/view_equipment_readme/<int:machine_id>', methods=['GET'])
    def view_equipment_readme(machine_id):
        """查看器械识别说明（开发中）"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        return jsonify({
            'success': False, 
            'error': '此功能正在开发中'
        })
    
    @app.route('/api/check_training_status', methods=['GET'])
    def check_training_status():
        """检查训练状态（开发中）"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        return jsonify({
            'success': False, 
            'error': '此功能正在开发中'
        })
    
    # ========== 器械污渍识别相关 ==========
    @app.route('/api/detect_equipment_stain', methods=['POST'])
    def detect_equipment_stain():
        """器械污渍识别（开发中）"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        return jsonify({
            'success': False, 
            'error': '器械污渍识别功能正在开发中'
        })
    
    @app.route('/api/get_equipment_stain_examples/<int:machine_id>', methods=['GET'])
    def get_equipment_stain_examples(machine_id):
        """获取器械污渍实例（开发中）"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        return jsonify({
            'success': False, 
            'error': '此功能正在开发中'
        })
    
    @app.route('/api/download_equipment_stain_examples/<int:machine_id>', methods=['GET'])
    def download_equipment_stain_examples(machine_id):
        """下载器械污渍实例（开发中）"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        return jsonify({
            'success': False, 
            'error': '此功能正在开发中'
        })
    
    # ========== 织物污渍识别相关 ==========
    @app.route('/api/detect_fabric_stain', methods=['POST'])
    def detect_fabric_stain():
        """织物污渍识别（开发中）"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        return jsonify({
            'success': False, 
            'error': '织物污渍识别功能正在开发中'
        })
    
    @app.route('/api/detect_fabric_stain_default', methods=['POST'])
    def detect_fabric_stain_default():
        """织物污渍识别-默认数据（开发中）"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        return jsonify({
            'success': False, 
            'error': '此功能正在开发中'
        })
    
    @app.route('/api/download_fabric_results/<int:machine_id>', methods=['GET'])
    def download_fabric_results(machine_id):
        """下载织物识别结果（开发中）"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        return jsonify({
            'success': False, 
            'error': '此功能正在开发中'
        })
    
    # ========== 消毒预测相关 ==========
    @app.route('/api/simulate_disinfection_default', methods=['POST'])
    def simulate_disinfection_default():
        """模拟消毒预测-默认数据（开发中）"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        return jsonify({
            'success': False, 
            'error': '消毒预测功能正在开发中'
        })
    
    @app.route('/api/download_agor_results/<int:machine_id>', methods=['GET'])
    def download_agor_results(machine_id):
        """下载消毒预测结果（开发中）"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        return jsonify({
            'success': False, 
            'error': '此功能正在开发中'
        })
