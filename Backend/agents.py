import os
import json
from groq import Groq
from dotenv import load_dotenv

from skill_domain import (
    DOMAIN_GENERAL,
    DOMAIN_TRENDING_HINTS,
    detect_skill_domain,
    domain_market_context,
)
from skill_filters import filter_skill_list


def _sanitize_learning_path_payload(data: dict) -> dict:
    """Strip generic labels from LLM learning-path skills; keep roadmap-only fields."""
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
    if out.get("demand_insight") is not None and not isinstance(out.get("demand_insight"), str):
        out["demand_insight"] = str(out["demand_insight"])
    steps = out.get("steps")
    if not isinstance(steps, list):
        return out
    new_steps = []
    for step in steps:
        if not isinstance(step, dict):
            continue
        sk = step.get("skill")
        if not isinstance(sk, str):
            continue
        kept = filter_skill_list([sk])
        if not kept:
            continue
        row = {**step, "skill": kept[0]}
        for key in ("guidance", "resource", "platform", "time"):
            if key in row and row[key] is not None and not isinstance(row[key], str):
                row[key] = str(row[key])
        new_steps.append(row)
    out["steps"] = new_steps
    return out

def extract_json(text: str):
    import re
    # Remove thinking tags if present
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = text.replace("```json", "").replace("```", "").strip()
    # Find JSON object first (prefer object over array)
    object_match = re.search(r'\{.*\}', text, re.DOTALL)
    if object_match:
        return object_match.group()
    # Fall back to array
    array_match = re.search(r'\[.*\]', text, re.DOTALL)
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
        max_tokens=500
    )
    
    text = extract_json(response.choices[0].message.content)
    try:
        skills = json.loads(text)
        skills = skills if isinstance(skills, list) else []
        return filter_skill_list(skills)
    except:
        return []

def generate_learning_path(
    missing_skills: list,
    target_role: str,
    demand_context: dict | None = None,
) -> dict:
    missing_skills = filter_skill_list(missing_skills if isinstance(missing_skills, list) else [])
    if not missing_skills:
        return {
            "message": "No skill gaps listed for this role.",
            "missing_skills_for_role": [],
            "demand_insight": "",
            "steps": [],
        }

    ctx = demand_context if isinstance(demand_context, dict) else {}
    ctx_bits = []
    if ctx.get("roles_in_current_set") is not None:
        ctx_bits.append(f"Roles in current search results: {ctx.get('roles_in_current_set')}")
    if ctx.get("match_score_percent") is not None:
        ctx_bits.append(f"Match score for this posting: {ctx.get('match_score_percent')}%")
    if ctx.get("top_missing_skill") is not None:
        ctx_bits.append(f"Strongest gap to highlight: {ctx.get('top_missing_skill')}")
    ctx_line = "\n".join(ctx_bits) if ctx_bits else "(no extra metrics)"

    prompt = f"""
You are a career coach building a ROLE-SPECIFIC learning roadmap (not generic advice).
Missing skills apply ONLY to this target role.

Return ONLY valid JSON — no markdown, no commentary.

Schema:
{{
  "missing_skills_for_role": [ "same actionable skills from input, ordered by impact" ],
  "demand_insight": "One concrete line like: Learning [skill] could unlock roughly X% more similar roles — use plausible X based on gaps vs role (e.g. 25-45%).",
  "priority_skill": "single skill to learn first",
  "estimated_time": "total weeks range e.g. 4-8 weeks",
  "message": "One short motivational line tying effort to interviews",
  "steps": [
    {{
      "skill": "skill name",
      "guidance": "2-3 sentences: what to learn and in what order",
      "resource": "Specific course, doc path, or practice project",
      "platform": "e.g. freeCodeCamp, Coursera, official docs, YouTube channel name",
      "time": "e.g. 1-2 weeks"
    }}
  ]
}}

Rules:
- steps must cover the main missing_skills (one step per major skill or combine closely related).
- resources must name real platforms or official documentation styles (no vague "online course").
- demand_insight must reference at least one missing skill and a percent or fraction.

Target role title: {target_role}
Missing skills: {missing_skills}

Context for demand line (use if helpful):
{ctx_line}
"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1200,
    )

    text = extract_json(response.choices[0].message.content)
    try:
        text = text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(text)
        out = _sanitize_learning_path_payload(parsed)
        if not out.get("missing_skills_for_role"):
            out["missing_skills_for_role"] = list(missing_skills)
        return out
    except Exception:
        top = missing_skills[0]
        n_roles = ctx.get("roles_in_current_set")
        insight = (
            f"Prioritizing {top} for this role typically widens your fit for similar postings."
        )
        if isinstance(n_roles, int) and n_roles > 0:
            insight = (
                f"In this set of {n_roles} roles, closing gaps on {top} is the fastest way to raise match quality."
            )
        return {
            "missing_skills_for_role": missing_skills,
            "demand_insight": insight,
            "priority_skill": top,
            "estimated_time": "4-6 weeks",
            "steps": [],
            "message": "Could not parse AI roadmap — retry or shorten skills list.",
        }

def analyze_market_demand(trending_skills: list, user_skills: list) -> dict:
    trending_skills = filter_skill_list(trending_skills if isinstance(trending_skills, list) else [])
    user_skills = filter_skill_list(user_skills if isinstance(user_skills, list) else [])
    domain = detect_skill_domain(user_skills)
    domain_hint = domain_market_context(domain)

    prompt = f"""
You are a job market analyst.
Given these market trending skills and user's current skills,
provide a brief market analysis.
Return ONLY a JSON object, no explanation, no markdown.
Format exactly:
{{
  "market_summary": "2 sentence market overview",
  "your_strength": "what the user is good at based on their skills",
  "biggest_opportunity": "single most impactful skill to learn",
  "demand_trend": "growing/stable/declining for user's skill set"
}}

{domain_hint}

Trending skills in market: {trending_skills}
User skills: {user_skills}
"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=500
    )
    
    text = extract_json(response.choices[0].message.content)
    try:
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except:
        hints = DOMAIN_TRENDING_HINTS.get(domain, DOMAIN_TRENDING_HINTS[DOMAIN_GENERAL])
        return {
            "market_summary": "The job market is actively evolving.",
            "your_strength": "Your current skills show solid foundation.",
            "biggest_opportunity": trending_skills[0] if trending_skills else hints[0],
            "demand_trend": "growing"
        }
