function LearningPath({ learningPath }) {
  if (!learningPath) {
    return null;
  }

  const steps = Array.isArray(learningPath.steps) ? learningPath.steps : [];

  return (
    <div className="lp-card">
      <div className="lp-header">
        <div className="lp-title">Priority: {learningPath.priority_skill}</div>
        <div className="lp-time">{learningPath.estimated_time}</div>
      </div>
      <div className="lp-message">{learningPath.message}</div>
      <div className="lp-steps">
        {steps.map((step, index) => (
          <div className="lp-step" key={`${step.skill}-${index}`}>
            <div className="lp-step-num">{index + 1}</div>
            <div className="lp-step-info">
              <div className="lp-step-skill">{step.skill}</div>
              <div className="lp-step-resource">{step.resource}</div>
            </div>
            <div className="lp-step-time">{step.time}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default LearningPath;
