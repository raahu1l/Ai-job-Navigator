import os
import requests as req
from dotenv import load_dotenv
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

load_dotenv()

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")

COUNTRY_CODES = {
    "india": "in",
    "usa": "us",
    "uk": "gb",
    "canada": "ca",
    "australia": "au",
    "germany": "de",
    "france": "fr",
    "singapore": "sg",
}


def _redact_url_query(url_with_query: str) -> str:
    """Log-safe URL: mask app_key values."""
    try:
        parts = urlsplit(url_with_query)
        pairs = parse_qsl(parts.query, keep_blank_values=True)
        safe = []
        for k, v in pairs:
            if k == "app_key" and v:
                safe.append((k, f"{v[:4]}…" if len(v) > 4 else "***"))
            else:
                safe.append((k, v))
        return urlunsplit(
            (parts.scheme, parts.netloc, parts.path, urlencode(safe), parts.fragment)
        )
    except Exception:
        return "<url redact error>"


def _build_debug(
    *,
    source: str,
    request_url_redacted: str | None = None,
    http_status: int | None = None,
    adzuna_result_count: int | None = None,
    fallback_reason: str | None = None,
    error_body_snippet: str | None = None,
    credentials_present: bool = False,
) -> dict:
    return {
        "source": source,
        "request_url_redacted": request_url_redacted,
        "http_status": http_status,
        "adzuna_raw_result_count": adzuna_result_count,
        "fallback_reason": fallback_reason,
        "error_body_snippet": error_body_snippet,
        "credentials_present": credentials_present,
    }


def _adzuna_search_what_from_keywords(keywords: str) -> str:
    """
    Keep the caller-built search phrase intact.

    Older logic collapsed every query to the first token plus "developer"
    (for example: "mongo sql python java docker" became "mongo developer").
    That made user-entered skills after the first token effectively invisible.
    Query construction now happens in skill_domain.build_job_search_queries(),
    which emits focused, short phrases that are safe to pass through directly.
    """
    raw = (keywords or "").strip()
    if not raw:
        return ""
    return " ".join(raw.split())[:120]


def fetch_jobs(keywords: str, location: str = "india", results: int = 50) -> dict:
    """
    Fetch live jobs from Adzuna API.
    Falls back to static jobs.json only on real failures (missing keys, HTTP errors,
    network errors, invalid JSON). Empty HTTP 200 with zero results stays LIVE (empty list).
    """
    cred_ok = bool(
        ADZUNA_APP_ID
        and str(ADZUNA_APP_ID).strip()
        and ADZUNA_APP_KEY
        and str(ADZUNA_APP_KEY).strip()
    )

    if not cred_ok:
        print("Adzuna: credentials missing — check ADZUNA_APP_ID and ADZUNA_APP_KEY on the server")
        print("Fallback dataset activated")
        return _fallback_payload(
            reason="missing_credentials",
            debug_extra={"credentials_present": False},
        )

    country = COUNTRY_CODES.get(location.lower(), "in")
    base_url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    search_query = _adzuna_search_what_from_keywords(keywords)
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": min(max(results, 1), 50),
        "what": search_query,
    }
    # Optional location filter for cities / regions (not a country code)
    if location.lower() not in COUNTRY_CODES:
        params["where"] = location

    session = req.Session()
    request = req.Request("GET", base_url, params=params)
    prepped = session.prepare_request(request)

    try:
        response = session.send(prepped, timeout=15)
    except req.RequestException as e:
        redacted = _redact_url_query(prepped.url)
        print(f"Adzuna request URL (redacted): {redacted}")
        print(f"Adzuna status: (no response) — network error: {e}")
        print("Fallback dataset activated")
        return _fallback_payload(
            reason="request_failed",
            debug_extra={
                "request_url_redacted": redacted,
                "http_status": None,
                "error_body_snippet": str(e)[:500],
                "credentials_present": True,
            },
        )
    except Exception as e:
        redacted = _redact_url_query(prepped.url)
        print(f"Adzuna request URL (redacted): {redacted}")
        print(f"Adzuna unexpected error before parse: {e}")
        print("Fallback dataset activated")
        return _fallback_payload(
            reason="error",
            debug_extra={
                "request_url_redacted": redacted,
                "http_status": None,
                "error_body_snippet": str(e)[:500],
                "credentials_present": True,
            },
        )

    redacted = _redact_url_query(response.url)
    print(f"Adzuna request URL (redacted): {redacted}")

    status = response.status_code
    body_preview = ""
    try:
        body_preview = response.text[:800] if response.text else ""
    except Exception:
        pass

    print(f"Adzuna HTTP status code: {status}")

    if status != 200:
        snippet = body_preview.replace("\n", " ").strip()
        print(f"Adzuna error response (first 600 chars): {snippet[:600]}")
        print("Fallback dataset activated")
        return _fallback_payload(
            reason=f"http_{status}",
            debug_extra={
                "request_url_redacted": redacted,
                "http_status": status,
                "error_body_snippet": snippet[:500],
                "credentials_present": True,
            },
        )

    try:
        data = response.json()
    except ValueError as e:
        print(f"Adzuna response not valid JSON: {e}")
        print(f"Raw body preview: {body_preview[:400]}")
        print("Fallback dataset activated")
        return _fallback_payload(
            reason="invalid_json",
            debug_extra={
                "request_url_redacted": redacted,
                "http_status": status,
                "error_body_snippet": body_preview[:500],
                "credentials_present": True,
            },
        )

    raw_results = data.get("results")
    if raw_results is None:
        raw_results = []
    n_raw = len(raw_results)
    print(f"Adzuna jobs returned (raw count): {n_raw}")

    jobs = []
    for job in raw_results:
        jobs.append({
            "job_id": str(job.get("id", "")),
            "title": job.get("title", ""),
            "company": job.get("company", {}).get("display_name", "Unknown"),
            "location": job.get("location", {}).get("display_name", location),
            "description": job.get("description", ""),
            "url": job.get("redirect_url", ""),
            "salary_min": job.get("salary_min", 0),
            "salary_max": job.get("salary_max", 0),
            "skills": [],
        })

    count = len(jobs)
    dbg = _build_debug(
        source="adzuna",
        request_url_redacted=redacted,
        http_status=status,
        adzuna_result_count=n_raw,
        fallback_reason=None,
        credentials_present=True,
    )
    print("LIVE Adzuna jobs loaded")
    print(f"  Parsed job count: {count}")
    return {
        "jobs": jobs,
        "source": "adzuna",
        "count": count,
        "debug": dbg,
    }


