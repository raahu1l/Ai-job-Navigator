import { normalizeLearningPath } from "../analysisFallbacks";

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
  const steps = Array.isArray(data.steps) ? data.steps : [];
  const gaps = data.missing_skills_for_role || [];

  return (
    <div className="lp-card">
      <p className="lp-eyebrow">Learning roadmap</p>
      {targetRoleLabel && <p className="lp-target-line">{targetRoleLabel}</p>}

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

      {data.demand_insight && (
        <p className="lp-demand-insight" role="note">
          {data.demand_insight}
        </p>
      )}

      <div className="lp-header">
        <div className="lp-header-main">
          <h2 className="lp-title">Start here</h2>
          <p className="lp-priority-name">{data.priority_skill || gaps[0] || "Prioritize one gap"}</p>
        </div>
        {data.estimated_time && (
          <div className="lp-time" aria-label="Estimated time">
            {data.estimated_time}
          </div>
        )}
      </div>
      {data.message && <div className="lp-message">{data.message}</div>}

      {steps.length > 0 ? (
        <>
          <h3 className="lp-steps-heading">Step-by-step</h3>
          <ol className="lp-timeline">
            {steps.map((step, index) => (
              <li className="lp-step" key={`${step.skill}-${index}`}>
                <div className="lp-step-track" aria-hidden="true">
                  <span className="lp-step-marker">{index + 1}</span>
                </div>
                <div className="lp-step-body">
                  <div className="lp-step-head">
                    <span className="lp-step-skill">{step.skill}</span>
                    <span className="lp-step-time">{step.time}</span>
                  </div>
                  {step.guidance && (
                    <p className="lp-step-guidance">{step.guidance}</p>
                  )}
                  {step.resource && (
                    <p className="lp-step-resource">{step.resource}</p>
                  )}
                  {step.platform && (
                    <p className="lp-step-platform">
                      <span className="lp-step-platform-label">Platform</span>{" "}
                      {step.platform}
                    </p>
                  )}
                </div>
              </li>
            ))}
          </ol>
        </>
      ) : (
        gaps.length > 0 && (
          <p className="lp-steps-empty">
            Detailed steps unavailable — retry or shorten the skill list.
          </p>
        )
      )}
    </div>
  );
}

export default LearningPath;
