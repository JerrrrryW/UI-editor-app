"""
指令分类器模块
用于判断指令应该使用快速模式还是完整模式
"""
import re
from typing import Tuple, Dict

class InstructionClassifier:
    """指令分类器类"""
    
    # 简单修改关键词（应使用快速模式）
    SIMPLE_KEYWORDS = [
        # 样式相关
        '颜色', '背景', '字体', '大小', '粗体', '斜体', '下划线',
        '颜色', '背景色', '文字颜色', '边框', '圆角', '阴影',
        '间距', '边距', '内边距', '外边距', 'padding', 'margin',
        '宽度', '高度', '透明度', '显示', '隐藏',
        'color', 'background', 'font', 'size', 'bold', 'italic', 'underline',
        'border', 'radius', 'shadow', 'spacing', 'width', 'height', 'opacity',
        
        # 文本相关
        '文字', '文本', '内容', '标题', '段落', '替换',
        'text', 'content', 'title', 'paragraph', 'replace',
        
        # 简单属性
        '链接', 'href', 'src', '属性', 'attribute',
        '类名', 'class', 'id',
    ]
    
    # 复杂修改关键词（应使用完整模式）
    COMPLEX_KEYWORDS = [
        # 结构修改
        '添加', '删除', '插入', '移动', '重新排列', '重组',
        '新增', '创建', '生成', '移除', '清空',
        'add', 'delete', 'insert', 'remove', 'create', 'generate',
        'restructure', 'reorganize', 'move',
        
        # 布局变更
        '布局', '网格', '栅格', '列', '行', '响应式',
        'layout', 'grid', 'column', 'row', 'responsive',
        'flexbox', 'flex',
        
        # 组件/元素添加
        '按钮', '导航栏', '菜单', '表格', '列表', '表单',
        '图片', '视频', '输入框', '下拉框',
        'button', 'navbar', 'menu', 'table', 'list', 'form',
        'image', 'video', 'input', 'dropdown',
        
        # JavaScript/交互
        '点击', '悬停', '动画', '过渡', '交互', '事件',
        'click', 'hover', 'animation', 'transition', 'interactive',
        'script', 'javascript',
    ]
    
    @classmethod
    def classify(cls, instruction: str) -> Tuple[str, Dict]:
        """
        分类指令
        
        Args:
            instruction: 用户输入的修改指令
            
        Returns:
            (mode, metadata) 元组
            - mode: 'fast' 或 'full'
            - metadata: 分类相关的元数据
        """
        instruction_lower = instruction.lower()
        
        # 计算匹配分数
        simple_score = 0
        complex_score = 0
        
        # 检查简单关键词
        for keyword in cls.SIMPLE_KEYWORDS:
            if keyword.lower() in instruction_lower:
                simple_score += 1
        
        # 检查复杂关键词
        for keyword in cls.COMPLEX_KEYWORDS:
            if keyword.lower() in instruction_lower:
                complex_score += 1
        
        # 长度检查：过长的指令通常更复杂
        if len(instruction) > 200:
            complex_score += 2
        
        # 多句检查：包含多个句子通常更复杂
        sentence_count = len(re.split(r'[。！？.!?；;]', instruction))
        if sentence_count > 3:
            complex_score += 1
        
        # 特殊模式检查
        if cls._is_pure_style_change(instruction_lower):
            simple_score += 3
        
        if cls._is_content_addition(instruction_lower):
            complex_score += 3
        
        # 决策逻辑
        metadata = {
            'simple_score': simple_score,
            'complex_score': complex_score,
            'instruction_length': len(instruction),
            'sentence_count': sentence_count
        }
        
        # 如果复杂分数明显更高，使用完整模式
        if complex_score > simple_score + 1:
            return 'full', metadata
        
        # 如果简单分数更高或相等，使用快速模式
        if simple_score > 0 and simple_score >= complex_score:
            return 'fast', metadata
        
        # 默认使用完整模式（保守策略）
        return 'full', metadata
    
    @staticmethod
    def _is_pure_style_change(instruction: str) -> bool:
        """判断是否为纯样式修改"""
        style_patterns = [
            r'(改|变|修改|设置|调整).*(颜色|背景|字体|大小)',
            r'(change|modify|set|adjust).*(color|background|font|size)',
            r'将.*(颜色|背景|字体).*改',
            r'make.*\s+(bigger|smaller|larger|red|blue|green|bold)',
        ]
        
        for pattern in style_patterns:
            if re.search(pattern, instruction, re.IGNORECASE):
                return True
        return False
    
    @staticmethod
    def _is_content_addition(instruction: str) -> bool:
        """判断是否为内容添加"""
        addition_patterns = [
            r'(添加|新增|插入|加入).*(元素|组件|部分|section)',
            r'(add|insert|append|create).*(element|component|section|div)',
            r'在.*中.*添加',
        ]
        
        for pattern in addition_patterns:
            if re.search(pattern, instruction, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def should_use_fast_mode(cls, instruction: str) -> bool:
        """
        简化接口：判断是否应该使用快速模式
        
        Args:
            instruction: 用户输入的修改指令
            
        Returns:
            True 如果应该使用快速模式，否则 False
        """
        mode, _ = cls.classify(instruction)
        return mode == 'fast'

