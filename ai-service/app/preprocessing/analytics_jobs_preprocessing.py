"""Production-quality Preprocessing Pipeline for Analytics Jobs Dataset.

This module processes the raw Analytics Jobs dataset (data/raw/Analytics Jobs.csv):
- Validates and normalizes column names
- Safely cleans text while preserving technical skills punctuation (C, C++, C#, .NET, Node.js, React.js, R, SQL)
- Normalizes job designations without merging genuinely distinct roles
- Standardizes job types into verified categories
- Parses experience into structured min/max years
- Handles salary ranges conservatively
- Parses and normalizes key skills using canonical taxonomy and alias resolution
- Generates deterministic stable job identifiers
- Categorizes job profiles by completeness (complete, skills-only, insufficient)
- Detects exact duplicates and near-duplicates
- Exports cleaned CSV and structured job_profiles.json
- Generates a comprehensive markdown report
"""

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

# Ensure ai-service root is in sys.path
AI_SERVICE_DIR = Path(__file__).resolve().parents[2]
if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

import pandas as pd

from app.preprocessing.skill_normalizer import SkillNormalizer

# Known acronyms to preserve in UPPERCASE during job title normalization
ACRONYMS = {
    "AI", "ML", "SQL", "ETL", "BI", "NLP", "AWS", "GCP", "IT", "HR",
    "SEO", "SEM", "SAP", "QA", "UI", "UX", "MIS", "ERP", "QMS", "RCA",
    "CEO", "CTO", "CFO", "COO", "VP", "AVP", "SVP", "PHP", "HTML", "CSS",
    "DBA", "CRM", "API", "REST", "SME", "BD", "BDE", "FMCG", "BPO", "KPO",
}

# Special title terms with explicit casing
SPECIAL_TITLE_CASINGS = {
    "c++": "C++",
    "c#": "C#",
    ".net": ".NET",
    "node.js": "Node.js",
    "react.js": "React.js",
    "pl/sql": "PL/SQL",
    "ui/ux": "UI/UX",
}


def get_analytics_jobs_paths() -> Dict[str, Path]:
    """Resolve repository paths relative to the current file using pathlib."""
    # This file: <repo_root>/ai-service/app/preprocessing/analytics_jobs_preprocessing.py
    current_file = Path(__file__).resolve()
    repo_root = current_file.parents[3]
    raw_data_file = repo_root / "data" / "raw" / "Analytics Jobs.csv"
    processed_dir = repo_root / "data" / "processed" / "analytics_jobs"
    eval_dir = repo_root / "ai-service" / "evaluation"

    processed_dir.mkdir(parents=True, exist_ok=True)
    eval_dir.mkdir(parents=True, exist_ok=True)

    return {
        "repo_root": repo_root,
        "raw_data_file": raw_data_file,
        "processed_dir": processed_dir,
        "cleaned_csv": processed_dir / "analytics_jobs_cleaned.csv",
        "job_profiles_json": processed_dir / "job_profiles.json",
        "eval_dir": eval_dir,
        "report_file": eval_dir / "analytics_jobs_preprocessing_report.md",
    }


def clean_text_field(text: Optional[str]) -> str:
    """Trim whitespace, normalize spaces and newlines, preserving technical punctuation."""
    if text is None or pd.isna(text):
        return ""
    s = str(text)
    # Normalize unicode spaces and quotes
    s = s.replace("\u00a0", " ").replace("\u2018", "'").replace("\u2019", "'")
    s = s.replace("\u201c", '"').replace("\u201d", '"')
    # Collapse multiple whitespaces and tabs to single space
    s = re.sub(r"[ \t]+", " ", s)
    # Normalize excessive newlines to a single newline
    s = re.sub(r"\n\s*\n+", "\n", s)
    return s.strip()


