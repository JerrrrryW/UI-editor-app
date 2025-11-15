"""
API 客户端模块
统一处理不同 LLM API 提供商
"""
import requests
import time
from typing import Dict, Optional

class APIResponse:
    """统一的 API 响应格式"""
    
    def __init__(self, success: bool, content: str = "", error: str = "", metadata: Optional[dict] = None):
        self.success = success
        self.content = content
        self.error = error
        self.metadata = metadata or {}
    
    def to_dict(self):
        return {
            'success': self.success,
            'content': self.content,
            'error': self.error,
            'metadata': self.metadata
        }


class OpenAIFormatClient:
    """
    OpenAI 格式 API 客户端
    支持 OpenRouter、OpenAI、SiliconFlow 等
    """
    
    def __init__(self, api_key: str, base_url: str, model: str, provider_name: str = "openai"):
        """
        初始化客户端
        
        Args:
            api_key: API 密钥
            base_url: API 端点 URL
            model: 模型名称
            provider_name: 提供商名称
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.provider_name = provider_name
    
    def generate_fast_operations(self, instruction: str, html_code: str, max_retries: int = 3) -> APIResponse:
        """
        生成快速模式的JSON操作指令
        
        Args:
            instruction: 修改指令
            html_code: 原始 HTML（用于分析）
            max_retries: 最大重试次数
            
        Returns:
            APIResponse 对象，content为JSON字符串
        """
        system_prompt = """You are a frontend expert that generates precise DOM manipulation instructions.
Your task is to analyze a user's design instruction and output a JSON array of operations.

IMPORTANT: Return ONLY valid JSON, no explanations or markdown.

Supported operation types:
1. style_change: Modify CSS properties
   {"type": "style_change", "selector": "CSS selector", "property": "CSS property", "value": "new value"}

2. text_replace: Replace text content
   {"type": "text_replace", "selector": "CSS selector", "newText": "new text"}

3. attribute_modify: Change HTML attributes
   {"type": "attribute_modify", "selector": "CSS selector", "attribute": "attr name", "value": "new value"}

4. class_toggle: Add/remove CSS classes
   {"type": "class_toggle", "selector": "CSS selector", "className": "class name", "action": "add|remove"}

5. visibility_toggle: Show/hide elements
   {"type": "visibility_toggle", "selector": "CSS selector", "action": "show|hide"}

Rules:
- Use specific CSS selectors (prefer class/id over tag names)
- Keep operations atomic and focused
- Limit to 10 operations max
- Return empty array [] if instruction is too complex for fast mode"""

        user_prompt = f"""Instruction: {instruction}

HTML structure (first 2000 chars for context):
{html_code[:2000]}

