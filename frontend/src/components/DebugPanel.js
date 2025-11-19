import React from 'react';

const DebugPanel = ({ infoQueue, history, contextSummary }) => {
  return (
    <section className="panel debug-panel">
      <div className="panel-head">
        <div>
          <p className="eyebrow">研究模式</p>
          <h2>调试视图</h2>
        </div>
      </div>

      <div className="debug-grid">
        <div className="debug-card">
          <header>
            <h3>Priority Queue</h3>
            <span>{infoQueue.length} items</span>
          </header>
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>描述</th>
                <th>Stage</th>
                <th>Priority</th>
              </tr>
            </thead>
            <tbody>
              {infoQueue.slice(0, 10).map((item) => (
                <tr key={item.id}>
                  <td>{item.rank}</td>
                  <td>{item.description}</td>
                  <td>{item.stageName}</td>
                  <td>{Math.round(item.priority * 100)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="debug-card">
          <header>
            <h3>UI-diff 记录</h3>
          </header>
          <ul className="diff-list">
            {history.slice(-8).reverse().map((entry) => (
              <li key={entry.id}>
                <div>
                  <strong>{entry.instruction}</strong>
                  <small>{new Date(entry.timestamp).toLocaleTimeString()}</small>
                </div>
                <div className="diff-meta">
                  <span>{entry.scope || 'current'}</span>
                  {entry.warnings?.length ? (
                    <span className="warning-flag">⚠ {entry.warnings.length}</span>
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {contextSummary && (
        <div className="debug-card">
          <header>
            <h3>上下文摘要</h3>
          </header>
          <div className="summary-row">
            <div>
              <p className="eyebrow">Persona</p>
              <strong>{contextSummary.persona?.name}</strong>
              <small>{contextSummary.persona?.role}</small>
            </div>
            <div>
              <p className="eyebrow">Stage</p>
              <strong>{contextSummary.scenario?.stageCount}</strong>
              <small>{contextSummary.scenario?.name}</small>
            </div>
            <div>
              <p className="eyebrow">Components</p>
              <strong>{contextSummary.componentStats?.total}</strong>
              <small>可用模块</small>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};

export default DebugPanel;
