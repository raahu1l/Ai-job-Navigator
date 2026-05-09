function JobResults({ results, onGetLearningPath }) {
  const getMatchScoreColor = (matchScore) => {
    const n = Number(matchScore) || 0;
    if (n >= 80) {
      return "#22C55E";
    }
    if (n >= 50) {
      return "#F59E0B";
    }
    return "#EF4444";
  };

  const safeResults = Array.isArray(results) ? results : [];

  return (
    <div className="job-results-list">
      {safeResults.map((job, index) => {
        const matched = Array.isArray(job.matched_skills) ? job.matched_skills : [];
        const missing = Array.isArray(job.missing_skills) ? job.missing_skills : [];
        const score = Number(job.match_score) || 0;
        const title = job.title || "Role";
        const company = job.company || "Employer";
        const scoreColor = getMatchScoreColor(score);

        return (
          <article
            key={`${job.job_id || title}-${company}-${index}`}
            className="job-card"
          >
            <div className="job-card__header">
              <div className="job-card__titles">
                <h3 className="job-title">{title}</h3>
                <p className="job-company">{company}</p>
              </div>
              <div
                className="job-card__score-block"
                style={{ "--job-score-color": scoreColor }}
              >
                <span className="job-card__score-label">Match</span>
                <span className="job-card__score-value">{Math.round(score)}%</span>
              </div>
            </div>

            <div className="job-card__progress-wrap">
              <div className="progress-bar" aria-hidden="true">
                <div
                  className="progress-fill"
                  style={{
                    width: `${Math.min(100, Math.max(0, score))}%`,
                    background: scoreColor,
                  }}
                />
              </div>
            </div>

            <div className="job-card__sections">
              <section className="job-card__skill-block">
                <p className="skills-label matched">Matched</p>
                <div className="pills">
                  {matched.length > 0 ? (
                    matched.map((skill, skillIndex) => (
                      <span
                        key={`${title}-matched-${skill}-${skillIndex}`}
                        className="pill matched"
                      >
                        {skill}
                      </span>
                    ))
                  ) : (
                    <span className="pill pill--muted">Add aligned skills to improve match</span>
                  )}
                </div>
              </section>
              <section className="job-card__skill-block">
                <p className="skills-label missing">Gaps / next</p>
                <div className="pills">
                  {missing.length > 0 ? (
                    missing.map((skill, skillIndex) => (
                      <span
                        key={`${title}-missing-${skill}-${skillIndex}`}
                        className="pill missing"
                      >
                        {skill}
                      </span>
                    ))
                  ) : (
                    <span className="pill pill--muted">See full listing for details</span>
                  )}
                </div>
              </section>
            </div>

            <button
              type="button"
              className="learning-path-btn"
              onClick={() =>
                onGetLearningPath({
                  ...job,
                  missing_skills: missing,
                  title,
                })
              }
            >
              Get learning path
            </button>
          </article>
        );
      })}
    </div>
  );
}

export default JobResults;
