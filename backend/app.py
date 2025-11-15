"""
Flask 主应用
提供 REST API 服务
"""
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import io
from datetime import datetime

from config import Config
from api_clients import APIClientFactory
from html_processor import HTMLProcessor
from session_manager import SessionManager
from instruction_classifier import InstructionClassifier

# 创建 Flask 应用
app = Flask(__name__)

# 配置 CORS - 允许前端访问
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:3000", 
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001"
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# 初始化管理器
session_manager = SessionManager()
html_processor = HTMLProcessor()

# 提供商与可用模型映射
MODELS_MAP = {
    'openrouter': [
        {'id': 'openai/gpt-4o', 'name': 'GPT-4o'},
        {'id': 'openai/gpt-4o-mini', 'name': 'GPT-4o Mini'},
        {'id': 'anthropic/claude-3.5-sonnet', 'name': 'Claude 3.5 Sonnet'},
        {'id': 'google/gemini-2.0-flash-exp:free', 'name': 'Gemini 2.0 Flash (Free)'},
    ],
    'openai': [
        {'id': 'gpt-4o', 'name': 'GPT-4o'},
        {'id': 'gpt-4o-mini', 'name': 'GPT-4o Mini'},
        {'id': 'gpt-4-turbo', 'name': 'GPT-4 Turbo'},
    ],
    'siliconflow': [
        {'id': 'deepseek-ai/DeepSeek-V3', 'name': 'DeepSeek V3'},
        {'id': 'Qwen/Qwen2.5-72B-Instruct', 'name': 'Qwen 2.5 72B'},
        {'id': 'meta-llama/Meta-Llama-3.1-70B-Instruct', 'name': 'Llama 3.1 70B'},
    ],
    'gemini': [
        {'id': 'gemini-2.0-flash-exp', 'name': 'Gemini 2.0 Flash'},
        {'id': 'gemini-1.5-pro', 'name': 'Gemini 1.5 Pro'},
        {'id': 'gemini-1.5-flash', 'name': 'Gemini 1.5 Flash'},
    ]
}


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/session', methods=['POST'])
def create_session():
    """创建新会话"""
    try:
        session_id = session_manager.create_session()
        return jsonify({
            'success': True,
            'session_id': session_id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/upload', methods=['POST'])
def upload_html():
    """
    上传 HTML 文件
    Body: {
        "session_id": "...",
        "html_content": "..."
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        session_id = data.get('session_id')
        html_content = data.get('html_content')
        
        if not session_id:
            return jsonify({
                'success': False,
                'error': '缺少 session_id'
            }), 400
        
        if not html_content:
            return jsonify({
                'success': False,
                'error': '缺少 html_content'
            }), 400
        
        # 验证会话
        session = session_manager.get_session(session_id)
        if not session:
            return jsonify({
                'success': False,
                'error': '无效的会话 ID'
            }), 404
        
        # 清理和验证 HTML
        cleaned_html = html_processor.clean_markdown_code_block(html_content)
        is_valid, error_msg = html_processor.validate_html(cleaned_html)
        
        if not is_valid:
            return jsonify({
                'success': False,
                'error': f'HTML 验证失败: {error_msg}'
            }), 400
        
        # 保存到会话
        session_manager.set_original_html(session_id, cleaned_html)
        
        return jsonify({
            'success': True,
            'message': 'HTML 上传成功',
            'html_content': cleaned_html
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


@app.route('/api/modify', methods=['POST'])
def modify_html():
    """
    修改 HTML - 智能路由版本
    自动选择快速模式或完整模式
    Body: {
        "session_id": "...",
        "instruction": "...",
        "api_provider": "openrouter|openai|siliconflow|gemini",
        "model": "...",
        "force_mode": "fast|full" (可选，强制使用某种模式)
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        session_id = data.get('session_id')
        instruction = data.get('instruction')
        api_provider = data.get('api_provider', 'openrouter')
        model = data.get('model')
        force_mode = data.get('force_mode')  # 新增：允许强制模式
        
        # 验证必需参数
        if not session_id:
            return jsonify({'success': False, 'error': '缺少 session_id'}), 400
        if not instruction:
            return jsonify({'success': False, 'error': '缺少 instruction'}), 400
        
        # 获取会话
        session = session_manager.get_session(session_id)
        if not session:
            return jsonify({'success': False, 'error': '无效的会话 ID'}), 404
        
        # 获取当前 HTML
        current_html = session_manager.get_current_html(session_id)
        if not current_html:
            return jsonify({
                'success': False,
                'error': '请先上传 HTML 文件'
            }), 400
        
        # 获取 API 密钥
        api_key = Config.get_api_key(api_provider)
        if not api_key:
            return jsonify({
                'success': False,
                'error': f'未配置 {api_provider} API 密钥'
            }), 400
        
        # 使用默认模型（如果未指定）
        if not model:
            model = Config.get_default_model(api_provider)
        
        # 创建 API 客户端
        try:
            client = APIClientFactory.create_client(
                provider=api_provider,
                api_key=api_key,
                model=model
            )
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'创建 API 客户端失败: {str(e)}'
            }), 500
        
        # 智能路由：决定使用快速模式还是完整模式
        use_fast_mode = False
        selected_mode = 'full'  # 默认完整模式
        
        if force_mode == 'fast':
            use_fast_mode = True
            selected_mode = 'fast'
        elif force_mode == 'full':
            use_fast_mode = False
            selected_mode = 'full'
        else:
            # 使用分类器自动判断
            mode, classify_meta = InstructionClassifier.classify(instruction)
            use_fast_mode = (mode == 'fast')
            selected_mode = mode
        
        # 尝试快速模式
        if use_fast_mode:
            fast_response = client.generate_fast_operations(instruction, current_html)
            
            if fast_response.success:
                # 验证返回的JSON
                import json
                try:
                    operations = json.loads(fast_response.content)
                    if isinstance(operations, list) and len(operations) > 0:
                        # 快速模式成功，返回操作指令
                        return jsonify({
                            'success': True,
                            'mode': 'fast',
                            'operations': operations,
                            'metadata': fast_response.metadata
                        })
                except json.JSONDecodeError:
                    pass  # JSON解析失败，降级到完整模式
            
            # 快速模式失败，自动降级到完整模式
            # 继续执行下面的完整模式逻辑
        
        # 完整模式：调用 LLM 修改 HTML
        response = client.modify_html(instruction, current_html)
        selected_mode = 'full'  # 标记实际使用了完整模式
        
        if not response.success:
            return jsonify({
                'success': False,
                'error': response.error
            }), 500
        
        # 清理返回的 HTML
        modified_html = html_processor.clean_markdown_code_block(response.content)
        
        # 验证修改后的 HTML
        is_valid, error_msg = html_processor.validate_html(modified_html)
        if not is_valid:
            # 如果验证失败，返回错误 HTML
            modified_html = html_processor.format_error_html(
                f"LLM 返回的 HTML 无效: {error_msg}"
            )
        
        # 添加到历史
        session_manager.add_history(
            session_id=session_id,
            instruction=instruction,
            modified_html=modified_html,
            api_provider=api_provider,
            model=model,
            change_description=None,  # 预留字段
            mode=selected_mode  # 新增：记录使用的模式
        )
        
        return jsonify({
            'success': True,
            'mode': 'full',  # 完整模式
            'html_content': modified_html,
            'metadata': response.metadata
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


@app.route('/api/modify-fast', methods=['POST'])
def modify_html_fast():
    """
    快速模式修改 HTML
    生成JSON操作指令而非完整HTML
    Body: {
        "session_id": "...",
        "instruction": "...",
        "api_provider": "openrouter|openai|siliconflow|gemini",
        "model": "..."
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        session_id = data.get('session_id')
        instruction = data.get('instruction')
        api_provider = data.get('api_provider', 'openrouter')
        model = data.get('model')
        
        # 验证必需参数
        if not session_id:
            return jsonify({'success': False, 'error': '缺少 session_id'}), 400
        if not instruction:
            return jsonify({'success': False, 'error': '缺少 instruction'}), 400
        
        # 获取会话
        session = session_manager.get_session(session_id)
        if not session:
            return jsonify({'success': False, 'error': '无效的会话 ID'}), 404
        
        # 获取当前 HTML
        current_html = session_manager.get_current_html(session_id)
        if not current_html:
            return jsonify({
                'success': False,
                'error': '请先上传 HTML 文件'
            }), 400
        
        # 获取 API 密钥
        api_key = Config.get_api_key(api_provider)
        if not api_key:
            return jsonify({
                'success': False,
                'error': f'未配置 {api_provider} API 密钥'
            }), 400
        
        # 使用默认模型（如果未指定）
        if not model:
            model = Config.get_default_model(api_provider)
        
        # 创建 API 客户端
        try:
            client = APIClientFactory.create_client(
                provider=api_provider,
                api_key=api_key,
                model=model
            )
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'创建 API 客户端失败: {str(e)}'
            }), 500
        
        # 调用 LLM 生成操作指令
        response = client.generate_fast_operations(instruction, current_html)
        
        if not response.success:
            return jsonify({
                'success': False,
                'error': response.error,
                'fallback_needed': True  # 提示前端需要降级
            }), 500
        
        # 验证返回的是否为有效JSON
        import json
        try:
            operations = json.loads(response.content)
            if not isinstance(operations, list):
                # 不是数组，返回失败要求降级
                return jsonify({
                    'success': False,
                    'error': 'LLM返回格式无效',
                    'fallback_needed': True
                }), 500
            
            # 如果LLM返回空数组，表示认为太复杂，需要降级
            if len(operations) == 0:
                return jsonify({
                    'success': False,
                    'error': '指令过于复杂，需要完整模式处理',
                    'fallback_needed': True
                }), 500
                
        except json.JSONDecodeError:
            return jsonify({
                'success': False,
                'error': 'JSON解析失败',
                'fallback_needed': True
            }), 500
        
        # 返回操作指令（前端负责执行）
        return jsonify({
            'success': True,
            'mode': 'fast',
            'operations': operations,
            'metadata': response.metadata
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}',
            'fallback_needed': True
        }), 500


@app.route('/api/history/<session_id>', methods=['GET'])
def get_history(session_id):
    """获取修改历史"""
    try:
        session = session_manager.get_session(session_id)
        if not session:
            return jsonify({
                'success': False,
                'error': '无效的会话 ID'
            }), 404
        
        history = session_manager.get_history(session_id)
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


@app.route('/api/revert', methods=['POST'])
def revert_to_history():
    """
    回退到指定历史版本
    Body: {
        "session_id": "...",
        "history_id": "..."
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        session_id = data.get('session_id')
        history_id = data.get('history_id')
        
        if not session_id or not history_id:
            return jsonify({
                'success': False,
                'error': '缺少必需参数'
            }), 400
        
        # 回退到指定版本
        html_content = session_manager.revert_to_history(session_id, history_id)
        
        if html_content is None:
            return jsonify({
                'success': False,
                'error': '未找到指定的历史记录'
            }), 404
        
        return jsonify({
            'success': True,
            'html_content': html_content
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


@app.route('/api/current/<session_id>', methods=['GET'])
def get_current_html(session_id):
    """获取当前 HTML"""
    try:
        html_content = session_manager.get_current_html(session_id)
        original_html = session_manager.get_original_html(session_id)
        
        if html_content is None:
            return jsonify({
                'success': False,
                'error': '会话不存在或未上传 HTML'
            }), 404
        
        return jsonify({
            'success': True,
            'current_html': html_content,
            'original_html': original_html
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


@app.route('/api/download', methods=['POST'])
def download_html():
    """
    下载 HTML 文件
    Body: {
        "session_id": "...",
        "history_id": "..." (可选，不提供则下载当前版本)
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        session_id = data.get('session_id')
        history_id = data.get('history_id')
        
        if not session_id:
            return jsonify({
                'success': False,
                'error': '缺少 session_id'
            }), 400
        
        # 获取 HTML 内容
        if history_id:
            # 下载历史版本
            entry = session_manager.get_history_entry(session_id, history_id)
            if not entry:
                return jsonify({
                    'success': False,
                    'error': '未找到指定的历史记录'
                }), 404
            html_content = entry['after_html']
            filename = f"modified_{history_id[:8]}.html"
        else:
            # 下载当前版本
            html_content = session_manager.get_current_html(session_id)
            if not html_content:
                return jsonify({
                    'success': False,
                    'error': '会话不存在或未上传 HTML'
                }), 404
            filename = f"modified_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        # 创建内存文件
        buffer = io.BytesIO()
        buffer.write(html_content.encode('utf-8'))
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='text/html'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


@app.route('/api/generate-suggestions', methods=['POST'])
def generate_suggestions():
    """
    生成修改建议
    Body: {
        "session_id": "...",
        "api_provider": "openrouter|openai|siliconflow|gemini",
        "model": "..."
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        session_id = data.get('session_id')
        api_provider = data.get('api_provider', 'openrouter')
        model = data.get('model')
        
        if not session_id:
            return jsonify({'success': False, 'error': '缺少 session_id'}), 400
        
        # 获取当前 HTML
        current_html = session_manager.get_current_html(session_id)
        if not current_html:
            return jsonify({
                'success': False,
                'error': '请先上传 HTML 文件'
            }), 400
        
        # 获取 API 密钥
        api_key = Config.get_api_key(api_provider)
        if not api_key:
            return jsonify({
                'success': False,
                'error': f'未配置 {api_provider} API 密钥'
            }), 400
        
        # 使用默认模型（如果未指定）
        if not model:
            model = Config.get_default_model(api_provider)
        
        # 创建 API 客户端
        try:
            client = APIClientFactory.create_client(
                provider=api_provider,
                api_key=api_key,
                model=model
            )
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'创建 API 客户端失败: {str(e)}'
            }), 500
        
        # 生成建议的 prompt
        suggestion_prompt = f"""You are a UI/UX expert analyzing an HTML webpage. 
Generate 5 specific, actionable suggestions to improve this webpage's design and user experience.

Focus on:
- Visual hierarchy and typography
- Color scheme and contrast
- Layout and spacing
- Responsiveness
- User interaction elements

Respond with ONLY 5 suggestions, numbered 1-5. Each suggestion should be:
- Specific and actionable
- Described in natural language (no code or class names)
- Brief (one sentence)

HTML to analyze:
{current_html[:3000]}...

Suggestions:
1."""
        
        # 调用 LLM
        from api_clients import OpenAIFormatClient, GeminiClient
        
        if api_provider == 'gemini':
            response_text = client.modify_html("", suggestion_prompt)  # 使用 modify_html 接口
            if not response_text.success:
                return jsonify({
                    'success': False,
                    'error': response_text.error
                }), 500
            response_content = response_text.content
        else:
            # 直接调用 API
            import requests
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            if api_provider == 'openrouter':
                headers["HTTP-Referer"] = "https://github.com/html-editor-app"
                headers["X-Title"] = "HTML Editor App"
            
            endpoint = Config.get_endpoint(api_provider)
            req_data = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a UI/UX expert providing design suggestions."},
                    {"role": "user", "content": suggestion_prompt}
                ],
                "max_tokens": 800,
                "temperature": 0.7
            }
            
            api_response = requests.post(endpoint, headers=headers, json=req_data, timeout=60)
            if api_response.status_code != 200:
                return jsonify({
                    'success': False,
                    'error': f'API 错误: {api_response.status_code}'
                }), 500
            
            result = api_response.json()
            response_content = result['choices'][0]['message']['content'].strip()
        
        # 解析建议
        suggestions = []
        lines = response_content.split('\n')
        for line in lines:
            line = line.strip()
            for i in range(1, 6):
                if line.startswith(f"{i}.") or line.startswith(f"{i})"):
                    suggestion = line.split('.', 1)[1].strip() if '.' in line else line.split(')', 1)[1].strip()
                    if suggestion:
                        suggestions.append(suggestion)
                        break
        
        return jsonify({
            'success': True,
            'suggestions': suggestions[:5]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


@app.route('/api/models/<provider>', methods=['GET'])
def get_available_models(provider):
    """获取指定提供商的可用模型列表"""
    models_map = {
        'openrouter': [
            {'id': 'openai/gpt-4o', 'name': 'GPT-4o'},
            {'id': 'openai/gpt-4o-mini', 'name': 'GPT-4o Mini'},
            {'id': 'anthropic/claude-3.5-sonnet', 'name': 'Claude 3.5 Sonnet'},
            {'id': 'google/gemini-2.0-flash-exp:free', 'name': 'Gemini 2.0 Flash (Free)'},
        ],
        'openai': [
            {'id': 'gpt-4o', 'name': 'GPT-4o'},
            {'id': 'gpt-4o-mini', 'name': 'GPT-4o Mini'},
            {'id': 'gpt-4-turbo', 'name': 'GPT-4 Turbo'},
        ],
        'siliconflow': [
            {'id': 'deepseek-ai/DeepSeek-V3', 'name': 'DeepSeek V3'},
            {'id': 'Qwen/Qwen2.5-72B-Instruct', 'name': 'Qwen 2.5 72B'},
            {'id': 'meta-llama/Meta-Llama-3.1-70B-Instruct', 'name': 'Llama 3.1 70B'},
        ],
        'gemini': [
            {'id': 'gemini-2.0-flash-exp', 'name': 'Gemini 2.0 Flash'},
            {'id': 'gemini-1.5-pro', 'name': 'Gemini 1.5 Pro'},
            {'id': 'gemini-1.5-flash', 'name': 'Gemini 1.5 Flash'},
        ]
    }
    
    models = models_map.get(provider, [])
    return jsonify({
        'success': True,
        'models': models
    })


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=Config.FLASK_PORT,
        debug=Config.DEBUG
    )

