from flask import Flask, jsonify, request
from flask_cors import CORS
from matcher import analyze, get_trending
from agents import extract_skills_from_jd, generate_learning_path, analyze_market_demand
from crew import SkillNavCrew
from job_fetcher import fetch_jobs

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://ai-job-navigator-gamma.vercel.app"
]}})


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/test")
def test():
    return {"status": "working"}


@app.post("/api/analyze")
def analyze_route():
    payload = request.get_json(silent=True) or {}
    skills = payload.get("skills", [])
    job_results = payload.get("job_results")
    n_live = len(job_results) if isinstance(job_results, list) else 0
    if n_live > 0:
        print(f"/api/analyze: LIVE job_results count={n_live}")
    else:
        print("/api/analyze: no job_results → matcher will use static fallback path")
    return jsonify(analyze(skills, job_results))


@app.get("/api/trending")
def trending_route():
    """Technical skills from Adzuna titles/descriptions + whitelist (not Kaggle categories)."""
    skills_raw = request.args.get("skills", "").strip()
    user_skills = [s.strip() for s in skills_raw.split(",") if s.strip()] if skills_raw else None
    return jsonify(get_trending(user_skills=user_skills))


@app.post("/api/extract-skills")
def extract_skills_route():
    payload = request.get_json(silent=True) or {}
    job_description = payload.get("job_description", "")
    skills = extract_skills_from_jd(job_description)
    return jsonify({"skills": skills})


@app.post("/api/learning-path")
def learning_path_route():
    payload = request.get_json(silent=True) or {}
    missing_skills = payload.get("missing_skills", [])
    target_role = payload.get("target_role", "")
    demand_context = payload.get("demand_context")
    return jsonify(
        generate_learning_path(
            missing_skills,
            target_role,
            demand_context=demand_context if isinstance(demand_context, dict) else None,
        )
    )


@app.post("/api/market-analysis")
def market_analysis_route():
    payload = request.get_json(silent=True) or {}
    trending_skills = payload.get("trending_skills", [])
    user_skills = payload.get("user_skills", [])
    return jsonify(analyze_market_demand(trending_skills, user_skills))


@app.post("/api/crew-run")
def crew_run_route():
    payload = request.get_json(silent=True) or {}
    user_skills = payload.get("user_skills", [])
    job_results = payload.get("job_results", [])
    trending_skills = payload.get("trending_skills", [])
    crew = SkillNavCrew()
    return jsonify(crew.run(user_skills, job_results, trending_skills))


@app.post("/api/fetch-jobs")
def fetch_jobs_route():
    payload = request.get_json(silent=True) or {}
    keywords = payload.get("keywords", "")
    location = payload.get("location", "india")
    result = fetch_jobs(keywords, location)
    out = {
        "jobs": result["jobs"],
        "count": result["count"],
        "source": result["source"],
    }
    if result.get("debug"):
        out["debug"] = result["debug"]
    return jsonify(out)


@app.get("/api/locations")
def locations_route():
    return jsonify({
        "locations": ["India", "Bangalore", "Mumbai", "Delhi",
                      "Hyderabad", "Pune", "Chennai", "USA", "UK",
                      "Canada", "Australia", "Remote"]
    })


if __name__ == "__main__":
    app.run(port=5000)
