from flask import Flask, jsonify, request
from flask_cors import CORS
from matcher import analyze, get_trending
from agents import extract_skills_from_jd, generate_learning_path, analyze_market_demand
from crew import SkillNavCrew

app = Flask(__name__)
CORS(app)


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/api/analyze")
def analyze_route():
    payload = request.get_json(silent=True) or {}
    skills = payload.get("skills", [])
    return jsonify(analyze(skills))


@app.get("/api/trending")
def trending_route():
    return jsonify(get_trending())


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
    return jsonify(generate_learning_path(missing_skills, target_role))


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


if __name__ == "__main__":
    app.run(port=5000)
