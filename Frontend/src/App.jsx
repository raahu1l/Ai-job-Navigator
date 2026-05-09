import { useEffect, useMemo, useRef, useState } from "react";
import "./App.css";
import SkillInput from "./components/SkillInput";
import JobResults from "./components/JobResults";
import TrendChart from "./components/TrendChart";
import MarketAnalysis from "./components/MarketAnalysis";
import LearningPath from "./components/LearningPath";
import {
  EXPLORATORY_BANNER,
  DEFAULT_MARKET_ANALYSIS,
  FALLBACK_TRENDING_CHART,
  normalizeMarketAnalysis,
  buildFallbackResultsFromJobs,
  buildMinimalPlaceholderResults,
  isExploratoryResults,
} from "./analysisFallbacks";

const API_BASE = "https://ai-job-navigator-m9gq.onrender.com";

const SLIM_JOB_DESC_MAX = 5000;

function slimJobsForMarketInsights(jobs) {
  const arr = Array.isArray(jobs) ? jobs : [];
  return arr.map((j) => ({
    job_id: String(j.job_id ?? ""),
    title: j.title || "",
    company: j.company || "",
    description:
      typeof j.description === "string"
        ? j.description.slice(0, SLIM_JOB_DESC_MAX)
        : "",
  }));
}

