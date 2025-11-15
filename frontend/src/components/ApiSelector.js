import React, { useState, useEffect } from 'react';
import { getAvailableModels, getProviderSupport } from '../services/api';
import '../styles/ApiSelector.css';

const ApiSelector = ({ onSelectionChange, disabled }) => {
  const [provider, setProvider] = useState('openrouter');
  const [model, setModel] = useState('');
  const [models, setModels] = useState([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(true);
  const [providerSupport, setProviderSupport] = useState(null);
  const [supportLoading, setSupportLoading] = useState(true);
  const [supportError, setSupportError] = useState('');

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
    const checkProviderSupport = async () => {
      setSupportLoading(true);
      setSupportError('');
      try {
        const response = await getProviderSupport();
        if (response.success) {
          setProviderSupport(response.providers || {});
        } else {
          setSupportError(response.error || '检查失败');
        }
      } catch (error) {
        setSupportError(error.message || '检查失败');
      } finally {
        setSupportLoading(false);
      }
    };

    checkProviderSupport();
  }, []);

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

  const getStatusBadge = (providerId) => {
    const info = providerSupport?.[providerId];
    if (!info) {
      return {
        text: '待检测',
        className: 'unknown',
        tooltip: '后端尚未返回检测信息'
      };
    }

    const baseTooltipParts = [];

    if (!info.has_api_key) {
      return {
        text: '未配置',
        className: 'missing',
        tooltip: '请在后端 .env 中配置该提供商的 API 密钥'
      };
    }

    const validation = info.validation;
    const status = validation?.status || 'unknown';
    if (validation?.message) {
      baseTooltipParts.push(validation.message);
    }
    if (validation?.checked_at) {
      try {
        const formatted = new Date(validation.checked_at).toLocaleString();
        baseTooltipParts.push(`检测时间：${formatted}`);
      } catch (error) {
        baseTooltipParts.push(`检测时间：${validation.checked_at}`);
      }
    }

    const tooltip = baseTooltipParts.join('\n') || '尚未检测该密钥';

    const mapping = {
      valid: { text: '验证通过', className: 'valid' },
      invalid: { text: '密钥无效', className: 'invalid' },
      error: { text: '验证失败', className: 'error' },
      unknown: { text: '待检测', className: 'unknown' }
    };

    const badge = mapping[status] || mapping.unknown;
    return { ...badge, tooltip };
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
            <div className="support-header">
              <small>后端支持自检</small>
              {supportLoading ? (
                <span className="support-pill checking">检测中...</span>
              ) : supportError ? (
                <span className="support-pill error">{supportError}</span>
              ) : (
                <span className="support-pill ok">已更新</span>
              )}
            </div>
            {!supportLoading && !supportError && providerSupport && (
              <div className="support-status">
                {providers.map((p) => (
                  <div key={p.id} className="support-status-item">
                    <div className="status-row">
                      <span className="provider-name-label">{p.name}</span>
                      <span
                        className={`support-badge ${getStatusBadge(p.id).className}`}
                        title={getStatusBadge(p.id).tooltip}
                      >
                        {getStatusBadge(p.id).text}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
            {!supportLoading && supportError && (
              <small className="support-error-tip">请确认后端已启动并允许 /api/provider-support</small>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ApiSelector;
