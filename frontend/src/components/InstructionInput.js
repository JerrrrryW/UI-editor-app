import React, { useState } from 'react';
import '../styles/InstructionInput.css';

const InstructionInput = ({ 
  onSubmit, 
  onGenerateSuggestions, 
  disabled, 
  loading,
  suggestions,
  loadingSuggestions,
  hasHtml
}) => {
  const [instruction, setInstruction] = useState('');

  const handleSubmit = () => {
    if (instruction.trim()) {
      onSubmit(instruction.trim());
      setInstruction('');
    }
  };

  const handleKeyPress = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      handleSubmit();
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setInstruction(suggestion);
  };

  return (
    <div className="instruction-input">
      <div className="input-header">
        <label htmlFor="instruction-textarea">修改指令</label>
        <span className="char-count">{instruction.length} 字符</span>
      </div>
      
      <textarea
        id="instruction-textarea"
        value={instruction}
        onChange={(e) => setInstruction(e.target.value)}
        onKeyDown={handleKeyPress}
        placeholder="用自然语言描述你想要的修改，例如：将背景色改为深色、增大标题字体等"
        disabled={disabled || loading}
        rows={4}
      />

      <div className="suggestions-section">
        <div className="suggestions-header">
          <small>AI 修改建议</small>
          <button
            className="generate-suggestions-btn"
            onClick={onGenerateSuggestions}
            disabled={!hasHtml || disabled || loading || loadingSuggestions}
          >
            {loadingSuggestions ? (
              <>
                <span className="spinner-small"></span>
                生成中...
              </>
            ) : (
              '生成修改建议'
            )}
          </button>
        </div>
        
        {suggestions && suggestions.length > 0 && (
          <div className="suggestions-list">
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                className="suggestion-btn"
                onClick={() => handleSuggestionClick(suggestion)}
                disabled={disabled || loading}
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}
      </div>

      <button
        className="submit-btn"
        onClick={handleSubmit}
        disabled={disabled || loading || !instruction.trim()}
      >
        {loading ? (
          <>
            <span className="spinner"></span>
            处理中...
          </>
        ) : (
          <>
            执行修改 <small>(Ctrl+Enter)</small>
          </>
        )}
      </button>
    </div>
  );
};

export default InstructionInput;

