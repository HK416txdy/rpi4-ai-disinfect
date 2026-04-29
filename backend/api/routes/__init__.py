"""
API路由注册模块
"""
from pathlib import Path
from flask import Flask


def register_routes(app: Flask, base_dir: Path):
    """注册所有 API 路由"""
    
    # 导入并注册各个模块的路由
    from api.routes.auth_routes import register_auth_routes
    from api.routes.machine_routes import register_machine_routes
    from api.routes.detection_routes import register_detection_routes
    from api.routes.disinfection_routes import register_disinfection_routes
    from api.routes.report_routes import register_report_routes
    from api.routes.camera_routes import register_camera_routes
    from api.routes.runtime_routes import register_runtime_routes
    from api.routes.placeholder_routes import register_placeholder_routes
    from api.routes.hardware_routes import register_hardware_routes

    register_auth_routes(app, base_dir)
    register_machine_routes(app, base_dir)
    register_detection_routes(app, base_dir)
    register_disinfection_routes(app, base_dir)
    register_report_routes(app, base_dir)
    register_camera_routes(app, base_dir)
    register_runtime_routes(app, base_dir)
    register_placeholder_routes(app, base_dir)  # 占位路由（开发中的功能）
    register_hardware_routes(app, base_dir)

    print("✅ 所有 API 路由注册完成")
