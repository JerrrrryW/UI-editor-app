import React, { useEffect, useState } from 'react';
import ContextPanel from './components/ContextPanel';
import StagePlan from './components/StagePlan';
import PagePreview from './components/PagePreview';
import InstructionPanel from './components/InstructionPanel';
import DebugPanel from './components/DebugPanel';
import {
  createSession,
  healthCheck,
  fetchTemplates,
  configureContext,
  generateUISchema,
  editSchema,
  fetchHistory,
  undoEdit,
  exportSchemaFile,
  fetchDebugInfo,
} from './services/api';
import './styles/App.css';

const DEFAULT_TASK_SPEC = `任务：新一批实验配置上线，需要监控运行状态并在异常时联动告警。
- 关注 CPU / GPU 使用率、批次成功率和延迟
- 运维工程师希望保留 Playbook 快捷入口
- 需要跨页面过滤条件一致，支持地域、实验批次、部署版本`;

const initialContext = {
  taskSpec: DEFAULT_TASK_SPEC,
  personaId: 'ops_engineer',
  scenarioId: 'experiment_monitoring',
  personaNotes: '',
  componentLibrary: '',
};

function App() {
  const [status, setStatus] = useState('checking');
  const [sessionId, setSessionId] = useState(null);
  const [templates, setTemplates] = useState({ personas: [], scenarios: [] });
  const [contextForm, setContextForm] = useState(initialContext);
  const [contextSummary, setContextSummary] = useState(null);
  const [schema, setSchema] = useState(null);
  const [stagePlan, setStagePlan] = useState([]);
  const [infoQueue, setInfoQueue] = useState([]);
  const [history, setHistory] = useState([]);
  const [instruction, setInstruction] = useState('');
  const [logs, setLogs] = useState([]);
  const [warnings, setWarnings] = useState([]);
  const [selectedPage, setSelectedPage] = useState(null);
  const [alert, setAlert] = useState('');
  const [loading, setLoading] = useState({
    context: false,
    generate: false,
    edit: false,
  });

  useEffect(() => {
    const init = async () => {
      try {
        await healthCheck();
        setStatus('connected');
        const sessionRes = await createSession();
        if (sessionRes.success) {
          setSessionId(sessionRes.session_id);
        }
        const templateRes = await fetchTemplates();
        setTemplates(templateRes);
      } catch (err) {
        console.error(err);
        setStatus('error');
        setAlert(err?.error || '后端未响应，请确认服务已启动');
      }
    };
    init();
  }, []);

  const refreshHistory = async (id = sessionId) => {
    if (!id) return;
    const res = await fetchHistory(id);
    if (res.success) {
      setHistory(res.history);
    }
  };

  const handleContextSave = async () => {
    if (!sessionId) return;
    setLoading((prev) => ({ ...prev, context: true }));
    setAlert('');
    try {
      let libraryValue = undefined;
      if (contextForm.componentLibrary) {
        libraryValue = JSON.parse(contextForm.componentLibrary);
      }
      const payload = {
        taskSpec: contextForm.taskSpec,
        personaId: contextForm.personaId,
        scenarioId: contextForm.scenarioId,
        personaNotes: contextForm.personaNotes,
        componentLibrary: libraryValue,
      };
      const res = await configureContext(sessionId, payload);
      if (res.success) {
        setContextSummary(res.summary);
        setSchema(null);
        setStagePlan([]);
        setInfoQueue([]);
        setSelectedPage(null);
        setLogs([]);
        setWarnings([]);
        setAlert('上下文已同步，可继续生成界面');
      } else {
        setAlert(res.error || '保存失败');
      }
    } catch (err) {
      setAlert(err.error || '上下文解析失败，请检查 JSON 格式');
    } finally {
      setLoading((prev) => ({ ...prev, context: false }));
    }
  };

  const handleGenerate = async () => {
    if (!sessionId) return;
    setLoading((prev) => ({ ...prev, generate: true }));
    setAlert('');
    try {
      const res = await generateUISchema(sessionId);
      if (res.success) {
        setSchema(res.schema);
        setStagePlan(res.stagePlan);
        setInfoQueue(res.infoQueue);
        const firstPage = res.schema.pages?.[0]?.id;
        setSelectedPage(firstPage || null);
        setLogs(['界面生成完成']);
        await refreshHistory();
      } else {
        setAlert(res.error || '生成失败');
      }
    } catch (err) {
      setAlert(err.error || '生成异常');
    } finally {
      setLoading((prev) => ({ ...prev, generate: false }));
    }
  };

  const handleInstructionSubmit = async () => {
    if (!sessionId || !schema) {
      setAlert('请先生成界面');
      return;
    }
    if (!instruction.trim()) {
      setAlert('请输入自然语言指令');
      return;
    }
    setLoading((prev) => ({ ...prev, edit: true }));
    setAlert('');
    try {
      const res = await editSchema(sessionId, instruction.trim());
      if (res.success) {
        setSchema(res.schema);
        setLogs(res.log);
        setWarnings(res.warnings || []);
        setInstruction('');
        await refreshHistory();
      } else {
        setWarnings(res.warnings || []);
        setAlert(res.error || '执行失败');
      }
    } catch (err) {
      setWarnings([err.error || '执行失败']);
      setAlert(err.error || '执行失败');
    } finally {
      setLoading((prev) => ({ ...prev, edit: false }));
    }
  };

  const handleUndo = async () => {
    if (!sessionId) return;
    try {
      const res = await undoEdit(sessionId);
      if (res.success) {
        setSchema(res.schema);
        await refreshHistory();
      } else {
        setAlert(res.error || '无法撤销');
      }
    } catch (err) {
      setAlert(err.error || '撤销失败');
    }
  };

  const handleExport = async () => {
    if (!sessionId) return;
    try {
      await exportSchemaFile(sessionId);
    } catch (err) {
      setAlert('导出失败');
    }
  };

  const handleRefreshDebug = async () => {
    if (!sessionId) return;
    try {
      const res = await fetchDebugInfo(sessionId);
      if (res.success && res.infoQueue) {
        setInfoQueue(res.infoQueue);
      }
    } catch (err) {
      console.warn('debug fetch skipped', err);
    }
  };

  useEffect(() => {
    if (schema) {
      handleRefreshDebug();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [schema]);

  const highlighted = schema?.metadata?.lastModifiedComponents || [];

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <h1>复杂任务界面生成 + 自然语言编辑</h1>
          <p>任务描述 / Persona / 组件库 → 界面族 + UI-diff</p>
        </div>
        <div className={`status ${status}`}>
          <span className="dot" />
          {status === 'connected' ? '后端已连接' : '连接中'}
        </div>
      </header>

      {alert && (
        <div className="alert-banner">
          <span>{alert}</span>
          <button onClick={() => setAlert('')}>×</button>
        </div>
      )}

      <main className="workspace">
        <div className="column narrow">
          <ContextPanel
            templates={templates}
            formState={contextForm}
            onChange={setContextForm}
            onSubmit={handleContextSave}
            loading={loading.context}
            summary={contextSummary}
          />
          <StagePlan
            stagePlan={stagePlan}
            infoQueue={infoQueue}
            onGenerate={handleGenerate}
            loading={loading.generate}
            disabled={!contextSummary}
          />
        </div>

        <div className="column main">
          <PagePreview
            schema={schema}
            selectedPageId={selectedPage}
            onSelectPage={setSelectedPage}
            highlighted={highlighted}
          />
          <InstructionPanel
            instruction={instruction}
            onChange={setInstruction}
            onSubmit={handleInstructionSubmit}
            onUndo={handleUndo}
            onExport={handleExport}
            loading={loading.edit}
            logs={logs}
            warnings={warnings}
            history={history}
          />
        </div>

        <div className="column narrow">
          <DebugPanel
            infoQueue={infoQueue}
            history={history}
            contextSummary={contextSummary}
          />
        </div>
      </main>
    </div>
  );
}

export default App;
