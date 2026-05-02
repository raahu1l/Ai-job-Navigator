import json
from pathlib import Path

import pandas as pd


def main():
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "data"
    mappings_dir = data_dir / "mappings"

    postings_path = data_dir / "postings.csv"
    job_skills_path = data_dir / "job_skills.csv"
    skills_map_path = mappings_dir / "skills.csv"
    output_path = data_dir / "jobs.json"

    postings_df = pd.read_csv(postings_path, usecols=["job_id", "title", "company_name"])
    job_skills_df = pd.read_csv(job_skills_path, usecols=["job_id", "skill_abr"])
    skills_map_df = pd.read_csv(skills_map_path, usecols=["skill_abr", "skill_name"])

    skills_with_names_df = job_skills_df.merge(skills_map_df, on="skill_abr", how="left")

    skills_by_job_df = (
        skills_with_names_df.dropna(subset=["skill_name"])
        .groupby("job_id", as_index=False)["skill_name"]
        .agg(list)
        .rename(columns={"skill_name": "skills"})
    )

    jobs_df = postings_df.merge(skills_by_job_df, on="job_id", how="inner")

    jobs_df = jobs_df.dropna(subset=["title", "company_name"])
    jobs_df = jobs_df.drop_duplicates(subset=["job_id"])
    jobs_df = jobs_df[jobs_df["skills"].apply(lambda skills: len(skills) >= 2)]

    sample_size = min(500, len(jobs_df))
    jobs_df = jobs_df.sample(n=sample_size, random_state=42)

    jobs_output = []
    for row in jobs_df.itertuples(index=False):
        jobs_output.append(
            {
                "job_id": str(row.job_id),
                "title": row.title,
                "company": row.company_name,
                "skills": row.skills,
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(jobs_output, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(jobs_output)} jobs to {output_path}")


if __name__ == "__main__":
    main()
