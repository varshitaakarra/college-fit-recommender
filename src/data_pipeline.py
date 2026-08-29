"""
data_pipeline.py
Pulls college data from the College Scorecard API and cleans it.
"""

import os
import requests
import pandas as pd

API_KEY = os.environ.get("COLLEGE_SCORECARD_API_KEY")
BASE_URL = "https://api.data.gov/ed/collegescorecard/v1/schools"

SCHOOL_NAMES = [
    "Rutgers University-New Brunswick",
    "Pennsylvania State University-Main Campus",
    "New York University",
]

FIELDS = [
    "school.name",
    "school.city",
    "school.state",
    "latest.cost.avg_net_price.overall",
    "latest.completion.rate_suppressed.overall",
    "latest.earnings.10_yrs_after_entry.median",
    "latest.student.size",
    "latest.student.demographics.student_faculty_ratio",
]


def fetch_school(name: str) -> dict:
    params = {
        "api_key": API_KEY,
        "school.name": name,
        "fields": ",".join(FIELDS),
        "per_page": 1,
    }
    response = requests.get(BASE_URL, params=params, timeout=15)
    response.raise_for_status()
    results = response.json().get("results", [])
    if not results:
        print(f"No result found for '{name}' — check the exact official name.")
        return {}
    return results[0]


def fetch_all_schools(names: list) -> pd.DataFrame:
    rows = []
    for name in names:
        print(f"Fetching: {name}")
        data = fetch_school(name)
        if data:
            rows.append(data)
    return pd.DataFrame(rows)


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={
        "school.name": "school",
        "school.city": "city",
        "school.state": "state",
        "latest.cost.avg_net_price.overall": "net_cost",
        "latest.completion.rate_suppressed.overall": "grad_rate",
        "latest.earnings.10_yrs_after_entry.median": "median_salary_10yr",
        "latest.student.size": "student_size",
        "latest.student.demographics.student_faculty_ratio": "student_faculty_ratio",
    })
    numeric_cols = ["net_cost", "grad_rate", "median_salary_10yr",
                     "student_size", "student_faculty_ratio"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median())
    return df.set_index("school")


if __name__ == "__main__":
    raw_df = fetch_all_schools(SCHOOL_NAMES)
    raw_df.to_csv("data/raw/schools_raw.csv", index=False)
    clean_df = clean_data(raw_df)
    clean_df.to_csv("data/processed/schools_clean.csv")
    print(clean_df)
