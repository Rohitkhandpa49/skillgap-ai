# Baseline Candidate-to-Job Matching Engine Evaluation Report

**Generated for SkillGap AI Matching Engine (Analytics Jobs Corpus)**

## 1. Architecture

```
Candidate Profile
       │
       ▼
Skill Normalizer ──► Canonical Skills & Preserved Unresolved Skills
       │
       ├─────────────────────────────────┬─────────────────────────────────┐
       ▼                                 ▼                                 ▼
Candidate Text (Summary + Skills)   Explicit Skills Set            Experience Comparator
       │                                 │                                 │
       ▼                                 ▼                                 │
TF-IDF Candidate Vector             Skill Overlap Calculation              │
       │                                 │                                 │
       ▼                                 ▼                                 │
Cosine Text Similarity (0.0–1.0)    Skill Overlap Score (0.0–1.0)          │
       │                                 │                                 │
       └────────────────► Weighted Score ◄─────────────────────────────────┘
                                │
                                ▼
                       Deterministic Ranking
                     (Score desc, Overlap desc, ID asc)
                                │
                                ▼
                       Top-K Job Recommendations
                    + Human-Readable Explanations
```

### Core Components
1. **Candidate Skill Normalization**: Normalizes incoming raw candidate skills using the canonical taxonomy (`data/skills.json` and `data/aliases.json`). For instance, `ML` resolves to `Machine Learning`, `Postgres` to `PostgreSQL`, and `ReactJS` to `React`, while retaining unknown domain-specific tools.
2. **TF-IDF Vector Space**: Scikit-learn `TfidfVectorizer` fitted solely on the job corpus (`14,840` postings). Technical tokens such as `C++`, `C#`, `.NET`, `Node.js`, `React.js`, and `R` are preserved via custom regex tokenization without character loss.
3. **Explicit Skill Overlap**: Exact set overlap normalized by total required job skills:
   $$\text{Skill Overlap Score} = \frac{\text{Matched Required Skills}}{\text{Total Required Job Skills}}$$
4. **Text Similarity**: Cosine similarity between candidate representation and pre-computed sparse job matrix.
5. **Deterministic Ranking**: Primary sort by `match_score` descending, secondary tie-breaker by `skill_overlap` descending, and final tie-breaker by `job_id` ascending.

---

## 2. Weighting Formula

$$\text{Final Match Score} = \left(0.70 \times \text{Skill Overlap} + 0.30 \times \text{TF-IDF Text Similarity}\right) \times 100$$

> [!NOTE]
> **Baseline Heuristic Weighting**: This weighting is a deterministic heuristic designed for cold-start explainability. It is not a scientifically trained ML weighting.
>
> **Strict Isolation**: The supervised JDS salary-hike classifier and SDS personality-success classifier are **strictly excluded** from job matching to ensure personality predictions do not introduce algorithmic bias into job suitability.

---

## 3. Evaluation on Synthetic Candidates

Tested against 5 diverse synthetic candidate profiles representing distinct specializations:

### Synthetic Candidate A (Data Analyst) (`candidate_a_data_analyst`)
- **Skills**: SQL, Excel, Python, Power BI, Data Analysis
- **Summary**: Experienced Data Analyst skilled in extracting insights using SQL queries, creating executive dashboards in Power BI and Excel, and performing exploratory data analysis with Python.
- **Inference Latency**: 1164.17 ms

| Rank | Job Title | Match Score | Skill Overlap | Text Sim | Matched Skills | Missing Skills | Experience |
| :---: | :--- | :---: | :---: | :---: | :--- | :--- | :---: |
| 1 | **Data Analyst MIS Executive** | **75.3%** | 100.0% | 17.7% | Data Analysis | None | compatible |
| 2 | **Data Analytics** | **74.8%** | 100.0% | 16.0% | Data Analysis | None | compatible |
| 3 | **Data Analyst / Travel Based Company / Mansarovar ( Jaipur )** | **73.5%** | 100.0% | 11.8% | Data Analysis | None | compatible |
| 4 | **Manager/ Sr. Manager Ã¢â?¬â?? Data Analytics** | **72.9%** | 100.0% | 9.8% | Data Analysis | None | gap |
| 5 | **Research Associate** | **72.4%** | 100.0% | 8.1% | Excel | None | compatible |

