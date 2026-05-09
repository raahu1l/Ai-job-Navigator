"""
Infer user career domain from skill strings for market/trending/job-fetch bias.
"""
from __future__ import annotations

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
    DOMAIN_DESIGN: ("UI/UX", "Figma", "Communication", "Marketing", "Research"),
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


def domain_job_search_query(domain: str) -> str:
    return DOMAIN_JOB_SEARCH_QUERY.get(domain, DOMAIN_JOB_SEARCH_QUERY[DOMAIN_GENERAL])


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
