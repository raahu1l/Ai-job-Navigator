"""
Infer user career domain from skill strings for market/trending/job-fetch bias.
"""
from __future__ import annotations

import re
from collections import Counter


def normalize_skill_key(s: str) -> str:
    return str(s).strip().lower()


DOMAIN_TECH = "tech"
DOMAIN_FINANCE = "finance"
DOMAIN_SALES = "sales"
DOMAIN_MARKETING = "marketing"
DOMAIN_HR = "hr"
DOMAIN_DESIGN = "design"
DOMAIN_GENERAL = "general"

DOMAIN_DISPLAY_LABELS: dict[str, str] = {
    DOMAIN_TECH: "Technology",
    DOMAIN_FINANCE: "Finance & accounting",
    DOMAIN_SALES: "Sales",
    DOMAIN_MARKETING: "Marketing",
    DOMAIN_HR: "Human resources",
    DOMAIN_DESIGN: "Design",
    DOMAIN_GENERAL: "General / mixed",
}


def domain_display_label(domain: str) -> str:
    return DOMAIN_DISPLAY_LABELS.get(domain, DOMAIN_DISPLAY_LABELS[DOMAIN_GENERAL])


# Short context line for demand UI (not a "skill" label).
DOMAIN_MARKET_CONTEXT_SUBTITLE: dict[str, str] = {
    DOMAIN_TECH: "Based on live software & data hiring signals",
    DOMAIN_FINANCE: "Based on live finance & analyst hiring signals",
    DOMAIN_SALES: "Based on live sales hiring signals",
    DOMAIN_MARKETING: "Based on live marketing hiring signals",
    DOMAIN_HR: "Based on live people & recruiting hiring signals",
    DOMAIN_DESIGN: "Based on live design hiring signals",
    DOMAIN_GENERAL: "Based on live hiring signals in your search",
}


def domain_market_subtitle(domain: str) -> str:
    return DOMAIN_MARKET_CONTEXT_SUBTITLE.get(
        domain, DOMAIN_MARKET_CONTEXT_SUBTITLE[DOMAIN_GENERAL]
    )


# Noun phrase for opportunity lines (avoid "sample" / "listing" wording).
DOMAIN_ROLE_MATCH_NOUN: dict[str, str] = {
    DOMAIN_TECH: "technical",
    DOMAIN_FINANCE: "analyst and finance",
    DOMAIN_SALES: "sales",
    DOMAIN_MARKETING: "marketing",
    DOMAIN_HR: "people-ops",
    DOMAIN_DESIGN: "design",
    DOMAIN_GENERAL: "matching",
}


def domain_role_match_noun(domain: str) -> str:
    return DOMAIN_ROLE_MATCH_NOUN.get(domain, DOMAIN_ROLE_MATCH_NOUN[DOMAIN_GENERAL])


# (domain, tuple of lowercase substrings to match against each user skill)
_DOMAIN_TRIGGERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        DOMAIN_FINANCE,
        (
            "finance", "financial", "accounting", "accountant", "fp&a", "fp a",
            "risk", "audit", "cfa", "excel", "bookkeeping", "treasury", "tax",
            "budget", "investment", "banking",
        ),
    ),
    (
        DOMAIN_SALES,
        (
            "sales", "crm", "negotiation", "business development", "sdr", "bdr",
            "account executive", "revenue", "pipeline",
        ),
    ),
    (
        DOMAIN_MARKETING,
        (
            "marketing", "seo", "sem", "content", "brand", "growth", "campaign",
            "social media", "copywriting", "demand gen",
        ),
    ),
    (
        DOMAIN_HR,
        (
            "hr", "human resources", "recruiting", "recruitment", "talent",
            "people ops", "compensation", "onboarding",
        ),
    ),
    (
        DOMAIN_DESIGN,
        (
            "design", "ui/ux", "ux", "ui", "figma", "sketch", "prototype",
            "visual", "creative",
        ),
    ),
    (
        DOMAIN_TECH,
        (
            "python", "java", "javascript", "typescript", "react", "node",
            "sql", "aws", "azure", "gcp", "docker", "kubernetes", "devops",
            "engineer", "developer", "programming", "software", "data engineer",
            "machine learning", "ml", "ai", "cloud", "backend", "frontend",
            "full stack", "git", "api",
        ),
    ),
)

