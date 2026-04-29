# AI消毒机前端项目

这是一个独立的前端项目，用于AI消毒机系统的用户界面。

## 项目结构

```
frontend/
├── static/          # 静态资源
│   ├── css/        # 样式文件
│   ├── js/         # JavaScript文件
│   ├── images/     # 图片资源
│   └── uploads/    # 上传文件
└── templates/      # HTML模板
    ├── dashboard.html
    ├── login.html
    ├── machine_detail.html
    ├── llm_report.html
    └── camera/
        └── panel.html
```

## 技术栈

- HTML5
- CSS3
- JavaScript (原生)
- Flask模板引擎

## 使用方法

### 作为独立项目运行

1. 安装Flask:
```bash
pip install flask
```

2. 创建启动脚本 `run_frontend.py`:
```python
from flask import Flask, render_template

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'your-secret-key'

@app.route('/')
def index():
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

3. 运行:
```bash
python run_frontend.py
```

### 与后端集成

当前端需要与后端API集成时，修改API端点指向实际的后端服务地址。

## 开发说明

- 所有静态文件放在 `static/` 目录
- 所有HTML模板放在 `templates/` 目录
- CSS样式在 `static/css/` 中管理
- JavaScript逻辑在 `static/js/` 中管理

## 后续优化建议

1. 迁移到现代前端框架 (Vue.js / React)
2. 添加构建工具 (Vite / Webpack)
3. 实现组件化开发
4. 添加状态管理
5. 实现响应式设计优化
