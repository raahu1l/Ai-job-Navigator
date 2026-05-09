import os
import json
from groq import Groq
from dotenv import load_dotenv

from skill_domain import (
    DOMAIN_GENERAL,
    DOMAIN_TRENDING_HINTS,
    detect_skill_domain,
    domain_market_context,
)
from skill_filters import filter_skill_list

def extract_json(text: str):
    import re
    # Remove thinking tags if present
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = text.replace("```json", "").replace("```", "").strip()
    # Find JSON object first (prefer object over array)
    object_match = re.search(r'\{.*\}', text, re.DOTALL)
    if object_match:
        return object_match.group()
    # Fall back to array
    array_match = re.search(r'\[.*\]', text, re.DOTALL)
    if array_match:
        return array_match.group()
    return text.strip()

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "qwen/qwen3-32b"

def extract_skills_from_jd(job_description: str) -> list:
    prompt = f"""
You are a skill extraction expert. 
Extract only the technical and professional skills from this job description.
Return ONLY a JSON array of skill strings. No explanation, no markdown, just the array.
Example: ["Python", "SQL", "Machine Learning", "Communication"]

Job Description:
{job_description}
"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=500
    )
    
    text = extract_json(response.choices[0].message.content)
    try:
        skills = json.loads(text)
        skills = skills if isinstance(skills, list) else []
        return filter_skill_list(skills)
    except:
        return []

def generate_learning_path(missing_skills: list, target_role: str) -> dict:
    missing_skills = filter_skill_list(missing_skills if isinstance(missing_skills, list) else [])
    if not missing_skills:
        return {"message": "You have all required skills!", "steps": []}
    
    prompt = f"""
You are a career coach. Given these missing skills for a {target_role} role,
create a prioritized learning path.
Return ONLY a JSON object with no explanation, no markdown.
Format exactly like this:
{{
  "priority_skill": "most important skill to learn first",
  "estimated_time": "X weeks",
  "steps": [
    {{"skill": "skill name", "resource": "best free resource", "time": "X weeks"}},
    {{"skill": "skill name", "resource": "best free resource", "time": "X weeks"}}
  ],
  "message": "encouraging one line message"
}}

Missing skills: {missing_skills}
Target role: {target_role}
"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=800
    )
    
    text = extract_json(response.choices[0].message.content)
    try:
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except:
        return {
            "priority_skill": missing_skills[0] if missing_skills else "",
            "estimated_time": "4 weeks",
            "steps": [],
            "message": "Focus on one skill at a time."
        }

def analyze_market_demand(trending_skills: list, user_skills: list) -> dict:
    trending_skills = filter_skill_list(trending_skills if isinstance(trending_skills, list) else [])
    user_skills = filter_skill_list(user_skills if isinstance(user_skills, list) else [])
    domain = detect_skill_domain(user_skills)
    domain_hint = domain_market_context(domain)

    prompt = f"""
You are a job market analyst.
Given these market trending skills and user's current skills,
provide a brief market analysis.
Return ONLY a JSON object, no explanation, no markdown.
Format exactly:
{{
  "market_summary": "2 sentence market overview",
  "your_strength": "what the user is good at based on their skills",
  "biggest_opportunity": "single most impactful skill to learn",
  "demand_trend": "growing/stable/declining for user's skill set"
}}

{domain_hint}

Trending skills in market: {trending_skills}
User skills: {user_skills}
"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=500
    )
    
    text = extract_json(response.choices[0].message.content)
    try:
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except:
        hints = DOMAIN_TRENDING_HINTS.get(domain, DOMAIN_TRENDING_HINTS[DOMAIN_GENERAL])
        return {
            "market_summary": "The job market is actively evolving.",
            "your_strength": "Your current skills show solid foundation.",
            "biggest_opportunity": trending_skills[0] if trending_skills else hints[0],
            "demand_trend": "growing"
        }
