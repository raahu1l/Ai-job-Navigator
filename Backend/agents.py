import os
import json
from groq import Groq
from dotenv import load_dotenv

from market_insights import (
    build_live_batch_market_analysis,
    build_market_demand_insight,
    merge_roadmap_response,
    skill_demand_from_jobs,
)
from skill_domain import (
    DOMAIN_GENERAL,
    DOMAIN_TRENDING_HINTS,
    detect_skill_domain,
    domain_market_context,
)
from skill_filters import filter_skill_list


def _as_str_list(val) -> list[str]:
    if not isinstance(val, list):
        return []
    out = []
    for x in val:
        if isinstance(x, str) and x.strip():
            out.append(x.strip())
    return out


def _sanitize_learning_path_payload(data: dict) -> dict:
    """Normalize roadmap_steps skill names; coerce list/string fields."""
    if not isinstance(data, dict):
        return data
    out = dict(data)
    ms = out.get("missing_skills_for_role")
    if isinstance(ms, list):
        out["missing_skills_for_role"] = filter_skill_list(
            [str(x) for x in ms if isinstance(x, str)]
        )
    ps = out.get("priority_skill")
    if isinstance(ps, str):
        kept = filter_skill_list([ps])
        out["priority_skill"] = kept[0] if kept else ""
    keys_str = ("demand_insight", "market_demand_insight", "estimated_time")
    for k in keys_str:
        if k in out and out[k] is not None and not isinstance(out[k], str):
            out[k] = str(out[k])

    steps_key = None
    if isinstance(out.get("roadmap_steps"), list):
        steps_key = "roadmap_steps"
    elif isinstance(out.get("steps"), list):
        steps_key = "steps"
    else:
        return out

    raw_steps = out[steps_key]
    new_steps: list[dict] = []
    for step in raw_steps:
        if not isinstance(step, dict):
            continue
        sk = step.get("skill")
        if not isinstance(sk, str):
            continue
        kept = filter_skill_list([sk])
        if not kept:
            continue
        row = {**step, "skill": kept[0]}
        for lk in ("why_it_matters", "estimated_time", "progression", "practice_project"):
            if lk in row and row[lk] is not None and not isinstance(row[lk], str):
                row[lk] = str(row[lk])
        for lk in ("resources", "youtube_channels", "tools_and_apps"):
            if lk in row:
                row[lk] = _as_str_list(row[lk])
        bw = row.get("best_websites")
        sites: list[dict] = []
        if isinstance(bw, list):
            for item in bw[:2]:
                if not isinstance(item, dict):
                    continue
                name = item.get("name")
                url = item.get("url")
                if isinstance(name, str) and name.strip() and isinstance(url, str) and url.strip():
                    sites.append({"name": name.strip(), "url": url.strip()})
        row["best_websites"] = sites
        new_steps.append(row)
    out["roadmap_steps"] = new_steps
    out["steps"] = new_steps
    return out


def extract_json(text: str):
    import re
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = text.replace("```json", "").replace("```", "").strip()
    object_match = re.search(r"\{.*\}", text, re.DOTALL)
    if object_match:
        return object_match.group()
    array_match = re.search(r"\[.*\]", text, re.DOTALL)
    if array_match:
        return array_match.group()
    return text.strip()


load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "qwen/qwen3-32b"


def extract_skills_from_jd(job_description: str) -> list:
    prompt = f"""
You are a skill extraction expert. 
Extract only the technical and professional skills from this job description.
Return ONLY a JSON array of skill strings. No explanation, no markdown, just the array.
Example: ["Python", "SQL", "Machine Learning", "Communication"]

Job Description:
{job_description}
"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=500,
    )

    text = extract_json(response.choices[0].message.content)
    try:
        skills = json.loads(text)
        skills = skills if isinstance(skills, list) else []
        return filter_skill_list(skills)
    except Exception:
        return []


ROADMAP_JSON_SCHEMA_HINT = """
Return ONLY JSON (no markdown). Use exactly these keys:

