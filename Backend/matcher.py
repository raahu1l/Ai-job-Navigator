import json
import re
from pathlib import Path

from job_fetcher import fetch_jobs
from skill_domain import (
    detect_skill_domain,
    domain_job_search_query,
    prioritize_trending_for_domain,
)
from skill_filters import filter_skill_list
from technical_trending import extract_technical_skills_from_job, trending_from_jobs


DATA_PATH = Path(__file__).resolve().parent / "data" / "jobs.json"

with DATA_PATH.open("r", encoding="utf-8") as f:
    JOBS = json.load(f)


def _skills_from_live_job(job: dict) -> list[str]:
    """Skills for scoring: whitelist tech from title/description plus any API-provided tags."""
    found = extract_technical_skills_from_job(job)
    for s in job.get("skills") or []:
        if isinstance(s, str) and s.strip():
            found.add(s.strip())
    if found:
        return list(found)
    title = str(job.get("title") or "")
    words = re.findall(r"[A-Za-z][A-Za-z0-9+.#-]{1,}", title)
    skip = {
        "senior", "junior", "lead", "manager", "director", "remote", "full", "time", "part",
        "the", "and", "for", "with", "our", "global",
    }
    out = [w for w in words if w.lower() not in skip][:8]
    raw = out if out else ["Role-specific requirements"]
    return filter_skill_list(raw) or ["Role-specific requirements"]


def _analyze_live_jobs(user_skill_set: set[str], job_results: list) -> list:
    results = []
    for job in job_results[:50]:
        display_skills = _skills_from_live_job(job)
        matched_skills: list[str] = []
        missing_skills: list[str] = []
        for disp in display_skills:
            n = disp.lower().strip()
            if n in user_skill_set:
                matched_skills.append(disp)
            else:
                missing_skills.append(disp)
        matched_skills = filter_skill_list(matched_skills)
        missing_skills = filter_skill_list(missing_skills)
        total = max(len(matched_skills) + len(missing_skills), 1)
        match_score = round((len(matched_skills) / total) * 100, 2)
        results.append(
            {
                "job_id": str(job.get("job_id", "")),
                "title": str(job.get("title") or "Role"),
                "company": str(job.get("company") or "Unknown"),
                "match_score": match_score,
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
            }
        )
    results.sort(key=lambda item: item["match_score"], reverse=True)
    return results[:10]


def analyze(user_skills: list, job_results: list | None = None) -> list:
    user_skill_set = {str(skill).strip().lower() for skill in user_skills if str(skill).strip()}
    if not user_skill_set:
        return []

    if isinstance(job_results, list) and len(job_results) > 0:
        live = _analyze_live_jobs(user_skill_set, job_results)
        if live:
            return live

    results = []

    for job in JOBS:
        job_skills = job.get("skills", [])
        total_job_skills = len(job_skills)
        if total_job_skills == 0:
            continue

        matched_skills = []
        missing_skills = []

        for skill in job_skills:
            normalized_skill = str(skill).strip().lower()
            if normalized_skill in user_skill_set:
                matched_skills.append(skill)
            else:
                missing_skills.append(skill)

        matched_skills = filter_skill_list(matched_skills)
        missing_skills = filter_skill_list(missing_skills)
        total_effective = len(matched_skills) + len(missing_skills)
        if total_effective == 0:
            continue
        matched_count = len(matched_skills)
        match_score = (matched_count / total_effective) * 100
        if match_score == 0:
            continue

        results.append(
            {
                "job_id": str(job.get("job_id", "")),
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "match_score": round(match_score, 2),
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
            }
        )

    results.sort(key=lambda item: item["match_score"], reverse=True)
    if results:
        return results[:10]

    # Fallback: if none of the entered skills match the dataset vocabulary,
    # still return jobs so the UI can show actionable missing-skill guidance.
    fallback = []
    for job in JOBS[:10]:
        job_skills = filter_skill_list(
            [str(skill).strip() for skill in job.get("skills", []) if str(skill).strip()]
        )
        fallback.append(
            {
                "job_id": str(job.get("job_id", "")),
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "match_score": 0.0,
                "matched_skills": [],
                "missing_skills": job_skills,
            }
        )

    return fallback


def get_trending(top_n: int = 15, user_skills: list | None = None) -> list:
    """
    Technical skills only: parsed from live Adzuna job titles + descriptions
    against a whitelist. Does not use legacy Kaggle `skills` categories.
    Falls back to the same extraction on static jobs (title/description only).
    """
    domain = detect_skill_domain(user_skills)
    search_q = domain_job_search_query(domain)
    result = fetch_jobs(search_q, "india", results=50)
    jobs = result.get("jobs") or []
    trending = trending_from_jobs(jobs, top_n=top_n * 2)
    trending = prioritize_trending_for_domain(trending, domain, top_n)
    if trending:
        print(
            f"Trending skills: {len(trending)} entries (domain={domain}) from job fetch "
            f"(source={result.get('source', '?')}, jobs={len(jobs)})"
        )
        return trending

    # No whitelist hits from live/fallback fetch — try local JSON titles (no category fields)
    trending = trending_from_jobs(JOBS, top_n=top_n * 2)
    trending = prioritize_trending_for_domain(trending, domain, top_n)
    if trending:
        print(f"Trending skills: fallback static titles only, {len(trending)} entries")
        return trending

    return []
