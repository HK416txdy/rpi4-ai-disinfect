"""
硬件控制路由模块
处理来自硬件设备的通信和控制命令
"""
from pathlib import Path
from flask import Flask, request, jsonify, session
from datetime import datetime
import json
from typing import Dict, Any
import threading
import cv2


def register_hardware_routes(app: Flask, base_dir: Path):
    """注册硬件相关路由"""

    # 存储设备状态和命令的简单内存存储（生产环境应使用数据库）
    device_states = {}
    pending_commands = {}

    # 线程锁保护共享数据结构
    device_states_lock = threading.Lock()
    pending_commands_lock = threading.Lock()

    @app.route('/api/health', methods=['GET'])
    def health_check():
        """健康检查接口"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'AI消毒机后端'
        })

    @app.route('/api/hardware/detection', methods=['POST'])
    def receive_hardware_detection():
        """接收硬件检测数据"""
        try:
            data = request.json
            if not data:
                return jsonify({'success': False, 'error': '无数据'}), 400

            machine_id = data.get('machine_id')
            detection_data = data.get('detection_data')
            timestamp = data.get('timestamp')

            if not machine_id or not detection_data:
                return jsonify({'success': False, 'error': '缺少必要参数'}), 400

            # 处理检测数据
            result = _process_detection_data(machine_id, detection_data, timestamp)

            # 更新设备状态
            with device_states_lock:
                device_states[machine_id] = {
                    'last_detection': timestamp,
                    'status': 'active',
                    'last_update': datetime.now().isoformat()
                }

            return jsonify({
                'success': True,
                'processed': True,
                'result': result,
                'timestamp': datetime.now().isoformat()
            })

        except Exception as e:
            print(f"处理硬件检测数据失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/hardware/control/<int:machine_id>', methods=['GET'])
    def get_hardware_commands(machine_id):
        """获取设备的控制命令"""
        try:
            with pending_commands_lock:
                commands = pending_commands.get(machine_id, {'commands': []})

                # 获取后清除待处理命令（避免重复执行）
                if commands['commands']:
                    pending_commands[machine_id] = {'commands': []}

            return jsonify(commands)

        except Exception as e:
            print(f"获取控制命令失败: {e}")
            return jsonify({'commands': []}), 500

    @app.route('/api/hardware/control/<int:machine_id>', methods=['POST'])
    def send_hardware_command(machine_id):
        """发送控制命令到硬件设备"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401

        try:
            data = request.json
            command = data.get('command')
            parameters = data.get('parameters', {})

            if not command:
                return jsonify({'success': False, 'error': '缺少命令参数'}), 400

            # 验证命令类型
            valid_commands = ['power_on', 'power_off', 'restart', 'update_config', 'calibrate']
            if command not in valid_commands:
                return jsonify({'success': False, 'error': f'无效命令: {command}'}), 400

            # 创建命令
            cmd_data = {
                'id': f"cmd_{int(datetime.now().timestamp())}",
                'command': command,
                'parameters': parameters,
                'timestamp': datetime.now().isoformat(),
                'from_user': session.get('user')
            }

            # 添加到待处理命令队列
            with pending_commands_lock:
                if machine_id not in pending_commands:
                    pending_commands[machine_id] = {'commands': []}

                pending_commands[machine_id]['commands'].append(cmd_data)

            print(f"📤 控制命令已发送到设备 {machine_id}: {command}")

            return jsonify({
                'success': True,
                'command_id': cmd_data['id'],
                'message': f'命令 {command} 已发送到设备 {machine_id}'
            })

        except Exception as e:
            print(f"发送控制命令失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/hardware/status', methods=['POST'])
    def receive_hardware_status():
        """接收硬件状态更新"""
        try:
            data = request.json
            machine_id = data.get('machine_id')
            status = data.get('status')
            timestamp = data.get('timestamp')

            if not machine_id:
                return jsonify({'success': False, 'error': '缺少机器ID'}), 400

            # 更新设备状态
            with device_states_lock:
                device_states[machine_id] = {
                    'status': status,
                    'last_update': timestamp,
                    'online': True
                }

            return jsonify({'success': True, 'received': True})

        except Exception as e:
            print(f"接收硬件状态失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/hardware/status/<int:machine_id>', methods=['GET'])
    def get_hardware_status(machine_id):
        """获取硬件设备状态"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401

        try:
            with device_states_lock:
                status = device_states.get(machine_id, {
                    'status': 'unknown',
                    'last_update': None,
                    'online': False
                })

            # 计算运行时间（如果有运行时间数据）
            runtime_info = _calculate_runtime_info(machine_id)

            return jsonify({
                'success': True,
                'machine_id': machine_id,
                'status': status,
                'runtime_info': runtime_info
            })

        except Exception as e:
            print(f"获取硬件状态失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/hardware/upload', methods=['POST'])
    def upload_hardware_image():
        """接收硬件上传的图片并分析"""
        try:
            # 获取上传的文件
            image_file = request.files.get('image')
            machine_id = request.form.get('machine_id')
            timestamp = request.form.get('timestamp')
            detection_info = request.form.get('detection_info')

            if not image_file or not machine_id:
                return jsonify({'success': False, 'error': '缺少必要参数'}), 400

            # 解析检测信息
            detection_data = {}
            if detection_info:
                try:
                    detection_data = json.loads(detection_info)
                except:
                    detection_data = {}

            # 保存图片
            upload_dir = base_dir / 'frontend' / 'static' / 'uploads' / 'hardware'
            upload_dir.mkdir(parents=True, exist_ok=True)

            filename = f"hardware_{machine_id}_{timestamp or 'upload'}.jpg"
            filepath = upload_dir / filename
            image_file.save(filepath)

            # 读取图片进行分析
            image = cv2.imread(str(filepath))
            if image is None:
                return jsonify({'success': False, 'error': '图片读取失败'}), 400

            # 获取应用上下文
            app_context = app.config.get('APP_CONTEXT')
            if not app_context:
                return jsonify({'success': False, 'error': '应用上下文未初始化'}), 500

            # 进行污渍检测
            grayscale_result = app_context.detector.analyze_grayscale(image)
            stain_result = app_context.detector.detect_stains(image)

            # 分析污染等级
            gray_value = grayscale_result.get('mean_grayscale', 128) if grayscale_result.get('success') else 128
            colony_density = 1000  # 默认值，可以从检测结果扩展
            pollution_info = app_context.detector.get_pollution_level(gray_value, colony_density)

            # 使用AI预测器计算消毒参数
            disinfection_params = {}
            if app_context.predictor and grayscale_result.get('success'):
                disinfection_params = app_context.predictor.predict_disinfection_params(
                    scene_type=1,  # 默认场景
                    disinfection_object=1,  # 默认对象
                    bacteria_type='普通细菌(大肠杆菌等)',
                    pollution_grayscale=int(gray_value),
                    colony_density=colony_density,
                    pollution_type=pollution_info['pollution_level'],
                    pollution_level=pollution_info['pollution_level'],
                    severity_level=pollution_info['severity_level'],
                    compliance_standard=1
                )

            # 计算GPIO持续时间（基于污染等级）
            gpio_duration = _calculate_gpio_duration(pollution_info, disinfection_params)

            # 准备响应数据
            result = {
                'success': True,
                'machine_id': int(machine_id),
                'timestamp': timestamp,
                'filename': filename,
                'gpio_duration': gpio_duration,
                'analysis': {
                    'grayscale_analysis': grayscale_result,
                    'stain_detection': stain_result,
                    'pollution_assessment': pollution_info,
                    'disinfection_params': disinfection_params
                },
                'message': f'图片已接收并分析，GPIO持续时间: {gpio_duration}秒'
            }

            print(f"[HARDWARE] 收到设备 {machine_id} 的图片，分析完成，GPIO时长: {gpio_duration}s")
            return jsonify(result)

        except Exception as e:
            print(f"硬件图片上传处理失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500


def _process_detection_data(machine_id: int, detection_data: Dict[str, Any], timestamp: str) -> Dict[str, Any]:
    """处理检测数据"""
    try:
        # 获取应用上下文
        from flask import current_app
        app_context = current_app.config.get('APP_CONTEXT')

        if not app_context:
            return {'error': '应用上下文未初始化'}

        # 提取检测结果
        grayscale = detection_data.get('grayscale_analysis', {})
        stains = detection_data.get('stain_detection', {})

        # 使用AI预测器进行进一步分析
        if app_context.predictor and grayscale.get('success'):
            # 基于灰度分析进行污染预测
            gray_value = grayscale.get('mean_grayscale', 128)
            colony_density = 1000  # 默认值，可以从检测数据扩展

            pollution_info = app_context.detector.get_pollution_level(gray_value, colony_density)

            # 生成消毒建议
            disinfection_params = app_context.predictor.predict_disinfection_params(
                scene_type=1,  # 默认场景
                disinfection_object=1,  # 默认对象
                bacteria_type='普通细菌(大肠杆菌等)',
                pollution_grayscale=int(gray_value),
                colony_density=colony_density,
                pollution_type=pollution_info['pollution_level'],
                pollution_level=pollution_info['pollution_level'],
                severity_level=pollution_info['severity_level'],
                compliance_standard=1
            )

            return {
                'machine_id': machine_id,
                'timestamp': timestamp,
                'detection': {
                    'grayscale_analysis': grayscale,
                    'stain_detection': stains,
                    'pollution_assessment': pollution_info
                },
                'ai_analysis': disinfection_params,
                'recommendations': {
                    'disinfection_mode': disinfection_params.get('disinfection_mode'),
                    'estimated_time': disinfection_params.get('disinfection_time', 0),
                    'energy_saving': disinfection_params.get('energy_saving_rate', 0)
                }
            }

        return {
            'machine_id': machine_id,
            'timestamp': timestamp,
            'detection': {
                'grayscale_analysis': grayscale,
                'stain_detection': stains
            },
            'ai_analysis': None
        }

    except Exception as e:
        print(f"处理检测数据异常: {e}")
        return {'error': str(e)}


def _calculate_runtime_info(machine_id: int) -> Dict[str, Any]:
    """计算设备运行时间信息"""
    # 这里应该从数据库或持久化存储中获取实际数据
    # 目前使用模拟数据
    return {
        'total_runtime_hours': 1247.5,  # 模拟数据
        'current_session_hours': 2.5,
        'maintenance_due_hours': 500,  # 距下次维护的小时数
        'health_percentage': 85.3,  # 设备健康度 百分比
        'estimated_lifespan_remaining_months': 18
    }


def _calculate_gpio_duration(pollution_info: Dict[str, Any], disinfection_params: Dict[str, Any]) -> int:
    """计算GPIO持续时间（秒）"""
    try:
        # 基于污染等级和消毒参数计算持续时间
        level = pollution_info.get('pollution_level', 1)
        severity = pollution_info.get('severity_level', 1)
        duration = disinfection_params.get('disinfection_time', 0)

        # 简单的计算示例：根据污染等级和严重程度调整时间
        gpio_duration = max(10, min(300, duration + level * 10 + severity * 5))

        return gpio_duration

    except Exception as e:
        print(f"计算GPIO持续时间失败: {e}")
        return 60  # 默认60秒