Generate JSON operations array:"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        if self.provider_name == 'openrouter':
            headers["HTTP-Referer"] = "https://github.com/html-editor-app"
            headers["X-Title"] = "HTML Editor App"
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 1500,
            "temperature": 0.2  # 低温度保证输出稳定
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=data,
                    timeout=60
                )
                
                if response.status_code == 429:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 20
                        time.sleep(wait_time)
                        continue
                    else:
                        return APIResponse(
                            success=False,
                            error="速率限制：请稍后重试"
                        )
                
                if response.status_code != 200:
                    error_msg = f"API 错误 {response.status_code}: {response.text}"
                    return APIResponse(success=False, error=error_msg)
                
                result = response.json()
                
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content'].strip()
                    
                    # 清理markdown代码块标记
                    if content.startswith('```'):
                        lines = content.split('\n')
                        content = '\n'.join(lines[1:-1]) if len(lines) > 2 else content
                    
                    metadata = {
                        'model': self.model,
                        'provider': self.provider_name,
                        'usage': result.get('usage', {}),
                        'mode': 'fast'
                    }
                    
                    return APIResponse(
                        success=True,
                        content=content,
                        metadata=metadata
                    )
                else:
                    return APIResponse(
                        success=False,
                        error="API 返回格式错误：未找到 choices"
                    )
                    
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    continue
                return APIResponse(success=False, error="请求超时")
                
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(3)
                    continue
                return APIResponse(success=False, error=f"请求失败: {str(e)}")
        
        return APIResponse(success=False, error="达到最大重试次数")
    
    def modify_html(self, instruction: str, html_code: str, max_retries: int = 3) -> APIResponse:
        """
        调用 LLM 修改 HTML
        
        Args:
            instruction: 修改指令
            html_code: 原始 HTML
            max_retries: 最大重试次数
            
        Returns:
            APIResponse 对象
        """
        system_prompt = (
            "You are a skilled frontend developer who modifies HTML code based on design instructions. "
            "Return ONLY the complete modified HTML code without any explanations or markdown formatting."
        )
        
        user_prompt = f"""Given the HTML code and a design instruction, apply the change and return the full modified HTML file.
Do NOT skip any parts of the code — output the complete modified HTML with only the necessary edits.

Instruction:
{instruction}

Original HTML:
{html_code}

Modified HTML:"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        # OpenRouter 特定的 headers
        if self.provider_name == 'openrouter':
            headers["HTTP-Referer"] = "https://github.com/html-editor-app"
            headers["X-Title"] = "HTML Editor App"
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 16384,
            "temperature": 0.3
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=data,
                    timeout=120
                )
                
                # 处理速率限制
                if response.status_code == 429:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 30
                        time.sleep(wait_time)
                        continue
                    else:
                        return APIResponse(
                            success=False,
                            error=f"速率限制：请稍后重试"
                        )
                
                # 处理其他错误
                if response.status_code != 200:
                    error_msg = f"API 错误 {response.status_code}: {response.text}"
                    return APIResponse(success=False, error=error_msg)
                
                # 解析响应
                result = response.json()
                
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content'].strip()
                    
                    # 提取 metadata
                    metadata = {
                        'model': self.model,
                        'provider': self.provider_name,
                        'usage': result.get('usage', {})
                    }
                    
                    return APIResponse(
                        success=True,
                        content=content,
                        metadata=metadata
                    )
                else:
                    return APIResponse(
                        success=False,
                        error="API 返回格式错误：未找到 choices"
                    )
                    
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    continue
                return APIResponse(success=False, error="请求超时")
                
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
                return APIResponse(success=False, error=f"请求失败: {str(e)}")
        
        return APIResponse(success=False, error="达到最大重试次数")


class GeminiClient:
    """Google Gemini API 客户端"""
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-exp"):
        """
        初始化 Gemini 客户端
        
        Args:
            api_key: Google API 密钥
            model: 模型名称
        """
        self.api_key = api_key
        self.model = model
        
        # 延迟导入 google.generativeai
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.genai = genai
            self.initialized = True
        except ImportError:
            self.initialized = False
            self.error_message = "google-generativeai 库未安装"
        except Exception as e:
            self.initialized = False
            self.error_message = f"Gemini 初始化失败: {str(e)}"
    
    def generate_fast_operations(self, instruction: str, html_code: str, max_retries: int = 3) -> APIResponse:
        """
        生成快速模式的JSON操作指令
        
        Args:
            instruction: 修改指令
            html_code: 原始 HTML（用于分析）
            max_retries: 最大重试次数
            
        Returns:
            APIResponse 对象，content为JSON字符串
        """
        if not self.initialized:
            return APIResponse(
                success=False,
                error=self.error_message
            )
        
        prompt = f"""You are a frontend expert that generates precise DOM manipulation instructions.
Analyze this design instruction and output a JSON array of operations.

IMPORTANT: Return ONLY valid JSON, no explanations or markdown.