{
  "missing_skills_for_role": ["ordered actionable gaps from INPUT_MISSING"],
  "priority_skill": "first to learn — must be one of INPUT_MISSING",
  "estimated_time": "realistic TOTAL range summed from steps e.g. 6-12 weeks",
  "message": "single practical line: what completing this roadmap unlocks interview-wise — no fluff",
  "roadmap_steps": [
    {
      "skill": "canonical skill name matching INPUT_MISSING",
      "why_it_matters": "2-4 sentences: concrete tasks this skill enables FOR THIS ROLE",
      "estimated_time": "honest duration for working adults e.g. 3-5 weeks — not hours",
      "resources": ["freeCodeCamp X", "official docs topic", "Khan Academy / Mode / etc."],
      "youtube_channels": ["named channel relevant to skill", "named playlist"],
      "tools_and_apps": ["tool or site e.g. pgAdmin / Excel / Salesforce"],
      "best_websites": [
        {"name": "Authoritative site name", "url": "https://…"},
        {"name": "Second high-quality site", "url": "https://…"}
      ],
      "progression": "beginner milestones → intermediate: list 4-7 concrete checkpoints",
      "practice_project": "one small shipped artifact e.g. build X that proves the skill"
    }
  ]
}

Rules for best_websites: EXACTLY 1-2 entries. Must be well-known official or academy sites
(e.g. react.dev, sqlbolt.com, mode.com SQL tutorial, HubSpot Academy, Google Skillshop, Figma Learn).
NO generic blogs or SEO spam. URLs must be real https links.
"""


def generate_learning_path(
    missing_skills: list,
    target_role: str,
    demand_context: dict | None = None,
) -> dict:
    missing_skills = filter_skill_list(missing_skills if isinstance(missing_skills, list) else [])
    ctx = demand_context if isinstance(demand_context, dict) else {}
    raw_jobs = ctx.get("live_jobs")
    live_jobs = raw_jobs if isinstance(raw_jobs, list) else []

    demand_skills_preview = skill_demand_from_jobs(live_jobs)
    market_primary, bullets, analytics = build_market_demand_insight(
        live_jobs or None,
        missing_skills,
    )

    empty_out = (
        lambda msg: merge_roadmap_response(
            {
                "message": msg,
                "missing_skills_for_role": missing_skills,
                "estimated_time": "",
                "market_demand_insight": (
                    demand_skills_preview["facts_block"]
                    if demand_skills_preview["total_jobs"] > 0
                    else "No postings were analyzed for demand data."
                ),
                "priority_skill": missing_skills[0] if missing_skills else "",
                "demand_summary_lines": demand_skills_preview["facts_lines"],
                "skill_demand_analytics": analytics,
                "steps": [],
                "roadmap_steps": [],
            },
            market_demand_insight=market_primary or demand_skills_preview["facts_block"],
            demand_support_bullets=bullets or demand_skills_preview["facts_lines"],
            analytics=analytics,
            missing_skills=missing_skills,
            estimated_total_from_steps=None,
        )
    )

    if not missing_skills:
        return empty_out("No skill gaps listed for this role.")

    facts_for_llm = "\n".join(
        ["DATA FROM LIVE POSTINGS (analyze roadmaps ONLY with these counts in mind):"]
        + demand_skills_preview["facts_lines"]
        + bullets
        if (demand_skills_preview["facts_lines"] or bullets)
        else [
            "DATA: No extractable whitelist skills across live postings.",
            (
                "If N listings were sent but extraction is sparse, cite that demand quantification "
                "is unavailable and rely on authoritative learning resources anyway."
                if ctx.get("roles_in_current_set")
                else "No postings context."
            ),
        ]
    )

    metric_bits = []
    if ctx.get("roles_in_current_set") is not None:
        metric_bits.append(f"Listings displayed in UI (context): {ctx.get('roles_in_current_set')}")
    if ctx.get("match_score_percent") is not None:
        metric_bits.append(f"Current role match score: {ctx.get('match_score_percent')}%")
    if ctx.get("top_missing_skill"):
        metric_bits.append(f"Primary gap highlighted: {ctx.get('top_missing_skill')}")

    metric_line = "\n".join(metric_bits) if metric_bits else ""

    prompt = f"""
