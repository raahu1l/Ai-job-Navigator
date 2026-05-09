import { normalizeLearningPath } from "../analysisFallbacks";

function ListLabel({ title, items, className = "" }) {
  if (!Array.isArray(items) || items.length === 0) {
    return null;
  }
  return (
    <div className={`lp-mini-list ${className}`}>
      <span className="lp-mini-label">{title}</span>
      <ul>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function LearningPath({
  targetRoleLabel,
  learningPath,
  loading,
  errorMessage,
}) {
  if (loading && !learningPath) {
    return (
      <div className="lp-card lp-card--loading" role="status">
        <div className="lp-loading-text">Generating roadmap…</div>
        {targetRoleLabel && (
          <p className="lp-target-line">{targetRoleLabel}</p>
        )}
      </div>
    );
  }

  if (errorMessage) {
    return (
      <div className="lp-card lp-card--error" role="alert">
        <p className="lp-eyebrow">Learning roadmap</p>
        {targetRoleLabel && (
          <p className="lp-target-line lp-target-line--error">{targetRoleLabel}</p>
        )}
        <p className="lp-error-text">{errorMessage}</p>
      </div>
    );
  }

  if (!learningPath) {
    return null;
  }

  const data = normalizeLearningPath(learningPath);
  const gaps = data.missing_skills_for_role || [];
  const steps = data.roadmap_steps?.length ? data.roadmap_steps : data.steps;
  const mdi = data.market_demand_insight || data.demand_insight;
  const lines = data.demand_summary_lines || [];
  const topDemand = data.skill_demand_analytics?.top_demanded_skills || [];
  const nJobs =
    typeof data.skill_demand_analytics?.total_live_jobs_analyzed === "number"
      ? data.skill_demand_analytics.total_live_jobs_analyzed
      : null;
  const showMarketBlock =
    Boolean(mdi && mdi.trim()) ||
    lines.length > 0 ||
    topDemand.length > 0 ||
    (nJobs != null && nJobs >= 0);

  return (
    <div className="lp-card">
      <p className="lp-eyebrow">Learning roadmap</p>
      {targetRoleLabel && <p className="lp-target-line">{targetRoleLabel}</p>}

      {showMarketBlock && (
        <div className="lp-market-block">
          <h3 className="lp-subheading">Market signal (live listings analyzed)</h3>
          {nJobs != null && (
            <p className="lp-market-meta">{nJobs} postings in this fetch</p>
          )}
          {mdi && <p className="lp-demand-insight">{mdi}</p>}
          {lines.length > 0 && (
            <ul className="lp-demand-bullets">
              {lines.map((line, i) => (
                <li key={`${line}-${i}`}>{line}</li>
              ))}
            </ul>
          )}
          {topDemand.length > 0 && (
            <div className="lp-top-demand">
              <span className="lp-mini-label">Top demanded (this set)</span>
              <ul>
                {topDemand.map((row) => (
                  <li key={row.skill}>
                    <strong>{row.skill}</strong> — {row.jobs_with_skill} jobs (
                    ~{row.pct_of_jobs}%)
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {gaps.length > 0 && (
        <div className="lp-missing-block">
          <h3 className="lp-subheading">Skills to close for this role</h3>
          <ul className="lp-missing-chips" aria-label="Missing skills">
            {gaps.map((s) => (
              <li key={s}>
                <span className="lp-missing-chip">{s}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="lp-header">
        <div className="lp-header-main">
          <h2 className="lp-title">Start here</h2>
          <p className="lp-priority-name">
            {data.priority_skill || gaps[0] || "Prioritize one gap"}
          </p>
        </div>
        {data.estimated_time && (
          <div className="lp-time" aria-label="Estimated time overall">
            {data.estimated_time}
          </div>
        )}
      </div>

      {data.message && (
        <div className="lp-message lp-message--muted">{data.message}</div>
      )}

      {steps.length > 0 ? (
        <>
          <h3 className="lp-steps-heading">Step-by-step (per gap)</h3>
          <ol className="lp-roadmap-steps">
            {steps.map((step, index) => (
              <li className="lp-roadmap-step-card" key={`${step.skill}-${index}`}>
                <header className="lp-roadstep-head">
                  <span className="lp-roadstep-num">{index + 1}</span>
                  <div>
                    <h4 className="lp-roadstep-skill">{step.skill}</h4>
                    {step.estimated_time && (
                      <span className="lp-roadstep-time">{step.estimated_time}</span>
                    )}
                  </div>
                </header>
                {step.why_it_matters && (
                  <section className="lp-roadstep-section">
                    <span className="lp-snippet-label">Why it matters here</span>
                    <p className="lp-snippet-body">{step.why_it_matters}</p>
                  </section>
                )}
                {(step.guidance || step.progression) && (
                  <section className="lp-roadstep-section">
                    <span className="lp-snippet-label">Progression</span>
                    <p className="lp-snippet-body">
                      {step.progression || step.guidance}
                    </p>
                  </section>
                )}
                <ListLabel title="Resources" items={step.resources} />
                <ListLabel
                  title="YouTube"
                  items={step.youtube_channels}
                  className="lp-youtube"
                />
                <ListLabel title="Tools & apps" items={step.tools_and_apps} />
                {step.practice_project && (
                  <section className="lp-roadstep-project">
                    <span className="lp-snippet-label">Practice project</span>
                    <p className="lp-snippet-body">{step.practice_project}</p>
                  </section>
                )}
                {!step.resources?.length && step.resource && (
                  <p className="lp-step-resource">{step.resource}</p>
                )}
                {step.platform && (
                  <p className="lp-step-platform">
                    <span className="lp-step-platform-label">Extra</span>{" "}
                    {step.platform}
                  </p>
                )}
              </li>
            ))}
          </ol>
        </>
      ) : (
        gaps.length > 0 && (
          <p className="lp-steps-empty">
            Detailed roadmap steps missing — retry generation.
          </p>
        )
      )}
    </div>
  );
}

export default LearningPath;
