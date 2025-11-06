import React, { useState, useEffect, useCallback } from 'react';
import FileUploader from './components/FileUploader';
import InstructionInput from './components/InstructionInput';
import ApiSelector from './components/ApiSelector';
import ComparisonView from './components/ComparisonView';
import HistoryPanel from './components/HistoryPanel';
import {
  createSession,
  uploadHTML,
  modifyHTML,
  getHistory,
  revertToHistory,
  downloadHTML,
  healthCheck
} from './services/api';
import './styles/App.css';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [originalHtml, setOriginalHtml] = useState('');
  const [currentHtml, setCurrentHtml] = useState('');
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [apiProvider, setApiProvider] = useState('openrouter');
  const [model, setModel] = useState('');
  const [fileName, setFileName] = useState('');
  const [error, setError] = useState('');
  const [backendStatus, setBackendStatus] = useState('checking');
  const [suggestions, setSuggestions] = useState([]);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);

  // 初始化会话
  useEffect(() => {
    const initSession = async () => {
      try {
        // 检查后端健康状态
        await healthCheck();
        setBackendStatus('connected');
        
        // 创建会话
        const response = await createSession();
        if (response.success) {
          setSessionId(response.session_id);
        } else {
          setError('创建会话失败');
          setBackendStatus('error');
        }
      } catch (error) {
        console.error('Failed to initialize session:', error);
        setError('无法连接到后端服务，请确保后端已启动');
        setBackendStatus('error');
      }
    };

    initSession();
  }, []);

  // 上传文件处理
  const handleFileUpload = async (content, name) => {
    setLoading(true);
    setError('');

    try {
      // 如果没有会话ID或上传失败，尝试重新创建会话
      let currentSessionId = sessionId;
      
      if (!currentSessionId) {
        const sessionResponse = await createSession();
        if (sessionResponse.success) {
          currentSessionId = sessionResponse.session_id;
          setSessionId(currentSessionId);
        } else {
          setError('创建会话失败');
          return;
        }
      }

      const response = await uploadHTML(currentSessionId, content);
      
      if (response.success) {
        setOriginalHtml(response.html_content);
        setCurrentHtml(response.html_content);
        setFileName(name);
        setHistory([]); // 清空历史记录
        setSuggestions([]); // 清空建议
      } else {
        // 如果是会话ID无效，尝试重新创建会话后再上传
        if (response.error && response.error.includes('会话')) {
          const sessionResponse = await createSession();
          if (sessionResponse.success) {
            currentSessionId = sessionResponse.session_id;
            setSessionId(currentSessionId);
            
            // 重试上传
            const retryResponse = await uploadHTML(currentSessionId, content);
            if (retryResponse.success) {
              setOriginalHtml(retryResponse.html_content);
              setCurrentHtml(retryResponse.html_content);
              setFileName(name);
              setHistory([]);
              setSuggestions([]);
            } else {
              setError(retryResponse.error || '上传失败');
            }
          } else {
            setError('创建会话失败');
          }
        } else {
          setError(response.error || '上传失败');
        }
      }
    } catch (error) {
      console.error('Upload error:', error);
      setError('上传失败：' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 修改指令处理
  const handleInstructionSubmit = async (instruction) => {
    if (!currentHtml) {
      setError('请先上传 HTML 文件');
      return;
    }

    if (!sessionId) {
      setError('会话已失效，请重新上传文件');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await modifyHTML(sessionId, instruction, apiProvider, model);
      
      if (response.success) {
        setCurrentHtml(response.html_content);
        
        // 刷新历史记录
        const historyResponse = await getHistory(sessionId);
        if (historyResponse.success) {
          setHistory(historyResponse.history);
        }
      } else {
        // 如果是会话问题，提示用户重新上传
        if (response.error && response.error.includes('会话')) {
          setError('会话已失效，请重新上传 HTML 文件');
          setSessionId(null);
          setOriginalHtml('');
          setCurrentHtml('');
          setHistory([]);
        } else {
          setError(response.error || '修改失败');
        }
      }
    } catch (error) {
      console.error('Modify error:', error);
      setError('修改失败：' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  };

  // API 选择变更处理
  const handleApiSelectionChange = useCallback((provider, selectedModel) => {
    setApiProvider(provider);
    setModel(selectedModel);
  }, []);

  // 回退到历史版本
  const handleRevert = async (historyId) => {
    if (!sessionId) return;

    setLoading(true);
    setError('');

    try {
      const response = await revertToHistory(sessionId, historyId);
      
      if (response.success) {
        setCurrentHtml(response.html_content);
      } else {
        setError(response.error || '回退失败');
      }
    } catch (error) {
      console.error('Revert error:', error);
      setError('回退失败：' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 下载 HTML
  const handleDownload = async (historyId = null) => {
    if (!sessionId) return;

    try {
      await downloadHTML(sessionId, historyId);
    } catch (error) {
      console.error('Download error:', error);
      setError('下载失败：' + (error.response?.data?.error || error.message));
    }
  };

  // 生成修改建议
  const handleGenerateSuggestions = async () => {
    if (!currentHtml) {
      setError('请先上传 HTML 文件');
      return;
    }

    if (!sessionId) {
      setError('会话已失效，请重新上传文件');
      return;
    }

    setLoadingSuggestions(true);
    setError('');

    try {
      const response = await fetch(`http://localhost:8000/api/generate-suggestions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          api_provider: apiProvider,
          model: model
        }),
      });

      const data = await response.json();

      if (data.success) {
        setSuggestions(data.suggestions || []);
      } else {
        // 如果是会话问题，提示用户重新上传
        if (data.error && data.error.includes('会话')) {
          setError('会话已失效，请重新上传 HTML 文件');
          setSessionId(null);
          setOriginalHtml('');
          setCurrentHtml('');
          setHistory([]);
          setSuggestions([]);
        } else {
          setError(data.error || '生成建议失败');
        }
      }
    } catch (error) {
      console.error('Generate suggestions error:', error);
      setError('生成建议失败：' + error.message);
    } finally {
      setLoadingSuggestions(false);
    }
  };

  return (
    <div className="app">
      {/* 顶部导航栏 */}
      <header className="app-header">
        <h1>HTML 智能编辑器</h1>
        <div className="header-info">
          {fileName && <span className="file-name">{fileName}</span>}
          <span className={`status-indicator status-${backendStatus}`}>
            {backendStatus === 'checking' && '连接中...'}
            {backendStatus === 'connected' && '已连接'}
            {backendStatus === 'error' && '连接失败'}
          </span>
        </div>
      </header>

      {/* 错误提示 */}
      {error && (
        <div className="error-banner">
          <span className="error-message">{error}</span>
          <button className="error-close" onClick={() => setError('')}>×</button>
        </div>
      )}

      {/* 主内容区 */}
      <div className="app-content">
        {/* 左侧控制面板 */}
        <aside className="control-panel">
          <div className="control-section">
            <h2>上传文件</h2>
            <FileUploader
              onFileUpload={handleFileUpload}
              disabled={loading || backendStatus !== 'connected'}
            />
          </div>

          <div className="control-section">
            <ApiSelector
              onSelectionChange={handleApiSelectionChange}
              disabled={loading || backendStatus !== 'connected'}
            />
          </div>

          <div className="control-section">
            <h2>修改指令</h2>
            <InstructionInput
              onSubmit={handleInstructionSubmit}
              onGenerateSuggestions={handleGenerateSuggestions}
              disabled={!currentHtml || backendStatus !== 'connected'}
              loading={loading}
              suggestions={suggestions}
              loadingSuggestions={loadingSuggestions}
              hasHtml={!!currentHtml}
            />
          </div>

          <div className="control-section">
            <h2>历史记录</h2>
            <HistoryPanel
              history={history}
              onRevert={handleRevert}
              onDownload={handleDownload}
              disabled={loading}
            />
          </div>

          <div className="control-actions">
            <button
              className="action-btn download-current-btn"
              onClick={() => handleDownload()}
              disabled={!currentHtml || loading}
            >
              下载当前版本
            </button>
          </div>
        </aside>

        {/* 右侧预览区 */}
        <main className="preview-area">
          <ComparisonView
            originalHtml={originalHtml}
            currentHtml={currentHtml}
            loading={loading}
          />
        </main>
      </div>

      {/* 底部信息栏 */}
      <footer className="app-footer">
        <p>使用自然语言描述修改，例如：将背景色改为深色、增大标题字体等</p>
        <p className="footer-credits">
          Powered by React + Flask | 支持 OpenRouter、OpenAI、SiliconFlow、Gemini
        </p>
      </footer>
    </div>
  );
}

export default App;
