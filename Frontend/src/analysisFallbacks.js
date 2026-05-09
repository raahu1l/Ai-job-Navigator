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

function normStrList(arr) {
  if (!Array.isArray(arr)) {
    return [];
  }
  return arr.filter((x) => typeof x === "string" && x.trim());
}

/** Prefer new roadmap_steps; fall back to legacy steps. */
function normalizeRoadmapSteps(source) {
  if (!Array.isArray(source)) {
    return [];
  }
  return source.map((s, i) => {
    const legacyRes = typeof s?.resource === "string" ? s.resource : "";
    const resourcesArr = normStrList(s?.resources);
    const fallbackRes =
      resourcesArr.length > 0
        ? resourcesArr
        : legacyRes
          ? [legacyRes.trim()]
          : [];
    const est =
      typeof s?.estimated_time === "string"
        ? s.estimated_time
        : typeof s?.time === "string"
          ? s.time
          : "";
    return {
      skill: s?.skill || `Step ${i + 1}`,
      why_it_matters: typeof s?.why_it_matters === "string" ? s.why_it_matters : "",
      guidance: typeof s?.guidance === "string" ? s.guidance : "",
      progression: typeof s?.progression === "string" ? s.progression : "",
      practice_project:
        typeof s?.practice_project === "string" ? s.practice_project : "",
      resources: fallbackRes,
      youtube_channels: normStrList(s?.youtube_channels),
      tools_and_apps: normStrList(s?.tools_and_apps),
      platform: typeof s?.platform === "string" ? s.platform : "",
      estimated_time: est,
      time: est,
    };
  });
}

export function normalizeLearningPath(raw) {
  const d = raw && typeof raw === "object" ? raw : {};
  const roadmapRaw =
    Array.isArray(d.roadmap_steps) && d.roadmap_steps.length > 0
      ? d.roadmap_steps
      : Array.isArray(d.steps)
        ? d.steps
        : [];
  const safeSteps = normalizeRoadmapSteps(roadmapRaw);
  const missingList = Array.isArray(d.missing_skills_for_role)
    ? d.missing_skills_for_role.filter((x) => typeof x === "string" && x.trim())
    : [];
  const mdi =
    typeof d.market_demand_insight === "string"
      ? d.market_demand_insight.trim()
      : "";
  const dsi =
    typeof d.demand_insight === "string" ? d.demand_insight.trim() : "";
  const demandLines = normStrList(d.demand_summary_lines);
  return {
    missing_skills_for_role: missingList,
    demand_insight: dsi || mdi,
    market_demand_insight: mdi || dsi,
    demand_summary_lines: demandLines,
    skill_demand_analytics:
      d.skill_demand_analytics && typeof d.skill_demand_analytics === "object"
        ? d.skill_demand_analytics
        : null,
    priority_skill: typeof d.priority_skill === "string" ? d.priority_skill : "",
    estimated_time: typeof d.estimated_time === "string" ? d.estimated_time : "",
    message: typeof d.message === "string" ? d.message : "",
    steps: safeSteps,
    roadmap_steps: safeSteps,
  };
}

export function buildFallbackResultsFromJobs(jobs, userSkills) {
  const skills = Array.isArray(userSkills) ? userSkills : [];
  return (jobs || []).slice(0, 10).map((job, index) => {
    const gaps =
      skills.length > 0
        ? [`Align: ${skills[0]}`, "Read full description", "Tailor your CV"]
        : ["Review posting", "Compare requirements", "Note key tools"];
    return {
      job_id: String(job.job_id ?? job.id ?? index),
      title: job.title || "Open role",
      company: job.company || "Employer",
      match_score: 0,
      required_skills: gaps,
      matched_skills: [],
      missing_skills: gaps,
    };
  });
}

export function buildMinimalPlaceholderResults(userSkills) {
  const skills = Array.isArray(userSkills) ? userSkills : [];
  const matched = skills.slice(0, 4);
  const gaps = [
    "Networking & referrals",
    "Keyword-tuned resume",
    "Portfolio or case study",
  ];
  const required = [...matched, ...gaps];
  return [
    {
      job_id: "exploratory",
      title: "Related opportunities & domains",
      company: "Explore",
      match_score: 0,
      required_skills: required,
      matched_skills: matched,
      missing_skills: gaps,
    },
  ];
}

export function isExploratoryResults(list) {
  if (!Array.isArray(list) || list.length === 0) {
    return true;
  }
  return list.every((r) => (Number(r.match_score) || 0) < 1);
}
