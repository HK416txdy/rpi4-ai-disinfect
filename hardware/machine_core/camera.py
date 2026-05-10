#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
树莓派运动触发控制器 - 服务器控制版 v3
==========================================
服务器决定 GPIO 高电平时长，树莓派只负责执行
"""

import cv2
import numpy as np
import requests
import json
import time
import threading
import os
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from collections import deque

try:
    import RPi.GPIO as GPIO
    IS_RPI = True
except ImportError:
    print("[WARN] 未检测到 RPi.GPIO，进入模拟模式")
    IS_RPI = False

    class MockGPIO:
        BCM = 'BCM'; BOARD = 'BOARD'; OUT = 'OUT'; HIGH = 1; LOW = 0
        _pins = {}
        @classmethod
        def setmode(cls, mode): pass
        @classmethod
        def setwarnings(cls, flag): pass
        @classmethod
        def setup(cls, pin, mode): cls._pins[pin] = 0
        @classmethod
        def output(cls, pin, state):
            cls._pins[pin] = state
            print(f"[GPIO-MOCK] 引脚 {pin} -> {'HIGH' if state == cls.HIGH else 'LOW'}")
        @classmethod
        def input(cls, pin): return cls._pins.get(pin, 0)
        @classmethod
        def cleanup(cls): cls._pins.clear()
    GPIO = MockGPIO()


class Config:
    CAMERA_INDEX      = 0
    FRAME_WIDTH       = 640
    FRAME_HEIGHT      = 480
    FPS               = 30
    GPIO_PIN          = 17
    GPIO_MODE         = 'BCM'
    MOTION_THRESHOLD  = 25
    MIN_CHANGE_AREA   = 500
    BLUR_SIZE         = 5
    STABILITY_FRAMES  = 15
    MAX_WAIT_FRAMES   = 300
    TRIGGER_FRAMES    = 3
    COOLDOWN_FRAMES   = 5
    BG_HISTORY        = 100
    BG_VAR_THRESHOLD  = 16
    BG_DETECT_SHADOWS = False
    LEARNING_PERIOD   = 30
    USE_CLAHE         = True
    CLAHE_CLIP        = 2.0
    CLAHE_GRID        = 8
    SHOW_PREVIEW      = True
    PREVIEW_FPS       = 10
    PREVIEW_SCALE     = 0.75
    HEADLESS_MODE     = False
    SERVER_URL        = "http://172.20.10.11:5000"   # ★★★ 你的服务器IP ★★★
    MACHINE_ID        = 1
    UPLOAD_TIMEOUT    = 30
    HEARTBEAT_INTERVAL = 30
    MAX_RETRIES       = 3
    DEFAULT_DURATION  = 5.0
    SAVE_IMAGES       = True
    SAVE_DIR          = "/home/pi/detections"


class StableMotionDetector:
    def __init__(self, threshold=Config.MOTION_THRESHOLD,
                 min_area=Config.MIN_CHANGE_AREA,
                 blur_size=Config.BLUR_SIZE):
        self.threshold = threshold
        self.min_area = min_area
        self.blur_size = blur_size if blur_size % 2 == 1 else blur_size + 1
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=Config.BG_HISTORY,
            varThreshold=Config.BG_VAR_THRESHOLD,
            detectShadows=Config.BG_DETECT_SHADOWS
        )
        self.clahe = cv2.createCLAHE(
            clipLimit=Config.CLAHE_CLIP,
            tileGridSize=(Config.CLAHE_GRID, Config.CLAHE_GRID)
        )
        self.trigger_queue = deque(maxlen=Config.TRIGGER_FRAMES)
        self.cooldown_counter = 0
        self.learning_frames = 0

    def _preprocess(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if Config.USE_CLAHE:
            gray = self.clahe.apply(gray)
        gray = cv2.GaussianBlur(gray, (self.blur_size, self.blur_size), 0)
        return gray

    def detect_change(self, frame):
        if frame is None:
            return False, 0.0, np.zeros((10, 10), dtype=np.uint8), np.zeros((10, 10), dtype=np.uint8)

        processed = self._preprocess(frame)
        self.learning_frames += 1

        if self.learning_frames <= Config.LEARNING_PERIOD:
            self.bg_subtractor.apply(processed)
            remaining = Config.LEARNING_PERIOD - self.learning_frames
            return False, 0.0, np.zeros_like(processed), processed

        fg_mask = self.bg_subtractor.apply(processed)
        _, fg_mask = cv2.threshold(fg_mask, self.threshold, 255, cv2.THRESH_BINARY)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel, iterations=1)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        total_area = 0
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > self.min_area:
                total_area += area

        frame_area = frame.shape[0] * frame.shape[1]
        change_ratio = total_area / frame_area if frame_area > 0 else 0.0
        frame_has_motion = total_area > self.min_area and change_ratio > 0.001

        if self.cooldown_counter > 0:
            self.cooldown_counter -= 1
            return False, change_ratio, fg_mask, processed

        self.trigger_queue.append(frame_has_motion)
        has_change = len(self.trigger_queue) == Config.TRIGGER_FRAMES and all(self.trigger_queue)

        if has_change:
            self.cooldown_counter = Config.COOLDOWN_FRAMES
            self.trigger_queue.clear()

        return has_change, change_ratio, fg_mask, processed

    def reset(self):
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=Config.BG_HISTORY,
            varThreshold=Config.BG_VAR_THRESHOLD,
            detectShadows=Config.BG_DETECT_SHADOWS
        )
        self.trigger_queue.clear()
        self.cooldown_counter = 0
        self.learning_frames = 0


class GPIOController:
    def __init__(self, pin=Config.GPIO_PIN, mode=Config.GPIO_MODE):
        self.pin = pin
        self.is_high = False
        if mode.upper() == 'BCM':
            GPIO.setmode(GPIO.BCM)
        else:
            GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)
        print(f"[GPIO] 引脚 {pin} 初始化完成，当前状态: LOW")

    def set_high(self):
        GPIO.output(self.pin, GPIO.HIGH)
        self.is_high = True
        print(f"[GPIO] 引脚 {self.pin} -> HIGH")

    def set_low(self):
        GPIO.output(self.pin, GPIO.LOW)
        self.is_high = False
        print(f"[GPIO] 引脚 {self.pin} -> LOW")

    def cleanup(self):
        self.set_low()
        GPIO.cleanup()
        print(f"[GPIO] 引脚 {self.pin} 已清理")


class HardwareCommunicator:
    def __init__(self, server_url=Config.SERVER_URL, machine_id=Config.MACHINE_ID):
        self.server_url = server_url.rstrip('/')
        self.machine_id = machine_id
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'RaspberryPi-MotionController/1.0'})
        self.is_connected = False
        self.running = False
        self.heartbeat_thread = None

    def connect(self):
        if '你的' in self.server_url or 'example' in self.server_url:
            print(f"[NET] 警告: SERVER_URL 未配置真实IP")
            return False
        try:
            resp = self.session.get(f"{self.server_url}/api/health", timeout=5)
            if resp.status_code == 200:
                self.is_connected = True
                print(f"[NET] 服务器连接成功: {self.server_url}")
                return True
            print(f"[NET] 服务器响应异常: HTTP {resp.status_code}")
            return False
        except Exception as e:
            print(f"[NET] 连接失败: {e}")
            print("[NET] 进入离线模式")
            return False

    def disconnect(self):
        self.running = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=5)
        self.is_connected = False
        print("[NET] 通信器已断开")

    def upload_image(self, image, detection_info):
        if not self.is_connected:
            print("[NET] 离线模式，跳过上传")
            return None

        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
        success, img_encoded = cv2.imencode('.jpg', image, encode_param)
        if not success:
            print("[NET] 图片编码失败")
            return None

        img_bytes = img_encoded.tobytes()
        files = {'image': ('detection.jpg', img_bytes, 'image/jpeg')}
        data = {
            'machine_id': self.machine_id,
            'timestamp': datetime.now().isoformat(),
            'detection_info': json.dumps(detection_info, ensure_ascii=False)
        }

        for attempt in range(1, Config.MAX_RETRIES + 1):
            try:
                print(f"[NET] 正在上传... (尝试 {attempt}/{Config.MAX_RETRIES})")
                resp = self.session.post(
                    f"{self.server_url}/api/hardware/upload",
                    files=files, data=data, timeout=Config.UPLOAD_TIMEOUT
                )
                if resp.status_code == 200:
                    result = resp.json()
                    print(f"[NET] 上传成功: {result}")
                    return result
                print(f"[NET] 上传失败: HTTP {resp.status_code}")
                if attempt < Config.MAX_RETRIES:
                    time.sleep(2 ** attempt)
            except Exception as e:
                print(f"[NET] 上传异常: {e}")
                if attempt < Config.MAX_RETRIES:
                    time.sleep(2 ** attempt)
        return None

    def get_control_signal(self):
        """★★★ 获取服务器控制信号（包括 gpio_duration）★★★"""
        if not self.is_connected:
            return None
        try:
            resp = self.session.get(
                f"{self.server_url}/api/hardware/control/{self.machine_id}",
                timeout=5
            )
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception as e:
            print(f"[NET] 获取控制信号失败: {e}")
            return None

    def start_heartbeat(self):
        if self.running:
            return
        self.running = True
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        print(f"[NET] 心跳线程启动，间隔 {Config.HEARTBEAT_INTERVAL}s")

    def _heartbeat_loop(self):
        while self.running:
            if not self.is_connected:
                time.sleep(Config.HEARTBEAT_INTERVAL)
                continue
            try:
                payload = {
                    'machine_id': self.machine_id,
                    'timestamp': datetime.now().isoformat(),
                    'status': {
                        'online': True,
                        'gpio_state': 'HIGH' if (IS_RPI and GPIO.input(Config.GPIO_PIN)) else 'LOW',
                        'rpi': IS_RPI
                    }
                }
                self.session.post(f"{self.server_url}/api/hardware/heartbeat", json=payload, timeout=5)
            except Exception as e:
                print(f"[NET] 心跳失败: {e}")
            time.sleep(Config.HEARTBEAT_INTERVAL)


class MotionTriggeredController:
    def __init__(self):
        self.is_running = False
        self.camera = None
        self.motion_detector = None
        self.gpio = None
        self.communicator = None
        self.preview_counter = 0

        if Config.SAVE_IMAGES:
            os.makedirs(Config.SAVE_DIR, exist_ok=True)

    def _init_camera(self):
        self.camera = cv2.VideoCapture(Config.CAMERA_INDEX, cv2.CAP_V4L2)
        if not self.camera.isOpened():
            self.camera = cv2.VideoCapture(Config.CAMERA_INDEX)
            if not self.camera.isOpened():
                print("[CAM] 错误：无法打开摄像头")
                return False

        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, Config.FRAME_WIDTH)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.FRAME_HEIGHT)
        self.camera.set(cv2.CAP_PROP_FPS, Config.FPS)
        self.camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
        self.camera.set(cv2.CAP_PROP_EXPOSURE, -6)
        self.camera.set(cv2.CAP_PROP_AUTO_WB, 0)
        self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        print("[CAM] 摄像头预热中...")
        for _ in range(10):
            self.camera.read()
            time.sleep(0.05)

        actual_w = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"[CAM] 摄像头就绪: {actual_w}x{actual_h}")
        return True

    def _show_preview(self, frame, fg_mask, has_change, change_ratio, status_text):
        if not Config.SHOW_PREVIEW or Config.HEADLESS_MODE:
            return

        self.preview_counter += 1
        if self.preview_counter % (Config.FPS // Config.PREVIEW_FPS) != 0:
            return

        if Config.PREVIEW_SCALE != 1.0:
            h, w = frame.shape[:2]
            frame = cv2.resize(frame, (int(w * Config.PREVIEW_SCALE), int(h * Config.PREVIEW_SCALE)))
            if fg_mask is not None and fg_mask.size > 1:
                fg_mask = cv2.resize(fg_mask, (int(w * Config.PREVIEW_SCALE), int(h * Config.PREVIEW_SCALE)))

        preview = frame.copy()
        color = (0, 0, 255) if has_change else ((0, 255, 0) if "稳定" in status_text else (255, 255, 0))
        cv2.putText(preview, f"Status: {status_text}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.putText(preview, f"Ratio: {change_ratio:.4f}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        if fg_mask is not None and fg_mask.size > 1:
            fg_color = cv2.cvtColor(fg_mask, cv2.COLOR_GRAY2BGR)
            h, w = preview.shape[:2]
            small = cv2.resize(fg_color, (w // 4, h // 4))
            preview[0:small.shape[0], w - small.shape[1]:w] = small

        cv2.imshow('Motion Detection', preview)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            self.is_running = False
        elif key == ord('s'):
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            cv2.imwrite(f"{Config.SAVE_DIR}/manual_{ts}.jpg", frame)
            print(f"  [SAVE] 手动保存: manual_{ts}.jpg")

    def _wait_for_motion_end(self):
        stable_count = 0
        frame_count = 0
        last_change_frame = None
        last_change_info = None
        max_change_ratio = 0.0
        motion_started = False

        print(f"[DETECT] 开始检测...（前{Config.LEARNING_PERIOD}帧学习背景，请保持静止）")

        while stable_count < Config.STABILITY_FRAMES and frame_count < Config.MAX_WAIT_FRAMES:
            ret, frame = self.camera.read()
            if not ret:
                print("[CAM] 读取帧失败")
                break

            frame_count += 1
            has_change, change_ratio, fg_mask, processed = self.motion_detector.detect_change(frame)

            if self.motion_detector.learning_frames <= Config.LEARNING_PERIOD:
                remaining = Config.LEARNING_PERIOD - self.motion_detector.learning_frames
                if frame_count % 10 == 0:
                    print(f"  [LEARN] 背景学习中... 还剩 {remaining} 帧")
                self._show_preview(frame, fg_mask, False, 0, f"学习中...({remaining})")
                continue

            if has_change:
                motion_started = True
                stable_count = 0
                last_change_frame = frame.copy()
                last_change_info = {
                    'change_ratio': round(change_ratio, 6),
                    'frame_index': frame_count,
                    'timestamp': datetime.now().isoformat()
                }
                max_change_ratio = max(max_change_ratio, change_ratio)
                print(f"  [MOTION] 确认运动! (比例: {change_ratio:.4f})")
                self.gpio.set_high()
            else:
                if motion_started:
                    stable_count += 1
                    if stable_count == 1:
                        print(f"  [STABLE] 画面开始稳定...")
                    elif stable_count % 5 == 0:
                        print(f"  [STABLE] 稳定中... ({stable_count}/{Config.STABILITY_FRAMES})")

            status = "运动中" if has_change else (f"稳定({stable_count}/{Config.STABILITY_FRAMES})" if motion_started else "等待")
            self._show_preview(frame, fg_mask, has_change, change_ratio, status)

        if last_change_frame is not None:
            print(f"[DETECT] 运动结束，共 {frame_count} 帧，最大变化: {max_change_ratio:.4f}")
            last_change_info.update({
                'total_frames': frame_count,
                'max_change_ratio': round(max_change_ratio, 6),
                'stability_frames': stable_count,
                'detection_mode': 'mog2_stable'
            })
            return last_change_frame, last_change_info
        else:
            print("[DETECT] 未检测到运动")
            return None, {}

    def _get_duration_from_server(self, image, detection_info):
        """
        ★★★ 上传图片并从服务器获取控制时长 ★★★
        优先级：
          1. upload 接口返回的 gpio_duration
          2. control 接口获取最新配置
          3. 默认配置值
        """
        print("[UPLOAD] 正在上传图片到服务器...")

        # 先上传图片
        result = self.communicator.upload_image(image, detection_info)

        if result and 'gpio_duration' in result:
            duration = float(result['gpio_duration'])
            print(f"[SERVER] 服务器指令: GPIO HIGH {duration} 秒")
            return duration

        # 如果上传失败或无 duration，尝试获取控制信号
        print("[SERVER] 上传无响应，尝试获取控制信号...")
        control = self.communicator.get_control_signal()
        if control and 'gpio_duration' in control:
            duration = float(control['gpio_duration'])
            print(f"[SERVER] 控制信号: GPIO HIGH {duration} 秒")
            return duration

        # 离线模式，使用默认
        print(f"[SERVER] 离线模式，使用默认: {Config.DEFAULT_DURATION}s")
        return Config.DEFAULT_DURATION

    def _hold_high(self, duration):
        print(f"[GPIO] 保持 HIGH {duration} 秒...")
        self.gpio.set_high()

        start = time.time()
        preview_counter = 0

        while time.time() - start < duration:
            ret, frame = self.camera.read()

            if Config.SHOW_PREVIEW and ret and not Config.HEADLESS_MODE:
                preview_counter += 1
                if preview_counter % (Config.FPS // Config.PREVIEW_FPS) == 0:
                    preview = frame.copy()
                    remaining = duration - (time.time() - start)
                    cv2.putText(preview, f"GPIO HIGH - {remaining:.1f}s", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                    cv2.imshow('Motion Detection', preview)

                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        self.is_running = False
                        break

            time.sleep(0.05)

        self.gpio.set_low()
        print("[GPIO] 已恢复 LOW")

    def run(self):
        print("\n" + "=" * 60)
        print("  树莓派运动触发控制器（服务器控制版 v3.3）")
        print("=" * 60)

        print("\n[INIT] 系统初始化...")
        self.gpio = GPIOController(pin=Config.GPIO_PIN)

        if not self._init_camera():
            print("[FATAL] 摄像头初始化失败，退出")
            self.gpio.cleanup()
            return

        self.motion_detector = StableMotionDetector(
            threshold=Config.MOTION_THRESHOLD,
            min_area=Config.MIN_CHANGE_AREA,
            blur_size=Config.BLUR_SIZE
        )

        self.communicator = HardwareCommunicator()
        self.communicator.connect()
        self.communicator.start_heartbeat()

        print("\n[CONFIG] 当前配置:")
        print(f"  摄像头: {Config.FRAME_WIDTH}x{Config.FRAME_HEIGHT} @ {Config.FPS}fps")
        print(f"  GPIO: 引脚 {Config.GPIO_PIN} (BCM)")
        print(f"  检测: MOG2 + 防抖({Config.TRIGGER_FRAMES}帧确认)")
        print(f"  服务器: {Config.SERVER_URL}")
        print(f"  模式: {'在线' if self.communicator.is_connected else '离线'}")
        print(f"  控制方式: 服务器决定 GPIO 时长")
        print("\n[HELP] 按键: 'q'=退出, 's'=保存")
        print("-" * 60 + "\n")

        self.is_running = True
        cycle_count = 0

        try:
            while self.is_running:
                cycle_count += 1
                print(f"\n{'─' * 50}")
                print(f"[CYCLE #{cycle_count}] 等待运动...")
                print(f"{'─' * 50}")

                final_frame, detection_info = self._wait_for_motion_end()

                if final_frame is None:
                    continue

                if Config.SAVE_IMAGES:
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    save_path = f"{Config.SAVE_DIR}/motion_{ts}.jpg"
                    cv2.imwrite(save_path, final_frame)
                    print(f"[SAVE] 图片已保存: {save_path}")

                # ★★★ 关键：上传图片，服务器返回控制时长 ★★★
                duration = self._get_duration_from_server(final_frame, detection_info)

                # ★★★ 执行服务器指令：保持 HIGH 指定时长 ★★★
                self._hold_high(duration)

                self.motion_detector.reset()
                print("[READY] 等待下次运动...")

        except KeyboardInterrupt:
            print("\n[EXIT] 用户中断 (Ctrl+C)")
        except Exception as e:
            print(f"\n[ERROR] 异常: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.shutdown()

    def shutdown(self):
        print("\n[SHUTDOWN] 正在关闭系统...")
        self.is_running = False

        if self.gpio:
            self.gpio.cleanup()

        if self.communicator:
            self.communicator.disconnect()

        if self.camera and self.camera.isOpened():
            self.camera.release()
            print("[CAM] 摄像头已释放")

        if not Config.HEADLESS_MODE:
            cv2.destroyAllWindows()
        print("[DONE] 系统已安全关闭")


if __name__ == "__main__":
    controller = MotionTriggeredController()
    controller.run()