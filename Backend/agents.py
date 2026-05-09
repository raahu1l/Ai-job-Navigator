import os
import json
from groq import Groq
from dotenv import load_dotenv

from market_insights import build_market_demand_insight, merge_roadmap_response, skill_demand_from_jobs
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
      "progression": "beginner milestones → intermediate: list 4-7 concrete checkpoints",
      "practice_project": "one small shipped artifact e.g. build X that proves the skill"
    }
  ]
}
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


def analyze_market_demand(
    trending_skills: list,
    user_skills: list,
    live_jobs: list | None = None,
) -> dict:
    trending_skills = filter_skill_list(trending_skills if isinstance(trending_skills, list) else [])
    user_skills = filter_skill_list(user_skills if isinstance(user_skills, list) else [])
    domain = detect_skill_domain(user_skills)
    domain_hint = domain_market_context(domain)

    live_block = ""
    if isinstance(live_jobs, list) and len(live_jobs) > 0:
        dv = skill_demand_from_jobs(live_jobs)
        live_block = f"""
FACTS_EXTRACTED_FROM_LIVE_LISTINGS ({dv['total_jobs']} jobs; whitelist scan of titles/descriptions):
{dv['facts_block']}
Do NOT state percentages unless they derive from counts above."""
    else:
        live_block = "No live postings payload for this analysis — rely on trending list + domain only."

    prompt = f"""
You are a job market analyst.
Ground claims in FACTS_EXTRACTED when present; otherwise be conservative — no fabricated survey stats.

Return ONLY JSON, no markdown:
{{
  "market_summary": "2 concise sentences anchored to FACTS/TRENDS",
  "your_strength": "one sentence from user_skills vs trend context",
  "biggest_opportunity": "skill from FACTS_HIGH_DEMAND_or_trend_or_user_gap",
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
        max_tokens=450,
    )

    text = extract_json(response.choices[0].message.content)
    try:
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception:
        hints = DOMAIN_TRENDING_HINTS.get(domain, DOMAIN_TRENDING_HINTS[DOMAIN_GENERAL])
        return {
            "market_summary": "Market snapshots without live payloads are directional only.",
            "your_strength": "Your declared skills anchor your positioning.",
            "biggest_opportunity": trending_skills[0] if trending_skills else hints[0],
            "demand_trend": "growing",
        }
