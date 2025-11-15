/**
 * DOM修改执行器
 * 负责将JSON操作指令应用到HTML DOM上
 */

class DOMPatcher {
  /**
   * 应用操作列表到HTML内容
   * @param {string} htmlContent - 原始HTML内容
   * @param {Array} operations - 操作指令数组
   * @returns {Promise<{success: boolean, html: string, error?: string}>}
   */
  static async applyOperations(htmlContent, operations) {
    try {
      // 创建临时DOM解析器
      const parser = new DOMParser();
      const doc = parser.parseFromString(htmlContent, 'text/html');

      // 应用每个操作
      for (let i = 0; i < operations.length; i++) {
        const operation = operations[i];
        
        try {
          await this._applyOperation(doc, operation);
        } catch (error) {
          console.error(`操作 ${i + 1} 失败:`, operation, error);
          // 继续执行其他操作，不中断
        }
      }

      // 序列化回HTML
      const modifiedHtml = new XMLSerializer().serializeToString(doc);

      return {
        success: true,
        html: modifiedHtml
      };
    } catch (error) {
      return {
        success: false,
        error: `DOM操作失败: ${error.message}`
      };
    }
  }

  /**
   * 应用单个操作
   * @private
   */
  static async _applyOperation(doc, operation) {
    const { type, selector } = operation;

    // 查找目标元素
    const elements = doc.querySelectorAll(selector);
    
    if (elements.length === 0) {
      console.warn(`未找到匹配的元素: ${selector}`);
      return;
    }

    // 根据操作类型执行
    switch (type) {
      case 'style_change':
        this._applyStyleChange(elements, operation);
        break;
      
      case 'text_replace':
        this._applyTextReplace(elements, operation);
        break;
      
      case 'attribute_modify':
        this._applyAttributeModify(elements, operation);
        break;
      
      case 'class_toggle':
        this._applyClassToggle(elements, operation);
        break;
      
      case 'visibility_toggle':
        this._applyVisibilityToggle(elements, operation);
        break;
      
      default:
        console.warn(`未知的操作类型: ${type}`);
    }
  }

  /**
   * 样式修改
   */
  static _applyStyleChange(elements, operation) {
    const { property, value } = operation;
    
    elements.forEach(el => {
      // 获取现有style属性
      const existingStyle = el.getAttribute('style') || '';
      
      // 解析现有样式
      const styles = this._parseInlineStyles(existingStyle);
      
      // 更新样式
      styles[property] = value;
      
      // 重新组合style属性
      const newStyle = Object.entries(styles)
        .map(([k, v]) => `${k}: ${v}`)
        .join('; ');
      
      el.setAttribute('style', newStyle);
    });
  }

  /**
   * 文本替换
   */
  static _applyTextReplace(elements, operation) {
    const { newText } = operation;
    
    elements.forEach(el => {
      // 只替换文本节点，保留子元素
      if (el.childNodes.length === 1 && el.childNodes[0].nodeType === Node.TEXT_NODE) {
        el.textContent = newText;
      } else {
        // 如果有子元素，只替换直接文本节点
        el.childNodes.forEach(node => {
          if (node.nodeType === Node.TEXT_NODE) {
            node.textContent = newText;
          }
        });
      }
    });
  }

  /**
   * 属性修改
   */
  static _applyAttributeModify(elements, operation) {
    const { attribute, value } = operation;
    
    elements.forEach(el => {
      el.setAttribute(attribute, value);
    });
  }

  /**
   * 类名切换
   */
  static _applyClassToggle(elements, operation) {
    const { className, action } = operation;
    
    elements.forEach(el => {
      const classes = el.getAttribute('class') || '';
      const classList = classes.split(' ').filter(c => c.trim());
      
      if (action === 'add') {
        if (!classList.includes(className)) {
          classList.push(className);
        }
      } else if (action === 'remove') {
        const index = classList.indexOf(className);
        if (index > -1) {
          classList.splice(index, 1);
        }
      }
      
      el.setAttribute('class', classList.join(' '));
    });
  }

  /**
   * 可见性切换
   */
  static _applyVisibilityToggle(elements, operation) {
    const { action } = operation;
    
    elements.forEach(el => {
      const styles = this._parseInlineStyles(el.getAttribute('style') || '');
      
      if (action === 'hide') {
        styles['display'] = 'none';
      } else if (action === 'show') {
        delete styles['display'];  // 移除display属性，恢复默认
      }
      
      const newStyle = Object.entries(styles)
        .map(([k, v]) => `${k}: ${v}`)
        .join('; ');
      
      el.setAttribute('style', newStyle);
    });
  }

  /**
   * 解析内联样式字符串为对象
   * @private
   */
  static _parseInlineStyles(styleStr) {
    const styles = {};
    
    if (!styleStr) return styles;
    
    styleStr.split(';').forEach(rule => {
      const [property, value] = rule.split(':').map(s => s.trim());
      if (property && value) {
        styles[property] = value;
      }
    });
    
    return styles;
  }

  /**
   * 验证操作指令格式
   * @param {Array} operations - 操作指令数组
   * @returns {{valid: boolean, error?: string}}
   */
  static validateOperations(operations) {
    if (!Array.isArray(operations)) {
      return { valid: false, error: '操作指令必须是数组' };
    }

    for (let i = 0; i < operations.length; i++) {
      const op = operations[i];
      
      if (!op.type) {
        return { valid: false, error: `操作 ${i + 1} 缺少 type 字段` };
      }
      
      if (!op.selector) {
        return { valid: false, error: `操作 ${i + 1} 缺少 selector 字段` };
      }

      // 根据类型验证必需字段
      switch (op.type) {
        case 'style_change':
          if (!op.property || !op.value) {
            return { valid: false, error: `操作 ${i + 1} 缺少 property 或 value` };
          }
          break;
        
        case 'text_replace':
          if (op.newText === undefined) {
            return { valid: false, error: `操作 ${i + 1} 缺少 newText` };
          }
          break;
        
        case 'attribute_modify':
          if (!op.attribute || op.value === undefined) {
            return { valid: false, error: `操作 ${i + 1} 缺少 attribute 或 value` };
          }
          break;
        
        case 'class_toggle':
          if (!op.className || !op.action) {
            return { valid: false, error: `操作 ${i + 1} 缺少 className 或 action` };
          }
          break;
        
        case 'visibility_toggle':
          if (!op.action) {
            return { valid: false, error: `操作 ${i + 1} 缺少 action` };
          }
          break;
        
        default:
          return { valid: false, error: `操作 ${i + 1} 的类型 ${op.type} 不支持` };
      }
    }

    return { valid: true };
  }
}

export default DOMPatcher;

