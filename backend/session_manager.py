"""
会话管理模块
管理用户会话和修改历史
"""
from datetime import datetime
from typing import Dict, List, Optional
import uuid

class SessionManager:
    """会话管理器类"""
    
    def __init__(self):
        """初始化会话管理器"""
        self.sessions: Dict[str, dict] = {}
    
    def create_session(self) -> str:
        """
        创建新会话
        
        Returns:
            会话 ID
        """
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            'current_html': None,
            'original_html': None,
            'history': [],
            'created_at': datetime.now().isoformat()
        }
        return session_id
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """
        获取会话信息
        
        Args:
            session_id: 会话 ID
            
        Returns:
            会话数据或 None
        """
        return self.sessions.get(session_id)
    
    def set_original_html(self, session_id: str, html_content: str):
        """
        设置原始 HTML
        
        Args:
            session_id: 会话 ID
            html_content: HTML 内容
        """
        session = self.get_session(session_id)
        if session:
            session['original_html'] = html_content
            session['current_html'] = html_content
    
    def add_history(self, session_id: str, instruction: str, 
                   modified_html: str, api_provider: str, model: str,
                   change_description: Optional[dict] = None, mode: str = 'full'):
        """
        添加修改历史
        
        Args:
            session_id: 会话 ID
            instruction: 修改指令
            modified_html: 修改后的 HTML
            api_provider: API 提供商
            model: 使用的模型
            change_description: 变更描述（预留字段）
            mode: 使用的模式 ('fast' 或 'full')
        """
        session = self.get_session(session_id)
        if not session:
            return
        
        # 获取当前 HTML 作为这次修改的 "before"
        before_html = session['current_html']
        
        history_entry = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'instruction': instruction,
            'before_html': before_html,
            'after_html': modified_html,
            'api_provider': api_provider,
            'model': model,
            'change_description': change_description,  # 预留字段
            'mode': mode  # 新增：记录使用的模式
        }
        
        session['history'].append(history_entry)
        session['current_html'] = modified_html
    
    def get_history(self, session_id: str) -> List[dict]:
        """
        获取修改历史
        
        Args:
            session_id: 会话 ID
            
        Returns:
            历史记录列表
        """
        session = self.get_session(session_id)
        if not session:
            return []
        
        # 返回简化的历史信息（不包含完整 HTML）
        return [
            {
                'id': entry['id'],
                'timestamp': entry['timestamp'],
                'instruction': entry['instruction'],
                'api_provider': entry['api_provider'],
                'model': entry['model'],
                'mode': entry.get('mode', 'full')  # 兼容旧数据
            }
            for entry in session['history']
        ]
    
    def revert_to_history(self, session_id: str, history_id: str) -> Optional[str]:
        """
        回退到指定历史版本
        
        Args:
            session_id: 会话 ID
            history_id: 历史记录 ID
            
        Returns:
            回退后的 HTML 或 None
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        # 查找历史记录
        for entry in session['history']:
            if entry['id'] == history_id:
                # 更新当前 HTML
                session['current_html'] = entry['after_html']
                return entry['after_html']
        
        return None
    
    def get_current_html(self, session_id: str) -> Optional[str]:
        """
        获取当前 HTML
        
        Args:
            session_id: 会话 ID
            
        Returns:
            当前 HTML 或 None
        """
        session = self.get_session(session_id)
        if session:
            return session['current_html']
        return None
    
    def get_original_html(self, session_id: str) -> Optional[str]:
        """
        获取原始 HTML
        
        Args:
            session_id: 会话 ID
            
        Returns:
            原始 HTML 或 None
        """
        session = self.get_session(session_id)
        if session:
            return session['original_html']
        return None
    
    def get_history_entry(self, session_id: str, history_id: str) -> Optional[dict]:
        """
        获取完整的历史记录条目
        
        Args:
            session_id: 会话 ID
            history_id: 历史记录 ID
            
        Returns:
            历史记录条目或 None
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        for entry in session['history']:
            if entry['id'] == history_id:
                return entry
        
        return None

