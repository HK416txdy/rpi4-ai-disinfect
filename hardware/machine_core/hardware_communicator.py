"""
硬件通信模块
负责与后端服务器通信，发送检测数据和接收控制命令
"""
import requests
import json
import time
from typing import Dict, Any, Optional
import threading
from datetime import datetime


class HardwareCommunicator:
    """硬件通信器，负责与后端服务器的数据交换"""

    def __init__(self, server_url: str = "http://localhost:5000", machine_id: int = 1):
        self.server_url = server_url.rstrip('/')
        self.machine_id = machine_id
        self.session = requests.Session()
        self.is_connected = False
        self.last_heartbeat = None
        self.heartbeat_thread = None
        self.running = False

    def connect(self) -> bool:
        """连接到服务器"""
        try:
            # 测试连接
            response = self.session.get(f"{self.server_url}/api/health", timeout=5)
            if response.status_code == 200:
                self.is_connected = True
                print(f"✅ 硬件通信器连接成功 - 机器ID: {self.machine_id}")
                return True
            else:
                print(f"❌ 服务器响应异常: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 连接服务器失败: {e}")
            return False

    def disconnect(self):
        """断开连接"""
        self.running = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join()
        self.is_connected = False
        print("📴 硬件通信器已断开")

    def send_detection_data(self, detection_data: Dict[str, Any]) -> Dict[str, Any]:
        """发送检测数据到服务器"""
        if not self.is_connected:
            return {'success': False, 'error': '未连接到服务器'}

        try:
            payload = {
                'machine_id': self.machine_id,
                'timestamp': datetime.now().isoformat(),
                'detection_data': detection_data
            }

            response = self.session.post(
                f"{self.server_url}/api/hardware/detection",
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                print(f"📤 检测数据发送成功: {len(detection_data)} 项数据")
                return result
            else:
                return {
                    'success': False,
                    'error': f'服务器错误: {response.status_code}'
                }

        except Exception as e:
            print(f"❌ 发送检测数据失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_control_commands(self) -> Optional[Dict[str, Any]]:
        """获取控制命令"""
        if not self.is_connected:
            return None

        try:
            response = self.session.get(
                f"{self.server_url}/api/hardware/control/{self.machine_id}",
                timeout=5
            )

            if response.status_code == 200:
                commands = response.json()
                if commands.get('commands'):
                    print(f"📥 收到控制命令: {len(commands['commands'])} 条")
                return commands
            else:
                return None

        except Exception as e:
            print(f"❌ 获取控制命令失败: {e}")
            return None

    def send_status_update(self, status_data: Dict[str, Any]) -> bool:
        """发送状态更新"""
        if not self.is_connected:
            return False

        try:
            payload = {
                'machine_id': self.machine_id,
                'timestamp': datetime.now().isoformat(),
                'status': status_data
            }

            response = self.session.post(
                f"{self.server_url}/api/hardware/status",
                json=payload,
                timeout=5
            )

            return response.status_code == 200

        except Exception as e:
            print(f"❌ 发送状态更新失败: {e}")
            return False

    def start_heartbeat(self, interval: int = 30):
        """启动心跳线程"""
        if self.running:
            return

        self.running = True
        self.heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            args=(interval,),
            daemon=True
        )
        self.heartbeat_thread.start()
        print(f"💓 启动心跳线程，间隔: {interval}秒")

    def _heartbeat_loop(self, interval: int):
        """心跳循环"""
        while self.running:
            try:
                # 发送心跳
                status_data = {
                    'online': True,
                    'last_seen': datetime.now().isoformat()
                }
                self.send_status_update(status_data)
                self.last_heartbeat = datetime.now()

            except Exception as e:
                print(f"❌ 心跳发送失败: {e}")

            time.sleep(interval)


# 示例使用函数
def demo_hardware_communication():
    """演示硬件通信功能"""
    from hardware.machine_core.detector import StainDetector

    # 创建通信器
    communicator = HardwareCommunicator(machine_id=1)

    # 连接服务器
    if not communicator.connect():
        print("无法连接到服务器")
        return

    # 创建检测器
    detector = StainDetector()

    # 初始化摄像头
    if detector.initialize_camera():
        print("摄像头初始化成功，开始检测循环...")

        try:
            communicator.start_heartbeat()

            for i in range(5):  # 演示5次检测
                # 捕获图像
                image = detector.capture_image()
                if image is not None:
                    # 分析图像
                    analysis = detector.analyze_grayscale(image)
                    stains = detector.detect_stains(image)

                    # 准备检测数据
                    detection_data = {
                        'grayscale_analysis': analysis,
                        'stain_detection': stains,
                        'image_info': {
                            'width': image.shape[1],
                            'height': image.shape[0],
                            'channels': image.shape[2] if len(image.shape) > 2 else 1
                        }
                    }

                    # 发送到服务器
                    result = communicator.send_detection_data(detection_data)
                    print(f"检测结果: {result}")

                    # 检查控制命令
                    commands = communicator.get_control_commands()
                    if commands and commands.get('commands'):
                        print(f"收到命令: {commands['commands']}")

                time.sleep(2)  # 间隔2秒

        finally:
            detector.release()
            communicator.disconnect()

    else:
        print("摄像头初始化失败")


if __name__ == "__main__":
    demo_hardware_communication()
