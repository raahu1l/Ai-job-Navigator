import os
import requests as req
from dotenv import load_dotenv

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
    "singapore": "sg"
}


def fetch_jobs(keywords: str, location: str = "india", results: int = 20) -> dict:
    """
    Fetch live jobs from Adzuna API.
    Falls back to static jobs.json only if the API request fails, returns an error
    status, rate-limits, or yields no job results.
    """
    try:
        country = COUNTRY_CODES.get(location.lower(), "in")

        url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
        params = {
            "app_id": ADZUNA_APP_ID,
            "app_key": ADZUNA_APP_KEY,
            "results_per_page": results,
            "what": keywords,
            "content-type": "application/json"
        }

        if location.lower() not in COUNTRY_CODES:
            params["where"] = location

        response = req.get(url, params=params, timeout=10)

        if response.status_code != 200:
            print(f"Adzuna API error: HTTP {response.status_code}")
            if response.status_code == 429:
                print("Adzuna rate limit (429) — using fallback")
            return _fallback_payload(reason=f"http_{response.status_code}")

        try:
            data = response.json()
        except ValueError as e:
            print(f"Adzuna response not valid JSON: {e}")
            return _fallback_payload(reason="invalid_json")

        raw_results = data.get("results")
        if not raw_results:
            print("Adzuna returned empty results — using fallback")
            return _fallback_payload(reason="empty_response")

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
                "skills": []
            })

        if not jobs:
            print("Adzuna parsed zero jobs — using fallback")
            return _fallback_payload(reason="empty_after_parse")

        count = len(jobs)
        print(f"Using LIVE Adzuna analysis — {count} job(s) fetched")
        return {"jobs": jobs, "source": "adzuna", "count": count}

    except req.RequestException as e:
        print(f"Adzuna fetch error (network): {e}")
        return _fallback_payload(reason="request_failed")
    except Exception as e:
        print(f"Adzuna fetch error: {e}")
        return _fallback_payload(reason="error")


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


def _fallback_payload(reason: str = "") -> dict:
    jobs = _load_static_jobs()
    count = len(jobs)
    if reason:
        print(f"Fallback reason: {reason}")
    print(f"Using FALLBACK static dataset — {count} job(s)")
    return {"jobs": jobs, "source": "fallback", "count": count}


def get_job_description(job: dict) -> str:
    """Extract clean description text from job"""
    return job.get("description", "")
