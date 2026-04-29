#!/usr/bin/env python
"""
AI消毒机系统 - 快速启动脚本
"""
import sys
from pathlib import Path

# 添加src到路径
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR / 'src'))

def check_dependencies():
    """检查依赖"""
    print("🔍 检查依赖...")
    
    required_packages = ['flask']
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ 缺少依赖: {', '.join(missing)}")
        print("💡 请运行: pip install -r requirements.txt")
        return False
    
    print("✅ 依赖检查通过")
    return True


def check_directories():
    """检查并创建必要目录"""
    print("📁 检查目录结构...")
    
    dirs = [
        BASE_DIR / 'config',
        BASE_DIR / 'data',
        BASE_DIR / 'reports',
        BASE_DIR / 'update',
    ]
    
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    print("✅ 目录结构就绪")


def print_banner():
    """打印启动横幅"""
    print("\n" + "=" * 60)
    print("🤖 AI消毒机管理系统")
    print("=" * 60)
    print("📦 版本: 1.0.0 (重构版)")
    print("🏗️ 架构: 面向对象模块化设计")
    print("=" * 60 + "\n")


def main():
    """主函数"""
    print_banner()
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 检查目录
    check_directories()
    
    # 导入并启动
    from new_app import create_app, main as app_main
    
    print("🚀 启动AI消毒机系统...\n")
    app_main()


if __name__ == '__main__':
    main()
