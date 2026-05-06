function JobResults({ results }) {
  const getMatchScoreColor = (matchScore) => {
    if (matchScore >= 80) {
      return "#22C55E";
    }
    if (matchScore >= 50) {
      return "#F59E0B";
    }
    return "#EF4444";
  };

  return (
    <>
      {results.map((job, index) => (
        <div key={`${job.title}-${job.company}-${index}`} className="job-card">
          <h3 className="job-title">{job.title}</h3>
          <p className="job-company">{job.company}</p>
          <p
            className="match-score"
            style={{ color: getMatchScoreColor(job.match_score) }}
          >
            {job.match_score}%
          </p>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${job.match_score}%` }}
            ></div>
          </div>

          <div>
            <p className="skills-label matched">Matched Skills</p>
            <div className="pills">
              {job.matched_skills.map((skill, skillIndex) => (
                <span
                  key={`${job.title}-matched-${skill}-${skillIndex}`}
                  className="pill matched"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>

          <div>
            <p className="skills-label missing">Missing Skills</p>
            <div className="pills">
              {job.missing_skills.map((skill, skillIndex) => (
                <span
                  key={`${job.title}-missing-${skill}-${skillIndex}`}
                  className="pill missing"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        </div>
      ))}
    </>
  );
}

export default JobResults;