ACT AS: senior career coach grounded in sourcing and hiring reality.

RULES:
1) One roadmap_steps entry PER skill in INPUT_MISSING (same count). Do NOT merge aggressively.
2) Do NOT invent job-market percentages. For demand context, cite ONLY factual lines from FACTS_FROM_LIVE.
3) Estimated times must assume part-time evenings + weekends — no "learn SQL in two days".
4) resources / youtube_channels / tools_and_apps: name specific known platforms (no vague tutorials).
5) progression must read like a syllabus (Beginner → Intermediate), not motivational bullet fluff.
6) practice_project must be a single concrete deliverable (dataset or repo scale).
7) best_websites: 1-2 only; skill-specific; legitimate domains; full https URLs.

FACTS_FROM_LIVE (counts from extracted titles/descriptions of listings provided by the API):
{facts_for_llm}

ROLE_CONTEXT:
{metric_line}

Target role title: {target_role}
INPUT_MISSING_SKILLS: {json.dumps(missing_skills)}

{ROADMAP_JSON_SCHEMA_HINT}

Fill roadmap_steps[].skill strictly from INPUT_MISSING ({len(missing_skills)} items).
estimated_time TOTAL should logically align with SUM of realistic per-step durations.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.25,
        max_tokens=3500,
    )

    text = extract_json(response.choices[0].message.content)
    try:
        text = text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(text)
        out = _sanitize_learning_path_payload(parsed)
        merged = merge_roadmap_response(
            out,
            market_demand_insight=market_primary,
            demand_support_bullets=bullets,
            analytics={**analytics, "top_demanded_skills": demand_skills_preview.get("top_skills", [])},
            missing_skills=missing_skills,
            estimated_total_from_steps=out.get("estimated_time"),
        )
        if not merged.get("missing_skills_for_role"):
            merged["missing_skills_for_role"] = list(missing_skills)
        merged["demand_summary_lines"] = bullets or merged.get("demand_summary_lines", [])
        return merged
    except Exception:
        return merge_roadmap_response(
            {
                "missing_skills_for_role": missing_skills,
                "priority_skill": missing_skills[0],
                "estimated_time": "",
                "message": "Roadmap formatting failed — use demand lines below plus self-study on each gap.",
                "roadmap_steps": [],
                "steps": [],
            },
            market_demand_insight=market_primary or demand_skills_preview["facts_block"],
            demand_support_bullets=bullets or demand_skills_preview["facts_lines"],
            analytics=analytics,
            missing_skills=missing_skills,
            estimated_total_from_steps=None,
        )


def _live_job_title_sample(jobs: list, limit: int = 14) -> str:
    titles = []
    for j in jobs or []:
        if not isinstance(j, dict):
            continue
        t = str(j.get("title") or "").strip()
        if t and t not in titles:
            titles.append(t)
        if len(titles) >= limit:
            break
    if not titles:
        return "(no titles in payload)"
    return "; ".join(titles)


