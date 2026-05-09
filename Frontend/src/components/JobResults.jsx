import { formatMatchPercent } from "../analysisFallbacks";

const STRONG_MATCH_LINES = [
  "Your current skill set aligns strongly with this role.",
  "You already meet the primary requirements for this opportunity.",
  "This role closely matches your existing skills.",
];

function mergeRequiredSkills(job, matched, missing) {
  const fromApi = Array.isArray(job.required_skills) ? job.required_skills : [];
  if (fromApi.length > 0) {
    return fromApi;
  }
  const seen = new Set();
  const out = [];
  for (const x of [...matched, ...missing]) {
    const k = String(x).trim().toLowerCase();
    if (!k || seen.has(k)) {
      continue;
    }
    seen.add(k);
    out.push(x);
  }
  return out;
}

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
        const required = mergeRequiredSkills(job, matched, missing);
        const hasGaps = missing.length > 0;
        const hasRequirements = required.length > 0;
        const score = Number(job.match_score);
        const scoreSafe = Number.isFinite(score) ? score : 0;
        const title = job.title || "Role";
        const company = job.company || "Employer";
        const scoreColor = getMatchScoreColor(scoreSafe);

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
                <span className="job-card__score-value">{formatMatchPercent(scoreSafe)}%</span>
              </div>
            </div>

            <div className="job-card__progress-wrap">
              <div className="progress-bar" aria-hidden="true">
                <div
                  className="progress-fill"
                  style={{
                    width: `${Math.min(100, Math.max(0, scoreSafe))}%`,
                    background: scoreColor,
                  }}
                />
              </div>
            </div>

            <div className="job-card__sections">
              <section className="job-card__skill-block">
                <p className="skills-label required">Required skills</p>
                <div className="pills">
                  {required.length > 0 ? (
                    required.map((skill, skillIndex) => (
                      <span
                        key={`${title}-required-${skill}-${skillIndex}`}
                        className="pill pill--neutral"
                      >
                        {skill}
                      </span>
                    ))
                  ) : (
                    <span className="job-card__empty-skill">—</span>
                  )}
                </div>
              </section>
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
                    <span className="job-card__empty-skill">—</span>
                  )}
                </div>
              </section>
              <section className="job-card__skill-block">
                <p className="skills-label missing">Missing skills</p>
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
                    <span className="job-card__empty-skill">—</span>
                  )}
                </div>
              </section>
            </div>

            {hasGaps ? (
              <button
                type="button"
                className="learning-path-btn"
                onClick={() =>
                  onGetLearningPath({
                    ...job,
                    missing_skills: missing,
                    required_skills: required,
                    title,
                  })
                }
              >
                Get learning path
              </button>
            ) : (
              hasRequirements && (
              <p className="job-card__match-well" role="status">
                {STRONG_MATCH_LINES[index % STRONG_MATCH_LINES.length]}
              </p>
              )
            )}
            {!hasRequirements && (
              <p className="job-card__match-note" role="note">
                No clear skill list extracted from title/description for this posting.
              </p>
            )}
          </article>
        );
      })}
    </div>
  );
}

export default JobResults;
