import os
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import cv2
import datetime
from pathlib import Path
import json

# 设置随机种子
np.random.seed(42)
tf.random.set_seed(42)

# 数据加载和预处理类
class MedicalImageProcessor:
    def __init__(self, image_size=(224, 224)):
        self.image_size = image_size
        self.tool_categories = {
            'scalpel': 0,  # 解剖刀
            'straight_clamp': 1,  # 直解剖夹
            'straight_scissors': 2,  # 直马眼剪刀
            'curved_scissors': 3  # 弯马眼剪刀
        }
        self.position_categories = {
            'top': 0,  # 顶部（未被遮挡）
            'bottom': 1  # 底部（被遮挡）
        }

    def load_images_from_folders(self, base_folder, max_samples_per_class=None):
        """直接从基础文件夹的子目录加载图片"""
        images = []
        tool_labels = []
        position_labels = []
        filenames = []

        image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')

        if not os.path.exists(base_folder):
            print(f"错误: 文件夹 {base_folder} 不存在")
            return np.array([]), np.array([]), np.array([]), []

        print(f"正在从 {base_folder} 加载图片...")

        # 递归搜索所有子文件夹
        image_files = []
        for root, dirs, files in os.walk(base_folder):
            for file in files:
                if file.lower().endswith(image_extensions):
                    file_path = os.path.join(root, file)
                    image_files.append(file_path)
        
        print(f"总共找到 {len(image_files)} 个图片文件")

        # 从文件路径提取标签
        for file_path in image_files:
            try:
                print(f"处理图片: {file_path}")
                
                # 从文件路径提取文件夹信息
                relative_path = os.path.relpath(file_path, base_folder)
                folder_name = os.path.dirname(relative_path)
                
                print(f"相对路径: {relative_path}")
                print(f"文件夹名: {folder_name}")
                
                # 从文件夹名提取标签
                tool_label, position_label = self.extract_labels_from_foldername(folder_name)

                if tool_label is None:
                    print(f"警告: 无法识别路径 '{relative_path}' 中的工具类型，跳过")
                    continue

                # 使用matplotlib读取图片
                try:
                    # 使用 matplotlib.image.imread 读取图片
                    image = mpimg.imread(file_path)
                    if image is None:
                        print(f"❌ matplotlib无法读取图片: {file_path}")
                        continue
                    
                    # 检查图片通道数并处理
                    if len(image.shape) == 2:  # 灰度图
                        image = np.stack([image] * 3, axis=-1)
                    elif image.shape[2] == 4:  # RGBA图
                        image = image[:, :, :3]  # 取前三个通道(RGB)
                    
                    # 调整大小和归一化
                    from PIL import Image
                    pil_image = Image.fromarray((image * 255).astype(np.uint8) if image.dtype == np.float32 else image.astype(np.uint8))
                    pil_image = pil_image.resize(self.image_size)
                    image = np.array(pil_image)
                    image = image.astype('float32') / 255.0

                    images.append(image)
                    filenames.append(relative_path)
                    tool_labels.append(tool_label)
                    position_labels.append(position_label)
                    print(f"✅ 成功加载图片: {file_path}")
                    
                except Exception as img_error:
                    print(f"❌ 图片处理错误 {file_path}: {img_error}")
                    continue
                    
            except Exception as e:
                print(f"处理图片 {file_path} 时出错: {e}")
                continue

        if images:
            images = np.array(images)
            tool_labels = np.array(tool_labels, dtype=np.int32)
            position_labels = np.array(position_labels, dtype=np.int32)
            print(f"\n✅ 成功加载 {len(images)} 张图片")
        else:
            print("❌ 未找到任何可用的图片文件")

        return images, tool_labels, position_labels, filenames

    def extract_labels_from_foldername(self, folder_name):
        """从文件夹名提取工具和位置标签"""
        folder_lower = folder_name.lower()

        # 工具识别
        tool_label = None
        if any(keyword in folder_lower for keyword in ['scalpel', '解剖刀']):
            tool_label = 0
        elif any(keyword in folder_lower for keyword in ['straight_clamp', '直解剖夹']):
            tool_label = 1
        elif any(keyword in folder_lower for keyword in ['straight_scissors', '直马眼剪刀']):
            tool_label = 2
        elif any(keyword in folder_lower for keyword in ['curved_scissors', '弯马眼剪刀']):
            tool_label = 3

        # 位置识别
        position_label = 1 if any(keyword in folder_lower for keyword in ['bottom', '底部']) else 0

        return tool_label, position_label

    def preprocess_single_image(self, image_path):
        """预处理单张图片用于预测"""
        # 使用 matplotlib 读取图片
        image = mpimg.imread(image_path)
        if image is None:
            raise ValueError(f"无法读取图片: {image_path}")
        
        original_image = image.copy()
        
        # 检查图片通道数并处理
        if len(image.shape) == 2:  # 灰度图
            image = np.stack([image] * 3, axis=-1)
        elif image.shape[2] == 4:  # RGBA图
            image = image[:, :, :3]  # 取前三个通道(RGB)
        
        # 使用PIL调整大小
        from PIL import Image
        pil_image = Image.fromarray((image * 255).astype(np.uint8) if image.dtype == np.float32 else image.astype(np.uint8))
        pil_image = pil_image.resize(self.image_size)
        image = np.array(pil_image)
        image = image.astype('float32') / 255.0
        image = np.expand_dims(image, axis=0)
        
        return image, original_image

