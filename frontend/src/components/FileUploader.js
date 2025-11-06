import React, { useState } from 'react';
import '../styles/FileUploader.css';

const FileUploader = ({ onFileUpload, disabled }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [fileName, setFileName] = useState('');

  const handleDragOver = (e) => {
    e.preventDefault();
    if (!disabled) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (disabled) return;

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleFileInput = (e) => {
    const files = e.target.files;
    if (files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleFile = (file) => {
    if (!file.name.endsWith('.html') && !file.name.endsWith('.htm')) {
      alert('请上传 HTML 文件（.html 或 .htm）');
      return;
    }

    setFileName(file.name);

    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target.result;
      onFileUpload(content, file.name);
    };
    reader.onerror = (e) => {
      alert('文件读取失败');
      console.error(e);
    };
    reader.readAsText(file);
  };

  return (
    <div className="file-uploader">
      <div
        className={`upload-zone ${isDragging ? 'dragging' : ''} ${disabled ? 'disabled' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="file-input"
          accept=".html,.htm"
          onChange={handleFileInput}
          disabled={disabled}
          style={{ display: 'none' }}
        />
        <label htmlFor="file-input" className="upload-label">
          <div className="upload-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="12" y1="18" x2="12" y2="12" />
              <line x1="9" y1="15" x2="15" y2="15" />
            </svg>
          </div>
          <div className="upload-text">
            {fileName ? (
              <>
                <strong>{fileName}</strong>
                <br />
                <small>点击或拖放文件以更换</small>
              </>
            ) : (
              <>
                <strong>点击或拖放 HTML 文件到此处</strong>
                <br />
                <small>支持 .html 和 .htm 格式</small>
              </>
            )}
          </div>
        </label>
      </div>
    </div>
  );
};

export default FileUploader;

