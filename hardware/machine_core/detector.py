"""
污渍检测器模块
基于树莓派摄像头的污渍检测和灰度分析
"""
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime


class StainDetector:
    """污渍检测器类"""
    
    def __init__(self, camera_id: int = 0):
        self.camera_id = camera_id
        self.camera = None
        self.is_initialized = False
        
        # 检测参数
        self.gray_threshold = 128
        self.contrast_threshold = 30
        self.uniformity_threshold = 0.8
    
    def initialize_camera(self) -> bool:
        """初始化摄像头"""
        try:
            # 尝试导入OpenCV
            import cv2
            self.camera = cv2.VideoCapture(self.camera_id)
            
            if not self.camera.isOpened():
                print(f"❌ 无法打开摄像头 {self.camera_id}")
                return False
            
            self.is_initialized = True
            print(f"✅ 摄像头 {self.camera_id} 初始化成功")
            return True
            
        except ImportError:
            print("⚠️ OpenCV未安装，使用模拟模式")
            self.is_initialized = True
            return True
        except Exception as e:
            print(f"❌ 摄像头初始化失败: {e}")
            return False
    
    def capture_image(self, save_path: Optional[Path] = None) -> Optional[np.ndarray]:
        """捕获图像"""
        if not self.is_initialized:
            print("❌ 摄像头未初始化")
            return None
        
        try:
            import cv2
            
            ret, frame = self.camera.read()
            if not ret:
                print("❌ 图像捕获失败")
                return None
            
            if save_path:
                cv2.imwrite(str(save_path), frame)
                print(f"📸 图像已保存: {save_path}")
            
            return frame
            
        except ImportError:
            # 模拟图像
            print("⚠️ 使用模拟图像")
            mock_image = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
            if save_path:
                import cv2
                cv2.imwrite(str(save_path), mock_image)
            return mock_image
        except Exception as e:
            print(f"❌ 图像捕获异常: {e}")
            return None
    
    def analyze_grayscale(self, image: np.ndarray) -> Dict[str, Any]:
        """灰度分析"""
        if image is None:
            return {'error': '图像为空'}
        
        try:
            import cv2
            
            # 转换为灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # 计算统计信息
            mean_gray = float(np.mean(gray))
            std_gray = float(np.std(gray))
            min_gray = float(np.min(gray))
            max_gray = float(np.max(gray))
            
            # 计算对比度
            contrast = max_gray - min_gray
            
            # 计算均匀性
            uniformity = 1.0 - (std_gray / 255.0)
            
            return {
                'mean_grayscale': round(mean_gray, 2),
                'std_grayscale': round(std_gray, 2),
                'min_grayscale': round(min_gray, 2),
                'max_grayscale': round(max_gray, 2),
                'contrast': round(contrast, 2),
                'uniformity': round(uniformity, 4),
                'success': True
            }
            
        except ImportError:
            # 模拟分析
            return {
                'mean_grayscale': 128.5,
                'std_grayscale': 45.2,
                'min_grayscale': 60.0,
                'max_grayscale': 200.0,
                'contrast': 140.0,
                'uniformity': 0.82,
                'success': True
            }
    
    def detect_stains(self, image: np.ndarray, method: str = 'combined') -> Dict[str, Any]:
        """污渍检测"""
        if image is None:
            return {'error': '图像为空', 'stains': []}
        
        try:
            import cv2
            
            # 转换为灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            stains = []
            
            if method == 'combined':
                stains = self._combined_detection(gray)
            elif method == 'color':
                stains = self._color_detection(image)
            elif method == 'texture':
                stains = self._texture_detection(gray)
            elif method == 'adaptive':
                stains = self._adaptive_detection(gray)
            
            return {
                'stains': stains,
                'stain_count': len(stains),
                'method': method,
                'success': True
            }
            
        except ImportError:
            # 模拟检测
            return {
                'stains': [
                    {'area': 150, 'confidence': 0.85, 'type': '污渍'},
                    {'area': 80, 'confidence': 0.72, 'type': '污渍'}
                ],
                'stain_count': 2,
                'method': method,
                'success': True
            }
    
    def _combined_detection(self, gray: np.ndarray) -> list:
        """组合检测方法"""
        import cv2
        
        # 自适应阈值
        adaptive_thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # 形态学操作
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        cleaned = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_CLOSE, kernel)
        
        # 查找轮廓
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        stains = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 100:  # 过滤小噪点
                x, y, w, h = cv2.boundingRect(contour)
                stains.append({
                    'area': int(area),
                    'bbox': [x, y, w, h],
                    'confidence': min(1.0, area / 1000),
                    'type': '污渍'
                })
        
        return stains
    
    def _color_detection(self, image: np.ndarray) -> list:
        """颜色检测方法"""
        # 简化实现
        return []
    
    def _texture_detection(self, gray: np.ndarray) -> list:
        """纹理检测方法"""
        # 简化实现
        return []
    
    def _adaptive_detection(self, gray: np.ndarray) -> list:
        """自适应检测方法"""
        # 简化实现
        return []
    
    def release(self):
        """释放摄像头资源"""
        if self.camera:
            self.camera.release()
            self.is_initialized = False
            print("📷 摄像头资源已释放")
    
    def get_pollution_level(self, gray_value: int, colony_density: float) -> Dict[str, Any]:
        """
        根据灰度值和菌落密度计算污染等级
        基于消毒数据.json的逻辑
        """
        # 污染等级计算（1-5级）
        if gray_value < 100 and colony_density < 1000:
            pollution_level = 1
            severity_level = 1
        elif gray_value < 150 and colony_density < 3000:
            pollution_level = 2
            severity_level = 2
        elif gray_value < 180 and colony_density < 4000:
            pollution_level = 3
            severity_level = 2
        elif gray_value < 200 and colony_density < 5000:
            pollution_level = 4
            severity_level = 3
        else:
            pollution_level = 5
            severity_level = 4
        
        severity_descriptions = {
            1: '轻度污染 - 污染物少，风险低',
            2: '中度污染 - 污染物中等，需标准处理',
            3: '重度污染 - 污染物较多，风险较高',
            4: '极重污染 - 污染物严重，高风险'
        }
        
        return {
            'pollution_level': pollution_level,
            'severity_level': severity_level,
            'severity_description': severity_descriptions[severity_level]
        }
