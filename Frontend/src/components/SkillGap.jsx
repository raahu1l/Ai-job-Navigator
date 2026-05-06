function SkillGap({ results, className = "" }) {
  const missingSkillCounts = results.reduce((acc, job) => {
    const missingSkills = Array.isArray(job.missing_skills) ? job.missing_skills : [];

    missingSkills.forEach((skill) => {
      acc[skill] = (acc[skill] || 0) + 1;
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
        <p>No missing skills found in current results</p>
      ) : (
        <>
          <div className="insight-box">
            Learn {topSkill} to unlock {topSkillCount} more jobs
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
