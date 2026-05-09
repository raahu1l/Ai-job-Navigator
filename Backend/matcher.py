import json
import re
from pathlib import Path

from job_fetcher import fetch_jobs
from skill_domain import (
    detect_skill_domain,
    domain_job_search_query,
    prioritize_trending_for_domain,
)
from skill_filters import (
    filter_skill_list,
    filter_trending_results,
    is_blocked_skill,
    normalize_skill_key,
)
from technical_trending import extract_technical_skills_from_job, trending_from_jobs


DATA_PATH = Path(__file__).resolve().parent / "data" / "jobs.json"

with DATA_PATH.open("r", encoding="utf-8") as f:
    JOBS = json.load(f)

# Normalized synonyms: if user lists any variant, match any required skill in same group.
_USER_SKILL_ALIAS_GROUPS: tuple[frozenset[str], ...] = (
    frozenset({"microsoft excel", "excel"}),
    frozenset({"google cloud", "gcp"}),
    frozenset({"javascript", "js"}),
    frozenset({"typescript", "ts"}),
    frozenset({"aws", "amazon web services"}),
    frozenset({"kubernetes", "k8s"}),
    frozenset({"machine learning", "ml"}),
    frozenset({"artificial intelligence", "ai"}),
)


def expand_user_skill_match_keys(user_skills: list) -> set[str]:
    """Lowercase-normalized skill keys plus alias expansion for equitable matching."""
    base = {normalize_skill_key(str(s)) for s in user_skills if str(s).strip()}
    base.discard("")
    out = set(base)
    for group in _USER_SKILL_ALIAS_GROUPS:
        if base & group:
            out |= group
    return out


def _sanitize_job_result(row: dict) -> dict:
    """Apply global skill filter + dedupe to API job rows."""
    return {
        **row,
        "required_skills": filter_skill_list(row.get("required_skills")),
        "matched_skills": filter_skill_list(row.get("matched_skills")),
        "missing_skills": filter_skill_list(row.get("missing_skills")),
    }


def _required_skills_from_job(job: dict) -> list[str]:
    """Extract required skills from title + description (whitelist) plus API tags; may be empty."""
    found = extract_technical_skills_from_job(job)
    for s in job.get("skills") or []:
        if isinstance(s, str) and s.strip():
            found.add(s.strip())
    merged = filter_skill_list(list(found))
    if merged:
        return merged
    title = str(job.get("title") or "")
    words = re.findall(r"[A-Za-z][A-Za-z0-9+.#-]{1,}", title)
    skip = {
        "senior", "junior", "lead", "manager", "director", "remote", "full", "time", "part",
        "the", "and", "for", "with", "our", "global",
    }
    out: list[str] = []
    for w in words:
        if w.lower() in skip or is_blocked_skill(w):
            continue
        out.append(w)
        if len(out) >= 8:
            break
    return filter_skill_list(out)


def _analyze_live_jobs(user_skill_keys: set[str], job_results: list) -> list:
    results = []
    for job in job_results[:50]:
        required_skills = _required_skills_from_job(job)
        matched_skills: list[str] = []
        missing_skills: list[str] = []

        if not required_skills:
            match_score = 0.0
        else:
            for disp in required_skills:
                need = normalize_skill_key(disp)
                if need in user_skill_keys:
                    matched_skills.append(disp)
                else:
                    missing_skills.append(disp)

            total_req = len(matched_skills) + len(missing_skills)
            if missing_skills:
                match_score = round((len(matched_skills) / total_req) * 100, 2) if total_req else 0.0
            else:
                # 100% only when nothing is missing vs extracted requirements.
                match_score = 100.0

        results.append(
            {
                "job_id": str(job.get("job_id", "")),
                "title": str(job.get("title") or "Role"),
                "company": str(job.get("company") or "Unknown"),
                "match_score": match_score,
                "required_skills": required_skills,
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
            }
        )
    results.sort(key=lambda item: item["match_score"], reverse=True)
    return [_sanitize_job_result(r) for r in results]


def analyze(user_skills: list, job_results: list | None = None) -> list:
    user_skill_keys = expand_user_skill_match_keys(user_skills if isinstance(user_skills, list) else [])
    if not user_skill_keys:
        return []

    # Live payloads from Adzuna (or upstream) must never fall through to static Kaggle categories.
    if isinstance(job_results, list) and len(job_results) > 0:
        n = len(job_results)
        print("Using LIVE Adzuna analysis")
        print(f"  (live job_results: {n})")
        return _analyze_live_jobs(user_skill_keys, job_results)

    print("Using FALLBACK static dataset")
    results = []

    for job in JOBS:
        job_skills = job.get("skills", [])
        total_job_skills = len(job_skills)
        if total_job_skills == 0:
            continue

        required_skills = filter_skill_list(
            [str(skill).strip() for skill in job_skills if str(skill).strip()]
        )
        matched_skills: list[str] = []
        missing_skills: list[str] = []

        for skill in required_skills:
            if normalize_skill_key(skill) in user_skill_keys:
                matched_skills.append(skill)
            else:
                missing_skills.append(skill)

        matched_skills = filter_skill_list(matched_skills)
        missing_skills = filter_skill_list(missing_skills)
        total_effective = len(matched_skills) + len(missing_skills)
        if total_effective == 0:
            continue
        if missing_skills:
            match_score = round((len(matched_skills) / total_effective) * 100, 2)
        else:
            match_score = 100.0
        if missing_skills and match_score == 0:
            continue

        results.append(
            {
                "job_id": str(job.get("job_id", "")),
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "match_score": match_score,
                "required_skills": required_skills,
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
            }
        )

    results.sort(key=lambda item: item["match_score"], reverse=True)
    if results:
        # Cap UI payload on static corpus (can be large); live path stays aligned with fetched batch size.
        return [_sanitize_job_result(r) for r in results[:40]]

    # Fallback: if none of the entered skills match the dataset vocabulary,
    # still return jobs so the UI can show actionable missing-skill guidance.
    fallback = []
    for job in JOBS[:10]:
        job_skills = filter_skill_list(
            [str(skill).strip() for skill in job.get("skills", []) if str(skill).strip()]
        )
        fallback.append(
            _sanitize_job_result(
                {
                    "job_id": str(job.get("job_id", "")),
                    "title": job.get("title", ""),
                    "company": job.get("company", ""),
                    "match_score": 0.0,
                    "required_skills": job_skills,
                    "matched_skills": [],
                    "missing_skills": job_skills,
                }
            )
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
    src = result.get("source", "?")
    if src == "adzuna":
        print("Trending: Using LIVE Adzuna analysis")
    else:
        print(f"Trending: Using FALLBACK static dataset (fetch source={src})")

    trending = trending_from_jobs(jobs, top_n=top_n * 2)
    trending = prioritize_trending_for_domain(trending, domain, top_n)
    trending = filter_trending_results(trending)
    if trending:
        print(
            f"Trending skills: {len(trending)} entries (domain={domain}) "
            f"(source={src}, jobs={len(jobs)})"
        )
        return trending

    # No whitelist hits — try raw static JSON titles/descriptions only (no Kaggle categories)
    print("Trending: Fallback dataset activated (local JSON titles for whitelist enrichment)")
    trending = trending_from_jobs(JOBS, top_n=top_n * 2)
    trending = prioritize_trending_for_domain(trending, domain, top_n)
    trending = filter_trending_results(trending)
    if trending:
        print(f"Trending skills: fallback static titles only, {len(trending)} entries")
        return trending

    return []
