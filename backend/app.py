"""
AI消毒机系统 - 重构版主应用
基于面向对象架构
"""
import sys
import logging
from pathlib import Path

# 添加src到路径
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR / 'src'))

from flask import Flask
from api.routes import register_routes
from data_management.csv_manager import CSVManager
from machine_core.app_context import AppContext
from machine_core.logger import get_app_logger
from machine_core.config import Config


def create_app():
    """创建Flask应用"""
    
    # 初始化配置
    Config.init_directories()
    
    # 初始化日志
    logger = get_app_logger(Config.LOG_DIR)
    logger.info("AI消毒机系统启动中...")
    
    # 初始化Flask应用，指向前端目录
    app = Flask(
        __name__,
        static_folder=str(Config.STATIC_DIR),
        template_folder=str(Config.TEMPLATE_DIR)
    )
    app.secret_key = Config.SECRET_KEY
    
    # 初始化CSV系统
    csv_manager = CSVManager(Config.CSV_FILE)
    csv_manager.create_default_data()
    
    # 初始化应用上下文
    app_context = AppContext(Config.BASE_DIR)
    
    # 将共享资源存储到app.config中
    app.config['BASE_DIR'] = Config.BASE_DIR
    app.config['CSV_MANAGER'] = csv_manager
    app.config['APP_CONTEXT'] = app_context
    app.config['LOGGER'] = logger
    
    # 注册所有路由
    register_routes(app, Config.BASE_DIR)
    
    logger.info("应用创建完成")
    return app


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 AI消毒机系统启动中...")
    print("=" * 60)
    
    # 创建应用
    app = create_app()
    logger = app.config.get('LOGGER')
    
    # 从环境变量获取端口，如果没有则使用默认值
    import os
    port = int(os.environ.get('PORT', Config.PORT))

    print("\n" + "=" * 60)
    print("✅ 系统初始化完成")
    print(f"🌐 访问地址: http://localhost:{port}")
    print("👤 测试账号: admin/admin123 或 user1/user123")
    print("=" * 60)
    
    logger.info("系统初始化完成，准备启动服务")
    
    # 启动应用
    try:
        app.run(debug=Config.DEBUG, host=Config.HOST, port=port)
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        raise


if __name__ == '__main__':
    main()
