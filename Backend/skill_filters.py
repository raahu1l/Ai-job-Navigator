"""
Global blacklist for vague job-taxonomy / domain labels.
Apply anywhere skills are shown or aggregated (analysis, gaps, trending, extraction).

Matching uses normalize_skill_key() (trim, lowercase, collapse whitespace) for lookups.
Meaningful broad skills like Sales, Finance, Marketing, Communication stay allowed.
"""
from __future__ import annotations

import re
from typing import Any

# Normalized keys; entries must be lowercase, single-space collapsed.
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
        "research",
        "researcher",
        "researchers",
        "r&d",
        "r & d",
        "general",
        "professional",
    }
)


_WS_RE = re.compile(r"\s+")


def normalize_skill_key(skill: str) -> str:
    s = str(skill).strip().lower()
    if not s:
        return ""
    return _WS_RE.sub(" ", s)


def is_blocked_skill(skill: str) -> bool:
    if skill is None:
        return True
    key = normalize_skill_key(str(skill))
    if not key:
        return True
    return key in GLOBAL_SKILL_BLACKLIST


def filter_skill_list(skills: list | None) -> list[str]:
    """Drop blocked skills, dedupe case-insensitively; preserve first-seen casing."""
    if not skills:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for s in skills:
        if not isinstance(s, str):
            continue
        key = normalize_skill_key(s)
        if not key or key in seen:
            continue
        if is_blocked_skill(s):
            continue
        seen.add(key)
        out.append(s.strip())
    return out


def filter_skill_set(skills: set[str]) -> set[str]:
    return set(filter_skill_list(list(skills)))


def filter_trending_results(items: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Sanitize trending payloads: blocked skills removed, deduped by normalized name."""
    if not items:
        return []
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for it in items:
        if not isinstance(it, dict):
            continue
        sk = it.get("skill")
        if not isinstance(sk, str):
            continue
        key = normalize_skill_key(sk)
        if not key or key in seen or is_blocked_skill(sk):
            continue
        seen.add(key)
        out.append({"skill": sk.strip(), "count": it.get("count", 0)})
    return out
