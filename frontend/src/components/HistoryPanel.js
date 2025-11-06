import React from 'react';
import '../styles/HistoryPanel.css';

const HistoryPanel = ({ history, onRevert, onDownload, disabled }) => {
  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const getProviderIcon = (provider) => {
    return '';  // 移除所有图标
  };

  return (
    <div className="history-panel">
      <div className="history-header">
        <h3>修改历史</h3>
        <span className="history-count">{history.length} 条记录</span>
      </div>

      <div className="history-list">
        {history.length === 0 ? (
          <div className="history-empty">
            <div className="empty-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p>暂无修改历史</p>
            <small>执行修改后会显示在这里</small>
          </div>
        ) : (
          history.map((item, index) => (
            <div key={item.id} className="history-item">
              <div className="history-item-header">
                <span className="history-index">#{history.length - index}</span>
                <span className="history-time">{formatTimestamp(item.timestamp)}</span>
              </div>
              
              <div className="history-instruction">
                {item.instruction}
              </div>
              
              <div className="history-meta">
                <span className="history-provider">
                  {getProviderIcon(item.api_provider)} {item.api_provider}
                </span>
                <span className="history-model">{item.model}</span>
              </div>
              
              <div className="history-actions">
                <button
                  className="history-btn revert-btn"
                  onClick={() => onRevert(item.id)}
                  disabled={disabled}
                  title="回退到此版本"
                >
                  回退
                </button>
                <button
                  className="history-btn download-btn"
                  onClick={() => onDownload(item.id)}
                  disabled={disabled}
                  title="下载此版本"
                >
                  下载
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default HistoryPanel;

