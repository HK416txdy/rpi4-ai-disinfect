"""
认证路由模块
"""
from pathlib import Path
from flask import Flask, request, jsonify, render_template, session, redirect


def register_auth_routes(app: Flask, base_dir: Path):
    """注册认证相关路由"""
    
    @app.route('/')
    def index():
        """首页"""
        if 'user' not in session:
            return render_template('login.html')
        return redirect('/dashboard')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """登录"""
        # 处理POST请求(表单提交)
        if request.method == 'POST':
            # 检查是否是JSON请求
            if request.is_json:
                data = request.json
            else:
                # 表单提交
                data = request.form
            
            username = data.get('username')
            password = data.get('password')
            
            # 简单认证(实际应使用数据库)
            users = {
                'admin': 'admin123',
                'user1': 'user123'
            }
            
            if username in users and users[username] == password:
                session['user'] = username
                session['role'] = 'admin' if username == 'admin' else 'user'
                
                # 如果是JSON请求,返回JSON响应
                if request.is_json:
                    return jsonify({'success': True, 'user': username})
                
                # 表单提交,重定向到dashboard
                return redirect('/dashboard')
            else:
                # 如果是JSON请求
                if request.is_json:
                    return jsonify({'success': False, 'error': '用户名或密码错误'})
                
                # 表单提交,重新渲染登录页面并显示错误
                return render_template('login.html', error='用户名或密码错误')
        
        # GET请求,显示登录页面
        return render_template('login.html')
    
    @app.route('/logout', methods=['POST'])
    def logout():
        """登出"""
        session.clear()
        return jsonify({'success': True})
    
    @app.route('/dashboard')
    def dashboard():
        """仪表板"""
        if 'user' not in session:
            return render_template('login.html')
        
        # 获取所有消毒机数据
        csv_manager = app.config.get('CSV_MANAGER')
        if csv_manager:
            machines = csv_manager.load_machines()
        else:
            machines = []
        
        # 添加当前用户信息
        current_user = {
            'name': session['user'],
            'role': session.get('role', 'user')
        }
        
        return render_template('dashboard.html', 
                             machines=machines, 
                             current_user=current_user)
    
    @app.route('/machine/<int:machine_id>')
    def machine_detail(machine_id):
        """消毒机详情页面"""
        if 'user' not in session:
            return render_template('login.html')
        
        # 获取消毒机数据
        csv_manager = app.config.get('CSV_MANAGER')
        if csv_manager:
            machines = csv_manager.load_machines()
            machine = next((m for m in machines if m['id'] == machine_id), None)
        else:
            machine = None
        
        if not machine:
            return "消毒机不存在", 404
        
        return render_template('machine_detail.html', machine=machine)
    
    @app.route('/llm_report')
    def llm_report():
        """AI报告页面"""
        if 'user' not in session:
            return render_template('login.html')
        
        # 获取所有消毒机数据
        csv_manager = app.config.get('CSV_MANAGER')
        if csv_manager:
            machines = csv_manager.load_machines()
        else:
            machines = []
        
        return render_template('llm_report.html', machines=machines)
