import React from 'react';

const PagePreview = ({ schema, selectedPageId, onSelectPage, highlighted = [] }) => {
  const pages = schema?.pages || [];
  if (!pages.length) {
    return (
      <section className="panel preview-panel">
        <h2>界面预览</h2>
        <p className="placeholder">生成后可查看各 Page 的 Section 布局</p>
      </section>
    );
  }

  const activePage =
    pages.find((page) => page.id === selectedPageId) || pages[0];

  const gridTemplateColumns = 'repeat(12, minmax(0, 1fr))';

  return (
    <section className="panel preview-panel">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Step 3</p>
          <h2>界面族预览</h2>
        </div>
        <div className="page-tabs">
          {pages.map((page) => (
            <button
              key={page.id}
              className={page.id === activePage.id ? 'active' : ''}
              onClick={() => onSelectPage(page.id)}
            >
              {page.name}
            </button>
          ))}
        </div>
      </div>
      <p className="page-description">{activePage.description}</p>

      <div
        className="section-grid"
        style={{ gridTemplateColumns }}
      >
        {activePage.sections.map((section) => {
          const span = Math.min(section.layout?.colSpan || 12, 12);
          return (
            <div
              key={section.id}
              className={`section-card section-${section.role}`}
              style={{
                gridColumn: `span ${span}`,
                order: section.layout?.order || section.layout?.row || 1,
              }}
            >
              <header>
                <div>
                  <strong>{section.title || section.role}</strong>
                  <small>{section.role}</small>
                </div>
                <span>{span} / 12</span>
              </header>

              <div className="component-stack">
                {section.components.map((component) => {
                  const isHighlighted = highlighted.includes(component.id);
                  return (
                    <article
                      key={component.id}
                      className={`component-card ${
                        isHighlighted ? 'component-highlight' : ''
                      }`}
                    >
                      <div className="component-title">
                        <strong>{component.type}</strong>
                        <span>{component.role}</span>
                      </div>
                      <div className="component-meta">
                        <span>{component.dataRole}</span>
                        <span>
                          Span {component.layout?.colSpan || 4}
                        </span>
                      </div>
                      <div className="component-info">
                        <p>{component.meta?.description}</p>
                        {component.infoRefs?.length ? (
                          <small>Info: {component.infoRefs.join(', ')}</small>
                        ) : null}
                      </div>
                      {component.style?.emphasis === 'highlight' && (
                        <span className="tag">highlight</span>
                      )}
                    </article>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};

export default PagePreview;