### Synthetic Candidate B (Machine Learning Engineer) (`candidate_b_ml_engineer`)
- **Skills**: Python, Machine Learning, Deep Learning, TensorFlow, Scikit-Learn, NLP
- **Summary**: Machine learning practitioner with expertise developing predictive models, deep learning architectures using TensorFlow, and natural language processing pipelines in Python.
- **Inference Latency**: 1031.45 ms

| Rank | Job Title | Match Score | Skill Overlap | Text Sim | Matched Skills | Missing Skills | Experience |
| :---: | :--- | :---: | :---: | :---: | :--- | :--- | :---: |
| 1 | **Data Scientist-lead** | **88.1%** | 100.0% | 60.3% | Deep Learning, Machine Learning, Natural Language Processing | None | gap |
| 2 | **Python Developer** | **87.9%** | 100.0% | 59.8% | Deep Learning, Machine Learning, Natural Language Processing, Python | None | gap |
| 3 | **Python Developer** | **87.9%** | 100.0% | 59.8% | Deep Learning, Machine Learning, Natural Language Processing, Python | None | gap |
| 4 | **NLP Expert (natural Language Processing)** | **87.1%** | 100.0% | 56.9% | Deep Learning, Machine Learning, Natural Language Processing, Python | None | gap |
| 5 | **NLP Expert (natural Language Processing)** | **87.1%** | 100.0% | 56.9% | Deep Learning, Machine Learning, Natural Language Processing, Python | None | gap |

### Synthetic Candidate C (Data Engineer) (`candidate_c_data_engineer`)
- **Skills**: Python, SQL, Spark, Hadoop, ETL, Data Warehousing, Big Data
- **Summary**: Big Data Engineer focused on building distributed data pipelines using Apache Spark and Hadoop, designing scalable ETL workflows, and relational data warehousing.
- **Inference Latency**: 1118.49 ms

| Rank | Job Title | Match Score | Skill Overlap | Text Sim | Matched Skills | Missing Skills | Experience |
| :---: | :--- | :---: | :---: | :---: | :--- | :--- | :---: |
| 1 | **Data Scientist** | **79.0%** | 100.0% | 29.9% | Big Data, Hadoop, Python, Spark | None | gap |
| 2 | **Senior Big Data Engineer** | **76.7%** | 100.0% | 22.4% | Big Data, Hadoop | None | gap |
| 3 | **Senior Big Data Engineer** | **76.7%** | 100.0% | 22.4% | Big Data, Hadoop | None | gap |
| 4 | **Great Opportunity With Mnc: Looking For Spark Programmer** | **76.0%** | 100.0% | 20.0% | Spark | None | gap |
| 5 | **QA - Analytics** | **72.0%** | 100.0% | 6.8% | SQL | None | compatible |

### Synthetic Candidate D (Business Analyst) (`candidate_d_business_analyst`)
- **Skills**: Excel, SQL, Business Analysis, Tableau, Agile, Requirements Analysis
- **Summary**: Business Analyst experienced in bridging stakeholder requirements, functional documentation in Agile teams, SQL reporting, and building interactive Tableau visualizations.
- **Inference Latency**: 979.12 ms

| Rank | Job Title | Match Score | Skill Overlap | Text Sim | Matched Skills | Missing Skills | Experience |
| :---: | :--- | :---: | :---: | :---: | :--- | :--- | :---: |
| 1 | **Business Analyst** | **76.0%** | 100.0% | 20.2% | Business Analysis | None | gap |
| 2 | **Business Analyst** | **76.0%** | 100.0% | 20.2% | Business Analysis | None | gap |
| 3 | **Sr Assoc Business Analyst** | **75.9%** | 100.0% | 19.7% | Business Analysis | None | gap |
| 4 | **HCL Technologies Limited - Hiring Business Analyst Chennai** | **75.3%** | 100.0% | 17.6% | Business Analysis | None | gap |
| 5 | **Hiring For SAP Business Analyst Associate** | **74.2%** | 100.0% | 14.0% | Business Analysis | None | compatible |

### Synthetic Candidate E (Weak / Unrelated) (`candidate_e_weak_unrelated`)
- **Skills**: Woodworking, Creative Writing, Classical Guitar
- **Summary**: Acoustic musician and creative writer interested in exploring digital technology and analytical hobbies.
- **Inference Latency**: 757.46 ms

