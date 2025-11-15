/**
 * API 服务模块
 * 封装所有后端 API 调用
 */
import axios from 'axios';

// 创建 axios 实例
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000',
  timeout: 120000, // 2分钟超时
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response) {
      // 服务器返回错误状态码
      console.error('API Error:', error.response.data);
    } else if (error.request) {
      // 请求已发送但没有收到响应
      console.error('Network Error:', error.message);
    } else {
      // 其他错误
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);

/**
 * 创建新会话
 */
export const createSession = async () => {
  const response = await api.post('/api/session');
  return response.data;
};

/**
 * 上传 HTML 文件
 */
export const uploadHTML = async (sessionId, htmlContent) => {
  const response = await api.post('/api/upload', {
    session_id: sessionId,
    html_content: htmlContent,
  });
  return response.data;
};

/**
 * 修改 HTML - 智能路由版本
 * 自动选择快速模式或完整模式
 */
export const modifyHTML = async (sessionId, instruction, apiProvider, model, forceMode = null) => {
  const response = await api.post('/api/modify', {
    session_id: sessionId,
    instruction,
    api_provider: apiProvider,
    model,
    force_mode: forceMode,  // 可选：强制使用某种模式
  });
  return response.data;
};

/**
 * 快速模式修改 HTML（直接调用）
 * 返回JSON操作指令
 */
export const modifyHTMLFast = async (sessionId, instruction, apiProvider, model) => {
  const response = await api.post('/api/modify-fast', {
    session_id: sessionId,
    instruction,
    api_provider: apiProvider,
    model,
  });
  return response.data;
};

/**
 * 获取修改历史
 */
export const getHistory = async (sessionId) => {
  const response = await api.get(`/api/history/${sessionId}`);
  return response.data;
};

/**
 * 回退到指定版本
 */
export const revertToHistory = async (sessionId, historyId) => {
  const response = await api.post('/api/revert', {
    session_id: sessionId,
    history_id: historyId,
  });
  return response.data;
};

/**
 * 获取当前 HTML
 */
export const getCurrentHTML = async (sessionId) => {
  const response = await api.get(`/api/current/${sessionId}`);
  return response.data;
};

/**
 * 下载 HTML 文件
 */
export const downloadHTML = async (sessionId, historyId = null) => {
  const response = await api.post('/api/download', {
    session_id: sessionId,
    history_id: historyId,
  }, {
    responseType: 'blob',
  });
  
  // 创建下载链接
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', historyId ? `modified_${historyId.substring(0, 8)}.html` : `modified_${Date.now()}.html`);
  document.body.appendChild(link);
  link.click();
  link.parentNode.removeChild(link);
  window.URL.revokeObjectURL(url);
  
  return true;
};

/**
 * 获取后端提供商支持情况
 */
export const getProviderSupport = async () => {
  const response = await api.get('/api/provider-support');
  return response.data;
};

/**
 * 获取可用模型列表
 */
export const getAvailableModels = async (provider) => {
  const response = await api.get(`/api/models/${provider}`);
  return response.data;
};

/**
 * 健康检查
 */
export const healthCheck = async () => {
  const response = await api.get('/api/health');
  return response.data;
};

export default api;

