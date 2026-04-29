"""
日志配置模块
提供统一的日志记录功能
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


def setup_logger(name: str, log_dir: Path = None, level: int = logging.INFO) -> logging.Logger:
    """
    配置并返回logger实例
    
    Args:
        name: logger名称
        log_dir: 日志文件目录
        level: 日志级别
    
    Returns:
        配置好的logger实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件handler（如果指定了log_dir）
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f'{name}.log'
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_app_logger(log_dir: Path = None) -> logging.Logger:
    """获取应用级别的logger"""
    return setup_logger('aimachine', log_dir)


def get_route_logger(log_dir: Path = None) -> logging.Logger:
    """获取路由级别的logger"""
    return setup_logger('routes', log_dir)


def get_core_logger(log_dir: Path = None) -> logging.Logger:
    """获取核心模块级别的logger"""
    return setup_logger('core', log_dir)
