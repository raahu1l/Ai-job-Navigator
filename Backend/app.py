from flask import Flask, jsonify, request
from flask_cors import CORS
from matcher import analyze, get_trending
from market_insights import build_skill_demand_dashboard
from job_fetcher import fetch_jobs_multi
from skill_domain import build_job_search_queries, normalize_user_skills_list

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
    try:
        payload = request.get_json(silent=True) or {}
        skills = payload.get("skills", [])
        job_results = payload.get("job_results")
        n_live = len(job_results) if isinstance(job_results, list) else 0
        if n_live > 0:
            print(f"/api/analyze: LIVE job_results count={n_live}")
        else:
            print("/api/analyze: no job_results → matcher will use static fallback path")
        
        out = analyze(skills, job_results)
        _empty_area_msg = (
            "No matching jobs in this area. Try broader skills or different location."
        )
        if isinstance(out, dict):
            return jsonify({
                "results": [],
                "message": (out.get("message") or "").strip() or _empty_area_msg,
            })
        results = out if isinstance(out, list) else []
        if not results:
            return jsonify({"results": [], "message": _empty_area_msg})
        return jsonify(results)
    except Exception as e:
        print(f"Error in /api/analyze: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "results": [],
            "message": "Unable to process your request. Please try different skills or location."
        })


@app.get("/api/trending")
def trending_route():
    """Technical skills from Adzuna titles/descriptions + whitelist (not Kaggle categories)."""
    try:
        skills_raw = request.args.get("skills", "").strip()
        user_skills = [s.strip() for s in skills_raw.split(",") if s.strip()] if skills_raw else None
        return jsonify(get_trending(user_skills=user_skills))
    except Exception as e:
        print(f"Error in /api/trending: {e}")
        return jsonify([])


@app.post("/api/extract-skills")
def extract_skills_route():
    try:
        from agents import extract_skills_from_jd

        payload = request.get_json(silent=True) or {}
        job_description = payload.get("job_description", "")
        skills = extract_skills_from_jd(job_description)
        return jsonify({"skills": skills if isinstance(skills, list) else []})
    except Exception as e:
        print(f"Error in /api/extract-skills: {e}")
        return jsonify({"skills": []})


@app.post("/api/learning-path")
def learning_path_route():
    try:
        from agents import generate_learning_path

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
    except Exception as e:
        print(f"Error in /api/learning-path: {e}")
        return jsonify({"path": [], "next_steps": []})


@app.post("/api/skill-demand")
def skill_demand_route():
    """Top in-demand skills from live job text + inferred user domain (no LLM)."""
    try:
        payload = request.get_json(silent=True) or {}
        user_skills = payload.get("user_skills", [])
        live_jobs = payload.get("live_jobs")
        jobs = live_jobs if isinstance(live_jobs, list) else []
        us = user_skills if isinstance(user_skills, list) else []
        return jsonify(build_skill_demand_dashboard(us, jobs))
    except Exception as e:
        print(f"Error in /api/skill-demand: {e}")
        return jsonify({"top_skills": [], "insights": []})


@app.post("/api/market-analysis")
def market_analysis_route():
    try:
        from agents import analyze_market_demand

        payload = request.get_json(silent=True) or {}
        trending_skills = payload.get("trending_skills", [])
        user_skills = payload.get("user_skills", [])
        live_jobs = payload.get("live_jobs")
        lj = live_jobs if isinstance(live_jobs, list) else None
        return jsonify(analyze_market_demand(trending_skills, user_skills, live_jobs=lj))
    except Exception as e:
        print(f"Error in /api/market-analysis: {e}")
        return jsonify({"analysis": [], "summary": ""})


@app.post("/api/crew-run")
def crew_run_route():
    try:
        from crew import SkillNavCrew

        payload = request.get_json(silent=True) or {}
        user_skills = payload.get("user_skills", [])
        job_results = payload.get("job_results", [])
        trending_skills = payload.get("trending_skills", [])
        crew = SkillNavCrew()
        return jsonify(crew.run(user_skills, job_results, trending_skills))
    except Exception as e:
        print(f"Error in /api/crew-run: {e}")
        return jsonify({"recommendations": [], "summary": ""})


@app.post("/api/fetch-jobs")
def fetch_jobs_route():
    try:
        payload = request.get_json(silent=True) or {}
        keywords = payload.get("keywords", "")
        location = payload.get("location", "india")
        skills_raw = payload.get("skills")
        skills_list = normalize_user_skills_list(
            skills_raw if isinstance(skills_raw, list) else None,
            str(keywords) if keywords else "",
        )
        queries = build_job_search_queries(skills_list)
        result = fetch_jobs_multi(queries, location)
        out = {
            "jobs": result.get("jobs", []),
            "count": result.get("count", 0),
            "source": result.get("source", "unknown"),
        }
        if result.get("debug"):
            out["debug"] = result["debug"]
        return jsonify(out)
    except Exception as e:
        print(f"Error in /api/fetch-jobs: {e}")
        return jsonify({"jobs": [], "count": 0, "source": "error"})


@app.get("/api/locations")
def locations_route():
    return jsonify({
        "locations": ["India", "Bangalore", "Mumbai", "Delhi",
                      "Hyderabad", "Pune", "Chennai", "USA", "UK",
                      "Canada", "Australia", "Remote"]
    })


if __name__ == "__main__":
    app.run(port=5000)
