"""
摄像头路由模块
"""
from pathlib import Path
from flask import Flask, request, jsonify, session, render_template


def register_camera_routes(app: Flask, base_dir: Path):
    """注册摄像头相关路由"""
    
    @app.route('/camera')
    def camera_panel():
        """摄像头面板页面"""
        if 'user' not in session:
            return render_template('login.html')
        return render_template('camera/panel.html')
    
    @app.route('/camera/<int:device_id>')
    def camera_panel_with_id(device_id):
        """指定设备的摄像头面板页面"""
        if 'user' not in session:
            return render_template('login.html')
        return render_template('camera/panel.html', device_id=device_id)

    @app.route('/api/camera/status', methods=['GET'])
    def camera_status():
        """获取摄像头状态"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        
        # 返回摄像头状态
        return jsonify({
            'success': True,
            'status': 'ready',
            'message': '摄像头就绪'
        })

    @app.route('/api/camera/capture', methods=['POST'])
    def camera_capture_image():
        """拍照并保存图片"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401

        try:
            device_id = request.form.get('device_id')
            image_file = request.files.get('image')

            if not device_id or not image_file:
                return jsonify({'success': False, 'error': '缺少设备ID或图片文件'})

            # 确保上传目录存在
            upload_dir = base_dir / 'frontend' / 'static' / 'uploads' / 'camera'
            upload_dir.mkdir(parents=True, exist_ok=True)

            # 生成文件名
            timestamp = request.form.get('timestamp', '')
            filename = f"device_{device_id}_{timestamp or 'capture'}.jpg"
            filepath = upload_dir / filename

            # 保存文件
            image_file.save(filepath)

            return jsonify({
                'success': True,
                'filename': filename,
                'message': '图片保存成功'
            })

        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/camera/images/<int:device_id>', methods=['GET'])
    def get_device_images(device_id):
        """获取设备的图片列表"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401

        try:
            upload_dir = base_dir / 'frontend' / 'static' / 'uploads' / 'camera'

            if not upload_dir.exists():
                return jsonify({'success': True, 'images': []})

            images = []
            for file_path in upload_dir.glob(f'device_{device_id}_*.jpg'):
                stat = file_path.stat()
                images.append({
                    'filename': file_path.name,
                    'timestamp': stat.st_mtime * 1000,  # JavaScript时间戳
                    'size': stat.st_size
                })

            # 按时间倒序排序
            images.sort(key=lambda x: x['timestamp'], reverse=True)

            return jsonify({'success': True, 'images': images})

        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