function App() {
  const [trending, setTrending] = useState([]);
  const [results, setResults] = useState([]);
  const [liveJobs, setLiveJobs] = useState([]);
  const [location, setLocation] = useState("bangalore");
  const [activeAgent, setActiveAgent] = useState(-1);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingPhase, setLoadingPhase] = useState(null);
  const [error, setError] = useState("");
  const [isResultsHighlighted, setIsResultsHighlighted] = useState(false);
  const [marketAnalysis, setMarketAnalysis] = useState(null);
  const [learningPath, setLearningPath] = useState(null);
  const [roadmapVisible, setRoadmapVisible] = useState(false);
  const [roadmapTargetLabel, setRoadmapTargetLabel] = useState("");
  const [roadmapError, setRoadmapError] = useState(null);
  const [jobFetchMeta, setJobFetchMeta] = useState({
    count: 0,
    source: null,
  });
  const [showResultsSection, setShowResultsSection] = useState(false);
  const [trendingSkillsQuery, setTrendingSkillsQuery] = useState("");
  const resultsGridRef = useRef(null);
  const learningPathRef = useRef(null);
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
        const q = trendingSkillsQuery.trim();
        const url = q
          ? `${API_BASE}/api/trending?skills=${encodeURIComponent(q)}`
          : `${API_BASE}/api/trending`;
        const response = await fetch(url);

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
  }, [trendingSkillsQuery]);

  const handleAnalyze = async (skills) => {
    lastSkillsRef.current = skills;
    setTrendingSkillsQuery(skills.join(","));
    try {
      setRoadmapVisible(false);
      setLearningPath(null);
      setRoadmapTargetLabel("");
      setRoadmapError(null);
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
      setJobFetchMeta({
        count: typeof fetchJobsData?.count === "number" ? fetchJobsData.count : jobs.length,
        source: fetchJobsData?.source ?? null,
      });
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
            live_jobs: slimJobsForMarketInsights(jobs),
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
      setRoadmapVisible(false);
      setLearningPath(null);
      setJobFetchMeta({ count: 0, source: null });
      setLoadingPhase(null);
      window.setTimeout(() => {
        resultsGridRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 80);
    } finally {
      setIsLoading(false);
      setLoadingPhase(null);
    }
  };

  const handleClear = () => {
    setResults([]);
    setLiveJobs([]);
    setMarketAnalysis(null);
    setLearningPath(null);
    setRoadmapVisible(false);
    setRoadmapTargetLabel("");
    setRoadmapError(null);
    setJobFetchMeta({ count: 0, source: null });
    setActiveAgent(-1);
    setIsLoading(false);
    setLoadingPhase(null);
    setShowResultsSection(false);
    setTrendingSkillsQuery("");
    setError("");
  };

  const handleGetLearningPath = async (job, rolesInCurrentSet = 0) => {
    const title = job?.title || "Role";
    const company = job?.company || "Employer";
    const missing = Array.isArray(job?.missing_skills) ? job.missing_skills : [];
    if (missing.length === 0) {
      return;
    }
    setRoadmapVisible(true);
    setRoadmapTargetLabel(`${title} · ${company}`);
    setRoadmapError(null);
    setLearningPath(null);
    setError("");
    setLoadingPhase("roadmap");
    window.setTimeout(() => {
      learningPathRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 50);
    try {
      const response = await fetch(`${API_BASE}/api/learning-path`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          missing_skills: missing,
          target_role: title,
          demand_context: {
            roles_in_current_set: rolesInCurrentSet,
            match_score_percent: Math.round(Number(job?.match_score) || 0),
            top_missing_skill: missing[0] || "",
            live_jobs: slimJobsForMarketInsights(liveJobs),
          },
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to fetch learning path");
      }

      const data = await response.json();
      setLearningPath(data);
      window.setTimeout(() => {
        learningPathRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 120);
    } catch (err) {
      setRoadmapError(err.message || "Something went wrong");
      setLearningPath(null);
    } finally {
      setLoadingPhase(null);
    }
  };

  const loadingMessage =
    loadingPhase === "jobs"
      ? "Analyzing jobs..."
      : loadingPhase === "market"
        ? "Preparing market insights..."
        : loadingPhase === "roadmap"
          ? "Generating your roadmap..."
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
          <p className="hero-lead">
            Live job matches, skill gaps, trending demand, and a short learning roadmap—one flow.
          </p>
        </section>

        <div className="input-card input-card--compact">
          <SkillInput
            onAnalyze={handleAnalyze}
            isLoading={isLoading}
            hasResults={showResultsSection && !isLoading}
            onClear={handleClear}
            location={location}
            setLocation={setLocation}
          />
          {error && <p className="input-error">{error}</p>}
        </div>

        <div
          ref={resultsGridRef}
          className={`results-section ${isResultsHighlighted ? "results-section--highlight" : ""}`}
        >
          <section className="pipeline-card pipeline-card--sticky pipeline-card--compact">
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

          {(isLoading || showResultsSection) && (
            <>
              {loadingMessage && (
                <div className="analysis-loading-banner" role="status">
                  {loadingMessage}
                </div>
              )}

              {exploratoryMode && results.length > 0 && (
                <div className="exploratory-banner exploratory-banner--compact" role="note">
                  {EXPLORATORY_BANNER}
                </div>
              )}

              {(jobFetchMeta.source != null || jobFetchMeta.count > 0) && (
                <div className="live-data-row" role="status">
                  <p className="live-data-row__primary">
                    {jobFetchMeta.source === "adzuna"
                      ? `Analyzed ${jobFetchMeta.count} live job posting${jobFetchMeta.count === 1 ? "" : "s"}`
                      : `Analyzed ${jobFetchMeta.count} job posting${jobFetchMeta.count === 1 ? "" : "s"} for your search`}
                  </p>
                  <p className="live-data-row__secondary">
                    {jobFetchMeta.source === "adzuna"
                      ? "Powered by Adzuna market data"
                      : jobFetchMeta.source === "fallback"
                        ? "Curated sample listings — comparable matching experience"
                        : "SkillNav"}
                  </p>
                  {results.length > 0 && (
                    <p className="live-data-row__tertiary">
                      Showing{" "}
                      <span className="live-data-row__accent">{results.length}</span>
                      {" "}top matching role{results.length === 1 ? "" : "s"}
                    </p>
                  )}
                </div>
              )}

              {results.length > 0 && (
                <div className="jobs-column">
                  <JobResults
                    results={results}
                    onGetLearningPath={(job) =>
                      handleGetLearningPath(job, results.length)
                    }
                  />
                </div>
              )}

              <div className="chart-card chart-card--compact">
                <TrendChart trending={chartData} usingFallback={!trending?.length} />
              </div>

              <MarketAnalysis analysis={displayMarket} />

              {(roadmapVisible || loadingPhase === "roadmap") && (
                <div ref={learningPathRef} className="learning-path-anchor">
                  <LearningPath
                    targetRoleLabel={roadmapTargetLabel}
                    learningPath={learningPath}
                    loading={loadingPhase === "roadmap"}
                    errorMessage={roadmapError}
                  />
                </div>
              )}
            </>
          )}
        </div>
      </main>

      <footer className="footer">
        Built for AMD Developer Hackathon · lablab.ai 2025
      </footer>
    </div>
  );
}

export default App;
