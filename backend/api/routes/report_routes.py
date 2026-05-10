"""
报告生成路由模块
"""
from pathlib import Path
from flask import Flask, request, jsonify, session, render_template
import cv2
from datetime import datetime


def register_report_routes(app: Flask, base_dir: Path):
    """注册报告相关路由"""
    
    @app.route('/api/generate_report', methods=['POST'])
    def generate_report():
        """生成报告（基于LLM）"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        
        app_context = app.config.get('APP_CONTEXT')
        if not app_context:
            return jsonify({'success': False, 'error': '应用上下文未初始化'}), 500
        
        data = request.json
        machine_id = data.get('machine_id')
        
        # 获取机器数据
        csv_manager = app.config.get('CSV_MANAGER')
        if csv_manager:
            machines = csv_manager.load_machines()
            machine = next((m for m in machines if m['id'] == machine_id), None)
        else:
            machine = None

        if not machine:
            return jsonify({'success': False, 'error': '机器不存在'})

        # 获取运行时状态
        try:
            import json
            runtime_file = base_dir / 'data' / 'runtime_status.json'
            runtime_data = {}
            if runtime_file.exists():
                with open(runtime_file, 'r', encoding='utf-8') as f:
                    runtime_data = json.load(f)

            machine_runtime = runtime_data.get(str(machine_id), {})
        except:
            machine_runtime = {}

        # 生成LLM提示词
        prompt = f"""请根据以下消毒机设备数据生成一份专业的设备运行报告：

设备信息：
- 设备ID: {machine['id']}
- 设备名称: {machine['name']}
- 地理位置: {machine['location']}
- 运行状态: {machine['status']}
- 启用状态: {'已启用' if machine['enabled'] else '未启用'}
- 已消毒器械数量: {machine['disinfected_count']} 个
- 累计运行时长: {machine.get('runtime_hours', 0):.2f} 小时

运行状态：
- 当前是否运行: {'是' if machine_runtime.get('is_running', False) else '否'}
- 总运行时长: {machine_runtime.get('total_seconds', 0) / 3600:.2f} 小时
- 设备寿命状态: {machine_runtime.get('lifetime_status', {}).get('status', '未知')}

请生成一份包含以下内容的专业报告：
1. 设备运行概况
2. 性能分析
3. 维护建议
4. 未来优化建议