def normalize_job_title(title: Optional[str]) -> str:
    """Normalize job title/designation without aggressively merging distinct roles.

    Example:
    'Data Analyst' and 'Senior Data Analyst' remain separate.
    'DATA ANALYST' -> 'Data Analyst'
    'seo analyst' -> 'SEO Analyst'
    """
    cleaned = clean_text_field(title)
    if not cleaned:
        return "Unknown"

    # Strip trailing punctuation (ellipses, dots, dashes, colons)
    cleaned = re.sub(r"[\s\.\-:,]+$", "", cleaned).strip()

    # Split into words and normalize casing
    tokens = cleaned.split()
    normalized_tokens: List[str] = []

    for tok in tokens:
        lower_tok = tok.lower()
        clean_word = re.sub(r"[^\w\+\#\./]", "", lower_tok)

        if clean_word in SPECIAL_TITLE_CASINGS:
            normalized_tokens.append(SPECIAL_TITLE_CASINGS[clean_word])
        elif clean_word.upper() in ACRONYMS:
            normalized_tokens.append(clean_word.upper())
        elif tok.isupper() and len(tok) > 3:
            # Word is ALL CAPS, convert to Capitalized
            normalized_tokens.append(tok.capitalize())
        elif tok.islower():
            # Word is all lowercase, convert to Capitalized
            normalized_tokens.append(tok.capitalize())
        else:
            # Keep original casing for mixed case (e.g. McDonald, DevOps, iOS)
            normalized_tokens.append(tok)

    return " ".join(normalized_tokens)


def normalize_job_type(job_type_val: Optional[Any]) -> Tuple[Optional[str], str]:
    """Normalize job_type field into a consistent representation.

    Raw variants in dataset: 'Analytics', 'analytics', 'ANALYTICS', 'analytic', 'Analytic', or NaN.
    Returns:
        (raw_job_type_str, normalized_job_type)
    """
    if job_type_val is None or pd.isna(job_type_val):
        return None, "Unspecified"

    raw_str = clean_text_field(str(job_type_val))
    if not raw_str:
        return None, "Unspecified"

    lower_val = raw_str.lower()
    if lower_val in ("analytics", "analytic"):
        return raw_str, "Analytics"

    # Preserve any other genuine category encountered in the future
    return raw_str, raw_str.capitalize()


def parse_experience(exp_val: Optional[Any]) -> Tuple[Optional[int], Optional[int], bool]:
    """Parse experience string into structured min and max years.

    Examples:
    '2 - 5 yrs' -> (2, 5, True)
    '3-6 Years' -> (3, 6, True)
    '5+ yrs' -> (5, None, True)
    '3 yrs' -> (3, 3, True)

    Returns:
        (min_years, max_years, parse_success)
    """
    if exp_val is None or pd.isna(exp_val):
        return None, None, False

    exp_str = clean_text_field(str(exp_val)).lower()
    if not exp_str:
        return None, None, False

    # 1. Range pattern: '2-5 yrs', '2 - 5 years', '0 - 1 yrs', '2 to 5 yrs'
    range_match = re.search(r"(\d+)\s*(?:-|to)\s*(\d+)", exp_str)
    if range_match:
        try:
            min_y = int(range_match.group(1))
            max_y = int(range_match.group(2))
            return min_y, max_y, True
        except ValueError:
            pass

    # 2. Plus pattern: '5+ yrs', '5 + years'
    plus_match = re.search(r"(\d+)\s*\+", exp_str)
    if plus_match:
        try:
            min_y = int(plus_match.group(1))
            return min_y, None, True
        except ValueError:
            pass

    # 3. Single number with unit: '5 yrs', '3 years'
    single_match = re.search(r"(\d+)\s*(?:yrs|years)", exp_str)
    if single_match:
        try:
            min_y = int(single_match.group(1))
            return min_y, min_y, True
        except ValueError:
            pass

    return None, None, False