# Adzuna search keywords biased toward domain-relevant job postings
DOMAIN_JOB_SEARCH_QUERY: dict[str, str] = {
    DOMAIN_TECH: "software developer data engineer python aws react full stack",
    DOMAIN_FINANCE: "financial analyst accountant fp&a risk excel modeling audit",
    DOMAIN_SALES: "sales representative account executive crm business development",
    DOMAIN_MARKETING: "marketing manager seo content strategy digital marketing analytics",
    DOMAIN_HR: "human resources recruiter talent acquisition people operations",
    DOMAIN_DESIGN: "ux designer ui designer product designer figma creative",
    DOMAIN_GENERAL: "professional skills project coordinator operations specialist",
}


# Skills to surface first in trending when domain matches (must overlap whitelist where possible)
DOMAIN_TRENDING_HINTS: dict[str, tuple[str, ...]] = {
    DOMAIN_TECH: ("Python", "AWS", "React", "SQL", "Docker", "Kubernetes", "JavaScript"),
    DOMAIN_FINANCE: ("Excel", "Finance", "SQL", "Power BI", "Risk Analysis", "Financial Modeling"),
    DOMAIN_MARKETING: ("Marketing", "SEO", "Analytics", "CRM", "Communication", "Sales"),
    DOMAIN_SALES: ("Sales", "CRM", "Negotiation", "Communication", "Marketing"),
    DOMAIN_HR: ("Recruiting", "Communication", "HR", "Negotiation", "Excel"),
    DOMAIN_DESIGN: ("UI/UX", "Figma", "Communication", "Marketing", "User Research"),
    DOMAIN_GENERAL: ("Communication", "Excel", "Project Management", "SQL", "Marketing"),
}


def detect_skill_domain(user_skills: list | None) -> str:
    if not user_skills:
        return DOMAIN_GENERAL
    scores: Counter[str] = Counter()
    for raw in user_skills:
        low = str(raw).strip().lower()
        if not low:
            continue
        for domain, triggers in _DOMAIN_TRIGGERS:
            for t in triggers:
                if t in low or low in t:
                    scores[domain] += 1
                    break
    if not scores:
        return DOMAIN_GENERAL
    return scores.most_common(1)[0][0]


def detect_domain_from_job_text(job: dict | None) -> str:
    """Infer posting domain from title + description (same triggers as user skills)."""
    if not isinstance(job, dict):
        return DOMAIN_GENERAL
    blob = f"{job.get('title', '')} {job.get('description', '')}".strip().lower()
    if not blob:
        return DOMAIN_GENERAL
    scores: Counter[str] = Counter()
    for domain, triggers in _DOMAIN_TRIGGERS:
        for t in triggers:
            if t in blob:
                scores[domain] += 1
    if not scores:
        return DOMAIN_GENERAL
    return scores.most_common(1)[0][0]


def domain_job_search_query(domain: str) -> str:
    return DOMAIN_JOB_SEARCH_QUERY.get(domain, DOMAIN_JOB_SEARCH_QUERY[DOMAIN_GENERAL])


# Role-oriented Adzuna "what" terms (broaden recall beyond raw skill tokens alone).
_DOMAIN_ROLE_BOOST: dict[str, str] = {
    DOMAIN_TECH: (
        "software engineer backend developer full stack java python devops engineer "
        "cloud engineer data engineer site reliability"
    ),
    DOMAIN_FINANCE: (
        "financial analyst accountant fp&a finance analyst risk analyst "
        "treasury audit modeling"
    ),
    DOMAIN_SALES: (
        "sales executive account manager business development sdr bdr "
        "account executive revenue"
    ),
    DOMAIN_MARKETING: (
        "digital marketing marketing manager seo specialist growth marketing "
        "content strategist crm marketing performance marketing"
    ),
    DOMAIN_HR: (
        "human resources recruiter talent acquisition people partner hr business partner "
        "people operations"
    ),
    DOMAIN_DESIGN: (
        "ux designer ui designer product designer visual designer figma "
        "user experience creative designer"
    ),
    DOMAIN_GENERAL: (
        "specialist analyst coordinator project manager operations associate"
    ),
}


def domain_role_search_boost(domain: str) -> str:
    return _DOMAIN_ROLE_BOOST.get(domain, _DOMAIN_ROLE_BOOST[DOMAIN_GENERAL])


def normalize_user_skills_list(raw_skills: list | None, keywords_fallback: str = "") -> list[str]:
    """Flatten skills from UI or comma-separated keywords; preserves order, dedupes.
    Handles edge cases: multiple commas, whitespace, empty strings."""
    out: list[str] = []
    seen: set[str] = set()
    if raw_skills and isinstance(raw_skills, list):
        for item in raw_skills:
            for part in str(item).replace(";", ",").split(","):
                s = part.strip()
                if not s:
                    continue
                k = normalize_skill_key(s)
                if k and k not in seen:
                    seen.add(k)
                    out.append(s)
    elif keywords_fallback and str(keywords_fallback).strip():
        raw = str(keywords_fallback).strip()
        if "," in raw or ";" in raw:
            chunks = re.split(r"[,;]+", raw)
        else:
            chunks = raw.split()
        for part in chunks:
            s = part.strip()
            if not s:
                continue
            k = normalize_skill_key(s)
            if k and k not in seen:
                seen.add(k)
                out.append(s)
    return out


