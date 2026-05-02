import json
from collections import Counter
from pathlib import Path


DATA_PATH = Path(__file__).resolve().parent / "data" / "jobs.json"

with DATA_PATH.open("r", encoding="utf-8") as f:
    JOBS = json.load(f)


def analyze(user_skills: list) -> list:
    user_skill_set = {str(skill).strip().lower() for skill in user_skills if str(skill).strip()}
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
    return results[:10]


def get_trending(top_n: int = 15) -> list:
    skill_counter = Counter()
    skill_display = {}

    for job in JOBS:
        job_skills = job.get("skills", [])
        unique_job_skills = {str(skill).strip() for skill in job_skills if str(skill).strip()}

        for skill in unique_job_skills:
            normalized_skill = skill.lower()
            skill_counter[normalized_skill] += 1
            if normalized_skill not in skill_display:
                skill_display[normalized_skill] = skill

    trending = []
    for normalized_skill, count in skill_counter.most_common(top_n):
        trending.append({"skill": skill_display[normalized_skill], "count": count})

    return trending