def analyze_market_demand(
    trending_skills: list,
    user_skills: list,
    live_jobs: list | None = None,
) -> dict:
    trending_skills = filter_skill_list(trending_skills if isinstance(trending_skills, list) else [])
    user_skills = filter_skill_list(user_skills if isinstance(user_skills, list) else [])
    domain = detect_skill_domain(user_skills)
    domain_hint = domain_market_context(domain)

    if isinstance(live_jobs, list) and len(live_jobs) > 0:
        data_copy = build_live_batch_market_analysis(live_jobs, user_skills)
        if (data_copy.get("market_summary") or "").strip():
            return {
                "market_summary": data_copy["market_summary"],
                "your_strength": data_copy.get("your_strength") or "",
                "biggest_opportunity": data_copy.get("biggest_opportunity") or "",
                "demand_trend": data_copy.get("demand_trend") or "stable",
            }

    live_block = ""
    if isinstance(live_jobs, list) and len(live_jobs) > 0:
        dv = skill_demand_from_jobs(live_jobs)
        titles_line = _live_job_title_sample(live_jobs)
        live_block = f"""
LIVE_ADZUNA_BATCH ({dv['total_jobs']} roles; skills extracted from real titles + descriptions):
{dv['facts_block']}

VERBATIM_ROLE_TITLES (patterns / seniority / stacks employers actually advertise):
{titles_line}

RULES FOR COPY:
- market_summary MUST cite at least one concrete skill or pairing from FACTS above (e.g. "SQL and Excel").
- Name hiring patterns you can infer from ROLE_TITLES + FACTS (e.g. analyst vs engineer mix), not generic career advice.
- Forbidden: vague motivation, "employers value adaptability", "technology is important" without naming tools from FACTS.
- If FACTS are thin, say what is missing in one short clause—do not invent survey statistics.
- Do NOT state percentages unless they appear in FACTS lines above."""
    else:
        live_block = """No live job payload in this request.
Use Trending_skill_labels + User_skills + domain only. State clearly that signals are keyword-level, not from the current live batch.
Avoid generic filler—tie sentences to the user's stated skills and the trending labels only."""

    prompt = f"""
You are a job market analyst writing copy for a live job-matching product.

Return ONLY JSON, no markdown:
{{
  "market_summary": "Exactly 2 short sentences. When LIVE data exists: reference real extracted skills and recurring role-title patterns. When not: one sentence on keyword trends + one on limitations.",
  "your_strength": "One sentence: how user_skills intersect what employers show in this context (no fluff).",
  "biggest_opportunity": "One concrete skill or pairing to deepen (must echo FACTS or trending list; never a platitude).",
  "demand_trend": "one of growing/stable/declining"
}}

{domain_hint}

Trending_skill_labels (prior window): {trending_skills}
User_skills: {user_skills}

{live_block}
"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=520,
    )

    text = extract_json(response.choices[0].message.content)
    try:
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception:
        hints = DOMAIN_TRENDING_HINTS.get(domain, DOMAIN_TRENDING_HINTS[DOMAIN_GENERAL])
        if isinstance(live_jobs, list) and len(live_jobs) > 0:
            dv = skill_demand_from_jobs(live_jobs)
            fb = (dv.get("facts_block") or "").strip()
            ts = _live_job_title_sample(live_jobs, 8)
            return {
                "market_summary": (
                    f"Live batch signals: {fb[:320]}{'…' if len(fb) > 320 else ''} "
                    f"Role titles lean toward: {ts[:200]}{'…' if len(ts) > 200 else ''}"
                ).strip(),
                "your_strength": (
                    "Cross-check your listed skills against the frequency lines above to prioritize proof points."
                ),
                "biggest_opportunity": (
                    (dv.get("top_skills") or [{}])[0].get("skill")
                    if dv.get("top_skills")
                    else (trending_skills[0] if trending_skills else hints[0])
                ),
                "demand_trend": "growing",
            }
        return {
            "market_summary": (
                "No live batch was attached to this response—treat trending labels as directional keyword demand only, "
                "not employer-verified counts for your search."
            ),
            "your_strength": (
                f"Your stated skills ({', '.join(user_skills[:5]) or '—'}) frame where to focus proof and keyword alignment."
            ),
            "biggest_opportunity": trending_skills[0] if trending_skills else hints[0],
            "demand_trend": "growing",
        }