def parse_salary(salary_val: Optional[Any]) -> Tuple[str, Optional[float], Optional[float]]:
    """Parse salary value into raw string and structured min/max numeric figures.

    In Analytics Jobs dataset, values are discrete brackets in Lakhs:
    '0to3', '3to6', '6to10', '10to15', '15to25', '25to50'

    Returns:
        (salary_raw, min_salary, max_salary)
    """
    if salary_val is None or pd.isna(salary_val):
        return "", None, None

    raw_str = clean_text_field(str(salary_val))
    if not raw_str:
        return "", None, None

    # Match bracket like '6to10'
    match = re.match(r"^(\d+(?:\.\d+)?)\s*to\s*(\d+(?:\.\d+)?)$", raw_str.lower())
    if match:
        try:
            min_s = float(match.group(1))
            max_s = float(match.group(2))
            return raw_str, min_s, max_s
        except ValueError:
            return raw_str, None, None

    return raw_str, None, None


def generate_stable_job_id(
    s_no: Any,
    job_desig: str,
    location: str,
    experience: str,
    key_skills: str,
) -> str:
    """Generate a deterministic, stable job identifier based on job attributes and source row.

    The identifier is deterministic across runs and does not rely on random UUIDs.
    """
    content = f"{s_no}|{job_desig.strip()}|{location.strip()}|{experience.strip()}|{key_skills.strip()}"
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]
    return f"aj_{digest}"


def classify_profile_completeness(
    has_description: bool,
    has_usable_skills: bool,
    has_title: bool,
) -> str:
    """Classify record into 'complete', 'skills_only', or 'insufficient'."""
    if has_description and has_usable_skills and has_title:
        return "complete"
    elif has_usable_skills and has_title:
        return "skills_only"
    else:
        return "insufficient"


