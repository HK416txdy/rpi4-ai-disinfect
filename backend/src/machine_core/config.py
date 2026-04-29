"""
应用配置模块
集中管理应用的所有配置项
"""
from pathlib import Path
from typing import Dict, Any


class Config:
    """应用配置类"""
    
    # 基础路径 - 指向项目根目录
    BASE_DIR = Path(__file__).parent.parent.parent
    
    # 服务器配置
    HOST = '0.0.0.0'
    PORT = 5001
    DEBUG = True
    SECRET_KEY = 'your-secret-key-here-change-in-production'
    
    # 路径配置
    DATA_DIR = BASE_DIR / 'data'
    LOG_DIR = BASE_DIR / 'logs'
    REPORT_DIR = BASE_DIR / 'reports'
    UPDATE_DIR = BASE_DIR / 'update'
    FRONTEND_DIR = BASE_DIR / 'frontend'
    STATIC_DIR = FRONTEND_DIR / 'static'
    TEMPLATE_DIR = FRONTEND_DIR / 'templates'
    
    # CSV配置
    CSV_FILE = DATA_DIR / 'machines.csv'
    
    # 摄像头配置
    CAMERA_ID = 0
    
    # 检测参数
    GRAY_THRESHOLD = 128
    CONTRAST_THRESHOLD = 30
    UNIFORMITY_THRESHOLD = 0.8
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # 默认用户（仅用于开发环境）
    DEFAULT_USERS = {
        'admin': 'admin123',
        'user1': 'user123'
    }
    
    # 默认消毒机
    DEFAULT_MACHINES = [
        {
            'id': 1,
            'name': '消毒机A',
            'location': '北京市海淀区',
            'enabled': True,
            'status': '正常',
            'disinfected_count': 1250,
            'runtime_hours': 125.5
        },
        {
            'id': 2,
            'name': '消毒机B',
            'location': '上海市浦东新区',
            'enabled': True,
            'status': '警告',
            'disinfected_count': 890,
            'runtime_hours': 89.0
        }
    ]
    
    @classmethod
    def init_directories(cls):
        """初始化所有必要的目录"""
        dirs = [
            cls.DATA_DIR,
            cls.LOG_DIR,
            cls.REPORT_DIR,
            cls.UPDATE_DIR,
            cls.STATIC_DIR,
            cls.TEMPLATE_DIR
        ]
        
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """将配置转换为字典"""
        return {
            'BASE_DIR': cls.BASE_DIR,
            'HOST': cls.HOST,
            'PORT': cls.PORT,
            'DEBUG': cls.DEBUG,
            'SECRET_KEY': cls.SECRET_KEY,
            'DATA_DIR': cls.DATA_DIR,
            'LOG_DIR': cls.LOG_DIR,
            'REPORT_DIR': cls.REPORT_DIR,
            'CSV_FILE': cls.CSV_FILE,
            'CAMERA_ID': cls.CAMERA_ID,
        }


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    SECRET_KEY = 'change-this-to-a-secure-random-key-in-production'


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True


# 配置映射
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env: str = 'default') -> Config:
    """获取指定环境的配置"""
    return config_map.get(env, config_map['default'])


class MachineConfig:
    """消毒机配置类（保留向后兼容）"""
    
    def __init__(self):
        self.disinfection_modes = {
            1: {'name': '模式1（常规消毒）', 'intensity': '低'},
            2: {'name': '模式2（强化消毒）', 'intensity': '中'},
            3: {'name': '模式3（深度消毒）', 'intensity': '高'},
            4: {'name': '模式4（特殊消毒）', 'intensity': '极高'}
        }
        self.bacteria_types = {
            '普通细菌(大肠杆菌等)': {'risk_level': 1, 'base_time': 15},
            '致病菌(金黄色葡萄球菌等)': {'risk_level': 2, 'base_time': 20},
            '耐药菌(MRSA等)': {'risk_level': 3, 'base_time': 25},
            '特殊病原体(芽孢杆菌等)': {'risk_level': 4, 'base_time': 35}
        }
        self.compliance_standards = {
            1: {'name': '基础标准', 'min_sterilization_rate': 99.9},
            2: {'name': '医疗标准', 'min_sterilization_rate': 99.99},
            3: {'name': '高标准', 'min_sterilization_rate': 99.999}
        }
        self.pollution_severity = {
            1: '轻度污染 - 污染物少，风险低',
            2: '中度污染 - 污染物中等，需标准处理',
            3: '重度污染 - 污染物较多，风险较高',
            4: '极重污染 - 污染物严重，高风险'
        }
