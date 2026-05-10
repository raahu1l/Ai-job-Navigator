import json
import re
from pathlib import Path

from job_fetcher import fetch_jobs
from skill_domain import (
    DOMAIN_DESIGN,
    DOMAIN_FINANCE,
    DOMAIN_HR,
    DOMAIN_MARKETING,
    DOMAIN_SALES,
    DOMAIN_TECH,
    DOMAIN_GENERAL,
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

# Title hints that a role plausibly belongs to the user's domain (loose, for gating noise).
_TECH_TITLE_POSITIVE = (
    "engineer", "developer", "software", "devops", "programmer", "architect",
    "scientist", "sre", "cloud", "backend", "frontend", "full stack", "fullstack",
    "java", "python", "react", "node", "data engineer", "data scientist",
    "machine learning", "ml engineer", "ai engineer", "platform", "product",
    "technical", "dba", "database", "ios", "android", "qa", "quality assurance",
    "test automation", "security engineer", "network engineer", "support engineer",
    "systems", "it ", " tech", "digital", "analyst", "stack", "kubernetes",
    "docker", "aws", "azure", "scrum", "agile", "product manager", "program manager",
    "project manager",
)
_TECH_TITLE_CONFLICT = (
    "soil", "agricultur", "agronom", "dairy", "poultry", "livestock", "fertilizer",
    "farm ", "farming", "veterinar", "crop ", "tractor", "irrigation", "husbandry",
)
# Drop obvious non-professional-office verticals unless the user already matches strongly.
_NOISE_TITLE_MARKERS = (
    "soil ", "soil market", "agricultur", "agronom", "poultry", "fertilizer",
    "livestock", "dairy farm", "crop science", "tractor", "irrigation",
)
_MARKETING_TITLE_POSITIVE = (
    "marketing", "brand", "seo", "sem", "growth", "content", "digital", "campaign",
    "social media", "crm", "communications", "copywriter", "performance marketing",
    "demand gen", "product marketing", "b2b marketing",
)
_MARKETING_TITLE_CONFLICT = (
    "software engineer", "backend developer", "devops engineer", "java developer",
    "embedded engineer", "kernel", "firmware", "sre ",
)
_FINANCE_TITLE_POSITIVE = (
    "finance", "financial", "accountant", "accounting", "fp&a", "fp a", "treasury",
    "audit", "controller", "cfo", "investment", "risk", "tax", "payroll", "bookkeeper",
)
_FINANCE_TITLE_CONFLICT = (
    "software engineer", "frontend developer", "devops", "embedded", "mechanical engineer",
)
_SALES_TITLE_POSITIVE = (
    "sales", "business development", "account executive", "account manager", "bdr", "sdr",
    "revenue", "commercial", "enterprise sales", "inside sales",
)
_HR_TITLE_POSITIVE = (
    "human resources", "hr ", "hrbp", "people ", "talent", "recruiter", "recruitment",
)
_DESIGN_TITLE_POSITIVE = (
    "designer", "ux", "ui", "user experience", "figma", "visual", "creative", "product design",
)

_MIN_COMPOSITE_SCORE = 10.0
_HIT_BONUS_CAP = 30.0
_HIT_BONUS_PER_SKILL = 10.0


def _user_has_required_skill(
    disp: str,
    user_skill_keys: set[str],
    skills_list: list[str],
) -> bool:
    """Case-insensitive match: normalized equality or substring either way (user vs required)."""
    need = normalize_skill_key(disp)
    if need and need in user_skill_keys:
        return True
    d = str(disp).strip().lower()
    if not d:
        return False
    for us in skills_list:
        u = str(us).strip().lower()
        if not u:
            continue
        if d in u or u in d:
            return True
    return False


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


def _job_text_blob(job: dict) -> str:
    return f"{job.get('title', '')} {job.get('description', '')}".lower()


def _skill_mentioned_in_blob_lower(skill_raw: str, blob_lower: str) -> bool:
    s = str(skill_raw).strip().lower()
    if len(s) < 2:
        return False
    if len(s) <= 3:
        return bool(re.search(rf"(?<![a-z0-9]){re.escape(s)}(?![a-z0-9])", blob_lower))
    return s in blob_lower


def _user_skill_presence_hits(user_skills: list[str], blob_lower: str) -> int:
    """Count how many distinct user skills appear in title+description (substring / word-safe)."""
    hits = 0
    for raw in user_skills:
        if _skill_mentioned_in_blob_lower(raw, blob_lower):
            hits += 1
    return hits


def _title_lower(job: dict) -> str:
    return str(job.get("title") or "").lower()


def _should_drop_offtopic(
    domain: str,
    title_l: str,
    *,
    user_hits: int,
    match_score: float,
    n_matched: int,
) -> bool:
    """Drop obvious cross-domain noise when there is no skill signal."""
    if user_hits >= 1 or n_matched >= 1 or match_score >= 15:
        return False

    if domain == DOMAIN_TECH:
        if any(c in title_l for c in _TECH_TITLE_CONFLICT):
            return True
        if not any(p in title_l for p in _TECH_TITLE_POSITIVE):
            return True

    if domain == DOMAIN_MARKETING:
        if any(c in title_l for c in _MARKETING_TITLE_CONFLICT) and not any(
            p in title_l for p in _MARKETING_TITLE_POSITIVE
        ):
            return True
        if not any(p in title_l for p in _MARKETING_TITLE_POSITIVE):
            return True

    if domain == DOMAIN_FINANCE:
        if any(c in title_l for c in _FINANCE_TITLE_CONFLICT) and not any(
            p in title_l for p in _FINANCE_TITLE_POSITIVE
        ):
            return True
        if not any(p in title_l for p in _FINANCE_TITLE_POSITIVE):
            return True

    if domain == DOMAIN_SALES:
        if not any(p in title_l for p in _SALES_TITLE_POSITIVE):
            return True

    if domain == DOMAIN_HR:
        if not any(p in title_l for p in _HR_TITLE_POSITIVE):
            return True

    if domain == DOMAIN_DESIGN:
        if not any(p in title_l for p in _DESIGN_TITLE_POSITIVE):
            return True

    # Mixed / general: only remove hard tech conflict titles with zero signal
    if domain == DOMAIN_GENERAL:
        if any(c in title_l for c in _TECH_TITLE_CONFLICT) and user_hits == 0 and match_score < 5:
            return True

    return False


def _analyze_live_jobs(
    user_skills_list: list[str],
    user_skill_keys: set[str],
    job_results: list,
) -> list:
    user_domain = detect_skill_domain(user_skills_list)
    results: list[dict] = []

    for job in job_results:
        if not isinstance(job, dict):
            continue

        blob = _job_text_blob(job)
        required_skills = _required_skills_from_job(job)
        if not required_skills:
            inferred: list[str] = []
            for s in user_skills_list:
                if _skill_mentioned_in_blob_lower(s, blob):
                    inferred.append(s)
            required_skills = filter_skill_list(inferred)[:12]

        matched_skills: list[str] = []
        missing_skills: list[str] = []

        if not required_skills:
            match_score = 0.0
        else:
            for disp in required_skills:
                if _user_has_required_skill(disp, user_skill_keys, skills_list):
                    matched_skills.append(disp)
                else:
                    missing_skills.append(disp)

            total_req = len(matched_skills) + len(missing_skills)
            if missing_skills:
                match_score = round((len(matched_skills) / total_req) * 100, 2) if total_req else 0.0
            else:
                match_score = 100.0

        user_hits = _user_skill_presence_hits(user_skills_list, blob)
        title_l = _title_lower(job)

        # No extractable requirements and no evidence user skills appear → skip
        if not required_skills and user_hits == 0:
            continue

        hit_bonus = min(_HIT_BONUS_CAP, _HIT_BONUS_PER_SKILL * float(user_hits))
        composite = min(100.0, match_score + hit_bonus)

        if composite < _MIN_COMPOSITE_SCORE and len(matched_skills) == 0 and user_hits == 0:
            continue

        if _should_drop_offtopic(
            user_domain,
            title_l,
            user_hits=user_hits,
            match_score=match_score,
            n_matched=len(matched_skills),
        ):
            continue

        if any(m in title_l for m in _NOISE_TITLE_MARKERS):
            if user_hits < 1 and len(matched_skills) < 1 and match_score < 28:
                continue

        display_score = round(composite, 2)

        results.append(
            {
                "job_id": str(job.get("job_id", "")),
                "title": str(job.get("title") or "Role"),
                "company": str(job.get("company") or "Unknown"),
                "match_score": display_score,
                "required_skills": required_skills,
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
            }
        )

    results.sort(key=lambda item: item["match_score"], reverse=True)
    return [_sanitize_job_result(r) for r in results]


_NO_MATCH_MSG = (
    "No matching jobs found. Try different location or broader skills like 'Python' or 'Java'."
)


def analyze(user_skills: list, job_results: list | None = None) -> list | dict:
    skills_list = [str(s).strip() for s in (user_skills if isinstance(user_skills, list) else []) if str(s).strip()]
    user_skill_keys = expand_user_skill_match_keys(skills_list)
    if not user_skill_keys:
        return {"results": [], "message": _NO_MATCH_MSG}

    # Live payloads from Adzuna (or upstream) must never fall through to static Kaggle categories.
    if isinstance(job_results, list) and len(job_results) > 0:
        n = len(job_results)
        print("Using LIVE Adzuna analysis")
        print(f"  (live job_results: {n})")
        live = _analyze_live_jobs(skills_list, user_skill_keys, job_results)
        live = [j for j in live if (j.get("match_score") or 0) > 0]
        if not live:
            return {"results": [], "message": _NO_MATCH_MSG}
        return live

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
            if _user_has_required_skill(skill, user_skill_keys, skills_list):
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
    results = [r for r in results if (r.get("match_score") or 0) > 0]
    if results:
        return [_sanitize_job_result(r) for r in results[:40]]

    return {"results": [], "message": _NO_MATCH_MSG}


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

    print("Trending: Fallback dataset activated (local JSON titles for whitelist enrichment)")
    trending = trending_from_jobs(JOBS, top_n=top_n * 2)
    trending = prioritize_trending_for_domain(trending, domain, top_n)
    trending = filter_trending_results(trending)
    if trending:
        print(f"Trending skills: fallback static titles only, {len(trending)} entries")
        return trending

    return []
