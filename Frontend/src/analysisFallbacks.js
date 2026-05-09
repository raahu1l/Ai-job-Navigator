/** Demo-safe defaults when APIs return empty or partial data */

export const EXPLORATORY_BANNER =
  "No strong matches found — exploring related opportunities.";

export const DEFAULT_MARKET_ANALYSIS = {
  market_summary:
    "Demand for adaptable technical talent stays strong across cloud, data, and product engineering. Employers still reward clear proof of skills and shipped work.",
  your_strength:
    "The skills you entered are a usable foundation—keep tying each one to outcomes you can describe in interviews.",
  biggest_opportunity:
    "Going one level deeper on a high-demand tool (cloud, data, or a major framework) usually opens the next band of roles.",
  demand_trend: "growing",
};

export const DEFAULT_LEARNING_PATH = {
  priority_skill: "Focused upskilling",
  estimated_time: "4–6 weeks",
  steps: [
    {
      skill: "Stack fundamentals",
      resource: "Official documentation + one guided tutorial build",
      time: "1–2 weeks",
    },
    {
      skill: "Visible portfolio piece",
      resource: "Publish one repo or demo an employer can run locally",
      time: "1–2 weeks",
    },
    {
      skill: "Structured stories",
      resource: "Write STAR stories for your top three projects or wins",
      time: "1 week",
    },
  ],
  message:
    "Here is a practical default roadmap you can follow while we keep improving match quality for niche searches.",
};

export const FALLBACK_TRENDING_CHART = [
  { skill: "Python", count: 8 },
  { skill: "SQL", count: 7 },
  { skill: "Cloud (AWS/Azure)", count: 6 },
  { skill: "JavaScript", count: 6 },
  { skill: "Data analysis", count: 5 },
];

export function normalizeMarketAnalysis(raw) {
  const d = raw && typeof raw === "object" ? raw : {};
  return {
    market_summary: d.market_summary || DEFAULT_MARKET_ANALYSIS.market_summary,
    your_strength: d.your_strength || DEFAULT_MARKET_ANALYSIS.your_strength,
    biggest_opportunity:
      d.biggest_opportunity || DEFAULT_MARKET_ANALYSIS.biggest_opportunity,
    demand_trend: d.demand_trend || DEFAULT_MARKET_ANALYSIS.demand_trend,
  };
}

export function normalizeLearningPath(raw) {
  const d = raw && typeof raw === "object" ? raw : {};
  const steps = Array.isArray(d.steps) ? d.steps : [];
  const safeSteps =
    steps.length > 0
      ? steps.map((s, i) => ({
          skill: s?.skill || `Step ${i + 1}`,
          resource: s?.resource || "See course docs and community guides",
          time: s?.time || "1 week",
        }))
      : DEFAULT_LEARNING_PATH.steps;
  return {
    priority_skill: d.priority_skill || DEFAULT_LEARNING_PATH.priority_skill,
    estimated_time: d.estimated_time || DEFAULT_LEARNING_PATH.estimated_time,
    message: d.message || DEFAULT_LEARNING_PATH.message,
    steps: safeSteps,
  };
}

export function buildFallbackResultsFromJobs(jobs, userSkills) {
  const skills = Array.isArray(userSkills) ? userSkills : [];
  return (jobs || []).slice(0, 10).map((job, index) => ({
    job_id: String(job.job_id ?? job.id ?? index),
    title: job.title || "Open role",
    company: job.company || "Employer",
    match_score: 0,
    matched_skills: [],
    missing_skills:
      skills.length > 0
        ? [`Align: ${skills[0]}`, "Read full description", "Tailor your CV"]
        : ["Review posting", "Compare requirements", "Note key tools"],
  }));
}

export function buildMinimalPlaceholderResults(userSkills) {
  const skills = Array.isArray(userSkills) ? userSkills : [];
  return [
    {
      job_id: "exploratory",
      title: "Related opportunities & domains",
      company: "Explore",
      match_score: 0,
      matched_skills: skills.slice(0, 4),
      missing_skills: [
        "Networking & referrals",
        "Keyword-tuned resume",
        "Portfolio or case study",
      ],
    },
  ];
}

export function isExploratoryResults(list) {
  if (!Array.isArray(list) || list.length === 0) {
    return true;
  }
  return list.every((r) => (Number(r.match_score) || 0) < 1);
}
