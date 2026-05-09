from agents import (
    extract_skills_from_jd,
    generate_learning_path,
    analyze_market_demand
)
import json


class Agent:
    def __init__(self, role: str, goal: str, backstory: str):
        self.role = role
        self.goal = goal
        self.backstory = backstory

    def __repr__(self):
        return f"Agent(role={self.role})"


class Task:
    def __init__(self, description: str, agent: Agent, expected_output: str):
        self.description = description
        self.agent = agent
        self.expected_output = expected_output


class SkillNavCrew:
    def __init__(self):
        # Define all 4 agents
        self.job_researcher = Agent(
            role="Job Market Researcher",
            goal="Find and analyze relevant job postings based on user skills",
            backstory="Expert at analyzing job market trends and matching candidates to opportunities"
        )

        self.skill_extractor = Agent(
            role="Skill Extraction Specialist",
            goal="Extract required technical and professional skills from job descriptions",
            backstory="Specialized in identifying key skills from job postings with high accuracy"
        )

        self.gap_analyzer = Agent(
            role="Skill Gap Analyst",
            goal="Compare user skills against market demand and identify gaps",
            backstory="Expert at identifying skill gaps and market opportunities for career growth"
        )

        self.career_coach = Agent(
            role="Career Development Coach",
            goal="Generate personalized learning roadmaps to close skill gaps",
            backstory="Experienced career coach who creates actionable learning plans with real resources"
        )

        # Define tasks
        self.tasks = [
            Task(
                description="Research job market and identify matching opportunities",
                agent=self.job_researcher,
                expected_output="List of relevant jobs with match scores"
            ),
            Task(
                description="Extract required skills from job descriptions",
                agent=self.skill_extractor,
                expected_output="Structured list of required skills per job"
            ),
            Task(
                description="Analyze skill gaps between user profile and market demand",
                agent=self.gap_analyzer,
                expected_output="Prioritized list of missing skills with frequency counts"
            ),
            Task(
                description="Generate personalized learning path for skill gaps",
                agent=self.career_coach,
                expected_output="Step by step learning roadmap with resources and timelines"
            )
        ]

    def run(self, user_skills: list, job_results: list, trending_skills: list) -> dict:
        """
        Run the full crew pipeline:
        Task 1: Job Researcher - already done via matcher.py
        Task 2: Skill Extractor - extract skills from descriptions
        Task 3: Gap Analyzer - analyze market demand
        Task 4: Career Coach - generate learning path
        """
        pipeline_log = []

        # Task 1 - Job Researcher (results already fetched)
        pipeline_log.append({
            "agent": self.job_researcher.role,
            "task": self.tasks[0].description,
            "status": "completed",
            "output": f"Found {len(job_results)} matching jobs"
        })

        # Task 2 - Skill Extractor
        pipeline_log.append({
            "agent": self.skill_extractor.role,
            "task": self.tasks[1].description,
            "status": "running"
        })
        all_missing = []
        for job in job_results[:3]:
            all_missing.extend(job.get("missing_skills", []))
        unique_missing = list(set(all_missing))
        pipeline_log[-1]["status"] = "completed"
        pipeline_log[-1]["output"] = f"Identified {len(unique_missing)} unique skill gaps"

        # Task 3 - Gap Analyzer
        pipeline_log.append({
            "agent": self.gap_analyzer.role,
            "task": self.tasks[2].description,
            "status": "running"
        })
        market_analysis = analyze_market_demand(
            trending_skills=[s["skill"] for s in trending_skills[:5]],
            user_skills=user_skills
        )
        pipeline_log[-1]["status"] = "completed"
        pipeline_log[-1]["output"] = f"Market trend: {market_analysis.get('demand_trend', 'stable')}"

        # Task 4 - Career Coach
        pipeline_log.append({
            "agent": self.career_coach.role,
            "task": self.tasks[3].description,
            "status": "running"
        })
        target_role = job_results[0]["title"] if job_results else "Software Developer"
        learning_path = generate_learning_path(
            missing_skills=unique_missing[:5],
            target_role=target_role
        )
        pipeline_log[-1]["status"] = "completed"
        pipeline_log[-1]["output"] = f"Generated {len(learning_path.get('steps', []))} learning steps"

        return {
            "pipeline": pipeline_log,
            "market_analysis": market_analysis,
            "learning_path": learning_path,
            "skill_gaps": unique_missing
        }