Supported operation types:
1. style_change: {{"type": "style_change", "selector": "CSS selector", "property": "CSS property", "value": "new value"}}
2. text_replace: {{"type": "text_replace", "selector": "CSS selector", "newText": "new text"}}
3. attribute_modify: {{"type": "attribute_modify", "selector": "CSS selector", "attribute": "attr name", "value": "new value"}}
4. class_toggle: {{"type": "class_toggle", "selector": "CSS selector", "className": "class name", "action": "add|remove"}}
5. visibility_toggle: {{"type": "visibility_toggle", "selector": "CSS selector", "action": "show|hide"}}

Rules:
- Use specific CSS selectors
- Keep operations atomic
- Limit to 10 operations max
- Return empty array [] if too complex

Instruction: {instruction}

HTML structure (first 2000 chars):
{html_code[:2000]}

JSON operations array:"""
        
        for attempt in range(max_retries):
            try:
                model = self.genai.GenerativeModel(self.model)
                response = model.generate_content(prompt)
                
                if response and response.text:
                    content = response.text.strip()
                    
                    # 清理markdown代码块标记
                    if content.startswith('```'):
                        lines = content.split('\n')
                        content = '\n'.join(lines[1:-1]) if len(lines) > 2 else content
                    
                    metadata = {
                        'model': self.model,
                        'provider': 'gemini',
                        'mode': 'fast'
                    }
                    
                    return APIResponse(
                        success=True,
                        content=content,
                        metadata=metadata
                    )
                else:
                    return APIResponse(
                        success=False,
                        error="Gemini 返回空响应"
                    )
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(3)
                    continue
                return APIResponse(
                    success=False,
                    error=f"Gemini API 调用失败: {str(e)}"
                )
        
        return APIResponse(success=False, error="达到最大重试次数")
    
    def modify_html(self, instruction: str, html_code: str, max_retries: int = 3) -> APIResponse:
        """
        调用 Gemini 修改 HTML
        
        Args:
            instruction: 修改指令
            html_code: 原始 HTML
            max_retries: 最大重试次数
            
        Returns:
            APIResponse 对象
        """
        if not self.initialized:
            return APIResponse(
                success=False,
                error=self.error_message
            )
        
        prompt = f"""You are a skilled frontend developer who modifies HTML code based on design instructions.

Given the HTML code and a design instruction, apply the change and return the full modified HTML file.
Do NOT skip any parts of the code — output the complete modified HTML with only the necessary edits.
Return ONLY the HTML code without any explanations or markdown formatting.

Instruction:
{instruction}

Original HTML:
{html_code}

Modified HTML:"""
        
        for attempt in range(max_retries):
            try:
                model = self.genai.GenerativeModel(self.model)
                response = model.generate_content(prompt)
                
                if response and response.text:
                    content = response.text.strip()
                    
                    metadata = {
                        'model': self.model,
                        'provider': 'gemini'
                    }
                    
                    return APIResponse(
                        success=True,
                        content=content,
                        metadata=metadata
                    )
                else:
                    return APIResponse(
                        success=False,
                        error="Gemini 返回空响应"
                    )
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
                return APIResponse(
                    success=False,
                    error=f"Gemini API 调用失败: {str(e)}"
                )
        
        return APIResponse(success=False, error="达到最大重试次数")


class APIClientFactory:
    """API 客户端工厂"""
    
    @staticmethod
    def create_client(provider: str, api_key: str, model: str, base_url: Optional[str] = None):
        """
        创建 API 客户端
        
        Args:
            provider: 提供商名称 (openrouter, openai, siliconflow, gemini)
            api_key: API 密钥
            model: 模型名称
            base_url: API 端点（可选）
            
        Returns:
            API 客户端实例
        """
        if provider == 'gemini':
            return GeminiClient(api_key=api_key, model=model)
        else:
            # OpenAI 格式的提供商
            if not base_url:
                # 使用默认端点
                from config import Config
                base_url = Config.get_endpoint(provider)
            
            return OpenAIFormatClient(
                api_key=api_key,
                base_url=base_url,
                model=model,
                provider_name=provider
            )

