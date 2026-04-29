"""
污渍检测路由模块
"""
from pathlib import Path
from flask import Flask, request, jsonify, session


def register_detection_routes(app: Flask, base_dir: Path):
    """注册检测相关路由"""
    
    @app.route('/api/init_camera', methods=['POST'])
    def init_camera():
        """初始化摄像头"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        
        # 从 app.config 获取 AppContext
        app_context = app.config.get('APP_CONTEXT')
        if not app_context:
            return jsonify({'success': False, 'error': '应用上下文未初始化'}), 500
        
        success = app_context.detector.initialize_camera()
        return jsonify({'success': success})
    
    @app.route('/api/capture_image', methods=['POST'])
    def capture_image():
        """捕获图像并检测"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        
        app_context = app.config.get('APP_CONTEXT')
        if not app_context:
            return jsonify({'success': False, 'error': '应用上下文未初始化'}), 500
        
        data = request.json
        save_path = data.get('save_path')
        
        image = app_context.detector.capture_image(
            save_path=Path(save_path) if save_path else None
        )
        
        if image is None:
            return jsonify({'success': False, 'error': '图像捕获失败'})
        
        # 灰度分析
        grayscale_result = app_context.detector.analyze_grayscale(image)
        
        # 污渍检测
        detection_method = data.get('method', 'combined')
        stain_result = app_context.detector.detect_stains(image, method=detection_method)
        
        return jsonify({
            'success': True,
            'grayscale': grayscale_result,
            'stains': stain_result
        })
    
    @app.route('/api/analyze_pollution', methods=['POST'])
    def analyze_pollution():
        """分析污染等级"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        
        app_context = app.config.get('APP_CONTEXT')
        if not app_context:
            return jsonify({'success': False, 'error': '应用上下文未初始化'}), 500
        
        data = request.json
        gray_value = data.get('gray_value', 128)
        colony_density = data.get('colony_density', 1000)
        
        pollution_info = app_context.detector.get_pollution_level(gray_value, colony_density)
        
        return jsonify({
            'success': True,
            'pollution': pollution_info
        })
    
    @app.route('/api/release_camera', methods=['POST'])
    def release_camera():
        """释放摄像头"""
        app_context = app.config.get('APP_CONTEXT')
        if app_context:
            app_context.detector.release()
        return jsonify({'success': True})