# 构建模型
def create_medical_cnn_model(input_shape=(224, 224, 3), num_tool_classes=4, num_position_classes=2):
    inputs = keras.Input(shape=input_shape)
    x = layers.Conv2D(32, (3, 3), activation='relu')(inputs)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D((2, 2))(x)
    x = layers.Conv2D(64, (3, 3), activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D((2, 2))(x)
    x = layers.Conv2D(128, (3, 3), activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D((2, 2))(x)
    x = layers.Conv2D(256, (3, 3), activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D((2, 2))(x)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(512, activation='relu')(x)
    x = layers.Dropout(0.5)(x)
    x = layers.Dense(256, activation='relu')(x)
    x = layers.Dropout(0.3)(x)
    tool_output = layers.Dense(num_tool_classes, activation='softmax', name='tool_class')(x)
    position_output = layers.Dense(num_position_classes, activation='softmax', name='position_class')(x)
    model = keras.Model(inputs=inputs, outputs=[tool_output, position_output])
    return model

# 训练和评估类
class MedicalImageClassifier:
    def __init__(self, model, processor):
        self.model = model
        self.processor = processor

    def compile_model(self):
        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss={'tool_class': 'sparse_categorical_crossentropy', 'position_class': 'sparse_categorical_crossentropy'},
            loss_weights={'tool_class': 1.0, 'position_class': 1.0},
            metrics={'tool_class': 'accuracy', 'position_class': 'accuracy'}
        )

    def train(self, X_train, y_tool_train, y_position_train, X_val, y_tool_val, y_position_val, epochs=50):
        callbacks = [
            keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True),
            keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=5)
        ]
        history = self.model.fit(
            X_train,
            {'tool_class': y_tool_train, 'position_class': y_position_train},
            validation_data=(X_val, {'tool_class': y_tool_val, 'position_class': y_position_val}),
            epochs=epochs,
            batch_size=32,
            callbacks=callbacks,
            verbose=1
        )
        return history

    def evaluate(self, X_test, y_tool_test, y_position_test):
        tool_predictions, position_predictions = self.model.predict(X_test)
        tool_pred_labels = np.argmax(tool_predictions, axis=1)
        position_pred_labels = np.argmax(position_predictions, axis=1)
        print("\n" + "=" * 50)
        print("工具类型分类报告:")
        print("=" * 50)
        print(classification_report(y_tool_test, tool_pred_labels,
                                    target_names=['解剖刀', '直解剖夹', '直马眼剪刀', '弯马眼剪刀']))
        print("\n" + "=" * 50)
        print("位置分类报告:")
        print("=" * 50)
        print(classification_report(y_position_test, position_pred_labels, target_names=['顶部', '底部']))
        return tool_pred_labels, position_pred_labels

