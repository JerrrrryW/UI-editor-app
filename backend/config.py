"""
配置管理模块
管理 API 密钥和应用配置
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    """应用配置类"""
    
    # Flask 配置
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 8000))
    DEBUG = FLASK_ENV == 'development'
    
    # API 密钥
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    SILICONFLOW_API_KEY = os.getenv('SILICONFLOW_API_KEY')
    
    # API 端点配置
    API_ENDPOINTS = {
        'openrouter': 'https://openrouter.ai/api/v1/chat/completions',
        'openai': 'https://api.openai.com/v1/chat/completions',
        'siliconflow': 'https://api.siliconflow.cn/v1/chat/completions',
    }
    
    # 默认模型配置
    DEFAULT_MODELS = {
        'openrouter': 'openai/gpt-4o-mini',
        'openai': 'gpt-4o-mini',
        'siliconflow': 'deepseek-ai/DeepSeek-V3',
        'gemini': 'gemini-2.0-flash-exp'
    }
    
    # 会话配置
    MAX_HISTORY_SIZE = 50  # 最大历史记录数

    # 数据集配置
    DATASET_DIR = os.getenv('DATASET_DIR', os.path.join(BASE_DIR, '00-ui-datasets', 'webcode2m-natural-prompts', 'train'))
    DATASET_ARROW_FILE = os.getenv('DATASET_ARROW_FILE', os.path.join(DATASET_DIR, 'data-00000-of-00001.arrow'))
    
    @classmethod
    def get_api_key(cls, provider):
        """获取指定提供商的 API 密钥"""
        key_map = {
            'openrouter': cls.OPENROUTER_API_KEY,
            'openai': cls.OPENAI_API_KEY,
            'siliconflow': cls.SILICONFLOW_API_KEY,
            'gemini': cls.GOOGLE_API_KEY
        }
        return key_map.get(provider)
    
    @classmethod
    def get_endpoint(cls, provider):
        """获取指定提供商的 API 端点"""
        return cls.API_ENDPOINTS.get(provider)
    
    @classmethod
    def get_default_model(cls, provider):
        """获取指定提供商的默认模型"""
        return cls.DEFAULT_MODELS.get(provider)

