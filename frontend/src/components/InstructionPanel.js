import React from 'react';

const presetPrompts = [
  '在监控页面顶部增加一个 KPI 卡片突出系统健康度',
  '把告警列表移到右侧栏并缩窄宽度',
  '让所有过滤条改成双行布局保持一致',
];

const InstructionPanel = ({
  instruction,
  onChange,
  onSubmit,
  onUndo,
  onExport,
  loading,
  logs,
  warnings,
  history,
}) => {
  return (
    <section className="panel instruction-panel">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Step 4</p>
          <h2>自然语言编辑</h2>
        </div>
        <div className="actions">
          <button onClick={onUndo} className="ghost-btn">
            撤销一步
          </button>
          <button onClick={onExport} className="ghost-btn">
            导出 Schema
          </button>
        </div>
      </div>

      <textarea
        value={instruction}
        onChange={(e) => onChange(e.target.value)}
        rows={4}
        placeholder="例如：在配置页主列增加一个运行依赖表格，并保持与监控页的过滤条一致"
      />
      <div className="instruction-actions">
        <button className="primary-btn" onClick={onSubmit} disabled={loading}>
          {loading ? '执行中...' : '执行指令'}
        </button>
        <div className="prompt-list">
          {presetPrompts.map((prompt) => (
            <button
              key={prompt}
              type="button"
              onClick={() => onChange(prompt)}
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      {warnings?.length ? (
        <div className="warning-box">
          {warnings.map((warning) => (
            <p key={warning}>{warning}</p>
          ))}
        </div>
      ) : null}

      <div className="log-box">
        <header>
          <h3>最新执行日志</h3>
        </header>
        {logs?.length ? (
          <ul>
            {logs.map((log, index) => (
              <li key={`${log}-${index}`}>{log}</li>
            ))}
          </ul>
        ) : (
          <p className="placeholder">
            执行后的操作日志会展示在此，便于验证 UI-diff。
          </p>
        )}
      </div>

      <div className="history-box">
        <header>
          <h3>UI-diff 历史</h3>
          <span>{history.length} 步</span>
        </header>
        <ul>
          {history.slice(-6).reverse().map((item) => (
            <li key={item.id}>
              <div>
                <strong>{item.instruction}</strong>
                <small>{new Date(item.timestamp).toLocaleTimeString()}</small>
              </div>
              <span className="badge">{item.scope || 'current'}</span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
};

export default InstructionPanel;
