import {
  DEFAULT_LEARNING_PATH,
  normalizeLearningPath,
} from "../analysisFallbacks";

function LearningPath({ learningPath, loading }) {
  if (loading && !learningPath) {
    return (
      <div className="lp-card lp-card--loading" role="status">
        <div className="lp-loading-text">Generating roadmap...</div>
      </div>
    );
  }

  const data = normalizeLearningPath(
    learningPath || DEFAULT_LEARNING_PATH,
  );
  const steps = Array.isArray(data.steps) ? data.steps : [];

  return (
    <div className="lp-card">
      {loading && (
        <div className="lp-inline-loading" role="status">
          Generating roadmap...
        </div>
      )}
      <p className="lp-eyebrow">Learning roadmap</p>
      <div className="lp-header">
        <div className="lp-header-main">
          <h2 className="lp-title">Priority focus</h2>
          <p className="lp-priority-name">{data.priority_skill}</p>
        </div>
        <div className="lp-time" aria-label="Estimated time">
          {data.estimated_time}
        </div>
      </div>
      <div className="lp-message">{data.message}</div>
      <h3 className="lp-steps-heading">Steps</h3>
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
              <p className="lp-step-resource">{step.resource}</p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}

export default LearningPath;
