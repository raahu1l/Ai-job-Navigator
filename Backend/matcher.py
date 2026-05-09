import json
from pathlib import Path

from job_fetcher import fetch_jobs
from technical_trending import trending_from_jobs


DATA_PATH = Path(__file__).resolve().parent / "data" / "jobs.json"

with DATA_PATH.open("r", encoding="utf-8") as f:
    JOBS = json.load(f)


def analyze(user_skills: list) -> list:
    user_skill_set = {str(skill).strip().lower() for skill in user_skills if str(skill).strip()}
    if not user_skill_set:
        return []

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

        matched_count = len(matched_skills)
        match_score = (matched_count / total_job_skills) * 100
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
        job_skills = [str(skill).strip() for skill in job.get("skills", []) if str(skill).strip()]
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


def get_trending(top_n: int = 15) -> list:
    """
    Technical skills only: parsed from live Adzuna job titles + descriptions
    against a whitelist. Does not use legacy Kaggle `skills` categories.
    Falls back to the same extraction on static jobs (title/description only).
    """
    result = fetch_jobs(
        "software developer data engineer full stack",
        "india",
        results=50,
    )
    jobs = result.get("jobs") or []
    trending = trending_from_jobs(jobs, top_n=top_n)
    if trending:
        print(
            f"Trending skills: {len(trending)} entries from job fetch "
            f"(source={result.get('source', '?')}, jobs={len(jobs)})"
        )
        return trending

    # No whitelist hits from live/fallback fetch — try local JSON titles (no category fields)
    trending = trending_from_jobs(JOBS, top_n=top_n)
    if trending:
        print(f"Trending skills: fallback static titles only, {len(trending)} entries")
        return trending

    return []
