"""
HTML 处理模块
处理 HTML 清理、验证和格式化
"""
import re

class HTMLProcessor:
    """HTML 处理器类"""
    
    @staticmethod
    def clean_markdown_code_block(html_content):
        """
        清理 LLM 返回的 markdown 代码块标记
        
        Args:
            html_content: 可能包含 markdown 标记的 HTML 内容
            
        Returns:
            清理后的纯 HTML 内容
        """
        if not html_content:
            return ""
        
        content = html_content.strip()
        
        # 移除开头的 ```html 或 ```
        if content.startswith("```html"):
            content = content[7:].lstrip()
        elif content.startswith("```"):
            content = content[3:].lstrip()
        
        # 移除结尾的 ```
        if content.endswith("```"):
            content = content[:-3].rstrip()
        
        return content.strip()
    
    @staticmethod
    def validate_html(html_content):
        """
        简单验证 HTML 内容
        
        Args:
            html_content: HTML 内容
            
        Returns:
            (is_valid, error_message)
        """
        if not html_content:
            return False, "HTML 内容为空"
        
        # 检查是否包含基本的 HTML 标签
        has_html_tag = bool(re.search(r'<html|<!DOCTYPE', html_content, re.IGNORECASE))
        has_body_or_content = bool(re.search(r'<body|<div|<p|<h[1-6]', html_content, re.IGNORECASE))
        
        if not (has_html_tag or has_body_or_content):
            return False, "不是有效的 HTML 内容"
        
        return True, None
    
    @staticmethod
    def extract_summary(instruction, max_length=100):
        """
        提取指令摘要
        
        Args:
            instruction: 完整指令
            max_length: 最大长度
            
        Returns:
            指令摘要
        """
        if not instruction:
            return "无指令"
        
        if len(instruction) <= max_length:
            return instruction
        
        return instruction[:max_length] + "..."
    
    @staticmethod
    def format_error_html(error_message):
        """
        生成错误提示 HTML
        
        Args:
            error_message: 错误消息
            
        Returns:
            错误提示 HTML
        """
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>错误</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-color: #f5f5f5;
        }}
        .error-container {{
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            max-width: 500px;
            text-align: center;
        }}
        .error-icon {{
            font-size: 48px;
            color: #e74c3c;
            margin-bottom: 20px;
        }}
        h1 {{
            color: #e74c3c;
            margin-bottom: 10px;
        }}
        p {{
            color: #666;
            line-height: 1.6;
        }}
    </style>
</head>
<body>
    <div class="error-container">
        <div class="error-icon">⚠️</div>
        <h1>处理错误</h1>
        <p>{error_message}</p>
    </div>
</body>
</html>"""

