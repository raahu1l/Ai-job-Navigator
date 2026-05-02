from flask import Flask, jsonify, request
from flask_cors import CORS
from matcher import analyze, get_trending

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


if __name__ == "__main__":
    app.run(port=5000)
