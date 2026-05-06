function SkillInput({
  onAnalyze,
  isLoading,
  skillsInput,
  setSkillsInput,
  hasResults,
  onClear,
}) {

  const handleSubmit = (event) => {
    event.preventDefault();

    const skills = skillsInput
      .split(",")
      .map((skill) => skill.trim())
      .filter((skill) => skill !== "");

    onAnalyze(skills);
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="input-row">
      <input
        type="text"
        className="skill-input"
        value={skillsInput}
        onChange={(event) => setSkillsInput(event.target.value)}
        placeholder="Enter skills, comma separated"
      />
      <button type="submit" className="analyze-btn" disabled={isLoading}>
        {isLoading ? "Analyzing..." : "Analyze"}
      </button>
      {hasResults && (
        <button type="button" className="clear-btn" onClick={onClear}>
          Clear
        </button>
      )}
      </div>
    </form>
  );
}

export default SkillInput;
