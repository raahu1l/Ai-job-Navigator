import { useEffect, useState } from "react";

const SKILL_SUGGESTION_GROUPS = [
  { label: "Engineering", skills: ["Python", "React", "SQL"] },
  { label: "Cloud & DevOps", skills: ["AWS", "Docker", "Kubernetes"] },
  { label: "Marketing", skills: ["Marketing", "SEO", "Content Strategy"] },
  { label: "Sales", skills: ["Sales", "CRM", "Negotiation"] },
  { label: "Finance", skills: ["Finance", "Excel", "Risk Analysis"] },
  { label: "People", skills: ["HR", "Recruiting", "Communication"] },
  { label: "Product", skills: ["Product Management", "Analytics"] },
  { label: "Design", skills: ["UI/UX", "Figma", "Research"] },
];

function SkillInput({
  onAnalyze,
  isLoading,
  hasResults,
  onClear,
  exampleSkills,
  location,
  setLocation,
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

  const applySuggestionGroup = (groupSkills) => {
    setSkills([...groupSkills]);
    setInputValue("");
  };

  return (
    <div className="skill-input-root">
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
            placeholder={
              skills.length === 0
                ? "Enter your skills to discover matching careers, gaps, and learning paths"
                : "Add another skill — press Enter or comma to add"
            }
          />
        </div>
        <select
          className="location-select"
          value={location}
          onChange={(event) => setLocation(event.target.value)}
        >
          <option value="bangalore">Bangalore</option>
          <option value="mumbai">Mumbai</option>
          <option value="delhi">Delhi</option>
          <option value="hyderabad">Hyderabad</option>
          <option value="pune">Pune</option>
          <option value="chennai">Chennai</option>
          <option value="india">India</option>
          <option value="usa">USA</option>
          <option value="uk">UK</option>
          <option value="remote">Remote</option>
        </select>
        <button
          className="analyze-btn"
          onClick={handleSubmit}
          disabled={isLoading || skills.length === 0}
        >
          {isLoading ? "Analyzing..." : "Analyze"}
        </button>
        {hasResults && (
          <button type="button" className="clear-btn" onClick={onClear}>
            Clear
          </button>
        )}
      </div>
      <div className="skill-suggestions">
        <span className="skill-suggestions-label">Quick try — sample profiles</span>
        <div className="skill-suggestions-chips">
          {SKILL_SUGGESTION_GROUPS.map((group) => (
            <button
              key={group.label}
              type="button"
              className="skill-suggestion-chip"
              onClick={() => applySuggestionGroup(group.skills)}
              disabled={isLoading}
              title={group.skills.join(", ")}
            >
              {group.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export default SkillInput;
