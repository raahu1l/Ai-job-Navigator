import { EXPLORATORY_BANNER } from "../analysisFallbacks";

function SkillGap({ results, className = "" }) {
  const safeResults = Array.isArray(results) ? results : [];

  const missingSkillCounts = safeResults.reduce((acc, job) => {
    const missingSkills = Array.isArray(job.missing_skills)
      ? job.missing_skills
      : [];

    missingSkills.forEach((skill) => {
      if (skill == null || String(skill).trim() === "") {
        return;
      }
      const key = String(skill).trim();
      acc[key] = (acc[key] || 0) + 1;
    });

    return acc;
  }, {});

  const topMissingSkills = Object.entries(missingSkillCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  const [topSkill, topSkillCount] = topMissingSkills[0] || [];

  return (
    <div className={className}>
      <h3 className="card-title">Top Missing Skills</h3>

      {topMissingSkills.length === 0 ? (
        <div className="gap-fallback">
          <p className="gap-fallback-text">{EXPLORATORY_BANNER}</p>
          <p className="gap-fallback-hint">
            Try adding tools from the job titles you care about (e.g. Python, AWS, SQL)
            or widen your location to surface more signal.
          </p>
        </div>
      ) : (
        <>
          <div className="insight-box">
            Learn <strong>{topSkill}</strong> to unlock {topSkillCount} more roles in this set
          </div>
          <ul className="gap-list">
            {topMissingSkills.map(([skill, count]) => (
              <li key={skill} className="gap-row">
                <span className="gap-skill">{skill}</span>
                <span className="gap-badge">{count}</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}

export default SkillGap;
