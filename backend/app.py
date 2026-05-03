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

    # 获取项目根目录（backend的父目录）
    project_root = Path(__file__).parent.parent

    # 明确指定前端模板和静态文件目录
    template_dir = project_root / "frontend" / "templates"
    static_dir = project_root / "frontend" / "static"

    # 如果frontend目录不存在，则回退到Config中的配置
    if not template_dir.exists():
        template_dir = Config.TEMPLATE_DIR
        static_dir = Config.STATIC_DIR
        print(f"警告: frontend/templates不存在，使用默认模板目录: {template_dir}")

    # 打印调试信息
    print(f"模板目录: {template_dir}")
    print(f"模板目录是否存在: {template_dir.exists()}")
    print(f"login.html是否存在: {(template_dir / 'login.html').exists()}")

    # 初始化日志
    logger = get_app_logger(Config.LOG_DIR)
    logger.info("AI消毒机系统启动中...")
    logger.info(f"模板目录: {template_dir}")
    logger.info(f"静态文件目录: {static_dir}")

    # 初始化Flask应用，指向前端目录
    app = Flask(
        __name__,
        static_folder=str(static_dir),
        template_folder=str(template_dir)
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