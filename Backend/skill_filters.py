"""
Global blacklist for vague job-taxonomy / domain labels.
Apply anywhere skills are shown or aggregated (analysis, gaps, trending, extraction).
"""
from __future__ import annotations

# Normalized lowercase keys; matching is exact on normalized skill string.
GLOBAL_SKILL_BLACKLIST: frozenset[str] = frozenset(
    {
        "engineering",
        "information technology",
        "information technologies",
        "it",
        "technology",
        "technologies",
        "tech",
        "industry",
        "industries",
        "department",
        "technology sector",
        "organization",
        "organizational",
        "company",
        "consulting",
        "consultant",
        "professional services",
        "business",
        "management",
        "leadership",
        "strategy",
        "operations",
        "general business",
        "business development",
        "analyst",
        "administration",
        "human resources",
        "hr",
        "staffing",
        "employment",
        "corporate",
        "enterprise",
        "sector",
        "services",
        "solutions",
        "innovation",
        "digital transformation",
        "information systems",
        "computer science",
        "stem",
    }
)


def normalize_skill_key(skill: str) -> str:
    return str(skill).strip().lower()


def is_blocked_skill(skill: str) -> bool:
    if skill is None:
        return True
    s = str(skill).strip()
    if not s:
        return True
    return normalize_skill_key(s) in GLOBAL_SKILL_BLACKLIST


def filter_skill_list(skills: list | None) -> list[str]:
    """Drop blocked skills; preserve order and original casing."""
    if not skills:
        return []
    out: list[str] = []
    for s in skills:
        if not isinstance(s, str):
            continue
        if is_blocked_skill(s):
            continue
        out.append(s.strip())
    return out


def filter_skill_set(skills: set[str]) -> set[str]:
    return {s for s in skills if not is_blocked_skill(s)}
