import React, { useEffect, useRef } from 'react';
import '../styles/PreviewPanel.css';

const PreviewPanel = ({ html, title, loading }) => {
  const iframeRef = useRef(null);

  useEffect(() => {
    if (iframeRef.current && html) {
      const iframe = iframeRef.current;
      const doc = iframe.contentDocument || iframe.contentWindow.document;
      
      doc.open();
      doc.write(html);
      doc.close();
    }
  }, [html]);

  return (
    <div className="preview-panel">
      <div className="preview-header">
        <h3>{title}</h3>
        {loading && <span className="loading-indicator">加载中</span>}
      </div>
      
      <div className="preview-content">
        {html ? (
          <>
            <iframe
              ref={iframeRef}
              title={title}
              className="preview-iframe"
              sandbox="allow-same-origin allow-scripts"
            />
            {loading && (
              <div className="loading-overlay">
                <div className="loading-spinner">
                  <div className="spinner-ring"></div>
                  <div className="spinner-ring"></div>
                  <div className="spinner-ring"></div>
                  <div className="loading-text">AI 正在处理中...</div>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="preview-empty">
            <div className="empty-icon">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
            </div>
            <p>暂无预览内容</p>
            <small>请先上传 HTML 文件</small>
          </div>
        )}
      </div>
    </div>
  );
};

export default PreviewPanel;