def build_job_search_queries(user_skills: list[str]) -> list[str]:
    """
    Build focused Adzuna `what` strings from the user's actual skills.

    Adzuna can return sparse or noisy results for one long multi-skill query.
    Search several short skill+role phrases, then merge and rank the returned
    postings downstream.
    """
    skills = normalize_user_skills_list(user_skills, "")
    if not skills:
        return [domain_job_search_query(DOMAIN_GENERAL)]

    domain = detect_skill_domain(skills)
    queries: list[str] = []

    role_by_domain = {
        DOMAIN_TECH: "developer",
        DOMAIN_DESIGN: "designer",
        DOMAIN_FINANCE: "analyst",
        DOMAIN_SALES: "sales",
        DOMAIN_MARKETING: "marketing",
        DOMAIN_HR: "recruiter",
        DOMAIN_GENERAL: "specialist",
    }
    role = role_by_domain.get(domain, role_by_domain[DOMAIN_GENERAL])

    # Treat manually typed lowercase skills exactly like suggestion chips:
    # every important user skill gets a chance to fetch matching postings.
    for skill in skills[:6]:
        s = " ".join(str(skill).strip().split())
        if not s:
            continue
        q = f"{s} {role}".strip()
        if q and q not in queries:
            queries.append(q)

    # Add one broader domain query for recall. The matcher later rejects jobs
    # with no overlap, so this should not leak generic unrelated roles.
    if domain == DOMAIN_TECH:
        q = f"software engineer {' '.join(skills[:4])}".strip()
    else:
        q = f"{domain_job_search_query(domain)} {' '.join(skills[:3])}".strip()
    q = " ".join(q.split())[:120]
    if q and q not in queries:
        queries.append(q)

    return queries[:7]


def domain_market_context(domain: str) -> str:
    lines = {
        DOMAIN_TECH: (
            "User domain: TECHNOLOGY / SOFTWARE. Prioritize cloud, programming languages, "
            "frameworks, DevOps, and data engineering. Avoid generic 'technology' or 'IT' as skill names."
        ),
        DOMAIN_FINANCE: (
            "User domain: FINANCE / ACCOUNTING. Prioritize Excel, financial modeling, FP&A, "
            "risk, reporting tools, and compliance-adjacent skills. Do NOT emphasize AWS or programming "
            "unless the user listed them."
        ),
        DOMAIN_SALES: (
            "User domain: SALES / REVENUE. Prioritize CRM, pipeline, negotiation, account management, "
            "and sales tooling—not cloud architecture."
        ),
        DOMAIN_MARKETING: (
            "User domain: MARKETING / GROWTH. Prioritize SEO, analytics, content, campaigns, "
            "and marketing platforms—not backend engineering defaults."
        ),
        DOMAIN_HR: (
            "User domain: HR / PEOPLE. Prioritize recruiting, talent systems, employee relations, "
            "and communication—not software stack defaults."
        ),
        DOMAIN_DESIGN: (
            "User domain: DESIGN / UX. Prioritize design tools, research, prototyping, and collaboration—not "
            "generic engineering stacks unless listed."
        ),
        DOMAIN_GENERAL: (
            "User domain: GENERAL / MIXED. Balance actionable professional and technical skills; "
            "stay close to the user's stated skills."
        ),
    }
    return lines.get(domain, lines[DOMAIN_GENERAL])


def prioritize_trending_for_domain(
    trending: list[dict],
    domain: str,
    top_n: int,
) -> list[dict]:
    """Reorder trending items so domain-hint skills appear first when present, then by count."""
    if not trending:
        return []
    hints = DOMAIN_TRENDING_HINTS.get(domain, DOMAIN_TRENDING_HINTS[DOMAIN_GENERAL])
    hint_lower = {h.lower() for h in hints}
    by_skill = {normalize_skill_key(t["skill"]): t for t in trending}
    out: list[dict] = []
    seen: set[str] = set()
    for h in hints:
        k = h.lower()
        if k in by_skill and k not in seen:
            out.append(by_skill[k])
            seen.add(k)
    for t in trending:
        k = normalize_skill_key(t["skill"])
        if k not in seen:
            out.append(t)
            seen.add(k)
        if len(out) >= top_n:
            break
    return out[:top_n]
