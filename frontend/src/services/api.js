import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000',
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error('API Error:', error.response.data);
      return Promise.reject(error.response.data);
    }
    if (error.request) {
      console.error('Network Error:', error.message);
      return Promise.reject({ error: '网络异常' });
    }
    return Promise.reject(error);
  }
);

export const healthCheck = () => api.get('/api/health').then((res) => res.data);

export const createSession = () => api.post('/api/session').then((res) => res.data);

export const fetchTemplates = () => api.get('/api/templates').then((res) => res.data);

export const configureContext = (sessionId, payload) =>
  api
    .post('/api/context', {
      session_id: sessionId,
      task_spec: payload.taskSpec,
      scenario_id: payload.scenarioId,
      persona_id: payload.personaId,
      persona: payload.personaNotes ? { attention: [payload.personaNotes] } : {},
      component_library: payload.componentLibrary,
    })
    .then((res) => res.data);

export const generateUISchema = (sessionId) =>
  api.post('/api/generate', { session_id: sessionId }).then((res) => res.data);

export const fetchSchema = (sessionId) =>
  api.get(`/api/schema/${sessionId}`).then((res) => res.data);

export const editSchema = (sessionId, instruction) =>
  api.post('/api/edit', { session_id: sessionId, instruction }).then((res) => res.data);

export const fetchHistory = (sessionId) =>
  api.get(`/api/history/${sessionId}`).then((res) => res.data);

export const undoEdit = (sessionId) =>
  api.post('/api/undo', { session_id: sessionId }).then((res) => res.data);

export const fetchDebugInfo = (sessionId) =>
  api.get(`/api/debug/${sessionId}`).then((res) => res.data);

export const exportSchemaFile = async (sessionId) => {
  const response = await api.get(`/api/export/${sessionId}`, { responseType: 'blob' });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `ui_schema_${sessionId.slice(0, 6)}.json`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

export default api;