def _load_static_jobs() -> list:
    import json
    from pathlib import Path

    try:
        data_path = Path(__file__).resolve().parent / "data" / "jobs.json"
        with open(data_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Fallback also failed: {e}")
        return []


def _fallback_payload(reason: str = "", debug_extra: dict | None = None) -> dict:
    jobs = _load_static_jobs()
    count = len(jobs)
    if reason:
        print(f"Fallback reason: {reason}")
    extra = debug_extra or {}
    dbg = _build_debug(
        source="fallback",
        request_url_redacted=extra.get("request_url_redacted"),
        http_status=extra.get("http_status"),
        adzuna_raw_result_count=extra.get("adzuna_raw_result_count"),
        fallback_reason=reason or "unknown",
        error_body_snippet=extra.get("error_body_snippet"),
        credentials_present=extra.get("credentials_present", False),
    )
    return {"jobs": jobs, "source": "fallback", "count": count, "debug": dbg}


def fetch_jobs_multi(
    queries: list[str],
    location: str = "india",
    results_per_query: int = 50,
) -> dict:
    """
    Run multiple Adzuna searches and merge unique jobs by job_id (improves recall).
    Falls back like fetch_jobs if no live query succeeds.
    """
    clean_queries = []
    for q in queries or []:
        s = (q or "").strip()
        if s and s not in clean_queries:
            clean_queries.append(s)
    if not clean_queries:
        return fetch_jobs("", location, results=results_per_query)

    merged: list[dict] = []
    seen: set[str] = set()
    last_non_live: dict | None = None
    debug_parts: list[dict] = []

    for q in clean_queries[:8]:
        result = fetch_jobs(q, location, results=results_per_query)
        if result.get("source") != "adzuna":
            last_non_live = result
            continue
        dbg = result.get("debug")
        if isinstance(dbg, dict):
            debug_parts.append(dbg)
        for job in result.get("jobs") or []:
            jid = str(job.get("job_id") or "")
            if jid and jid not in seen:
                seen.add(jid)
                merged.append(job)

    if merged:
        primary_dbg = debug_parts[0] if debug_parts else _build_debug(
            source="adzuna",
            credentials_present=True,
        )
        return {
            "jobs": merged,
            "count": len(merged),
            "source": "adzuna",
            "debug": {
                **primary_dbg,
                "merged_queries": len(debug_parts),
                "merged_unique_jobs": len(merged),
            },
        }

    if last_non_live:
        return last_non_live
    return fetch_jobs(clean_queries[0], location, results=results_per_query)


def get_job_description(job: dict) -> str:
    """Extract clean description text from job"""
    return job.get("description", "")
