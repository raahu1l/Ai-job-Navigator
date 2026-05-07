import { useEffect, useRef, useState } from "react";
import "./App.css";
import SkillInput from "./components/SkillInput";
import JobResults from "./components/JobResults";
import SkillGap from "./components/SkillGap";
import TrendChart from "./components/TrendChart";

function App() {
  const [trending, setTrending] = useState([]);
  const [results, setResults] = useState([]);
  const [skillsInput, setSkillsInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [isResultsHighlighted, setIsResultsHighlighted] = useState(false);
  const resultsGridRef = useRef(null);

  useEffect(() => {
    const fetchTrending = async () => {
      try {
        setError("");
        const response = await fetch("https://ai-job-navigator-m9gq.onrender.com/api/trending");

        if (!response.ok) {
          throw new Error("Failed to fetch trending skills");
        }

        const data = await response.json();
        setTrending(Array.isArray(data) ? data : []);
      } catch (err) {
        setError(err.message || "Something went wrong");
      }
    };

    fetchTrending();
  }, []);

  const handleAnalyze = async (skills) => {
    try {
      setError("");
      setIsLoading(true);

      const response = await fetch("https://ai-job-navigator-m9gq.onrender.com/api/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ skills }),
      });

      if (!response.ok) {
        throw new Error("Failed to analyze skills");
      }

      const data = await response.json();
      const nextResults = Array.isArray(data) ? data : [];
      setResults(nextResults);

      if (nextResults.length > 0) {
        setIsResultsHighlighted(true);
        window.setTimeout(() => {
          resultsGridRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
        }, 50);
        window.setTimeout(() => {
          setIsResultsHighlighted(false);
        }, 1200);
      }
    } catch (err) {
      setError(err.message || "Something went wrong");
    } finally {
      setIsLoading(false);
    }
  };

  const runExample = (skills) => {
    setSkillsInput(skills.join(", "));
    handleAnalyze(skills);
  };

  const handleClear = () => {
    setResults([]);
  };

  const uniqueMissingCount = results.length > 0
    ? new Set(results.flatMap((r) => r.missing_skills)).size
    : 0;
  const top3Titles = results.slice(0, 3).map((r) => r.title);

  return (
    <div>
      <nav className="navbar">
        <div className="navbar-brand">⚡ SkillNav</div>
        <div className="navbar-sub">AI Job & Skill Navigator</div>
      </nav>

      <main className="page">
        <section className="hero">
          <h1>
            Find Your Perfect <span>Skill Match</span>
          </h1>
          <p>
            Analyze hundreds of job postings instantly. See your match score,
            skill gaps, and exactly what to learn next.
          </p>
          <div className="examples-label">Try an example:</div>
          <div className="examples">
            <button
              type="button"
              className="example-btn"
              onClick={() =>
                runExample([
                  "Python",
                  "Engineering",
                  "Information Technology",
                  "Research",
                ])
              }
            >
              Python Developer
            </button>
            <button
              type="button"
              className="example-btn"
              onClick={() =>
                runExample([
                  "Sales",
                  "Management",
                  "Business Development",
                  "Marketing",
                ])
              }
            >
              Sales Manager
            </button>
            <button
              type="button"
              className="example-btn"
              onClick={() =>
                runExample([
                  "Analyst",
                  "Research",
                  "Finance",
                  "Information Technology",
                ])
              }
            >
              Data Analyst
            </button>
          </div>
        </section>

        <div className="input-card">
          <SkillInput
            onAnalyze={handleAnalyze}
            isLoading={isLoading}
            skillsInput={skillsInput}
            setSkillsInput={setSkillsInput}
            hasResults={results.length > 0}
            onClear={handleClear}
          />
          {error && <p>{error}</p>}
        </div>

        <div className="chart-card">
          <TrendChart trending={trending} />
        </div>

        {results.length > 0 && (
          <div className="stats-bar">
            <div className="stat-item">
              <span className="stat-number">500</span>
              <span className="stat-label">Jobs Analyzed</span>
            </div>
            <div className="stat-item">
              <span className="stat-number">{results.length}</span>
              <span className="stat-label">Roles You Match</span>
            </div>
            <div className="stat-item">
              <span className="stat-number">{uniqueMissingCount}</span>
              <span className="stat-label">Skills to Learn</span>
            </div>
          </div>
        )}

        {results.length > 0 && (
          <div className="top-roles-bar">
            <span className="top-roles-label">
              You're best suited for:
            </span>
            {top3Titles.map((title) => (
              <span className="role-tag" key={title}>{title}</span>
            ))}
          </div>
        )}

        {results.length > 0 && (
          <div
            ref={resultsGridRef}
            className={`results-grid ${isResultsHighlighted ? "results-grid--highlight" : ""}`}
          >
            <SkillGap results={results} className="gap-card" />
            <div className="jobs-column">
              <JobResults results={results} />
            </div>
          </div>
        )}
      </main>

      <footer className="footer">
        Built for AMD Developer Hackathon · lablab.ai 2025
      </footer>
    </div>
  );
}

export default App;
