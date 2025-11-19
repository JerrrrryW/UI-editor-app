import React from 'react';

const ContextPanel = ({
  templates,
  formState,
  onChange,
  onSubmit,
  loading,
  summary,
}) => {
  const personas = templates.personas || [];
  const scenarios = templates.scenarios || [];
  const activePersona = personas.find((p) => p.id === formState.personaId);
  const activeScenario = scenarios.find((s) => s.id === formState.scenarioId);

  return (
    <section className="panel context-panel">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Step 1</p>
          <h2>任务输入与上下文</h2>
        </div>
        <button
          className="primary-btn"
          onClick={onSubmit}
          disabled={loading}
        >
          {loading ? '保存中...' : '同步上下文'}
        </button>
      </div>

      <label className="field">
        <span>任务描述 / 需求文档</span>
        <textarea
          value={formState.taskSpec}
          onChange={(e) => onChange({ ...formState, taskSpec: e.target.value })}
          rows={8}
          placeholder="粘贴需求文档或关键信息..."
        />
      </label>

      <div className="two-col">
        <label className="field">
          <span>Persona 角色</span>
          <select
            value={formState.personaId}
            onChange={(e) =>
              onChange({ ...formState, personaId: e.target.value })
            }
          >
            {personas.map((persona) => (
              <option key={persona.id} value={persona.id}>
                {persona.name} · {persona.role}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>任务场景</span>
          <select
            value={formState.scenarioId}
            onChange={(e) =>
              onChange({ ...formState, scenarioId: e.target.value })
            }
          >
            {scenarios.map((scenario) => (
              <option key={scenario.id} value={scenario.id}>
                {scenario.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      <label className="field">
        <span>Persona 补充关注点（可选）</span>
        <input
          type="text"
          value={formState.personaNotes}
          placeholder="例如：偏好标签筛选 / 希望看到历史改动"
          onChange={(e) =>
            onChange({ ...formState, personaNotes: e.target.value })
          }
        />
      </label>

      <label className="field">
        <div className="field-label">
          <span>组件库 JSON（可选）</span>
          <small>默认组件库已内置，粘贴 JSON 可覆盖</small>
        </div>
        <textarea
          rows={5}
          value={formState.componentLibrary}
          placeholder='[{"id":"card_kpi","type":"CardRow", ...}]'
          onChange={(e) =>
            onChange({ ...formState, componentLibrary: e.target.value })
          }
        />
      </label>

      {summary && (
        <div className="context-summary">
          <div>
            <p className="eyebrow">Persona</p>
            <h4>{summary.persona?.name || activePersona?.name}</h4>
            <p>{summary.persona?.tone || activePersona?.tone}</p>
            <ul>
              {(summary.persona?.focus || []).map((focus) => (
                <li key={focus}>{focus}</li>
              ))}
            </ul>
          </div>
          <div>
            <p className="eyebrow">任务摘要</p>
            <ul>
              {(summary.taskHighlights || []).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
          <div>
            <p className="eyebrow">组件统计</p>
            <p>{summary.componentStats?.total} 个可用组件</p>
            <small>
              {Object.entries(summary.componentStats?.types || {})
                .slice(0, 3)
                .map(([type, count]) => `${type}×${count}`)
                .join(' · ')}
            </small>
          </div>
        </div>
      )}

      <div className="template-hint">
        <strong>当前 Persona：</strong>
        {activePersona ? (
          <span>
            {activePersona.name} · {activePersona.role}
          </span>
        ) : null}
        <strong>当前场景：</strong>
        <span>{activeScenario?.name}</span>
      </div>
    </section>
  );
};

export default ContextPanel;
