import React from 'react';
import PreviewPanel from './PreviewPanel';
import '../styles/ComparisonView.css';

const ComparisonView = ({ originalHtml, currentHtml, loading }) => {
  return (
    <div className="comparison-view">
      <div className="comparison-panel">
        <PreviewPanel 
          html={originalHtml} 
          title="原始版本" 
          loading={false}
        />
      </div>
      
      <div className="comparison-divider"></div>
      
      <div className="comparison-panel">
        <PreviewPanel 
          html={currentHtml} 
          title="当前版本" 
          loading={loading}
        />
      </div>
    </div>
  );
};

export default ComparisonView;