# 模型管理类
class ModelManager:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.model_pattern = "medical_tool_classifier"
    
    def get_latest_model(self):
        """获取最新的模型文件"""
        model_files = []
        for file in os.listdir(self.base_dir):
            if file.startswith(self.model_pattern) and file.endswith('.h5'):
                model_files.append(file)
        
        if not model_files:
            return None
        
        # 按时间排序，返回最新的模型
        model_files.sort(reverse=True)
        return os.path.join(self.base_dir, model_files[0])
    
    def save_model_with_timestamp(self, model, prefix="medical_tool_classifier"):
        """使用时间戳保存模型，不覆盖原有模型"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        model_filename = f"{prefix}_{timestamp}.h5"
        model_path = os.path.join(self.base_dir, model_filename)
        model.save(model_path)
        print(f"✅ 模型已保存为: {model_path}")
        return model_path

class MedicalEquipmentDetector:
    def __init__(self, model_dir=None):
        self.processor = MedicalImageProcessor(image_size=(224, 224))
        self.model_dir = model_dir or os.path.dirname(__file__)
        self.model_manager = ModelManager(self.model_dir)
        
        # 加载最新模型
        self.load_latest_model()
        
        self.tool_names = ['解剖刀', '直解剖夹', '直马眼剪刀', '弯马眼剪刀']
        self.position_names = ['顶部', '底部']
    
    def load_latest_model(self, machine_id=None, machine_name=None):
        """加载对应消毒机的最新模型文件"""
        model_files = []  # 在这里初始化 model_files
    
        if machine_id and machine_name:
            # 查找对应消毒机的最新模型
            model_pattern = f"medical_tool_classifier_{machine_id}_{machine_name}_"
            for file in os.listdir(self.model_dir):
                if file.startswith(model_pattern) and file.endswith('.h5'):
                    model_files.append(file)
    
        if model_files:
            # 按时间戳排序，获取最新的模型
            model_files.sort(reverse=True)
            latest_model_path = os.path.join(self.model_dir, model_files[0])
            try:
                self.model = tf.keras.models.load_model(latest_model_path)
                print(f"✅ 加载消毒机专属模型: {latest_model_path}")
                return True
            except Exception as e:
                print(f"❌ 加载专属模型失败: {e}")
    
        # 如果找不到专属模型，回退到通用模型
        return self.load_generic_model()

    def load_generic_model(self):
        """加载通用模型（原有的逻辑）"""
        model_files = []
        for file in os.listdir(self.model_dir):
            if file.startswith("medical_tool_classifier") and file.endswith('.h5'):
                model_files.append(file)
    
        if model_files:
            # 按时间戳排序，获取最新的通用模型
            model_files.sort(reverse=True)
            latest_model_path = os.path.join(self.model_dir, model_files[0])
            try:
                self.model = tf.keras.models.load_model(latest_model_path)
                print(f"✅ 加载通用模型: {latest_model_path}")
                return True
            except Exception as e:
                print(f"❌ 加载模型失败: {e}")

        # 如果没有找到任何模型，创建新模型
        self.model = create_medical_cnn_model()
        print("⚠️ 使用未训练的模型，请先训练模型")
        return False

    # 修改 predict_single_image 方法，添加机器参数
    def predict_single_image(self, image_path, machine_id=None, machine_name=None):
        """预测单张图片"""
        try:
            # 每次预测前检查是否有对应消毒机的模型
            if machine_id and machine_name:
                self.load_latest_model(machine_id, machine_name)
            else:
                self.load_generic_model()

            # 使用处理器的预处理方法
            image, original_image = self.processor.preprocess_single_image(image_path)

            # 预测
            tool_pred, position_pred = self.model.predict(image, verbose=0)

            # 获取预测结果
            tool_idx = np.argmax(tool_pred[0])
            position_idx = np.argmax(position_pred[0])

            tool_confidence = float(tool_pred[0][tool_idx])
            position_confidence = float(position_pred[0][position_idx])
            overall_confidence = float((tool_confidence + position_confidence) / 2)

            # 生成维护建议
            status, maintenance_advice = self.generate_maintenance_advice(
                self.tool_names[tool_idx], 
                overall_confidence
            )
        
            return {
                'success': True,
               'tool_type': self.tool_names[tool_idx],
                'position': self.position_names[position_idx],
                'confidence': overall_confidence,
                'tool_confidence': tool_confidence,
                'position_confidence': position_confidence,
                'status': status,
                'maintenance_advice': maintenance_advice,
                'model_used': f"{machine_id}_{machine_name}" if machine_id and machine_name else "generic"
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def generate_maintenance_advice(self, tool_type, confidence):
        """生成维护建议"""
        if confidence > 0.9:
            status = '正常'
            advice = f'{tool_type}状态良好，可正常使用'
        elif confidence > 0.7:
            status = '需维护'
            advice = f'{tool_type}建议进行清洁和校准'
        else:
            status = '需更换'
            advice = f'{tool_type}磨损严重，建议更换'
        
        return status, advice


    def detect_equipment(self, image_path, machine_id, machine_name):
        """检测设备 - 与 predict_single_image 功能相同，但参数匹配web接口"""
        return self.predict_single_image(image_path, machine_id, machine_name)
    def train_with_default_data(self, base_folder, epochs=50, save_dir=None, machine_id=None, machine_name=None):
        """使用默认数据训练模型并保存"""
        global training_interrupted
        
        print("🔧 开始使用默认数据训练模型...")
        print(f"数据路径: {base_folder}")
        print(f"保存路径: {save_dir}")
        print(f"机器信息: {machine_id} - {machine_name}")
        
        try:
            # 检查训练数据目录
            if not os.path.exists(base_folder):
                return {'success': False, 'error': f'训练数据目录不存在: {base_folder}'}
            
            # 加载训练数据
            images, tool_labels, position_labels, filenames = self.processor.load_images_from_folders(base_folder)
            
            if len(images) == 0:
                return {'success': False, 'error': '没有找到训练图片'}
            
            print(f"✅ 成功加载 {len(images)} 张训练图片")
            
            # 分割数据集
            X_train, X_val, y_tool_train, y_tool_val, y_position_train, y_position_val = train_test_split(
                images, tool_labels, position_labels, test_size=0.2, random_state=42
            )
            
            # 创建分类器并训练
            classifier = MedicalImageClassifier(self.model, self.processor)
            classifier.compile_model()
            
            print("🎯 开始训练模型...")
            
            history = classifier.model.fit(
                X_train,
                {'tool_class': y_tool_train, 'position_class': y_position_train},
                validation_data=(X_val, {'tool_class': y_tool_val, 'position_class': y_position_val}),
                epochs=epochs,
                batch_size=32,
                callbacks=[
                    keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True),
                    keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=5),
                ],
                verbose=1
            )
            
            # 创建结果目录
            result_dir = None
            if save_dir:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                result_folder = f"{machine_id}_{machine_name}_{timestamp}"
                result_dir = Path(save_dir) / result_folder
                result_dir.mkdir(parents=True, exist_ok=True)
                
                # 保存训练图表
                self.plot_training_history(history, result_dir, machine_id, machine_name)
                
                # 保存训练报告
                training_report = {
                    "status": "completed",
                    "training_samples": len(images),
                    "training_date": datetime.datetime.now().isoformat(),
                    "machine_info": {
                        "id": machine_id,
                        "name": machine_name
                    },
                    "final_accuracy": {
                        'tool_accuracy': float(history.history['tool_class_accuracy'][-1]),
                        'position_accuracy': float(history.history['position_class_accuracy'][-1]),
                        'val_tool_accuracy': float(history.history['val_tool_class_accuracy'][-1]),
                        'val_position_accuracy': float(history.history['val_position_class_accuracy'][-1])
                    }
                }
                
                report_path = result_dir / "training_report.json"
                with open(report_path, 'w', encoding='utf-8') as f:
                    json.dump(training_report, f, ensure_ascii=False, indent=2)
                
                print(f"✅ 训练结果保存在: {result_dir}")
            
                # 保存模型 - 使用消毒机专属命名
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                if machine_id and machine_name:
                    model_filename = f"medical_tool_classifier_{machine_id}_{machine_name}_{timestamp}.h5"
                else:
                    model_filename = f"medical_tool_classifier_{timestamp}.h5"

                model_path = Path(self.model_dir) / model_filename
                classifier.model.save(model_path)

                print(f"✅ 模型已保存: {model_path}")

                return {
                    'success': True,
                    'model_path': str(model_path),
                    'training_samples': len(images),
                    'result_dir': str(result_dir) if result_dir else None,
                    'final_accuracy': {
                    'tool_accuracy': float(history.history['tool_class_accuracy'][-1]),
                    'position_accuracy': float(history.history['position_class_accuracy'][-1]),
                    'val_tool_accuracy': float(history.history['val_tool_class_accuracy'][-1]),
                    'val_position_accuracy': float(history.history['val_position_class_accuracy'][-1])
                },
                'message': '模型训练完成！'
            }
        
        except Exception as e:
           print(f"❌ 训练失败: {e}")
           return {'success': False, 'error': f'训练失败: {str(e)}'}
    
    def plot_training_history(self, history, save_dir, machine_id, machine_name):
        """绘制训练历史图表"""
        try:
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            
            # 工具分类损失
            axes[0, 0].plot(history.history['tool_class_loss'], label='训练损失')
            axes[0, 0].plot(history.history['val_tool_class_loss'], label='验证损失')
            axes[0, 0].set_title('工具分类损失')
            axes[0, 0].legend()
            axes[0, 0].grid(True, alpha=0.3)
            
            # 工具分类准确率
            axes[0, 1].plot(history.history['tool_class_accuracy'], label='训练准确率')
            axes[0, 1].plot(history.history['val_tool_class_accuracy'], label='验证准确率')
            axes[0, 1].set_title('工具分类准确率')
            axes[0, 1].legend()
            axes[0, 1].grid(True, alpha=0.3)
            
            # 位置分类损失
            axes[1, 0].plot(history.history['position_class_loss'], label='训练损失')
            axes[1, 0].plot(history.history['val_position_class_loss'], label='验证损失')
            axes[1, 0].set_title('位置分类损失')
            axes[1, 0].legend()
            axes[1, 0].grid(True, alpha=0.3)
            
            # 位置分类准确率
            axes[1, 1].plot(history.history['position_class_accuracy'], label='训练准确率')
            axes[1, 1].plot(history.history['val_position_class_accuracy'], label='验证准确率')
            axes[1, 1].set_title('位置分类准确率')
            axes[1, 1].legend()
            axes[1, 1].grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # 保存图表
            chart_path = save_dir / "training_history.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"✅ 训练图表已保存: {chart_path}")
            
        except Exception as e:
            print(f"❌ 保存训练图表失败: {e}")

# 创建全局检测器实例
equipment_detector = MedicalEquipmentDetector()

# 使用示例
if __name__ == "__main__":
    # 配置路径
    BASE_FOLDER = "C:/Users/bentr/Desktop/images"
    
    # 测试训练功能
    training_result = equipment_detector.train_with_default_data(
        BASE_FOLDER, 
        epochs=10,
        save_dir="./training_results",
        machine_id=1,
        machine_name="测试机器"
    )
    
    if training_result['success']:
        print(f"✅ 训练完成: {training_result['message']}")
    else:
        print(f"❌ 训练失败: {training_result['error']}")