import React, { useState, useEffect } from 'react';
import { searchDatasetSamples, selectDatasetSample } from '../services/api';
import '../styles/DatasetSampleModal.css';

const DatasetSampleModal = ({
  open,
  onClose,
  sessionId,
  onSampleApplied,
}) => {
  const [query, setQuery] = useState('');
  const [samples, setSamples] = useState([]);
  const [matched, setMatched] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (open) {
      setQuery('');
      handleSearch('');
    }
  }, [open]);

  const handleSearch = async (searchQuery) => {
    setLoading(true);
    setError('');
    try {
      const response = await searchDatasetSamples(searchQuery, 50);
      if (response.success) {
        setSamples(response.samples || []);
        setMatched(response.matched ?? 0);
      } else {
        setError(response.error || '搜索失败');
      }
    } catch (err) {
      setError(err.message || '搜索失败');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const value = e.target.value;
    setQuery(value);
  };

  const handleSearchSubmit = () => {
    handleSearch(query.trim());
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSearchSubmit();
    }
  };

  const handleSelect = async (sampleId) => {
    if (!sessionId) {
      setError('会话未初始化');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const response = await selectDatasetSample(sessionId, sampleId);
      if (response.success) {
        onSampleApplied(response.html_content, response.sample);
        onClose();
      } else {
        setError(response.error || '加载样本失败');
      }
    } catch (err) {
      setError(err.message || '加载样本失败');
    } finally {
      setLoading(false);
    }
  };

  if (!open) return null;

  return (
    <div className="dataset-modal-overlay" onClick={onClose}>
      <div className="dataset-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>数据集样本</h3>
          <button className="close-btn" type="button" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="search-bar">
          <input
            type="text"
            placeholder="通过 prompt 关键字搜索"
            value={query}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            disabled={loading}
          />
          <button
            className="search-btn"
            type="button"
            onClick={handleSearchSubmit}
            disabled={loading}
          >
            搜索
          </button>
          <span className="result-count">
            {loading ? '搜索中…' : `匹配 ${matched} 条`}
          </span>
        </div>

        {error && <div className="dataset-error">{error}</div>}

        <div className="sample-list">
          {!loading && samples.length === 0 ? (
            <div className="empty">暂无匹配结果</div>
          ) : (
            samples.map((sample) => (
              <div key={sample.id} className="sample-card">
                <div className="sample-info">
                  <p className="sample-prompt">{sample.prompt}</p>
                  <div className="sample-meta">
                    <span>{sample.prompt_type || '未知类型'}</span>
                    <span>{sample.dataset_source || '未知来源'}</span>
                  </div>
                </div>
                <button
                  className="select-btn"
                  type="button"
                  onClick={() => handleSelect(sample.id)}
                  disabled={loading}
                >
                  选择
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default DatasetSampleModal;
