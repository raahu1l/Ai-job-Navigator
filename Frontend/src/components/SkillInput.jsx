import { useEffect, useState } from "react";

function SkillInput({
  onAnalyze,
  isLoading,
  hasResults,
  onClear,
  exampleSkills,
}) {
  const [skills, setSkills] = useState([]);
  const [inputValue, setInputValue] = useState("");

  useEffect(() => {
    if (Array.isArray(exampleSkills) && exampleSkills.length > 0) {
      setSkills(exampleSkills);
      setInputValue("");
    }
  }, [exampleSkills]);

  const addSkill = (value) => {
    const trimmed = value.trim();
    if (!trimmed) {
      return;
    }
    setSkills((prev) => [...prev, trimmed]);
    setInputValue("");
  };

  const handleKeyDown = (event) => {
    if ((event.key === "Enter" || event.key === ",") && inputValue.trim()) {
      event.preventDefault();
      addSkill(inputValue);
    }
  };

  const handleInputChange = (event) => {
    const value = event.target.value;
    if (value.includes(",")) {
      addSkill(value.replace(",", ""));
      return;
    }
    setInputValue(value);
  };

  const removeSkill = (index) => {
    setSkills((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = () => {
    if (skills.length === 0) {
      return;
    }
    onAnalyze(skills);
    setSkills([]);
    setInputValue("");
  };

  return (
    <div>
      <div className="tags-input-wrapper">
        <div className="tags-container">
          {skills.map((skill, index) => (
            <span className="skill-tag" key={index}>
              {skill}
              <button type="button" className="tag-remove" onClick={() => removeSkill(index)}>×</button>
            </span>
          ))}
          <input
            className="tag-input"
            type="text"
            value={inputValue}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder={skills.length === 0 ? "Type a skill and press Enter..." : "Add more skills..."}
          />
        </div>
        <button
          className="analyze-btn"
          onClick={handleSubmit}
          disabled={isLoading || skills.length === 0}
        >
          {isLoading ? "Analyzing..." : "Analyze"}
        </button>
      </div>
      {hasResults && (
        <button type="button" className="clear-btn" onClick={onClear}>
          Clear
        </button>
      )}
    </div>
  );
}

export default SkillInput;
