"""
树莓派摄像头污渍检测模块
用于实时捕获图像、灰度分析和污渍识别
"""
import cv2
import numpy as np
import os
from datetime import datetime
import time
import threading
from .new import StainDetector
import tempfile
from pathlib import Path

# Pillow fallback
try:
    from PIL import Image
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False


class RaspberryPiStainDetector:
    def __init__(self):
        self.stain_detector = StainDetector()
        self.camera = None
        self.is_capturing = False
        self.capture_thread = None
        self.last_frame = None
        self.detection_callback = None
        self._fps = 12
        self._width = 1920
        self._height = 1080

    def initialize_camera(self, camera_index=0, width=1920, height=1080, fps=12, use_mjpeg=True):
        """
        初始化摄像头
        :param camera_index: 摄像头索引，默认为0
        :param width: 目标宽度（像素），默认1920
        :param height: 目标高度（像素），默认1080
        :param fps: 目标帧率，默认12
        :param use_mjpeg: 是否尝试使用MJPG编码（提高高分辨率帧率和稳定性）
        :return: 是否初始化成功
        """
        try:
            self.camera = cv2.VideoCapture(camera_index)
            if not self.camera.isOpened():
                print("❌ 摄像头初始化失败")
                return False

            # 设置摄像头参数
            self._width = width
            self._height = height
            self._fps = fps

            # 尝试设置MJPG四字符编码（有些USB摄像头支持，通过MJPG能稳定传输1080p较高帧率）
            if use_mjpeg:
                try:
                    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
                    self.camera.set(cv2.CAP_PROP_FOURCC, fourcc)
                except Exception:
                    # 不要因为设置编码失败而中断
                    pass

            # 设置分辨率和帧率
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, int(self._width))
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, int(self._height))
            self.camera.set(cv2.CAP_PROP_FPS, float(self._fps))

            # 读取一帧以确认设置生效
            ret, frame = self.camera.read()
            if not ret:
                print("⚠️ 摄像头读取测试帧失败，继续运行但功能可能受限")
            else:
                h, w = frame.shape[:2]
                print(f"✅ 摄像头初始化成功，实际分辨率: {w}x{h}, 目标: {self._width}x{self._height} @ {self._fps}fps")

            return True
        except Exception as e:
            print(f"❌ 摄像头初始化异常: {e}")
            return False
    
    def capture_single_image(self, save_path=None):
        """
        捕获单张图像
        :param save_path: 保存路径，如果为None则不保存
        :return: 图像数据或None
        """
        if self.camera is None or not self.camera.isOpened():
            print("❌ 摄像头未初始化或不可用")
            return None
        
        ret, frame = self.camera.read()
        if not ret or frame is None:
            print("❌ 无法从摄像头读取图像")
            return None
        
        # 确保是彩色BGR图
        if len(frame.shape) == 2 or frame.shape[2] == 1:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        # 转换为RGB格式
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 保存图像（如果指定了路径）
        if save_path:
            try:
                if PIL_AVAILABLE:
                    img_to_save = Image.fromarray(rgb_frame)
                    img_to_save.save(save_path)
                else:
                    # Pillow不可用，使用OpenCV写入（需要BGR）
                    cv2.imwrite(save_path, cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR))
                print(f"📸 图像已保存到: {save_path}")
            except Exception as e:
                print(f"❌ 保存图像失败: {e}")
        
        return rgb_frame
    
    def start_continuous_capture(self, callback_func=None):
        """
        开始连续捕获图像
        :param callback_func: 每次捕获后的回调函数
        """
        if self.is_capturing:
            print("⚠️ 捕获已在运行中")
            return
        
        self.detection_callback = callback_func
        self.is_capturing = True
        self.capture_thread = threading.Thread(target=self._capture_loop)
        self.capture_thread.start()
        print("📹 开始连续捕获")
    
    def stop_continuous_capture(self):
        """停止连续捕获"""
        self.is_capturing = False
        if self.capture_thread:
            self.capture_thread.join()
        print("🛑 停止连续捕获")
    
    def _capture_loop(self):
        """内部捕获循环"""
        frame_interval = 1.0 / max(1, self._fps)
        while self.is_capturing:
            frame = self.capture_single_image()
            if frame is not None:
                self.last_frame = frame
                if self.detection_callback:
                    # 在单独的线程中执行检测，避免阻塞捕获
                    detection_thread = threading.Thread(
                        target=self.detection_callback, 
                        args=(frame,)
                    )
                    detection_thread.daemon = True
                    detection_thread.start()
            time.sleep(frame_interval)  # 控制捕获频率

    def analyze_grayscale(self, image):
        """
        对图像进行灰度分析
        :param image: 输入图像 (numpy array)
        :return: 分析结果字典
        """
        if image is None:
            return None
        
        # 转换为灰度图
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image
        
        # 计算基本统计信息
        mean_val = np.mean(gray)
        std_val = np.std(gray)
        min_val = np.min(gray)
        max_val = np.max(gray)
        
        # 计算对比度（通过最大值和最小值差）
        contrast = max_val - min_val
        
        # 检测暗区和亮区的比例
        dark_threshold = 50  # 定义暗区阈值
        bright_threshold = 200  # 定义亮区阈值
        
        dark_pixels = np.sum(gray < dark_threshold)
        bright_pixels = np.sum(gray > bright_threshold)
        total_pixels = gray.size
        
        dark_ratio = dark_pixels / total_pixels
        bright_ratio = bright_pixels / total_pixels
        
        # 评估均匀性（标准差越大表示变化越大，可能意味着更多污渍）
        uniformity_score = 1.0 - (std_val / 255.0)  # 标准差越小越均匀
        
        return {
            'mean_brightness': float(mean_val),
            'std_deviation': float(std_val),
            'contrast': float(contrast),
            'dark_ratio': float(dark_ratio),
            'bright_ratio': float(bright_ratio),
            'uniformity_score': float(uniformity_score),
            'min_value': float(min_val),
            'max_value': float(max_val)
        }
    
    def detect_stains_from_camera(self, save_path=None, method='combined'):
        """
        从摄像头捕获的图像进行污渍检测
        :param save_path: 临时保存路径
        :param method: 检测方法
        :return: 检测结果
        """
        # 捕获图像
        captured_image = self.capture_single_image(save_path)
        if captured_image is None:
            return None
        
        # 如果需要保存，创建临时文件
        temp_path = None
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_dir = Path(tempfile.gettempdir())
            temp_path = str(temp_dir / f"temp_capture_{timestamp}.jpg")
            try:
                if PIL_AVAILABLE:
                    img_to_save = Image.fromarray(captured_image)
                    img_to_save.save(temp_path)
                else:
                    cv2.imwrite(temp_path, cv2.cvtColor(captured_image, cv2.COLOR_RGB2BGR))
            except Exception as e:
                print(f"❌ 保存临时图像失败: {e}")

        actual_path = save_path or temp_path
        
        if actual_path and os.path.exists(actual_path):
            try:
                # 使用污渍检测器进行检测
                results = self.stain_detector.detect_all_stains(
                    actual_path,
                    method=method,
                    visualize=False
                )
                
                # 添加灰度分析结果
                grayscale_analysis = self.analyze_grayscale(captured_image)
                results['grayscale_analysis'] = grayscale_analysis
                
                # 清理临时文件
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
                
                return results
            except Exception as e:
                print(f"❌ 污渍检测失败: {e}")
                # 清理临时文件
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
                return None
        else:
            print("❌ 图像文件不存在")
            return None

    def process_frame_for_detection(self, frame):
        """
        处理单帧图像进行污渍检测
        :param frame: 图像帧
        :return: 检测结果
        """
        # 创建临时文件来存储帧
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        temp_dir = Path(tempfile.gettempdir())
        temp_path = str(temp_dir / f"frame_temp_{timestamp}.jpg")

        try:
            # 保存帧到临时文件
            if PIL_AVAILABLE:
                img_to_save = Image.fromarray(frame)
                img_to_save.save(temp_path)
            else:
                cv2.imwrite(temp_path, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

            # 进行污渍检测
            results = self.stain_detector.detect_all_stains(
                temp_path,
                method='combined',
                visualize=False
            )
            
            # 添加灰度分析
            grayscale_analysis = self.analyze_grayscale(frame)
            results['grayscale_analysis'] = grayscale_analysis
            
            # 添加时间戳
            results['timestamp'] = timestamp
            
            return results
        except Exception as e:
            print(f"❌ 帧处理失败: {e}")
            return None
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def release_camera(self):
        """释放摄像头资源"""
        if self.camera:
            self.camera.release()
            print("📷 摄像头已释放")


# 示例使用函数
def demo_camera_detection():
    """演示摄像头污渍检测功能"""
    detector = RaspberryPiStainDetector()
    
    # 初始化摄像头
    if detector.initialize_camera():
        print("开始单次检测演示...")
        
        # 进行单次检测
        results = detector.detect_stains_from_camera()
        
        if results:
            print(f"检测到 {results['analysis']['total_stains']} 个污渍")
            print(f"覆盖率: {results['analysis']['coverage_percentage']:.2f}%")
            print(f"灰度分析 - 亮度均值: {results['grayscale_analysis']['mean_brightness']:.2f}")
            print(f"灰度分析 - 对比度: {results['grayscale_analysis']['contrast']:.2f}")
        else:
            print("检测失败")
        
        detector.release_camera()


if __name__ == "__main__":
    demo_camera_detection()
