function SkillGap({ results }) {
  if (!results || results.length === 0) {
    return <p>Analyze your skills to see gaps</p>;
  }

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
    <div>
      <h3>Top Missing Skills</h3>

      {topMissingSkills.length === 0 ? (
        <p>No missing skills found in current results</p>
      ) : (
        <>
          <ul>
            {topMissingSkills.map(([skill, count]) => (
              <li key={skill}>
                {skill}: {count}
              </li>
            ))}
          </ul>

          <p>
            Learn {topSkill} to unlock {topSkillCount} more jobs
          </p>
        </>
      )}
    </div>
  );
}

export default SkillGap;
