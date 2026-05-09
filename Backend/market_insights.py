"""
Real skill-demand statistics from live job listings (whitelist extraction).
Used for learning-path copy — percentages are computed from fetched jobs only.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from skill_domain import detect_skill_domain, domain_display_label
from skill_filters import normalize_skill_key
from technical_trending import extract_technical_skills_from_job


def skill_demand_from_jobs(jobs: list[dict] | None) -> dict[str, Any]:
    """
    Count how many jobs mention each whitelist skill (max once per job per skill).

    Returns:
      total_jobs, skill_counts (skill -> jobs mentioning it),
      top_skills: [{ skill, jobs_with_skill, pct_of_jobs }],
      lines: readable fact lines with real counts (no hallucinated percentages).
    """
    if not jobs:
        return {
            "total_jobs": 0,
            "skill_counts": {},
            "top_skills": [],
            "facts_lines": [],
            "facts_block": "(no live jobs supplied — skill demand percentages unavailable)",
        }

    total_jobs = len(jobs)
    skill_job_hits: Counter[str] = Counter()

    for job in jobs:
        if not isinstance(job, dict):
            continue
        found = extract_technical_skills_from_job(job)
        for skill in found:
            skill_job_hits[skill] += 1

    def _pct(count: int, tot: int) -> float:
        if tot <= 0:
            return 0.0
        return round(100 * count / tot, 1)

    # Top 5 by job mention count (stable order for ties: skill name)
    ranked = sorted(skill_job_hits.items(), key=lambda x: (-x[1], x[0].lower()))[:5]
    top_skills: list[dict[str, Any]] = []
    for skill, cnt in ranked:
        pct = _pct(cnt, total_jobs)
        top_skills.append({
            "skill": skill,
            "jobs_with_skill": cnt,
            "pct_of_jobs": pct,
        })

    facts_lines: list[str] = []
    for row in top_skills:
        s, c, p = row["skill"], row["jobs_with_skill"], row["pct_of_jobs"]
        facts_lines.append(f"{s}: mentioned in {c} of {total_jobs} analyzed listings (~{p}%).")

    facts_block = "\n".join(facts_lines) if facts_lines else "No whitelist skills extracted from listings."

    return {
        "total_jobs": total_jobs,
        "skill_counts": dict(skill_job_hits),
        "top_skills": top_skills,
        "facts_lines": facts_lines,
        "facts_block": facts_block,
    }


def _find_count_for_user_skill(skill: str, skill_counts: dict[str, int]) -> tuple[str | None, int]:
    """Map user-facing missing skill label to whitelist key (exact normalized match preferred)."""
    if not skill or not skill_counts:
        return None, 0
    nk = normalize_skill_key(skill)
    for canon, cnt in skill_counts.items():
        if normalize_skill_key(canon) == nk:
            return canon, cnt
    # Partial: missing "Excel" matches "Microsoft Excel" only if substring (careful)
    for canon, cnt in skill_counts.items():
        ck = normalize_skill_key(canon)
        if nk in ck or ck in nk:
            return canon, cnt
    return None, 0


def build_market_demand_insight(
    jobs: list[dict] | None,
    missing_skills: list[str],
    *,
    total_jobs_override: int | None = None,
) -> tuple[str, list[str], dict[str, Any]]:
    """
    Compose market_demand_insight string(s) strictly from extraction counts.

    Returns:
      primary_paragraph, bullet_lines supporting copy, analytics dict for API.
    """
    demand = skill_demand_from_jobs(jobs or [])
    total = demand["total_jobs"]
    if total_jobs_override is not None:
        total = total_jobs_override
    skill_counts = demand["skill_counts"]

    bullets: list[str] = []

    # Per missing skill: real mention rate in THIS job set
    for ms in missing_skills:
        canon, cnt = _find_count_for_user_skill(ms, skill_counts)
        if total <= 0:
            continue
        if canon is None or cnt <= 0:
            bullets.append(
                f"No exact whitelist hits for '{ms}' in analyzed listings text "
                f"(skills are matched from titles/descriptions; demand may still be high but not countable here)."
            )
            continue
        pct = round(100 * cnt / total, 1)
        bullets.append(
            f"'{canon}' appears in {cnt} of {total} analyzed live listings (~{pct}%)."
        )

    # Top skills summary
    if demand["top_skills"]:
        names = ", ".join(t["skill"] for t in demand["top_skills"][:5])
        bullets.append(
            f"In this fetched set of {demand['total_jobs']} postings, highest-signal demanded skills included: {names}."
        )

    # Comparative line: missing ∩ top set
    top_names = {t["skill"] for t in demand["top_skills"]}
    overlap = []
    for ms in missing_skills:
        c, ct = _find_count_for_user_skill(ms, skill_counts)
        if c and c in top_names and ct > 0:
            overlap.append(c)
    overlap_u = []
    seen = set()
    for x in overlap:
        if x not in seen:
            seen.add(x)
            overlap_u.append(x)

    primary = ""
    if total <= 0:
        primary = "No live postings were analyzed for demand percentages in this session."
    elif overlap_u and total > 0:
        pct_union = []
        labeled = []
        for name in overlap_u[:3]:
            cnt = skill_counts.get(name, 0)
            pct = round(100 * cnt / total, 1)
            pct_union.append(pct)
            labeled.append(name)
        if labeled:
            # Jobs that contain at least one of these listed skills (union, upper bound heuristic)
            primary = (
                f"Across {total} live listings analyzed in your search: {', '.join(labeled)} rank among the strongest demand signals; "
                f"mention rates for each are shown in the lines below."
            )
    elif demand["facts_lines"]:
        primary = (
            f"Across {demand['total_jobs']} fetched live listings (titles + descriptions scanned), skill demand rankings are summarized below."
        )
    else:
        primary = "Live listings yielded few extractable whitelist skills — broaden keywords or inspect posting text format."

    if not bullets and demand["facts_lines"]:
        bullets.extend(demand["facts_lines"])

    analytics = {
        "total_live_jobs_analyzed": demand["total_jobs"],
        "top_demanded_skills": demand["top_skills"],
        "skill_jobs_count": skill_counts,
    }

    headline = primary.strip()
    if not headline and bullets:
        headline = "Skill demand breakdown from analyzed live listings:"
    if not headline:
        headline = "No quantified demand snapshot for these listings."

    return headline, bullets, analytics


def count_jobs_mentioning_any_skill(
    jobs: list[dict] | None,
    skill_labels: list[str],
) -> int:
    """How many job dicts mention at least one of the given canonical skill labels (whitelist extract)."""
    if not jobs or not skill_labels:
        return 0
    want = {normalize_skill_key(s) for s in skill_labels if isinstance(s, str) and s.strip()}
    if not want:
        return 0
    n = 0
    for job in jobs:
        if not isinstance(job, dict):
            continue
        found = extract_technical_skills_from_job(job)
        for s in found:
            if normalize_skill_key(str(s)) in want:
                n += 1
                break
    return n


def build_skill_demand_dashboard(
    user_skills: list[str] | None,
    jobs: list[dict] | None,
) -> dict[str, Any]:
    """
    Compact demand snapshot for the dashboard: domain from user skills + frequencies from live jobs only.
    """
    us = [s for s in (user_skills or []) if isinstance(s, str) and s.strip()]
    domain = detect_skill_domain(us)
    dv = skill_demand_from_jobs(jobs)
    total = dv["total_jobs"]
    top = list(dv["top_skills"])

    insight_line = ""
    if total <= 0:
        insight_line = (
            "No live postings in this session—run another search to compute demand from real listings."
        )
    elif not top:
        insight_line = (
            "Few role-relevant skills matched our extraction rules in this set—"
            "posting text may use uncommon phrasing."
        )
    elif len(top) >= 2:
        s1, s2 = top[0]["skill"], top[1]["skill"]
        union_n = count_jobs_mentioning_any_skill(jobs, [s1, s2])
        pct_u = round(100 * union_n / total, 1) if total else 0.0
        dl = domain_display_label(domain)
        insight_line = (
            f"In this {total}-listing {dl.lower()} sample, roles mentioning {s1} or {s2} "
            f"cover ~{pct_u}% of postings—prioritizing both often widens similar opportunities fastest."
        )
    else:
        s1 = top[0]["skill"]
        p = top[0]["pct_of_jobs"]
        insight_line = f"Strongest repeated signal in this sample: {s1} (~{p}% of postings)."

    return {
        "domain_key": domain,
        "domain_label": domain_display_label(domain),
        "total_jobs_analyzed": total,
        "top_skills": top[:5],
        "insight_line": insight_line.strip(),
        "fact_lines": dv["facts_lines"][:5],
    }


def merge_roadmap_response(
    llm_payload: dict,
    *,
    market_demand_insight: str,
    demand_support_bullets: list[str],
    analytics: dict,
    missing_skills: list[str],
    estimated_total_from_steps: str | None,
) -> dict:
    """Pin market numbers to analytics output; normalize roadmap_steps vs steps."""
    out = dict(llm_payload) if isinstance(llm_payload, dict) else {}
    out["market_demand_insight"] = market_demand_insight
    out["demand_insight"] = market_demand_insight
    out["demand_summary_lines"] = demand_support_bullets
    out["skill_demand_analytics"] = analytics
    steps = out.get("roadmap_steps")
    if not isinstance(steps, list):
        steps = out.get("steps")
    if not isinstance(steps, list):
        steps = []
    out["roadmap_steps"] = steps
    # Back-compat for older UI
    out["steps"] = steps

    ms = out.get("missing_skills_for_role")
    if not isinstance(ms, list) or not ms:
        out["missing_skills_for_role"] = missing_skills

    if estimated_total_from_steps and not out.get("estimated_time"):
        out["estimated_time"] = estimated_total_from_steps

    return out
