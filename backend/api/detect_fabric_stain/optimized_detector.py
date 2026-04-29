"""
优化版衣物污渍检测器
专为1080p@12fps实时处理优化
"""
import cv2
import numpy as np
import time
import random
from collections import deque
import threading
from typing import Tuple, List, Dict, Optional

class OptimizedStainDetector:
    def __init__(self, buffer_size=5):
        """
        初始化优化版污渍检测器
        :param buffer_size: 帧缓冲区大小，用于运动检测和稳定性分析
        """
        self.frame_buffer = deque(maxlen=buffer_size)
        self.motion_threshold = 30  # 运动检测阈值
        self.min_contour_area = 100  # 最小轮廓面积
        self.processing_lock = threading.Lock()
        
        # 预定义的颜色范围（针对常见污渍优化）
        self.color_ranges = {
            'blood': ([0, 100, 100], [10, 255, 255]),      # 红色血迹
            'oil': ([15, 50, 50], [35, 255, 255]),         # 油渍（黄色调）
            'wine': ([130, 50, 50], [170, 255, 255]),      # 酒渍（紫色）
            'coffee': ([10, 60, 60], [25, 255, 255]),      # 咖啡渍（棕色）
            'ink': ([90, 80, 80], [130, 255, 255]),        # 墨水（蓝色）
            'grass': ([35, 80, 80], [85, 255, 255]),       # 草渍（绿色）
            'rust': ([0, 100, 100], [20, 255, 255]),       # 铁锈（橙红色）
            'sweat': ([0, 0, 150], [180, 50, 255])         # 汗渍（灰色偏白）
        }
        
        # 性能统计
        self.performance_stats = {
            'frame_count': 0,
            'total_processing_time': 0,
            'detection_count': 0,
            'average_fps': 0
        }
    
    def preprocess_frame_fast(self, frame: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        快速预处理帧
        :param frame: 输入帧 (RGB格式)
        :return: 灰度图和HSV图
        """
        # 转换为BGR（OpenCV格式）
        bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # 快速转换到灰度和HSV
        gray = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2HSV)
        
        return gray, hsv
    
    def detect_motion_fast(self, current_gray: np.ndarray) -> bool:
        """
        快速运动检测
        :param current_gray: 当前灰度帧
        :return: 是否检测到显著运动
        """
        if len(self.frame_buffer) < 2:
            self.frame_buffer.append(current_gray)
            return False
        
        # 取最近的帧进行比较
        prev_gray = self.frame_buffer[-1]
        
        # 计算帧差
        frame_diff = cv2.absdiff(prev_gray, current_gray)
        
        # 应用阈值
        _, thresh = cv2.threshold(frame_diff, self.motion_threshold, 255, cv2.THRESH_BINARY)
        
        # 计算变化像素比例
        change_ratio = np.count_nonzero(thresh) / thresh.size
        
        # 更新缓冲区
        self.frame_buffer.append(current_gray)
        
        # 如果变化超过5%，认为有运动
        return change_ratio > 0.05
    
    def detect_stains_optimized(self, hsv_frame: np.ndarray) -> Tuple[np.ndarray, List[Dict]]:
        """
        优化的污渍检测算法
        :param hsv_frame: HSV格式的帧
        :return: 污渍掩码和污渍信息列表
        """
        combined_mask = np.zeros(hsv_frame.shape[:2], dtype=np.uint8)
        stain_info_list = []
        
        # 并行处理多种颜色范围
        for stain_type, (lower, upper) in self.color_ranges.items():
            lower = np.array(lower, dtype=np.uint8)
            upper = np.array(upper, dtype=np.uint8)
            
            # 创建颜色掩码
            color_mask = cv2.inRange(hsv_frame, lower, upper)
            
            # 快速形态学操作
            kernel_small = np.ones((3, 3), np.uint8)
            kernel_medium = np.ones((5, 5), np.uint8)
            
            # 去噪
            color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_OPEN, kernel_small, iterations=1)
            # 填充空洞
            color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_CLOSE, kernel_medium, iterations=1)
            
            # 合并到总掩码
            combined_mask = cv2.bitwise_or(combined_mask, color_mask)
            
            # 提取该颜色的污渍信息
            contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area >= self.min_contour_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    stain_info_list.append({
                        'type': stain_type,
                        'area': area,
                        'bbox': (x, y, w, h),
                        'center': (x + w//2, y + h//2)
                    })
        
        return combined_mask, stain_info_list
    
    def calculate_stain_statistics(self, stain_info_list: List[Dict], frame_shape: Tuple[int, int]) -> Dict:
        """
        计算污渍统计数据
        :param stain_info_list: 污渍信息列表
        :param frame_shape: 帧尺寸 (height, width)
        :return: 统计信息字典
        """
        if not stain_info_list:
            return {
                'total_stains': 0,
                'total_area': 0,
                'coverage_percentage': 0,
                'stain_types': {},
                'largest_stain': None
            }
        
        total_area = sum(stain['area'] for stain in stain_info_list)
        frame_area = frame_shape[0] * frame_shape[1]
        coverage_percentage = (total_area / frame_area) * 100
        
        # 统计各类污渍数量
        stain_types = {}
        for stain in stain_info_list:
            stain_type = stain['type']
            stain_types[stain_type] = stain_types.get(stain_type, 0) + 1
        
        # 找到最大的污渍
        largest_stain = max(stain_info_list, key=lambda x: x['area'])
        
        return {
            'total_stains': len(stain_info_list),
            'total_area': total_area,
            'coverage_percentage': coverage_percentage,
            'stain_types': stain_types,
            'largest_stain': largest_stain
        }
    
    def process_frame_realtime(self, frame: np.ndarray) -> Optional[Dict]:
        """
        实时处理单帧图像
        :param frame: 输入帧 (RGB格式)
        :return: 处理结果或None（如果没有检测到运动）
        """
        start_time = time.time()
        
        with self.processing_lock:
            # 预处理
            gray_frame, hsv_frame = self.preprocess_frame_fast(frame)
            
            # 运动检测
            motion_detected = self.detect_motion_fast(gray_frame)
            
            if not motion_detected and len(self.frame_buffer) > 1:
                # 如果没有检测到运动且不是第一帧，跳过处理
                return None
            
            # 污渍检测
            stain_mask, stain_info = self.detect_stains_optimized(hsv_frame)
            
            # 统计分析
            statistics = self.calculate_stain_statistics(stain_info, frame.shape[:2])
            
            # 计算置信度（基于污渍数量和覆盖率）
            confidence = min(1.0, (statistics['total_stains'] * 0.1 + statistics['coverage_percentage'] * 0.01))
            
            # 性能统计
            processing_time = time.time() - start_time
            self.performance_stats['frame_count'] += 1
            self.performance_stats['total_processing_time'] += processing_time
            self.performance_stats['detection_count'] += 1
            
            if self.performance_stats['frame_count'] > 0:
                self.performance_stats['average_fps'] = self.performance_stats['frame_count'] / self.performance_stats['total_processing_time']
            
            return {
                'timestamp': time.time(),
                'frame_shape': frame.shape,
                'motion_detected': motion_detected,
                'stain_mask': stain_mask,
                'stain_info': stain_info,
                'statistics': statistics,
                'confidence': confidence,
                'processing_time': processing_time,
                'performance_stats': self.performance_stats.copy()
            }
    
    def batch_process_frames(self, frames: List[np.ndarray]) -> List[Optional[Dict]]:
        """
        批量处理帧序列
        :param frames: 帧列表
        :return: 处理结果列表
        """
        results = []
        for frame in frames:
            result = self.process_frame_realtime(frame)
            results.append(result)
        return results
    
    def get_performance_report(self) -> Dict:
        """获取性能报告"""
        return {
            'total_frames': self.performance_stats['frame_count'],
            'total_detections': self.performance_stats['detection_count'],
            'average_processing_time': (
                self.performance_stats['total_processing_time'] / max(self.performance_stats['detection_count'], 1)
            ),
            'average_fps': self.performance_stats['average_fps'],
            'efficiency_ratio': (
                self.performance_stats['detection_count'] / max(self.performance_stats['frame_count'], 1)
            )
        }
    
    def reset_performance_stats(self):
        """重置性能统计"""
        self.performance_stats = {
            'frame_count': 0,
            'total_processing_time': 0,
            'detection_count': 0,
            'average_fps': 0
        }

class RealTimeProcessor:
    def __init__(self, detector: OptimizedStainDetector, target_fps: int = 12):
        """
        实时处理器
        :param detector: 优化的污渍检测器
        :param target_fps: 目标帧率
        """
        self.detector = detector
        self.target_fps = target_fps
        self.frame_interval = 1.0 / target_fps
        self.is_running = False
        self.processing_thread = None
        self.result_callback = None
        self.frame_source = None
    
    def set_frame_source(self, frame_source):
        """设置帧源"""
        self.frame_source = frame_source
    
    def set_result_callback(self, callback):
        """设置结果回调函数"""
        self.result_callback = callback
    
    def start_processing(self):
        """开始实时处理"""
        if self.is_running:
            return
        
        self.is_running = True
        self.processing_thread = threading.Thread(target=self._processing_loop)
        self.processing_thread.start()
        print(f"🚀 实时处理已启动，目标FPS: {self.target_fps}")
    
    def stop_processing(self):
        """停止实时处理"""
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join()
        print("🛑 实时处理已停止")
    
    def _processing_loop(self):
        """处理循环"""
        last_frame_time = time.time()
        
        while self.is_running:
            current_time = time.time()
            
            # 控制帧率
            if current_time - last_frame_time < self.frame_interval:
                sleep_time = self.frame_interval - (current_time - last_frame_time)
                time.sleep(sleep_time)
                continue
            
            # 获取帧
            if self.frame_source:
                frame = self.frame_source()
                if frame is not None:
                    # 处理帧
                    result = self.detector.process_frame_realtime(frame)
                    
                    # 回调结果
                    if result and self.result_callback:
                        self.result_callback(result)
            
            last_frame_time = time.time()

# 使用示例和测试函数
def demo_optimized_detection():
    """演示优化版检测功能"""
    print("🎯 演示优化版污渍检测器")
    
    # 创建检测器
    detector = OptimizedStainDetector(buffer_size=3)
    
    # 创建一些测试帧
    test_frames = []
    for i in range(10):
        # 创建测试图像
        frame = np.random.randint(50, 200, (1080, 1920, 3), dtype=np.uint8)
        
        # 添加一些模拟污渍（随机圆圈）
        if i % 3 == 0:  # 每3帧添加污渍
            for _ in range(random.randint(1, 5)):
                x = random.randint(100, 1820)
                y = random.randint(100, 980)
                radius = random.randint(20, 80)
                color = [random.randint(0, 255) for _ in range(3)]
                cv2.circle(frame, (x, y), radius, color, -1)
        
        test_frames.append(frame)
    
    print(f"📊 处理 {len(test_frames)} 帧测试数据...")
    
    # 处理帧
    results = detector.batch_process_frames(test_frames)
    
    # 分析结果
    detections = [r for r in results if r is not None]
    print(f"✅ 成功处理 {len(detections)} 帧")
    
    if detections:
        avg_processing_time = sum(r['processing_time'] for r in detections) / len(detections)
        avg_fps = sum(r['performance_stats']['average_fps'] for r in detections) / len(detections)
        
        print(f"⏱️  平均处理时间: {avg_processing_time*1000:.2f} ms")
        print(f"📊 平均FPS: {avg_fps:.2f}")
        print(f"🎯 检测到污渍的帧数: {len([r for r in detections if r['statistics']['total_stains'] > 0])}")
    
    # 获取最终性能报告
    perf_report = detector.get_performance_report()
    print(f"\n📈 性能报告:")
    for key, value in perf_report.items():
        print(f"   {key}: {value}")

if __name__ == "__main__":
    import random
    demo_optimized_detection()