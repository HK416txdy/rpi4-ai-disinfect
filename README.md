# AI消毒机管理系统

基于树莓派4B的智能消毒机管理系统，采用面向对象架构设计。

## 🚀 快速开始

### 项目结构

项目已拆分为三个独立组件：

- `frontend/`: 前端Web界面
- `backend/`: 后端API和核心逻辑
- `hardware/`: 硬件控制和检测（树莓派专用）

每个组件都有独立的文档和依赖。

### 1. 安装依赖

每个组件有自己的依赖：

```bash
# 后端
cd backend
pip install -r requirements.txt

# 前端（如果需要额外依赖）
cd ../frontend
# 前端依赖已在backend中

# 硬件
cd ../hardware
pip install -r requirements.txt
```

### 2. 启动系统

启动后端服务：

```bash
cd backend
python run_new_app.py
```

### 3. 访问系统
- URL: http://localhost:5000
- 管理员: admin / admin123
- 用户: user1 / user123

## 📚 文档

完整文档请查看 [docs/](docs/) 目录：

- 🚀 [快速入门](docs/QUICKSTART.md) - 5分钟上手
- 📋 [项目总览](docs/PROJECT_OVERVIEW.md) - 全面了解
- 🏗️ [系统架构](docs/ARCHITECTURE.md) - 架构设计
- 🔄 [重构指南](docs/REFACTORING_GUIDE.md) - 重构说明
- 📊 [重构总结](docs/SUMMARY.md) - 重构成果

各组件独立文档：
- [后端文档](backend/README.md)
- [前端文档](frontend/README.md)
- [硬件文档](hardware/README.md)

## 🏗️ 项目结构

```
AImachine/
├── frontend/                     # 前端Web界面
│   ├── static/                  # CSS, JS, 图片
│   ├── templates/               # HTML模板
│   └── README.md                # 前端文档
├── backend/                      # 后端API和逻辑
│   ├── api/                     # API路由
│   ├── src/                     # 核心源代码
│   ├── config/                  # 配置文件
│   ├── data/                    # 数据文件
│   ├── tests/                   # 单元测试
│   ├── requirements.txt         # 后端依赖
│   └── README.md                # 后端文档
├── hardware/                     # 硬件控制模块
│   ├── machine_core/            # 硬件核心模块
│   │   ├── detector.py          # 污渍检测器
│   │   ├── raspberry_pi_camera.py # 树莓派摄像头接口
│   │   └── new.py               # 高级污渍检测算法
│   ├── requirements.txt         # 硬件依赖
│   └── README.md                # 硬件文档
├── docs/                        # 项目文档
├── pyproject.toml               # 项目配置
└── uv.lock                      # 依赖锁定
```

## ✨ 核心特性

- 🔍 **智能污渍检测** - 基于树莓派摄像头的实时检测
- 🤖 **消毒参数预测** - 基于100条真实数据的智能预测
- 📊 **数据分析** - 完整的统计和报告生成
- ⚡ **能耗优化** - 智能节能算法
- 📈 **运行时追踪** - 会话管理和性能监控
- 🎯 **面向对象** - 清晰的模块化架构

## 🧪 测试

```bash
# 运行后端单元测试
cd backend
python -m pytest tests/

# 运行特定测试
python tests/test_machine_core.py
```

## 📖 API文档

查看 [docs/QUICKSTART.md](docs/QUICKSTART.md) 获取完整的API参考。

## 🔧 配置

配置文件位于 `backend/config/` 目录，系统会自动生成默认配置。

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

**注意**: 这是重构版本，查看 [docs/REFACTORING_GUIDE.md](docs/REFACTORING_GUIDE.md) 了解重构详情。