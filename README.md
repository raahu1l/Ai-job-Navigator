# 🚀 SkillForge

### **AI-Powered Career Intelligence Platform**

![React](https://img.shields.io/badge/React-Frontend-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Flask](https://img.shields.io/badge/Flask-Backend-black?style=for-the-badge&logo=flask)
![Qwen3](https://img.shields.io/badge/Qwen3-32B-purple?style=for-the-badge)
![Groq](https://img.shields.io/badge/Groq-Inference-orange?style=for-the-badge)
![AMD](https://img.shields.io/badge/AMD-MI300X-red?style=for-the-badge)
![Version](https://img.shields.io/badge/Version-1.0.0-green?style=for-the-badge)

> An AI-powered multi-agent platform that analyzes live job market data, identifies skill gaps, tracks market demand, and generates personalized learning roadmaps using Qwen3-32B and real-world job postings.

---

## 🎯 The Problem

Students and professionals often struggle with:

- Which skills are actually in demand?
- Which jobs match their current skillset?
- What should they learn next?
- Which skills unlock more opportunities?

Most platforms provide generic advice instead of real market-driven insights.

---

## 💡 The Solution

SkillForge uses live job market data and an AI-powered multi-agent workflow to:

- Match users with relevant roles
- Identify missing skills
- Analyze real-world market demand
- Generate personalized learning roadmaps
- Recommend practical learning resources

👉 Live Demo: https://ai-job-navigator-gamma.vercel.app/

---

## 🤖 Multi-Agent Workflow

### 🔍 Agent 1 — Job Researcher
Fetches live job postings using Adzuna APIs.

### 🧠 Agent 2 — Skill Extractor
Uses Qwen3-32B to extract required skills from real-world job descriptions.

### 📊 Agent 3 — Gap Analyzer
Compares user skills against market requirements and calculates match scores.

### 🎯 Agent 4 — Career Coach
Generates personalized learning roadmaps, projects, and resource recommendations.

---

## 🧠 Why Qwen3-32B?

Qwen3-32B powers the intelligence layer of SkillForge.

It was selected for:
- Strong instruction-following
- Reliable structured JSON generation
- Accurate skill extraction from noisy job descriptions
- High-quality reasoning for roadmap generation

---

## 📱 Features

### 🚀 Career Intelligence
- Live job market analysis
- AI-powered role matching
- Skill gap identification
- Match percentage scoring
- Real-time market demand insights

### 📚 Personalized Learning
- AI-generated learning roadmaps
- Recommended websites & resources
- YouTube learning suggestions
- Practice project recommendations
- Estimated learning timelines

### 📊 Market Insights
- Top in-demand skills
- Domain-based trend analysis
- Live hiring pattern analysis
- Opportunity expansion insights

---

## 🛠️ Tech Stack

| Layer | Technology |
|------|-----------|
| Frontend | React + Vite |
| Backend | Flask |
| AI Model | Qwen3-32B |
| Workflow | CrewAI-inspired Multi-Agent Pipeline |
| APIs | Adzuna Job APIs |
| Inference | Groq |
| Charts | Recharts |
| Deployment | Vercel + Render |
| Infrastructure | AMD MI300X / ROCm-ready |

---

## 🚀 Getting Started

### Frontend Setup

```bash
cd Frontend
npm install
npm run dev
```

### Backend Setup

```bash
cd Backend
pip install -r requirements.txt
python app.py
```

---

## 🔑 Environment Variables

```env
GROQ_API_KEY=
ADZUNA_APP_ID=
ADZUNA_APP_KEY=
```

---

🔥 AMD Developer Cloud

SkillForge is architected for deployment on AMD MI300X GPU infrastructure with ROCm-compatible inference workflows.

The live demo currently uses Groq-hosted inference APIs during development, while the codebase remains ready for direct AMD GPU deployment using vLLM.

--- 

💡 Why This Project Matters

SkillForge focuses on solving a real-world problem:

Bridging the gap between:

current user skills
live market demand
personalized career growth

Instead of generic AI chat responses, the platform provides:

actionable market intelligence
real skill-gap analysis
practical learning guidance

---

Developed with the assistance of AI tools to accelerate development, debugging, UI refinement, and workflow orchestration.

---

## 👨‍💻 Author

**Rahul Walawalkar**  
GitHub: https://github.com/raahu1l

---

Built for the AMD Developer Hackathon 🚀
