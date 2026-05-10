#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
树莓派运动检测 - 服务端接收程序（带主动控制）
"""

import os
import json
from datetime import datetime
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = '/tmp/rpi_uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    test_file = os.path.join(UPLOAD_FOLDER, '.write_test')
    with open(test_file, 'w') as f:
        f.write('test')
    os.remove(test_file)
    print(f"[OK] 上传目录可写: {UPLOAD_FOLDER}")
except PermissionError:
    print(f"[ERROR] 上传目录无写权限: {UPLOAD_FOLDER}")
    raise

# 设备状态 + 控制配置存储
devices_status = {}
# ★★★ 设备控制配置（你可以在这里或数据库中管理）★★★
devices_config = {
    # machine_id: {'gpio_duration': 秒数, 'enabled': 是否启用}
    1: {'gpio_duration': 5.0, 'enabled': True},   # 默认设备1，5秒
}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_machine_folder(machine_id):
    folder = os.path.join(UPLOAD_FOLDER, str(machine_id))
    os.makedirs(folder, exist_ok=True)
    return folder


def decide_gpio_duration(machine_id, detection_info):
    """
    根据设备配置决定高电平持续时间
    优先级：设备配置 > 检测信息动态计算 > 默认值
    """
    # 1. 检查设备是否有专属配置
    if machine_id in devices_config:
        config = devices_config[machine_id]
        if not config.get('enabled', True):
            print(f"[CONTROL] 设备 {machine_id} 已禁用，返回 0")
            return 0.0
        # 使用配置的固定时长
        duration = config.get('gpio_duration', 5.0)
        print(f"[CONTROL] 设备 {machine_id} 配置时长: {duration}s")
        return float(duration)

    # 2. 无配置时，根据检测信息动态计算
    default = 5.0
    try:
        if detection_info:
            change_ratio = detection_info.get('max_change_ratio', 0)
            if change_ratio > 0.3:
                return 10.0
            elif change_ratio > 0.1:
                return 7.0
            elif change_ratio > 0.05:
                return 5.0
            else:
                return 3.0
    except Exception as e:
        print(f"[ERROR] 计算持续时间失败: {e}")
    return default


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'time': datetime.now().isoformat(),
        'service': 'rpi-motion-controller'
    })


@app.route('/api/hardware/upload', methods=['POST'])
def upload_image():
    print(f"\n[UPLOAD] 收到上传请求: {datetime.now().isoformat()}")

    if 'image' not in request.files:
        return jsonify({'success': False, 'error': '没有图片文件'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'error': '文件名为空'}), 400

    machine_id_str = request.form.get('machine_id', 'unknown')
    try:
        machine_id = int(machine_id_str)
    except ValueError:
        machine_id = machine_id_str

    timestamp = request.form.get('timestamp', datetime.now().isoformat())
    detection_info_str = request.form.get('detection_info', '{}')

    try:
        detection_info = json.loads(detection_info_str)
    except json.JSONDecodeError:
        detection_info = {}

    print(f"[UPLOAD] 设备ID: {machine_id}")
    print(f"[UPLOAD] 检测信息: {detection_info}")

    if file and allowed_file(file.filename):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = secure_filename(file.filename)
        filename = f"motion_{ts}_{safe_name}"

        machine_folder = get_machine_folder(machine_id)
        save_path = os.path.join(machine_folder, filename)
        file.save(save_path)

        print(f"[UPLOAD] 图片已保存: {save_path}")

        # ★★★ 根据设备配置返回 gpio_duration ★★★
        gpio_duration = decide_gpio_duration(machine_id, detection_info)
        print(f"[UPLOAD] 返回 gpio_duration: {gpio_duration}s")

        return jsonify({
            'success': True,
            'gpio_duration': gpio_duration,
            'message': '图片接收成功',
            'saved_filename': filename,
            'machine_id': machine_id,
            'server_time': datetime.now().isoformat()
        })
    else:
        return jsonify({'success': False, 'error': '不支持的文件类型'}), 400


@app.route('/api/hardware/control/<int:machine_id>', methods=['GET'])
def get_control(machine_id):
    """
    获取设备控制信号（树莓派主动查询）
    """
    print(f"[CONTROL] 设备 {machine_id} 请求控制信号")

    config = devices_config.get(machine_id, {'gpio_duration': 5.0, 'enabled': True})

    return jsonify({
        'machine_id': machine_id,
        'gpio_duration': config.get('gpio_duration', 5.0),
        'enabled': config.get('enabled', True),
        'commands': []
    })


@app.route('/api/hardware/control/<int:machine_id>', methods=['POST'])
def set_control(machine_id):
    """
    ★★★ 设置设备控制配置（管理员调用）★★★
    请求体: {"gpio_duration": 10.0, "enabled": true}
    """
    data = request.get_json() or {}

    if machine_id not in devices_config:
        devices_config[machine_id] = {}

    if 'gpio_duration' in data:
        devices_config[machine_id]['gpio_duration'] = float(data['gpio_duration'])
    if 'enabled' in data:
        devices_config[machine_id]['enabled'] = bool(data['enabled'])

    print(f"[ADMIN] 设备 {machine_id} 配置更新: {devices_config[machine_id]}")

    return jsonify({
        'success': True,
        'machine_id': machine_id,
        'config': devices_config[machine_id]
    })


@app.route('/api/hardware/heartbeat', methods=['POST'])
def heartbeat():
    data = request.get_json() or {}
    machine_id = data.get('machine_id', 'unknown')
    status = data.get('status', {})

    devices_status[machine_id] = {
        'last_seen': datetime.now().isoformat(),
        'status': status
    }

    print(f"[HEARTBEAT] 设备 {machine_id} 在线, GPIO: {status.get('gpio_state', 'unknown')}")

    return jsonify({
        'received': True,
        'server_time': datetime.now().isoformat()
    })


@app.route('/api/devices', methods=['GET'])
def list_devices():
    return jsonify({
        'devices': devices_status,
        'configs': devices_config,
        'count': len(devices_status)
    })


@app.errorhandler(413)
def too_large(e):
    return jsonify({'success': False, 'error': '文件过大'}), 413


@app.errorhandler(500)
def server_error(e):
    return jsonify({'success': False, 'error': '服务器内部错误'}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("  树莓派运动检测服务端（主动控制版）")
    print("=" * 60)
    print(f"上传目录: {os.path.abspath(UPLOAD_FOLDER)}")
    print("接口地址:")
    print("  GET  http://0.0.0.0:5000/api/health")
    print("  POST http://0.0.0.0:5000/api/hardware/upload")
    print("  GET  http://0.0.0.0:5000/api/hardware/control/<id>")
    print("  POST http://0.0.0.0:5000/api/hardware/control/<id>  ← 设置控制时长")
    print("  POST http://0.0.0.0:5000/api/hardware/heartbeat")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=False)