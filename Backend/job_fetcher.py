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


def fetch_jobs(keywords: str, location: str = "india", results: int = 20) -> list:
    """
    Fetch live jobs from Adzuna API.
    Falls back to static jobs.json if API fails.
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
            print(f"Adzuna API error: {response.status_code}")
            return _fallback_jobs()

        data = response.json()
        jobs = []

        for job in data.get("results", []):
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
            return _fallback_jobs()

        return jobs

    except Exception as e:
        print(f"Adzuna fetch error: {e}")
        return _fallback_jobs()


def _fallback_jobs() -> list:
    """Return static jobs.json as fallback"""
    import json
    from pathlib import Path

    try:
        data_path = Path(__file__).resolve().parent / "data" / "jobs.json"
        with open(data_path, "r", encoding="utf-8") as f:
            jobs = json.load(f)
        print("Using fallback static dataset")
        return jobs
    except Exception as e:
        print(f"Fallback also failed: {e}")
        return []


def get_job_description(job: dict) -> str:
    """Extract clean description text from job"""
    return job.get("description", "")
