"""Provider API key validation helpers."""

from datetime import datetime
from typing import Dict

import requests


class ProviderValidator:
    """Validate third-party provider API keys with lightweight checks."""

    OPENAI_FORMAT_MODEL_ENDPOINTS: Dict[str, str] = {
        'openrouter': 'https://openrouter.ai/api/v1/models',
        'openai': 'https://api.openai.com/v1/models',
        'siliconflow': 'https://api.siliconflow.cn/v1/models'
    }

    GEMINI_MODEL_ENDPOINT = 'https://generativelanguage.googleapis.com/v1/models'
    REQUEST_TIMEOUT = 10

    @classmethod
    def validate(cls, provider: str, api_key: str) -> Dict[str, str]:
        """Validate API key for the given provider."""
        timestamp = datetime.now().isoformat()

        if not api_key:
            return {
                'status': 'missing',
                'message': '未配置 API 密钥',
                'checked_at': timestamp
            }

        try:
            if provider in cls.OPENAI_FORMAT_MODEL_ENDPOINTS:
                return cls._validate_openai_format(provider, api_key, timestamp)
            if provider == 'gemini':
                return cls._validate_gemini(api_key, timestamp)
        except requests.RequestException as exc:
            return {
                'status': 'error',
                'message': f'网络异常：{str(exc)}',
                'checked_at': timestamp
            }
        except Exception as exc:  # pylint: disable=broad-except
            return {
                'status': 'error',
                'message': f'验证失败：{str(exc)}',
                'checked_at': timestamp
            }

        return {
            'status': 'unknown',
            'message': '该提供商暂不支持自动验证',
            'checked_at': timestamp
        }

    @classmethod
    def _validate_openai_format(cls, provider: str, api_key: str, timestamp: str) -> Dict[str, str]:
        url = cls.OPENAI_FORMAT_MODEL_ENDPOINTS[provider]
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        if provider == 'openrouter':
            headers['HTTP-Referer'] = 'https://github.com/html-editor-app'
            headers['X-Title'] = 'HTML Editor App'

        response = requests.get(url, headers=headers, timeout=cls.REQUEST_TIMEOUT)
        return cls._build_result(response, timestamp)

    @classmethod
    def _validate_gemini(cls, api_key: str, timestamp: str) -> Dict[str, str]:
        params = {'key': api_key}
        response = requests.get(
            cls.GEMINI_MODEL_ENDPOINT,
            params=params,
            timeout=cls.REQUEST_TIMEOUT
        )
        return cls._build_result(response, timestamp)

    @staticmethod
    def _build_result(response: requests.Response, timestamp: str) -> Dict[str, str]:
        status_code = response.status_code
        if status_code == 200:
            return {
                'status': 'valid',
                'message': '密钥可用',
                'checked_at': timestamp
            }

        truncated = response.text[:200] if response.text else response.reason
        status = 'invalid' if status_code in (401, 403) else 'error'

        return {
            'status': status,
            'message': f'HTTP {status_code}: {truncated}',
            'checked_at': timestamp
        }
