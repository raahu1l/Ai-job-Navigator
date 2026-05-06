function JobResults({ results }) {
  if (!results || results.length === 0) {
    return <p>No results yet</p>;
  }

  return (
    <div>
      {results.map((job, index) => (
        <div key={`${job.title}-${job.company}-${index}`}>
          <h3>{job.title}</h3>
          <p>{job.company}</p>
          <p>{job.match_score}%</p>

          <div>
            <p>Matched Skills:</p>
            <ul>
              {job.matched_skills.map((skill, skillIndex) => (
                <li key={`${job.title}-matched-${skill}-${skillIndex}`}>{skill}</li>
              ))}
            </ul>
          </div>

          <div>
            <p>Missing Skills:</p>
            <ul>
              {job.missing_skills.map((skill, skillIndex) => (
                <li key={`${job.title}-missing-${skill}-${skillIndex}`}>{skill}</li>
              ))}
            </ul>
          </div>
        </div>
      ))}
    </div>
  );
}

export default JobResults;
