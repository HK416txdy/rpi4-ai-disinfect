import cv2
import numpy as np
import os
from PIL import Image
import shutil
from pathlib import Path
import matplotlib.font_manager as fm

# Matplotlib optional
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except Exception:
    plt = None
    MATPLOTLIB_AVAILABLE = False

class StainDetector:
    def __init__(self):
        self.results = {}
        # 设置中文字体支持（仅在matplotlib可用时）
        if MATPLOTLIB_AVAILABLE:
            self.setup_chinese_font()

    def setup_chinese_font(self):
        """设置matplotlib中文字体支持"""
        try:
            # 设置支持中文的字体
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans', 'Arial Unicode MS']
            plt.rcParams['axes.unicode_minus'] = False
        except Exception as e:
            print(f"字体设置警告: {e}")

    def load_image(self, image_path):
        """加载图像 - 使用PIL处理中文路径"""
        print(f"📁 正在加载图片: {image_path}")
        
        if isinstance(image_path, str):
            # 使用PIL打开图像（支持中文路径）
            try:
                pil_image = Image.open(image_path)
                # 转换为OpenCV格式 (BGR)
                self.image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                if self.image is None:
                    raise ValueError(f"无法加载图像: {image_path}")
                print(f"✅ 图片加载成功，尺寸: {self.image.shape}")
            except Exception as e:
                raise ValueError(f"无法加载图像 {image_path}: {e}")
        else:
            self.image = image_path

        self.image_rgb = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        self.image_hsv = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)
        self.image_gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        return self.image_rgb

    def preprocess_image(self, blur_kernel=(5, 5)):
        """图像预处理"""
        blurred = cv2.GaussianBlur(self.image_gray, blur_kernel, 0)
        equalized = cv2.equalizeHist(blurred)
        return equalized

    def _default_hsv_ranges(self):
        # 更细化的颜色范围（适配常见织物污渍颜色）
        return [
            ([5, 60, 40], [25, 255, 255]),   # 棕色/褐色污渍
            ([0, 0, 0], [180, 60, 100]),     # 灰色/黑色污渍（暗污渍）
            ([15, 80, 80], [35, 255, 255]),  # 黄色污渍
            ([100, 80, 50], [140, 255, 255]) # 蓝绿色污渍（例如墨水）
        ]

    def detect_stains_by_color(self, hsv_ranges=None, min_area=200):
        """
        基于HSV颜色空间的污渍检测，返回二值掩码
        :param hsv_ranges: HSV颜色范围列表
        :param min_area: 最小污渍面积阈值
        """
        if hsv_ranges is None:
            hsv_ranges = self._default_hsv_ranges()

        combined_mask = np.zeros_like(self.image_gray)
        
        for lower, upper in hsv_ranges:
            lower = np.array(lower, dtype=np.uint8)
            upper = np.array(upper, dtype=np.uint8)
            mask = cv2.inRange(self.image_hsv, lower, upper)
            
            # 形态学操作去噪
            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
            
            # 轮廓过滤
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            filtered_mask = np.zeros_like(mask)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area >= min_area:
                    cv2.fillPoly(filtered_mask, [contour], 255)
            
            combined_mask = cv2.bitwise_or(combined_mask, filtered_mask)

        return combined_mask

    def detect_stains_by_color_from_rgb(self, rgb_image, hsv_ranges=None, min_area=50):
        """
        接受RGB图像（numpy array），返回: mask, confidence_map (0-255), boxes
        boxes: list of (x,y,w,h, area)
        """
        if rgb_image is None:
            return None
        # 保证为uint8
        img = rgb_image.astype(np.uint8)
        bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

        if hsv_ranges is None:
            hsv_ranges = self._default_hsv_ranges()

        combined_mask = np.zeros((hsv.shape[0], hsv.shape[1]), dtype=np.uint8)
        confidence = np.zeros_like(combined_mask, dtype=np.uint8)

        for idx, (lower, upper) in enumerate(hsv_ranges):
            lower = np.array(lower, dtype=np.uint8)
            upper = np.array(upper, dtype=np.uint8)
            mask = cv2.inRange(hsv, lower, upper)

            # 模糊和形态学优化小噪声
            mask = cv2.medianBlur(mask, 5)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3,3), np.uint8))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5,5), np.uint8))

            # 将不同范围的响应叠加到confidence中（权重相等）
            confidence = np.maximum(confidence, mask)
            combined_mask = cv2.bitwise_or(combined_mask, mask)

        # 进一步清理
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, np.ones((3,3), np.uint8), iterations=1)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, np.ones((5,5), np.uint8), iterations=1)

        # 轮廓检测，产生bounding boxes
        contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area:
                continue
            x, y, w, h = cv2.boundingRect(cnt)
            boxes.append((int(x), int(y), int(w), int(h), float(area)))

        return combined_mask, confidence, boxes

    def detect_stains_by_texture(self, threshold=0.1):
        """
        基于纹理分析的污渍检测
        """
        preprocessed = self.preprocess_image()
        texture_diff = cv2.Laplacian(preprocessed, cv2.CV_64F)
        texture_diff = np.abs(texture_diff)
        texture_diff = (texture_diff - texture_diff.min()) / (texture_diff.max() - texture_diff.min())

        _, texture_mask = cv2.threshold((texture_diff * 255).astype(np.uint8),
                                        threshold * 255, 255, cv2.THRESH_BINARY)
        return texture_mask

    def detect_stains_adaptive(self, block_size=11, C=2):
        """
        自适应阈值检测污渍
        """
        preprocessed = self.preprocess_image()
        adaptive_thresh = cv2.adaptiveThreshold(
            preprocessed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, block_size, C
        )
        return adaptive_thresh

    def morphological_operations(self, mask, kernel_size=3, iterations=2):
        """
        形态学操作优化掩码
        """
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        cleaned = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=iterations)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel, iterations=iterations)
        return cleaned

    def analyze_stains(self, final_mask):
        """
        分析检测到的污渍
        """
        contours, _ = cv2.findContours(final_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        stain_info = {
            'total_stains': len(contours),
            'total_area': 0,
            'stain_details': [],
            'contours': contours
        }

        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            stain_info['total_area'] += area

            x, y, w, h = cv2.boundingRect(contour)
            perimeter = cv2.arcLength(contour, True)
            if perimeter > 0:
                circularity = 4 * np.pi * area / (perimeter * perimeter)
            else:
                circularity = 0

            stain_info['stain_details'].append({
                'id': i + 1,
                'area': area,
                'bounding_box': (x, y, w, h),
                'circularity': circularity,
                'centroid': (x + w // 2, y + h // 2)
            })

        total_pixels = final_mask.shape[0] * final_mask.shape[1]
        stain_info['coverage_percentage'] = (stain_info['total_area'] / total_pixels) * 100

        return stain_info

    def calculate_cleaning_recommendation(self, stain_count, coverage_percentage):
        """
        根据污渍数量和覆盖率计算消毒推荐方案
        """
        try:
            # 重新设计评分逻辑，优先考虑污渍数量，覆盖率作为次要因素
            if stain_count == 0:
                # 没有污渍
                return {
                    'severity_score': 0,
                    'cleaning_time': 0,
                    'cleaning_intensity': "无需处理",
                    'cleaning_method': "无需消毒",
                    'disinfectant_amount': 0,
                    'recommendation_level': "无污渍"
                }

            # 根据污渍数量确定基础级别
            if stain_count == 1:
                # 单个污渍：主要看大小
                if coverage_percentage < 5:
                    base_level = 1  # 小污渍
                elif coverage_percentage < 20:
                    base_level = 2  # 中等污渍
                elif coverage_percentage < 50:
                    base_level = 3  # 大污渍
                else:   
                    base_level = 4  # 超大污渍

            elif stain_count <= 5:
                # 少量污渍
                if coverage_percentage < 10:
                    base_level = 2  # 分散小污渍
                elif coverage_percentage < 30:
                    base_level = 3  # 中等聚集
                else:
                    base_level = 4  # 密集污渍

            elif stain_count <= 20:
                # 中等数量污渍
                if coverage_percentage < 15:
                    base_level = 3  # 分散污渍
                elif coverage_percentage < 40:
                    base_level = 4  # 聚集污渍
                else:
                    base_level = 5  # 严重污染

            else:   
                # 大量污渍
                if coverage_percentage < 20:
                    base_level = 4  # 大量小污渍
                elif coverage_percentage < 50:
                    base_level = 5  # 中等污染
                else:
                    base_level = 6  # 严重污染

            # 根据基础级别确定具体方案
            if base_level == 1:
                cleaning_time = 1 + (coverage_percentage * 0.1)  # 1-2分钟
                cleaning_intensity = "轻柔"
                cleaning_method = "局部擦拭"
                disinfectant_amount = 0.2
            elif base_level == 2:
                cleaning_time = 2 + (coverage_percentage * 0.15)  # 2-5分钟
                cleaning_intensity = "轻柔"
                cleaning_method = "常规消毒液擦拭"
                disinfectant_amount = 0.5
            elif base_level == 3:
                cleaning_time = 5 + (coverage_percentage * 0.2)  # 5-15分钟
                cleaning_intensity = "中等"
                cleaning_method = "消毒液浸泡+擦拭"
                disinfectant_amount = 1.0
            elif base_level == 4:
                cleaning_time = 10 + (coverage_percentage * 0.3)  # 10-25分钟
                cleaning_intensity = "强力"
                cleaning_method = "强力消毒剂处理"
                disinfectant_amount = 2.0
            elif base_level == 5:
                cleaning_time = 15 + (coverage_percentage * 0.4)  # 15-35分钟
                cleaning_intensity = "深度"
                cleaning_method = "专业消毒剂深度清洁"
                disinfectant_amount = 3.0
            else:  # base_level == 6
                cleaning_time = 25 + (coverage_percentage * 0.5)  # 25-75分钟
                cleaning_intensity = "深度"
                cleaning_method = "高强度专业消毒处理"
                disinfectant_amount = 5.0

            # 确保时间在合理范围内
            cleaning_time = min(max(cleaning_time, 1), 60)

            # 严重程度评分（用于显示）
            severity_score = base_level * 5 + min(coverage_percentage / 10, 5)

            return {
                'severity_score': round(severity_score, 1),
                'cleaning_time': round(cleaning_time, 1),
                'cleaning_intensity': cleaning_intensity,
                'cleaning_method': cleaning_method,
                'disinfectant_amount': round(disinfectant_amount, 1),
                'recommendation_level': self.get_recommendation_level(base_level)
            }
    
        except Exception as e:
            print(f"❌ 计算清洁推荐时出错: {e}")
            # 返回一个安全的默认值
            return {
                'severity_score': 0,
                'cleaning_time': 0,
                'cleaning_intensity': "未知",
                'cleaning_method': "需要检查",
                'disinfectant_amount': 0,
                'recommendation_level': "未知"
            }
    def get_recommendation_level(self, base_level):
        """获取推荐级别"""
        levels = {
            1: "轻微处理",
            2: "轻度处理",
            3: "中度处理",
            4: "重度处理",
            5: "专业处理",
            6: "紧急处理"
        }
        return levels.get(base_level, "未知级别")

    def save_detection_results(self, machine_id, machine_name, upload_time, result_files):
        """保存检测结果到result文件夹"""
        import sys
        from pathlib import Path
        
        # 获取项目根目录
        BASE_DIR = Path(__file__).parent
        machine_folder = f"{machine_id}_{machine_name}"
        result_dir = BASE_DIR / 'update' / machine_folder / 'fabric' / 'result' / upload_time
        
        # 确保result目录存在
        result_dir.mkdir(parents=True, exist_ok=True)
        
        saved_files = {}
        
        for file_type, (file_data, filename) in result_files.items():
            file_path = result_dir / filename
            if isinstance(file_data, np.ndarray):
                # 如果是numpy数组（图像数据），使用OpenCV保存
                cv2.imwrite(str(file_path), file_data)
            else:
                # 如果是PIL图像或其他数据
                file_data.save(str(file_path))
            
            saved_files[file_type] = str(file_path.relative_to(BASE_DIR))
            print(f"💾 保存{file_type}结果: {file_path}")
        
        return saved_files

    def detect_all_stains(self, image_path, machine_id=None, machine_name=None, upload_time=None, method='combined', visualize=True):
        """
        综合污渍检测主函数
        """
        print(f"🔍 开始污渍检测，方法: {method}")
        self.load_image(image_path)

        if method == 'color':
            stain_mask = self.detect_stains_by_color()
        elif method == 'texture':
            stain_mask = self.detect_stains_by_texture()
        elif method == 'adaptive':
            stain_mask = self.detect_stains_adaptive()
        else:  # combined
            color_mask = self.detect_stains_by_color()
            texture_mask = self.detect_stains_by_texture()
            adaptive_mask = self.detect_stains_adaptive()
            stain_mask = cv2.bitwise_or(color_mask, texture_mask)
            stain_mask = cv2.bitwise_or(stain_mask, adaptive_mask)

        optimized_mask = self.morphological_operations(stain_mask)
        stain_analysis = self.analyze_stains(optimized_mask)

        # 计算消毒推荐
        cleaning_recommendation = self.calculate_cleaning_recommendation(
            stain_analysis['total_stains'],
            stain_analysis['coverage_percentage']
        )

        self.results = {
            'original_image': self.image_rgb,
            'stain_mask': optimized_mask,
            'analysis': stain_analysis,
            'cleaning_recommendation': cleaning_recommendation
        }

        # 保存结果图片
        if machine_id and machine_name and upload_time:
            result_files = {
                'mask': (optimized_mask, 'stain_mask.png'),
                'overlay': (self.create_overlay_image(), 'overlay.png')
            }
            
            saved_files = self.save_detection_results(machine_id, machine_name, upload_time, result_files)
            self.results['saved_files'] = saved_files

        if visualize and MATPLOTLIB_AVAILABLE:
            self.visualize_results()

        print(f"✅ 污渍检测完成: {stain_analysis['total_stains']} 个污渍, 覆盖率: {stain_analysis['coverage_percentage']:.2f}%")
        return self.results

    def create_overlay_image(self):
        """创建污渍区域叠加显示图像"""
        overlay = self.results['original_image'].copy()
        mask_rgb = np.zeros_like(self.results['original_image'])
        mask_rgb[self.results['stain_mask'] > 0] = [255, 0, 0]  # 红色显示污渍区域

        alpha = 0.3
        cv2.addWeighted(mask_rgb, alpha, overlay, 1 - alpha, 0, overlay)
        return overlay

    def visualize_results(self):
        """可视化结果"""
        # 确保字体设置已应用
        self.setup_chinese_font()
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))

        axes[0, 0].imshow(self.results['original_image'])
        axes[0, 0].set_title('原始图像')
        axes[0, 0].axis('off')

        axes[0, 1].imshow(self.results['stain_mask'], cmap='gray')
        axes[0, 1].set_title('检测到的污渍区域')
        axes[0, 1].axis('off')

        overlay = self.create_overlay_image()
        axes[1, 0].imshow(overlay)
        axes[1, 0].set_title('污渍区域叠加显示')
        axes[1, 0].axis('off')

        analysis = self.results['analysis']
        cleaning = self.results['cleaning_recommendation']

        # 显示污渍统计和消毒建议
        axes[1, 1].text(0.1, 0.95, f"污渍数量: {analysis['total_stains']}", fontsize=12)
        axes[1, 1].text(0.1, 0.90, f"污渍覆盖率: {analysis['coverage_percentage']:.2f}%", fontsize=12)
        axes[1, 1].text(0.1, 0.85, f"严重程度评分: {cleaning['severity_score']}", fontsize=12)
        axes[1, 1].text(0.1, 0.80, f"处理级别: {cleaning['recommendation_level']}", fontsize=12,
                        color='red' if cleaning['recommendation_level'] in ['重度处理', '专业处理'] else 'black')

        axes[1, 1].text(0.1, 0.70, "消毒建议:", fontsize=12, weight='bold')
        axes[1, 1].text(0.1, 0.65, f"方式: {cleaning['cleaning_method']}", fontsize=10)
        axes[1, 1].text(0.1, 0.60, f"时间: {cleaning['cleaning_time']} 分钟", fontsize=10)
        axes[1, 1].text(0.1, 0.55, f"力度: {cleaning['cleaning_intensity']}", fontsize=10)
        axes[1, 1].text(0.1, 0.50, f"消毒剂: {cleaning['disinfectant_amount']} ml", fontsize=10)

        axes[1, 1].set_xlim(0, 1)
        axes[1, 1].set_ylim(0, 1)
        axes[1, 1].axis('off')
        axes[1, 1].set_title('污渍分析及消毒建议')

        plt.tight_layout()
        plt.show()

    def save_results(self, output_path):
        """保存结果"""
        if not self.results:
            print("没有可保存的结果，请先运行检测")
            return

        # 使用PIL保存图像，避免中文路径问题
        mask_pil = Image.fromarray(self.results['stain_mask'])
        mask_pil.save(output_path + '_mask.png')

        overlay = self.results['original_image'].copy()
        mask_rgb = np.zeros_like(self.results['original_image'])
        mask_rgb[self.results['stain_mask'] > 0] = [255, 0, 0]
        alpha = 0.3
        cv2.addWeighted(mask_rgb, alpha, overlay, 1 - alpha, 0, overlay)

        # 转换回RGB并保存
        overlay_rgb = cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)
        overlay_pil = Image.fromarray(overlay_rgb)
        overlay_pil.save(output_path + '_overlay.png')

        with open(output_path + '_analysis.txt', 'w', encoding='utf-8') as f:
            analysis = self.results['analysis']
            cleaning = self.results['cleaning_recommendation']

            f.write("污渍分析报告\n")
            f.write("=" * 50 + "\n")
            f.write(f"污渍总数: {analysis['total_stains']}\n")
            f.write(f"总污渍面积: {analysis['total_area']:.2f} 像素\n")
            f.write(f"污渍覆盖率: {analysis['coverage_percentage']:.2f}%\n\n")

            f.write("消毒建议方案\n")
            f.write("=" * 50 + "\n")
            f.write(f"严重程度评分: {cleaning['severity_score']}\n")
            f.write(f"处理级别: {cleaning['recommendation_level']}\n")
            f.write(f"消毒方式: {cleaning['cleaning_method']}\n")
            f.write(f"消毒时间: {cleaning['cleaning_time']} 分钟\n")
            f.write(f"消毒力度: {cleaning['cleaning_intensity']}\n")
            f.write(f"消毒剂用量: {cleaning['disinfectant_amount']} ml\n\n")

            f.write("污渍详情:\n")
            for stain in analysis['stain_details']:
                f.write(f"污渍 {stain['id']}: 面积={stain['area']:.1f}, "
                        f"位置={stain['bounding_box']}, 圆形度={stain['circularity']:.3f}\n")

# 以下函数可以根据需要保留或移除
def process_images_from_train_folder():
    """处理train文件夹中的所有图片"""
    pass

def generate_summary_report(summary_report, output_dir):
    """生成处理摘要报告"""
    pass

def preview_first_image():
    """预览第一张图片的检测结果"""
    pass

if __name__ == "__main__":
    print("污渍检测模块独立运行测试")
    # 这里可以添加测试代码