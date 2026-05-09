import { useEffect, useMemo, useRef, useState } from "react";
import "./App.css";
import SkillInput from "./components/SkillInput";
import JobResults from "./components/JobResults";
import SkillGap from "./components/SkillGap";
import TrendChart from "./components/TrendChart";
import MarketAnalysis from "./components/MarketAnalysis";
import LearningPath from "./components/LearningPath";
import {
  EXPLORATORY_BANNER,
  DEFAULT_MARKET_ANALYSIS,
  DEFAULT_LEARNING_PATH,
  FALLBACK_TRENDING_CHART,
  normalizeMarketAnalysis,
  normalizeLearningPath,
  buildFallbackResultsFromJobs,
  buildMinimalPlaceholderResults,
  isExploratoryResults,
} from "./analysisFallbacks";

const API_BASE = "https://ai-job-navigator-m9gq.onrender.com";

function App() {
  const [trending, setTrending] = useState([]);
  const [results, setResults] = useState([]);
  const [liveJobs, setLiveJobs] = useState([]);
  const [location, setLocation] = useState("bangalore");
  const [activeAgent, setActiveAgent] = useState(-1);
  const [exampleSkills, setExampleSkills] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingPhase, setLoadingPhase] = useState(null);
  const [error, setError] = useState("");
  const [isResultsHighlighted, setIsResultsHighlighted] = useState(false);
  const [marketAnalysis, setMarketAnalysis] = useState(null);
  const [learningPath, setLearningPath] = useState(null);
  const [showResultsSection, setShowResultsSection] = useState(false);
  const resultsGridRef = useRef(null);
  const lastSkillsRef = useRef([]);

  const pipelineAgents = [
    { icon: "🔍", label: "Job Researcher" },
    { icon: "🧠", label: "Skill Extractor" },
    { icon: "📊", label: "Gap Analyzer" },
    { icon: "🎯", label: "Career Coach" },
  ];

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  const exploratoryMode = useMemo(
    () => isExploratoryResults(results),
    [results],
  );

  const chartData = useMemo(() => {
    if (Array.isArray(trending) && trending.length > 0) {
      return trending;
    }
    return FALLBACK_TRENDING_CHART;
  }, [trending]);

  useEffect(() => {
    const fetchTrending = async () => {
      try {
        setError("");
        const response = await fetch(`${API_BASE}/api/trending`);

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
    lastSkillsRef.current = skills;
    try {
      setShowResultsSection(true);
      setError("");
      setIsLoading(true);
      setLoadingPhase("jobs");
      setActiveAgent(0);
      await sleep(800);

      const fetchJobsResponse = await fetch(`${API_BASE}/api/fetch-jobs`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          keywords: skills.join(" "),
          location: location,
        }),
      });

      if (!fetchJobsResponse.ok) {
        throw new Error("Failed to fetch live jobs");
      }

      const fetchJobsData = await fetchJobsResponse.json();
      const jobs = Array.isArray(fetchJobsData?.jobs) ? fetchJobsData.jobs : [];
      setLiveJobs(jobs);
      setActiveAgent(1);
      await sleep(800);

      const response = await fetch(`${API_BASE}/api/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ skills, job_results: jobs }),
      });

      if (!response.ok) {
        throw new Error("Failed to analyze skills");
      }

      let data;
      try {
        data = await response.json();
      } catch {
        data = [];
      }
      let nextResults = Array.isArray(data) ? data : [];

      if (nextResults.length === 0 && jobs.length > 0) {
        nextResults = buildFallbackResultsFromJobs(jobs, skills);
      }
      if (nextResults.length === 0) {
        nextResults = buildMinimalPlaceholderResults(skills);
      }

      setResults(nextResults);
      setLearningPath(null);
      setActiveAgent(2);
      setLoadingPhase("market");
      await sleep(800);

      const topTrendingSkills = trending
        .slice(0, 5)
        .map((item) => item?.skill)
        .filter(Boolean);

      let marketPayload = { ...DEFAULT_MARKET_ANALYSIS };
      try {
        const marketResponse = await fetch(`${API_BASE}/api/market-analysis`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            trending_skills:
              topTrendingSkills.length > 0
                ? topTrendingSkills
                : FALLBACK_TRENDING_CHART.map((x) => x.skill),
            user_skills: skills,
          }),
        });

        if (marketResponse.ok) {
          const raw = await marketResponse.json();
          marketPayload = normalizeMarketAnalysis(raw);
        }
      } catch (err) {
        console.log("Market analysis error if any:", err);
      }
      setMarketAnalysis(marketPayload);

      setActiveAgent(3);
      setLoadingPhase("roadmap");
      await sleep(800);

      const top = nextResults[0] || {};
      const missingPool = Array.isArray(top.missing_skills)
        ? top.missing_skills
        : [];
      const missingForPath =
        missingPool.length > 0
          ? missingPool.slice(0, 5)
          : skills.slice(0, 3).length > 0
            ? skills.slice(0, 3)
            : ["Communication", "Technical depth", "Portfolio"];
      const role =
        top.title && top.title !== "Related opportunities & domains"
          ? top.title
          : `${skills[0] || "Target"} roles`;

      try {
        const lpRes = await fetch(`${API_BASE}/api/learning-path`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            missing_skills: missingForPath,
            target_role: role,
          }),
        });
        if (lpRes.ok) {
          const lpRaw = await lpRes.json();
          setLearningPath(normalizeLearningPath(lpRaw));
        } else {
          setLearningPath(normalizeLearningPath(DEFAULT_LEARNING_PATH));
        }
      } catch (err) {
        console.log("Learning path error:", err);
        setLearningPath(normalizeLearningPath(DEFAULT_LEARNING_PATH));
      }

      setActiveAgent(4);
      setLoadingPhase(null);

      setIsResultsHighlighted(true);
      window.setTimeout(() => {
        resultsGridRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 50);
      window.setTimeout(() => {
        setIsResultsHighlighted(false);
      }, 1200);
    } catch (err) {
      setError(err.message || "Something went wrong");
      setActiveAgent(-1);
      const sk = lastSkillsRef.current || [];
      setResults(buildMinimalPlaceholderResults(sk));
      setMarketAnalysis({ ...DEFAULT_MARKET_ANALYSIS });
      setLearningPath(normalizeLearningPath({ ...DEFAULT_LEARNING_PATH }));
      setLoadingPhase(null);
      window.setTimeout(() => {
        resultsGridRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 80);
    } finally {
      setIsLoading(false);
      setLoadingPhase(null);
    }
  };

  const runExample = (skills) => {
    setExampleSkills(skills);
    handleAnalyze(skills);
  };

  const handleClear = () => {
    setResults([]);
    setLiveJobs([]);
    setExampleSkills([]);
    setMarketAnalysis(null);
    setLearningPath(null);
    setActiveAgent(-1);
    setIsLoading(false);
    setLoadingPhase(null);
    setShowResultsSection(false);
    setError("");
  };

  const handleGetLearningPath = async (job) => {
    try {
      setLoadingPhase("roadmap");
      const missing = Array.isArray(job?.missing_skills) ? job.missing_skills : [];
      const response = await fetch(`${API_BASE}/api/learning-path`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          missing_skills: missing.length ? missing : ["Core skills"],
          target_role: job?.title || "Your target role",
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to fetch learning path");
      }

      const data = await response.json();
      setLearningPath(normalizeLearningPath(data));
    } catch (err) {
      setError(err.message || "Something went wrong");
      setLearningPath(normalizeLearningPath(DEFAULT_LEARNING_PATH));
    } finally {
      setLoadingPhase(null);
    }
  };

  const uniqueMissingCount =
    results.length > 0
      ? new Set(results.flatMap((r) => r.missing_skills || [])).size
      : 0;
  const top3Titles = results.slice(0, 3).map((r) => r.title).filter(Boolean);

  const loadingMessage =
    loadingPhase === "jobs"
      ? "Analyzing jobs..."
      : loadingPhase === "market"
        ? "Preparing market insights..."
        : loadingPhase === "roadmap"
          ? "Generating roadmap..."
          : null;

  const displayMarket = marketAnalysis || DEFAULT_MARKET_ANALYSIS;

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
            exampleSkills={exampleSkills}
            hasResults={showResultsSection && !isLoading}
            onClear={handleClear}
            location={location}
            setLocation={setLocation}
          />
          {error && <p className="input-error">{error}</p>}
        </div>

        {(isLoading || showResultsSection) && (
          <div
            ref={resultsGridRef}
            className={`results-section ${isResultsHighlighted ? "results-section--highlight" : ""}`}
          >
            <section className="pipeline-card pipeline-card--sticky">
              <div className="pipeline-title">AI Agent Pipeline</div>
              <div className="pipeline-row">
                {pipelineAgents.map((agent, index) => {
                  let state = "idle";
                  if (activeAgent === 4 || activeAgent > index) {
                    state = "completed";
                  } else if (activeAgent === index) {
                    state = "active";
                  }

                  return (
                    <div className="pipeline-item-wrap" key={agent.label}>
                      <div className={`pipeline-agent pipeline-agent--${state}`}>
                        <span className="pipeline-icon">{state === "completed" ? "✓" : agent.icon}</span>
                        <span className="pipeline-label">{agent.label}</span>
                      </div>
                      {index < pipelineAgents.length - 1 && <div className="pipeline-connector" />}
                    </div>
                  );
                })}
              </div>
            </section>

            {loadingMessage && (
              <div className="analysis-loading-banner" role="status">
                {loadingMessage}
              </div>
            )}

            {exploratoryMode && results.length > 0 && (
              <div className="exploratory-banner" role="note">
                {EXPLORATORY_BANNER}
              </div>
            )}

            {results.length > 0 && (
              <>
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

                <div className="top-roles-bar">
                  <span className="top-roles-label">
                    You're best suited for:
                  </span>
                  {(top3Titles.length > 0
                    ? top3Titles
                    : ["Software & data", "Product & delivery", "Cross-functional roles"]
                  ).map((title) => (
                    <span className="role-tag" key={title}>{title}</span>
                  ))}
                </div>

                <div className="results-grid results-grid--jobs-first">
                  <div className="jobs-column">
                    <JobResults
                      results={results}
                      onGetLearningPath={handleGetLearningPath}
                    />
                  </div>
                  <SkillGap results={results} className="gap-card" />
                </div>
              </>
            )}

            <MarketAnalysis analysis={displayMarket} />

            <div className="chart-card chart-card--in-results">
              <TrendChart trending={chartData} usingFallback={!trending?.length} />
            </div>

            <LearningPath
              learningPath={learningPath}
              loading={loadingPhase === "roadmap"}
            />
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
