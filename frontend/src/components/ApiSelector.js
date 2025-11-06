import React, { useState, useEffect } from 'react';
import { getAvailableModels } from '../services/api';
import '../styles/ApiSelector.css';

const ApiSelector = ({ onSelectionChange, disabled }) => {
  const [provider, setProvider] = useState('openrouter');
  const [model, setModel] = useState('');
  const [models, setModels] = useState([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(true);

  const providers = [
    { id: 'openrouter', name: 'OpenRouter' },
    { id: 'openai', name: 'OpenAI' },
    { id: 'siliconflow', name: 'SiliconFlow' },
    { id: 'gemini', name: 'Google Gemini' },
  ];

  useEffect(() => {
    loadModels(provider);
  }, [provider]);

  useEffect(() => {
    if (models.length > 0 && !model) {
      const defaultModel = models[0].id;
      setModel(defaultModel);
      onSelectionChange(provider, defaultModel);
    }
  }, [models, model, provider, onSelectionChange]);

  const loadModels = async (providerName) => {
    setLoadingModels(true);
    try {
      const response = await getAvailableModels(providerName);
      if (response.success && response.models) {
        setModels(response.models);
        if (response.models.length > 0) {
          const defaultModel = response.models[0].id;
          setModel(defaultModel);
          onSelectionChange(providerName, defaultModel);
        }
      }
    } catch (error) {
      console.error('Failed to load models:', error);
      setModels([]);
    } finally {
      setLoadingModels(false);
    }
  };

  const handleProviderChange = (e) => {
    const newProvider = e.target.value;
    setProvider(newProvider);
    setModel('');
  };

  const handleModelChange = (e) => {
    const newModel = e.target.value;
    setModel(newModel);
    onSelectionChange(provider, newModel);
  };

  return (
    <div className="api-selector">
      <div className="selector-header" onClick={() => setIsCollapsed(!isCollapsed)}>
        <h3>API 配置</h3>
        <button className="collapse-btn" type="button">
          {isCollapsed ? '展开' : '收起'}
        </button>
      </div>

      {!isCollapsed && (
        <div className="selector-content">
          <div className="selector-group">
            <label htmlFor="provider-select">提供商</label>
            <select
              id="provider-select"
              value={provider}
              onChange={handleProviderChange}
              disabled={disabled}
            >
              {providers.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          <div className="selector-group">
            <label htmlFor="model-select">模型</label>
            <select
              id="model-select"
              value={model}
              onChange={handleModelChange}
              disabled={disabled || loadingModels || models.length === 0}
            >
              {loadingModels ? (
                <option>加载中...</option>
              ) : models.length === 0 ? (
                <option>无可用模型</option>
              ) : (
                models.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name}
                  </option>
                ))
              )}
            </select>
          </div>

          <div className="api-info">
            <small>请确保已在后端配置相应的 API 密钥</small>
          </div>
        </div>
      )}
    </div>
  );
};

export default ApiSelector;

