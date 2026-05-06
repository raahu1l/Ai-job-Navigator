import { useState } from "react";

function SkillInput({ onAnalyze, isLoading }) {
  const [skillsInput, setSkillsInput] = useState("");

  const handleSubmit = (event) => {
    event.preventDefault();

    const skills = skillsInput
      .split(",")
      .map((skill) => skill.trim())
      .filter((skill) => skill !== "");

    onAnalyze(skills);
    setSkillsInput("");
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        value={skillsInput}
        onChange={(event) => setSkillsInput(event.target.value)}
        placeholder="Enter skills, comma separated"
      />
      <button type="submit" disabled={isLoading}>
        {isLoading ? "Analyzing..." : "Analyze"}
      </button>
    </form>
  );
}

export default SkillInput;
