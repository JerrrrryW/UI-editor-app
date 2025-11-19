import React from 'react';

const StagePlan = ({ stagePlan, infoQueue, onGenerate, loading, disabled }) => {
  return (
    <section className="panel stage-panel">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Step 2</p>
          <h2>多阶段规划</h2>
        </div>
        <button
          className="primary-btn"
          onClick={onGenerate}
          disabled={disabled || loading}
        >
          {loading ? '生成中...' : '生成界面族'}
        </button>
      </div>

      {stagePlan?.length ? (
        <div className="stage-list">
          {stagePlan.map((stage) => (
            <article key={stage.id} className="stage-card">
              <header>
                <span>Page {stage.order}</span>
                <strong>{stage.name}</strong>
              </header>
              <p>{stage.description}</p>
            </article>
          ))}
        </div>
      ) : (
        <p className="placeholder">保存上下文后生成，自动识别 2-3 个任务阶段</p>
      )}

      <div className="priority-queue">
        <header>
          <h3>Priority Queue（Top 6）</h3>
          <span>{infoQueue.length} 信息项</span>
        </header>
        {infoQueue.length ? (
          <ul>
            {infoQueue.slice(0, 6).map((item) => (
              <li key={item.id}>
                <span className="rank">#{item.rank}</span>
                <div>
                  <strong>{item.description}</strong>
                  <small>{item.stageName}</small>
                </div>
                <span className="badge">{Math.round(item.priority * 100)}%</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="placeholder">信息项将在生成时自动整理</p>
        )}
      </div>
    </section>
  );
};

export default StagePlan;