报告请用Markdown格式编写，结构清晰，内容专业。"""

        # 调用LLM API
        try:
            import json
            config_file = base_dir / 'data' / 'llm_config.json'
            if not config_file.exists():
                return jsonify({'success': False, 'error': 'LLM API未配置，请先配置API密钥'})

            with open(config_file, 'r', encoding='utf-8') as f:
                llm_config = json.load(f)

            if not llm_config.get('api_key'):
                return jsonify({'success': False, 'error': 'API密钥未设置'})

            # 调用OpenAI API
            import requests
            headers = {
                'Authorization': f'Bearer {llm_config["api_key"]}',
                'Content-Type': 'application/json'
            }

            payload = {
                'model': llm_config.get('model', 'gpt-3.5-turbo'),
                'messages': [
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 2000,
                'temperature': 0.7
            }

            response = requests.post(
                f'{llm_config.get("api_base", "https://api.openai.com/v1")}/chat/completions',
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                report_content = result['choices'][0]['message']['content']

                # 保存报告历史
                history_file = base_dir / 'data' / 'reports' / f'machine_{machine_id}' / 'history.json'
                history_file.parent.mkdir(parents=True, exist_ok=True)

                history = []
                if history_file.exists():
                    try:
                        with open(history_file, 'r', encoding='utf-8') as f:
                            history = json.load(f)
                    except:
                        history = []

                # 添加新报告
                history.append({
                    'timestamp': data.get('timestamp', ''),
                    'report': report_content,
                    'machine_id': machine_id,
                    'machine_name': machine['name']
                })

                # 只保留最近10个报告
                history = history[-10:]

                with open(history_file, 'w', encoding='utf-8') as f:
                    json.dump(history, f, ensure_ascii=False, indent=2)

                return jsonify({
                    'success': True,
                    'report': report_content
                })
            else:
                error_msg = response.json().get('error', {}).get('message', '未知错误')
                return jsonify({'success': False, 'error': f'LLM API调用失败: {error_msg}'})

        except requests.exceptions.RequestException as e:
            return jsonify({'success': False, 'error': f'网络请求失败: {str(e)}'})
        except Exception as e:
            return jsonify({'success': False, 'error': f'生成报告失败: {str(e)}'})

    @app.route('/api/reports', methods=['GET'])
    def list_reports():
        """列出报告"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        
        app_context = app.config.get('APP_CONTEXT')
        if not app_context:
            return jsonify({'success': False, 'error': '应用上下文未初始化'}), 500
        
        machine_id = request.args.get('machine_id', type=int)
        reports = app_context.report_generator.list_reports(machine_id)
        
        return jsonify({'success': True, 'reports': reports})
    
    @app.route('/api/report/<report_id>', methods=['GET'])
    def get_report(report_id):
        """获取单个报告"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        
        app_context = app.config.get('APP_CONTEXT')
        if not app_context:
            return jsonify({'success': False, 'error': '应用上下文未初始化'}), 500
        
        report = app_context.report_generator.load_report(report_id)
        
        if report is None:
            return jsonify({'success': False, 'error': '报告不存在'})
        
        return jsonify({'success': True, 'report': report})

    @app.route('/api/llm_config', methods=['GET', 'POST'])
    def llm_config():
        """获取和保存LLM配置"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401

        config_file = base_dir / 'data' / 'llm_config.json'

        if request.method == 'GET':
            # 获取配置
            if config_file.exists():
                try:
                    import json
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    return jsonify({
                        'success': True,
                        'config': {
                            'has_api_key': bool(config.get('api_key')),
                            'api_base': config.get('api_base', 'https://api.openai.com/v1'),
                            'model': config.get('model', 'gpt-3.5-turbo')
                        }
                    })
                except Exception as e:
                    return jsonify({'success': False, 'error': str(e)})
            else:
                return jsonify({
                    'success': True,
                    'config': {
                        'has_api_key': False,
                        'api_base': 'https://api.openai.com/v1',
                        'model': 'gpt-3.5-turbo'
                    }
                })

        elif request.method == 'POST':
            # 保存配置
            data = request.json
            config = {
                'api_key': data.get('api_key', ''),
                'api_base': data.get('api_base', 'https://api.openai.com/v1'),
                'model': data.get('model', 'gpt-3.5-turbo')
            }

            try:
                import json
                config_file.parent.mkdir(parents=True, exist_ok=True)
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
                return jsonify({'success': True, 'message': '配置已保存'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/report_history/<int:machine_id>', methods=['GET'])
    def report_history(machine_id):
        """获取设备的报告历史"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401

        history_file = base_dir / 'data' / 'reports' / f'machine_{machine_id}' / 'history.json'

        if history_file.exists():
            try:
                import json
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                return jsonify({'success': True, 'history': history})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        else:
            return jsonify({'success': True, 'history': []})

    @app.route('/api/analyze_image_with_llm', methods=['POST'])
    def analyze_image_with_llm():
        """上传图片并使用LLM进行分析"""
        if 'user' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401

        try:
            # 获取上传的图片
            image_file = request.files.get('image')
            machine_id = request.form.get('machine_id', type=int)
            analysis_type = request.form.get('analysis_type', 'stain_detection')  # stain_detection, pollution_analysis, disinfection_recommendation

            if not image_file:
                return jsonify({'success': False, 'error': '请上传图片文件'}), 400

            # 保存图片
            upload_dir = base_dir / 'frontend' / 'static' / 'uploads' / 'llm_analysis'
            upload_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"llm_{machine_id or 'unknown'}_{timestamp}.jpg"
            filepath = upload_dir / filename
            image_file.save(filepath)

            # 读取并分析图片
            image = cv2.imread(str(filepath))
            if image is None:
                return jsonify({'success': False, 'error': '图片读取失败'}), 400

            # 获取应用上下文
            app_context = app.config.get('APP_CONTEXT')
            if not app_context:
                return jsonify({'success': False, 'error': '应用上下文未初始化'}), 500

            # 进行图像分析
            grayscale_result = app_context.detector.analyze_grayscale(image)
            stain_result = app_context.detector.detect_stains(image)

            # 污染等级分析
            gray_value = grayscale_result.get('mean_grayscale', 128) if grayscale_result.get('success') else 128
            colony_density = stain_result.get('stain_count', 0) * 100  # 估算菌落密度
            pollution_info = app_context.detector.get_pollution_level(gray_value, colony_density)

            # 消毒参数预测
            disinfection_params = {}
            if app_context.predictor and grayscale_result.get('success'):
                disinfection_params = app_context.predictor.predict_disinfection_params(
                    scene_type=1,
                    disinfection_object=1,
                    bacteria_type='普通细菌(大肠杆菌等)',
                    pollution_grayscale=int(gray_value),
                    colony_density=colony_density,
                    pollution_type=pollution_info['pollution_level'],
                    pollution_level=pollution_info['pollution_level'],
                    severity_level=pollution_info['severity_level'],
                    compliance_standard=1
                )

            # 构建LLM提示词
            prompt = _build_image_analysis_prompt(
                analysis_type, grayscale_result, stain_result,
                pollution_info, disinfection_params, machine_id
            )

            # 调用LLM API
            llm_response = _call_llm_api(prompt, filepath)

            return jsonify({
                'success': True,
                'filename': filename,
                'analysis_type': analysis_type,
                'image_analysis': {
                    'grayscale': grayscale_result,
                    'stains': stain_result,
                    'pollution': pollution_info,
                    'disinfection': disinfection_params
                },
                'llm_analysis': llm_response,
                'timestamp': datetime.now().isoformat()
            })

        except Exception as e:
            print(f"图片LLM分析失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500


def _build_image_analysis_prompt(analysis_type, grayscale_result, stain_result, pollution_info, disinfection_params, machine_id):
    """构建图像分析的LLM提示词"""
    prompt = f"针对机器ID为{machine_id}的设备，进行以下内容的分析：\n"

    if analysis_type == 'stain_detection':
        prompt += "1. 检测图片中的污渍，并标记污渍位置。\n"
        prompt += "2. 分析污渍的可能成因，并给出相应的建议。\n"
    elif analysis_type == 'pollution_analysis':
        prompt += "1. 分析设备周围环境的污染程度。\n"
        prompt += "2. 根据污染等级，建议相应的处理措施。\n"
    elif analysis_type == 'disinfection_recommendation':
        prompt += "1. 根据设备当前状态，建议合适的消毒方案。\n"
        prompt += "2. 提供消毒效果的预期评估。\n"

    prompt += "\n请根据以上要求，结合图像分析结果，生成详细的分析报告。"

    return prompt


def _call_llm_api(prompt, image_path):
    """调用LLM API进行分析"""
    try:
        import json
        config_file = Path('data') / 'llm_config.json'
        if not config_file.exists():
            return {'success': False, 'error': 'LLM API未配置'}

        with open(config_file, 'r', encoding='utf-8') as f:
            llm_config = json.load(f)

        if not llm_config.get('api_key'):
            return {'success': False, 'error': 'API密钥未设置'}

        # 调用OpenAI API
        import requests
        headers = {
            'Authorization': f'Bearer {llm_config["api_key"]}',
            'Content-Type': 'application/json'
        }

        # 这里的model和temperature可以根据需要调整
        payload = {
            'model': llm_config.get('model', 'gpt-3.5-turbo'),
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 1500,
            'temperature': 0.7
        }

        response = requests.post(
            f'{llm_config.get("api_base", "https://api.openai.com/v1")}/chat/completions',
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            llm_content = result['choices'][0]['message']['content']

            return {'success': True, 'analysis': llm_content}

        else:
            error_msg = response.json().get('error', {}).get('message', '未知错误')
            return {'success': False, 'error': f'LLM API调用失败: {error_msg}'}

    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': f'网络请求失败: {str(e)}'}
    except Exception as e:
        return {'success': False, 'error': f'分析失败: {str(e)}'}