| Rank | Job Title | Match Score | Skill Overlap | Text Sim | Matched Skills | Missing Skills | Experience |
| :---: | :--- | :---: | :---: | :---: | :--- | :--- | :---: |
| 1 | **Academic Research Writer | Research Writing | MBA Job | MA English** | **28.2%** | 25.0% | 35.6% | Creative Writing | academic research, mba fresher, mba marketing | compatible |
| 2 | **Creative Content Writer** | **26.1%** | 16.7% | 48.2% | Creative Writing | Content Writing, Editorial, HTML, Journalism, Wordpress | gap |
| 3 | **Content Auditor** | **22.9%** | 25.0% | 17.9% | Creative Writing | Content Analysis, content research, copy writing | gap |
| 4 | **Content Optimization Executive - Nsez Phase II, Noida** | **19.3%** | 20.0% | 17.5% | Creative Writing | Google Analytics, academic, content optimization, writing | compatible |
| 5 | **Content Writer** | **19.2%** | 16.7% | 25.1% | Creative Writing | Content Writing, Google Analytics, SEM, SEO, Social Media Marketing | gap |

---

## 4. Behavioral & Sanity Test Matrix

| Sanity Test | Status | Expected Behavior | Verification Details |
| :--- | :---: | :--- | :--- |
| **Monotonic Skill Addition** | **PASS** | Adding a missing required job skill must not decrease score | Before: overlap=0.1667, score=18.04 | After: overlap=0.3333, score=36.91 |
| **Irrelevant Skill Addition** | **PASS** | Adding unrelated skills must not artificially increase overlap | Original overlap: 0.1667 | With irrelevant skills: 0.1667 |
| **Exact Skill Match** | **PASS** | Matching 100% of required skills gives 1.0 overlap | Overlap score: 1.0 |
| **Empty Candidate Safety** | **PASS** | Empty profile yields 0.0 scores without NaN or division by zero | Top score: 0.0 |
| **Job Without Skills** | **PASS** | Zero required skills handled safely without ZeroDivisionError | Evaluated job aj_8570469b5249: overlap=0.0 |
| **Missing Job Description** | **PASS** | Falls back cleanly to job title and skills | Job without description (aj_8013c710d906) matched with score 0.0 |
| **Deterministic Ranking** | **PASS** | Identical input produces identical ranking and scores | IDs match: True |

---

## 5. Performance & Latency

- **Corpus Size**: 14,840 preprocessed jobs
- **TF-IDF Matrix Shape**: `(14840, 10000)` sparse CSR matrix
- **Average Inference Runtime**: `1010.14 ms` per candidate
- **TF-IDF Vocabulary Size**: 10,000 features
- **Pre-fitting Strategy**: Vectorizer and job matrix are persisted to disk and transformed once; candidate queries require only a single sparse dot-product transformation.

---

## 6. Output Files & Artifacts

1. `ai-service/app/matching/schemas.py`: Pydantic candidate and result schemas
2. `ai-service/app/matching/baseline_matcher.py`: Core matching and ranking engine
3. `ai-service/app/services/job_matching_service.py`: Service wrapper
4. `ai-service/models/matching/tfidf_vectorizer.joblib`: Persisted TF-IDF vectorizer (422 KB)
5. `ai-service/models/matching/job_tfidf_matrix.joblib`: Persisted TF-IDF job matrix (4.5 MB)
6. `ai-service/models/matching/job_tfidf_job_ids.json`: Persisted job ID mapping (326 KB)
7. `ai-service/models/matching/baseline_matching_metadata.json`: Model and pipeline metadata
8. `ai-service/evaluation/matching/test_candidates.json`: 5 synthetic test profiles
9. `ai-service/training/demo_baseline_matcher.py`: Interactive CLI demonstration

---

## 7. Known Limitations & Future Work

1. **Cold-Start Heuristic Weights**: The $70/30$ split between skill overlap and text similarity is a transparent heuristic rather than a scientifically trained preference model.
2. **Keyword vs Semantic Synonymy**: TF-IDF cannot recognize deep semantic synonyms outside n-grams and alias tables (e.g. "Kubernetes orchestration" vs "container management"). Dense embeddings (Sentence-Transformers) will be introduced in future iterations.
3. **Exact Denominator Sensitivity**: Jobs with only 1 listed skill (e.g. only "Python") can reach 100% skill overlap easily, whereas jobs with 10 skills require broad coverage. The tie-breaker and text similarity partially temper this.
4. **Decision Support, Not Automated Decisions**: Match outputs are explainable ranking aids for career guidance and skill gap visualization, not automated hiring decisions.