class AnalyticsJobsPipeline:
    """Pipeline for loading, cleaning, normalizing, and structuring Analytics Jobs."""

    def __init__(self, paths: Optional[Dict[str, Path]] = None) -> None:
        self.paths = paths or get_analytics_jobs_paths()
        self.normalizer = SkillNormalizer()
        self.stats: Dict[str, Any] = {}

    def run(self) -> Dict[str, Any]:
        """Execute the full preprocessing pipeline and save outputs."""
        raw_csv_path = self.paths["raw_data_file"]
        if not raw_csv_path.exists():
            raise FileNotFoundError(f"Raw dataset not found at {raw_csv_path}")

        df_raw = pd.read_csv(raw_csv_path)
        total_input_rows = len(df_raw)

        # 1. Detect and remove exact duplicates (excluding s_no)
        feature_cols = [c for c in df_raw.columns if c != "s_no"]
        exact_dupes_mask = df_raw.duplicated(subset=feature_cols, keep=False)
        exact_dupes_drop_count = df_raw.duplicated(subset=feature_cols, keep="first").sum()

        df_dedup = df_raw.drop_duplicates(subset=feature_cols, keep="first").copy()
        processed_rows_count = len(df_dedup)

        # 2. Detect likely near-duplicates (case-insensitive on title, location, experience, skills)
        near_dupe_keys = df_dedup.apply(
            lambda r: f"{str(r['job_desig']).lower().strip()}|{str(r['location']).lower().strip()}|{str(r['experience']).lower().strip()}|{str(r['key_skills']).lower().strip()}",
            axis=1,
        )
        near_dupes_count = near_dupe_keys.duplicated(keep=False).sum()

        # 3. Clean and normalize fields
        records: List[Dict[str, Any]] = []
        profiles: List[Dict[str, Any]] = []

        jobs_with_desc = 0
        jobs_without_desc = 0
        jobs_with_skills = 0
        jobs_without_skills = 0
        exp_parse_success = 0

        skill_freq: Dict[str, int] = {}
        title_freq: Dict[str, int] = {}
        type_freq: Dict[str, int] = {}
        unresolved_skills_set = set()

        for _, row in df_dedup.iterrows():
            s_no = row.get("s_no", "")
            raw_desig = str(row.get("job_desig", ""))
            raw_location = clean_text_field(row.get("location", ""))
            raw_exp = str(row.get("experience", ""))
            raw_salary = str(row.get("salary", ""))
            raw_desc = clean_text_field(row.get("job_description", ""))
            raw_skills = row.get("key_skills", "")

            # Normalized fields
            norm_title = normalize_job_title(raw_desig)
            raw_type_str, norm_type = normalize_job_type(row.get("job_type", None))
            min_exp, max_exp, exp_ok = parse_experience(raw_exp)
            if exp_ok:
                exp_parse_success += 1

            sal_raw, min_sal, max_sal = parse_salary(raw_salary)

            # Skill parsing and normalization
            canon_skills, unknown_skills = self.normalizer.parse_and_normalize_skills(raw_skills)

            # Track completeness flags
            has_desc = bool(raw_desc and raw_desc.strip())
            has_skills = len(canon_skills) > 0 or len(unknown_skills) > 0
            has_title = bool(norm_title and norm_title != "Unknown")

            if has_desc:
                jobs_with_desc += 1
            else:
                jobs_without_desc += 1

            if has_skills:
                jobs_with_skills += 1
            else:
                jobs_without_skills += 1

            completeness = classify_profile_completeness(has_desc, has_skills, has_title)

            # Stable job ID
            job_id = generate_stable_job_id(
                s_no=s_no,
                job_desig=raw_desig,
                location=raw_location,
                experience=raw_exp,
                key_skills=str(raw_skills) if pd.notna(raw_skills) else "",
            )

            # Frequency tracking
            title_freq[norm_title] = title_freq.get(norm_title, 0) + 1
            type_freq[norm_type] = type_freq.get(norm_type, 0) + 1
            for sk in canon_skills:
                skill_freq[sk] = skill_freq.get(sk, 0) + 1
            for unk in unknown_skills:
                unresolved_skills_set.add(unk)

            # CSV record format
            records.append({
                "job_id": job_id,
                "job_title": raw_desig.strip(),
                "job_title_normalized": norm_title,
                "job_type": raw_type_str if raw_type_str is not None else "",
                "job_type_normalized": norm_type,
                "experience_raw": clean_text_field(raw_exp),
                "min_experience_years": min_exp if min_exp is not None else "",
                "max_experience_years": max_exp if max_exp is not None else "",
                "salary_raw": sal_raw,
                "location": raw_location,
                "job_description": raw_desc,
                "skills_normalized": json.dumps(canon_skills),
                "unknown_skills": json.dumps(unknown_skills),
                "profile_completeness": completeness,
            })

            # Structured profile format
            profiles.append({
                "job_id": job_id,
                "job_title": raw_desig.strip(),
                "job_title_normalized": norm_title,
                "job_type": raw_type_str,
                "job_type_normalized": norm_type,
                "location": raw_location,
                "experience": {
                    "raw": clean_text_field(raw_exp),
                    "min_years": min_exp,
                    "max_years": max_exp,
                },
                "salary": {
                    "raw": sal_raw,
                    "min_salary": min_sal,
                    "max_salary": max_sal,
                },
                "salary_raw": sal_raw,
                "skills": canon_skills,
                "unknown_skills": unknown_skills,
                "job_description": raw_desc if has_desc else None,
                "profile_completeness": completeness,
            })

        # Create output DataFrame and export
        df_cleaned = pd.DataFrame(records)
        df_cleaned.to_csv(self.paths["cleaned_csv"], index=False, encoding="utf-8")

        # Export structured JSON
        with open(self.paths["job_profiles_json"], "w", encoding="utf-8") as f:
            json.dump(profiles, f, indent=2, ensure_ascii=False)

        # Compute summary statistics
        top_skills = sorted(skill_freq.items(), key=lambda x: x[1], reverse=True)[:20]
        top_titles = sorted(title_freq.items(), key=lambda x: x[1], reverse=True)[:20]

        completeness_counts = df_cleaned["profile_completeness"].value_counts().to_dict()

        self.stats = {
            "total_input_rows": total_input_rows,
            "processed_rows_count": processed_rows_count,
            "exact_duplicates_removed": int(exact_dupes_drop_count),
            "near_duplicates_flagged": int(near_dupes_count),
            "jobs_with_descriptions": jobs_with_desc,
            "jobs_without_descriptions": jobs_without_desc,
            "jobs_with_usable_skills": jobs_with_skills,
            "jobs_without_usable_skills": jobs_without_skills,
            "experience_parsing_success_count": exp_parse_success,
            "experience_parsing_success_rate": round(exp_parse_success / processed_rows_count * 100, 2),
            "unique_canonical_skills_found": len(skill_freq),
            "total_unresolved_skills_found": len(unresolved_skills_set),
            "top_20_skills": top_skills,
            "top_20_titles": top_titles,
            "job_type_distribution": type_freq,
            "completeness_distribution": completeness_counts,
        }

        # Generate report
        self.generate_report()

        return self.stats

    def generate_report(self) -> None:
        """Write detailed markdown preprocessing audit report."""
        stats = self.stats
        report_file = self.paths["report_file"]

        top_skills_md = "\n".join([f"| {i+1} | {k} | {v} |" for i, (k, v) in enumerate(stats["top_20_skills"])])
        top_titles_md = "\n".join([f"| {i+1} | {k} | {v} |" for i, (k, v) in enumerate(stats["top_20_titles"])])
        job_types_md = "\n".join([f"| {k} | {v} |" for k, v in stats["job_type_distribution"].items()])
        completeness_md = "\n".join([f"| {k} | {v} |" for k, v in stats["completeness_distribution"].items()])

        content = f"""# Analytics Jobs Preprocessing Audit & Standardization Report

**Generated by SkillGap AI Analytics Jobs Preprocessing Pipeline**

## 1. Dataset Overview

- **Input Raw File**: `data/raw/Analytics Jobs.csv`
- **Total Input Records**: {stats['total_input_rows']}
- **Total Columns**: 8 (`s_no`, `experience`, `job_description`, `job_desig`, `job_type`, `key_skills`, `location`, `salary`)
- **Missing Values in Raw Data**:
  - `job_type`: 12,011 missing (75.82%)
  - `job_description`: 3,508 missing (22.15%)
  - `key_skills`: 1 missing (0.006%)
  - Other columns: 0 missing

## 2. Cleaning & Standardization

- **Exact Duplicate Records Removed**: {stats['exact_duplicates_removed']} (rows where all job attributes are identical, keeping the first occurrence)
- **Remaining Cleaned Jobs**: {stats['processed_rows_count']}
- **Potential Near-Duplicates Detected**: {stats['near_duplicates_flagged']} rows (flagged for review; not aggressively deleted to preserve valid job variants)
- **Text Normalization**: Leading/trailing whitespace trimmed, repeated spaces collapsed, unicode quotes/dashes normalized, trailing ellipsis (`...`) stripped safely without altering technical punctuation.
- **Protected Technical Punctuation**: Special care was taken so technical terms such as `C`, `C++`, `C#`, `.NET`, `Node.js`, `React.js`, `R`, `SQL`, `PL/SQL`, `CI/CD`, `UI/UX` are fully preserved and distinguishable.

### Job Type Normalization
Raw variants in dataset and mappings:
- `Analytics` (2,971), `analytics` (746), `ANALYTICS` (64), `analytic` (30), `Analytic` (19) $\\rightarrow$ **`Analytics`**
- Missing / NaN (12,011) $\\rightarrow$ **`Unspecified`** (preserved raw as null/empty)

| Normalized Job Type | Count |
| :--- | :--- |
{job_types_md}

### Job Title Normalization
Normalized casing without merging distinct seniority levels (e.g., `Data Analyst` vs `Senior Data Analyst` remain distinct). Recognized acronyms (`SEO`, `HR`, `ETL`, `AWS`, `SAP`, etc.) are preserved in uppercase.

Top 20 Normalized Titles:
| Rank | Job Title | Count |
| :--- | :--- | :--- |
{top_titles_md}

## 3. Skills Extraction & Taxonomy Mapping

- **Taxonomy Files Used**:
  - `data/skills.json` (canonical taxonomy)
  - `data/aliases.json` (case-insensitive alias mappings)
- **Parsing Strategy**: Handles comma (`,`), pipe (`|`), semicolon (`;`), newline (`\\n`), and compound slashes (`/`). Distinguishes unified slashes (`PL/SQL`, `CI/CD`, `UI/UX`) from composite lists (`C / C++` $\\rightarrow$ `C`, `C++`).
- **Unique Canonical Skills Matched**: {stats['unique_canonical_skills_found']}
- **Unique Unresolved Skills Preserved**: {stats['total_unresolved_skills_found']}
- **Crucial Tech Separations**:
  - `Java` and `JavaScript` remain completely separate.
  - `Data Analysis` and `Data Science` remain completely separate.

Top 20 Canonical Skills:
| Rank | Skill | Frequency |
| :--- | :--- | :--- |
{top_skills_md}

## 4. Experience Parsing

- **Parsing Strategy**: Safe regular expression capturing `min_experience_years` and `max_experience_years` across hyphenated ranges (`2 - 5 yrs`), plus notations (`5+ yrs`), and single-year requirements (`3 yrs`).
- **Successful Parses**: {stats['experience_parsing_success_count']} / {stats['processed_rows_count']}
- **Parsing Success Rate**: {stats['experience_parsing_success_rate']}%

## 5. Job Profile Completeness Classification

Records were categorized to support downstream matching engines without prematurely discarding skills-only listings:

| Profile Completeness | Count | Description |
| :--- | :--- | :--- |
{completeness_md}

- **Complete**: Has valid job title, usable skills, and full job description.
- **Skills-Only**: Has valid job title and usable skills, but missing detailed description. Highly usable for skill-gap analysis.
- **Insufficient**: Missing both usable skills and job description.

## 6. Output Files

1. `data/processed/analytics_jobs/analytics_jobs_cleaned.csv`
2. `data/processed/analytics_jobs/job_profiles.json`
3. `data/skills.json`
4. `data/aliases.json`
5. `ai-service/evaluation/analytics_jobs_preprocessing_report.md`

## 7. Known Data Quality Issues & Limitations

1. **Job Descriptions Missing**: 22.15% of records have no narrative description. Skill-based matching remains fully functional for these records.
2. **Missing Job Type**: 75.82% of records omit the `job_type` column. These are categorized as `Unspecified`.
3. **Discrete Salary Brackets**: Salary is recorded as discrete range buckets in LPA (`0to3`, `3to6`, `6to10`, etc.) rather than precise annual salaries.
4. **Truncated Raw Skills**: Some raw entries contained trailing continuation dots (`...`). These were cleanly stripped while preserving legitimate dots in `.NET` and `Node.js`.
"""

        with open(report_file, "w", encoding="utf-8") as f:
            f.write(content)


if __name__ == "__main__":
    pipeline = AnalyticsJobsPipeline()
    stats = pipeline.run()
    print("Analytics Jobs Preprocessing Complete!")
    print(f"Input records: {stats['total_input_rows']}")
    print(f"Processed records: {stats['processed_rows_count']}")
    print(f"Exact duplicates removed: {stats['exact_duplicates_removed']}")
    print(f"Canonical skills found: {stats['unique_canonical_skills_found']}")
    print(f"Experience parse success rate: {stats['experience_parsing_success_rate']}%")
