"""
Trending technical skills from job titles and descriptions only.
Uses a whitelist — never reads legacy Kaggle category fields on jobs.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Iterable

# Canonical display names; matching is case-insensitive. Longer phrases first (handled at runtime).
TECH_SKILL_WHITELIST: tuple[str, ...] = (
    "Spring Boot",
    "Google Cloud",
    "Machine Learning",
    "Deep Learning",
    "Data Science",
    "React Native",
    "Next.js",
    "Node.js",
    "Vue.js",
    "Angular",
    "TypeScript",
    "JavaScript",
    "Tailwind CSS",
    "ASP.NET",
    "FastAPI",
    "Django",
    "Flask",
    "Express",
    "GraphQL",
    "PostgreSQL",
    "MongoDB",
    "DynamoDB",
    "Elasticsearch",
    "BigQuery",
    "Snowflake",
    "Kubernetes",
    "Terraform",
    "Ansible",
    "Jenkins",
    "GitHub Actions",
    "TensorFlow",
    "PyTorch",
    "scikit-learn",
    "PySpark",
    "Apache Spark",
    "Apache Kafka",
    "Apache Airflow",
    "Ruby on Rails",
    "RESTful",
    "CI/CD",
    "C++",
    "C#",
    ".NET",
    "Android",
    "iOS",
    "Swift",
    "Kotlin",
    "Scala",
    "Golang",
    "Rust",
    "Bash",
    "Linux",
    "Ubuntu",
    "Docker",
    "Redis",
    "MySQL",
    "Oracle",
    "SQLite",
    "Pandas",
    "NumPy",
    "Keras",
    "Pytest",
    "JUnit",
    "Selenium",
    "Webpack",
    "GitLab",
    "GitHub",
    "Git",
    "Jira",
    "HTML",
    "CSS",
    "SASS",
    "PHP",
    "Laravel",
    "Rails",
    "Ruby",
    "Spring",
    "React",
    "Vue",
    "Java",
    "Python",
    "SQL",
    "AWS",
    "Azure",
    "GCP",
    "Kafka",
    "RabbitMQ",
    "Nginx",
    "Hadoop",
    "dbt",
    "Tableau",
    "Power BI",
    "Microservices",
    "Terraform",
    "DevOps",
    "SRE",
)

# Deduplicate while preserving order of first occurrence
_SEEN: set[str] = set()
_UNIQUE_WHITELIST: list[str] = []
for _s in TECH_SKILL_WHITELIST:
    if _s.lower() not in _SEEN:
        _SEEN.add(_s.lower())
        _UNIQUE_WHITELIST.append(_s)

# Longest first so e.g. JavaScript wins over Java
WHITELIST_BY_LENGTH: tuple[str, ...] = tuple(
    sorted(_UNIQUE_WHITELIST, key=len, reverse=True)
)


def _skill_regex(skill: str) -> re.Pattern:
    """Token-ish boundaries: avoid matching Java inside JavaScript, etc."""
    escaped = re.escape(skill)
    return re.compile(
        r"(?<![a-z0-9.#+\-/])" + escaped + r"(?![a-z0-9.#+\-/])",
        re.IGNORECASE,
    )


def extract_technical_skills_from_job(job: dict) -> set[str]:
    """Match whitelist against title + description only (not legacy skills arrays)."""
    title = str(job.get("title") or "")
    description = str(job.get("description") or "")
    text = f"{title}\n{description}"
    if not text.strip():
        return set()

    working = f" {text.lower()} "
    found: set[str] = set()

    for skill in WHITELIST_BY_LENGTH:
        pat = _skill_regex(skill)
        m = pat.search(working)
        if m:
            found.add(skill)
            working = (
                working[: m.start()]
                + (" " * (m.end() - m.start()))
                + working[m.end() :]
            )
    return found


def trending_from_jobs(jobs: Iterable[dict], top_n: int = 15) -> list[dict]:
    counter: Counter[str] = Counter()
    for job in jobs:
        for skill in extract_technical_skills_from_job(job):
            counter[skill] += 1

    out: list[dict] = []
    for skill, count in counter.most_common(top_n):
        out.append({"skill": skill, "count": count})
    return out
