@'
# SkillGap AI
## AI-Powered Data Science Career Intelligence

SkillGap AI is an analytics-first career intelligence platform designed to analyze data-science-related job markets, technical skills, salary patterns, and personality characteristics.

The project transforms organizer-provided datasets into evidence-backed career insights, statistical findings, machine-learning analysis, and actionable recommendations through an interactive web dashboard.

---

## 🎯 Problem Statement

Students and early-career professionals often struggle to understand:

- Which skills are associated with better salary outcomes
- What the current data-science job market looks like
- How experience, location, job type, and skills relate to compensation
- Which technical skill dimensions are associated with higher salary hikes
- Which personality characteristics are associated with higher success classifications
- How these findings can be converted into practical career recommendations

SkillGap AI addresses this challenge by combining exploratory data analysis, statistical analysis, machine learning, and interactive visualization.

---

## 💡 Core Objective

> Identify the skills, job-market factors, compensation patterns, and personality characteristics associated with opportunities and success in data-science-related careers, and convert those findings into evidence-backed career intelligence.

The platform focuses on **association, prediction, and analytical insight**.

It does **not** claim causation unless the underlying data and methodology support such a claim.

---

# 📊 Organizer Data

The project uses four organizer-provided datasets.

### 1. Analytics Jobs

Contains job-market information such as:

- Experience
- Job description
- Designation
- Job type
- Key skills
- Location
- Salary

Used primarily for:

**Job Market Intelligence**

---

### 2. DataScience Jobs

Contains information such as:

- Company
- Job title
- Minimum experience
- Average salary
- Minimum salary
- Maximum salary
- Number of jobs

Used primarily for:

**Data Science Job & Salary Intelligence**

---

### 3. JDS Skill Traits

Contains technical skill dimensions including:

- Big Data
- Mathematics / Statistics
- Coding
- AI / Machine Learning
- Dashboard / Storytelling

Target:

- Salary hike classification

Used primarily for:

**Technical Skill → Salary-Hike Intelligence**

---

### 4. SDS Personality Traits

Contains Big Five personality dimensions:

- Neuroticism
- Extraversion
- Openness
- Agreeableness
- Conscientiousness

Target:

- Success classification

Used primarily for:

**Personality → Success Intelligence**

---

## ⚠️ Data Governance

The organizer-provided raw datasets are treated as immutable source data.

Raw files are intentionally excluded from Git tracking.

```text
data/
├── raw/              # Organizer datasets — NOT committed
├── processed/        # Generated processed data
└── evaluation/      # Evaluation artifacts