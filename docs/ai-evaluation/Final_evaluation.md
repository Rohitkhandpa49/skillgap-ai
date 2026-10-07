# FINAL AI EVALUATION + SKILL ONTOLOGY + DATASET MASTER PROMPT

## AI Talent Matching & Skill Gap Engine
### From Resume Understanding to Career Growth

---

# 0. ROLE

Act as a **Principal AI/ML Engineer, NLP Research Engineer, Information Retrieval Engineer, Knowledge Graph/Ontology Engineer, Data Scientist, Evaluation Scientist, and Responsible-AI Reviewer**.

Your job is to make the AI portion of the AI Talent Matching & Skill Gap Engine scientifically defensible, measurable, explainable, reproducible, and hackathon-ready.

The system must not merely produce attractive AI-looking outputs.

It must answer:

1. Did the system correctly extract skills?
2. Did it correctly normalize skills?
3. Does semantic matching actually improve over keyword matching?
4. Are top-ranked jobs relevant?
5. Are identified skill gaps valid?
6. Are career recommendations logically useful?
7. Can the team demonstrate evidence of AI quality?
8. Can the system explain how its outputs were produced?
9. Can the system detect when it does not have enough evidence?
10. Can the evaluation be repeated after changing the model?

---

# 1. CORE AI PIPELINE

Use this canonical pipeline:

```text
                  RESUME
                    │
                    ▼
            Document Parsing
                    │
                    ▼
              Raw Text
                    │
                    ▼
           Text Preprocessing
                    │
                    ▼
             Section Detection
                    │
                    ▼
             Skill Extraction
                    │
                    ▼
          Skill Normalization
                    │
                    ▼
             Candidate Profile
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
     Skill Vector         Text Vector
          │                   │
          └─────────┬─────────┘
                    ▼
             Matching Engine
                    │
        ┌───────────┼────────────┐
        ▼           ▼            ▼
      Score     Explanation    Skill Gap
        │           │            │
        └───────────┼────────────┘
                    ▼
             Career Roadmap
                    │
                    ▼
             What-If Simulator
```

---

# 2. AI SYSTEM OBJECTIVES

The AI subsystem must support:

```text
A. Resume understanding
B. Skill extraction
C. Skill normalization
D. Evidence extraction
E. Candidate profiling
F. Job representation
G. Semantic similarity
H. Skill overlap
I. Hybrid ranking
J. Explainability
K. Skill-gap detection
L. Career recommendation
M. What-if simulation
N. Evaluation
O. Fairness analysis
```

---

# 3. PRINCIPLE: MEASURE BEFORE CLAIMING

Never write:

```text
"AI is highly accurate."
```

unless there is evidence.

Instead report:

```text
Skill extraction F1: 0.xx
Top-5 matching Recall: 0.xx
Normalization accuracy: 0.xx
```

If there is no statistically meaningful evaluation, say:

```text
"Prototype evaluation on a small manually labeled benchmark."
```

Do not fabricate metrics.

---

# 4. DATA LAYERS

Use five data layers:

```text
Layer 1 — Raw Documents
Layer 2 — Extracted Evidence
Layer 3 — Normalized Knowledge
Layer 4 — Evaluation Ground Truth
Layer 5 — Model Outputs
```

Do not overwrite raw evidence with normalized information.

Example:

```text
Raw:
"worked with JS and ReactJS"

Normalized:
JavaScript
React
```

Store both.

---

# 5. DATASET ARCHITECTURE

Recommended:

```text
data/
├── raw/
│   ├── resumes/
│   └── jobs/
│
├── processed/
│   ├── resume_text/
│   ├── job_text/
│   └── profiles/
│
├── ontology/
│   ├── skills.json
│   ├── aliases.json
│   ├── categories.json
│   ├── relationships.json
│   └── roles.json
│
├── evaluation/
│   ├── resume_skill_labels.json
│   ├── normalization_labels.json
│   ├── matching_labels.json
│   ├── gap_labels.json
│   └── recommendation_labels.json
│
└── outputs/
    ├── predictions/
    └── metrics/
```

---

# 6. DATA PROVENANCE

Every important dataset should have:

```text
source
version
createdAt
updatedAt
license/usage status
annotation method
annotator information where appropriate
```

Never silently mix:

```text
real-world data
synthetic data
manually created demo data
LLM-generated data
```

Label them separately.

---

# 7. SYNTHETIC DATA

Synthetic resumes and jobs are acceptable for a hackathon benchmark.

However:

```text
synthetic ≠ real-world validation
```

Clearly state:

```text
"This benchmark contains synthetic and manually curated examples."
```

Do not present synthetic benchmark performance as production accuracy.

---

# 8. DATASET SIZE

For a 15-hour hackathon prototype, a practical benchmark can be:

```text
20–50 resumes
20–50 jobs
50–150 normalized skills
5–15 role categories
```

The exact size is less important than:

```text
quality
coverage
clear labels
repeatability
```

---

# 9. SKILL ONTOLOGY

Create canonical skills.

Example:

```json
{
  "id": "SK001",
  "name": "Python",
  "category": "Programming",
  "aliases": [
    "python3",
    "python programming"
  ],
  "relatedSkills": [
    "NumPy",
    "Pandas",
    "FastAPI"
  ]
}
```

---

# 10. SKILL CATEGORIES

Recommended categories:

```text
Programming
Web Development
Mobile Development
Databases
Cloud
DevOps
AI/ML
Data Science
Data Engineering
Cybersecurity
Networking
Testing
Tools
Soft Skills
Domain Skills
```

Do not create unnecessary categories.

---

# 11. SKILL HIERARCHY

Support:

```text
Machine Learning
 ├── Supervised Learning
 ├── Unsupervised Learning
 ├── Model Evaluation
 └── Feature Engineering
```

And:

```text
Python
 ├── NumPy
 ├── Pandas
 ├── FastAPI
 └── Scikit-learn
```

Do not automatically assume that parent skill means every child skill is mastered.

---

# 12. SKILL RELATION TYPES

Use explicit relationships:

```text
IS_A
ALIAS_OF
RELATED_TO
PREREQUISITE_OF
USED_WITH
SUBSKILL_OF
```

Example:

```text
Docker
    USED_WITH
Kubernetes

Python
    USED_WITH
Pandas
```

---

# 13. ROLE ONTOLOGY

Represent roles:

```json
{
  "id": "ROLE001",
  "name": "Machine Learning Engineer",
  "requiredSkills": [],
  "preferredSkills": [],
  "experienceLevel": "entry"
}
```

Separate:

```text
required
preferred
optional
```

This is essential for meaningful gap analysis.

---

# 14. JOB REPRESENTATION

Each job should include:

```text
job ID
title
description
role category
required skills
preferred skills
experience
education
certifications
location if applicable
```

Example:

```json
{
  "id": "JOB001",
  "title": "Junior ML Engineer",
  "requiredSkills": [
    "Python",
    "Machine Learning",
    "SQL"
  ],
  "preferredSkills": [
    "Docker",
    "AWS"
  ]
}
```

---

# 15. ALIAS NORMALIZATION

Map:

```text
JS → JavaScript
ReactJS → React
React.js → React
Postgres → PostgreSQL
ML → Machine Learning
NLP → Natural Language Processing
K8s → Kubernetes
```

Normalization should be:

```text
case-insensitive
whitespace-tolerant
punctuation-aware
context-aware
```

---

# 16. AMBIGUOUS SKILLS

Some terms are ambiguous.

Example:

```text
R
Go
Spark
Java
Spring
```

Do not blindly extract them.

Require context where ambiguity is high.

Example:

```text
"Go programming"
```

is stronger evidence for Go than:

```text
"Go"
```

---

# 17. NEGATION

Detect negation where practical.

Example:

```text
"Interested in learning Kubernetes"
```

should NOT become:

```text
Kubernetes = demonstrated skill
```

Similarly:

```text
"Familiar with Docker"
```

is different evidence from:

```text
"Expert in Docker"
```

Do not automatically convert wording into exact proficiency.

---

# 18. EVIDENCE MODEL

Every extracted skill should ideally include:

```json
{
  "skill": "Python",
  "evidence": "Developed backend APIs using Python",
  "section": "Projects",
  "confidence": 0.96,
  "sourceType": "project"
}
```

Possible source types:

```text
skills_section
experience
project
education
certification
coursework
summary
```

---

# 19. CONFIDENCE

Confidence should represent extraction confidence.

Example:

```text
Explicit skill section:
0.95+

Strong contextual evidence:
0.80–0.95

Weak contextual evidence:
0.50–0.80

Ambiguous:
<0.50
```

Do not hardcode these ranges as universal truth.

Calibrate them using evaluation data where possible.

---

# 20. PROFICIENCY

If implementing proficiency:

Use evidence-based levels:

```text
Beginner
Intermediate
Advanced
Unknown
```

Do not claim:

```text
"Expert"
```

because a resume mentions a skill once.

Possible evidence:

```text
years of experience
project complexity
leadership
certification
production usage
advanced terminology
```

Still treat inferred proficiency as uncertain.

---

# 21. RESUME SKILL EXTRACTION BENCHMARK

Create ground truth:

```json
{
  "resumeId": "R001",
  "goldSkills": [
    "Python",
    "SQL",
    "Machine Learning"
  ]
}
```

Prediction:

```json
{
  "resumeId": "R001",
  "predictedSkills": [
    "Python",
    "SQL",
    "Machine Learning",
    "Docker"
  ]
}
```

Then calculate:

```text
True Positives
False Positives
False Negatives
```

---

# 22. PRECISION

```text
Precision =
TP / (TP + FP)
```

Meaning:

> Of all skills predicted, how many were correct?

High precision means fewer false skills.

---

# 23. RECALL

```text
Recall =
TP / (TP + FN)
```

Meaning:

> Of all real skills, how many did the system find?

High recall means fewer missed skills.

---

# 24. F1 SCORE

```text
F1 =
2 × Precision × Recall
/
(Precision + Recall)
```

Use F1 when balancing extraction precision and recall.

---

# 25. MICRO VS MACRO F1

Use:

```text
Micro F1
```

when evaluating overall skill instances.

Use:

```text
Macro F1
```

when each resume/skill group should have equal importance.

Report what you actually calculated.

---

# 26. NORMALIZATION EVALUATION

Ground truth:

```text
"JS" → JavaScript
"ReactJS" → React
"Postgres" → PostgreSQL
```

Metric:

```text
Normalization Accuracy =
Correct Canonical Mappings
/
Total Mappings
```

Also report:

```text
unknown/ambiguous rate
```

Do not force every unknown term into a canonical skill.

---

# 27. MATCHING GROUND TRUTH

For each candidate-job pair, label:

```text
Highly Relevant
Relevant
Partially Relevant
Not Relevant
```

Or:

```text
1 = relevant
0 = not relevant
```

Prefer graded relevance if possible.

---

# 28. MATCHING BASELINES

Always compare against at least one baseline.

Baseline:

```text
keyword overlap
```

AI model:

```text
embedding similarity
```

Hybrid:

```text
embedding
+
skill overlap
+
experience
+
education
```

This answers:

> Does the AI pipeline improve over a simpler method?

---

# 29. KEYWORD BASELINE

Example:

```text
Candidate skills:
Python, SQL, ML

Job:
Python, SQL, ML, Docker
```

Keyword overlap:

```text
3 / 4 = 75%
```

Use this only as a baseline, not as the final score.

---

# 30. SEMANTIC BASELINE

Compute:

```text
cosine(candidateEmbedding, jobEmbedding)
```

Normalize into a user-facing range only after defining the mathematical interpretation.

Do not assume raw cosine similarity is automatically a percentage.

---

# 31. HYBRID MODEL

Recommended:

```text
50% Semantic
30% Skill
10% Experience
10% Education/Certification
```

Keep weights configurable.

Example:

```json
{
  "semantic": 0.50,
  "skills": 0.30,
  "experience": 0.10,
  "education": 0.10
}
```

---

# 32. WEIGHT SENSITIVITY

Test multiple weights:

```text
50/30/10/10
60/25/10/5
40/40/10/10
```

Measure ranking quality.

Do not choose weights only because they "look good."

If no optimization is possible, document that the weights are expert-designed prototype weights.

---

# 33. RANKING METRICS

Use:

```text
Precision@K
Recall@K
MRR
NDCG@K
```

For a hackathon, at minimum:

```text
Precision@5
Recall@5
```

---

# 34. PRECISION@K

```text
Precision@5 =
Relevant jobs in top 5
/
5
```

Example:

```text
Top 5:
3 relevant

Precision@5 = 3/5 = 0.60
```

---

# 35. RECALL@K

```text
Recall@5 =
Relevant jobs in top 5
/
All relevant jobs
```

Use a known evaluation set.

---

# 36. MRR

Mean Reciprocal Rank measures how early the first relevant result appears.

```text
RR = 1 / rank_of_first_relevant_result
```

Then average over queries/candidates.

Higher is better.

---

# 37. NDCG

Use NDCG when relevance is graded:

```text
Highly Relevant = 3
Relevant = 2
Partially Relevant = 1
Irrelevant = 0
```

NDCG evaluates ranking quality while rewarding highly relevant items near the top.

---

# 38. SKILL GAP EVALUATION

For each candidate-role pair:

```text
Gold gaps
vs
Predicted gaps
```

Calculate:

```text
precision
recall
F1
```

Also check:

```text
required skill gap accuracy
preferred skill gap accuracy
```

A missing required skill should have higher priority than a missing preferred skill.

---

# 39. RECOMMENDATION EVALUATION

Career recommendations are harder to score automatically.

Use a rubric:

```text
0 = irrelevant
1 = weak
2 = somewhat relevant
3 = useful
4 = highly useful
```

Evaluate:

```text
relevance
actionability
skill alignment
sequence quality
explanation quality
```

Use human evaluation for the prototype.

Never fabricate automated recommendation accuracy.

---

# 40. ROADMAP LOGIC

A roadmap should respect prerequisites.

Example:

```text
Python
 ↓
NumPy/Pandas
 ↓
Machine Learning
 ↓
Model Deployment
 ↓
Docker
 ↓
Cloud
```

Do not recommend:

```text
Kubernetes
```

before the candidate has any relevant container/deployment foundation unless the roadmap explicitly includes prerequisites.

---

# 41. LEARNING PRIORITY SCORE

Possible:

```text
Priority =
Job Importance
×
Gap Severity
×
Number of Target Roles
×
Prerequisite Value
```

Normalize to:

```text
0–100
```

Document the formula.

---

# 42. ROLE TRANSITION GRAPH

Represent:

```text
Data Analyst
     ↓
Data Scientist
     ↓
ML Engineer
```

Edges may contain:

```text
required transition skills
```

Example:

```text
Data Analyst → Data Scientist

Transition Skills:
Python
Statistics
Machine Learning
```

This enables career-path recommendations.

---

# 43. CAREER PATH EVALUATION

Check:

```text
Does every recommended step address a real gap?
Are prerequisites ordered?
Does the target role require the final skills?
Are recommendations redundant?
```

---

# 44. WHAT-IF EVALUATION

Test:

```text
Add relevant missing skill
```

Expected:

```text
score should usually increase
```

Test:

```text
Add irrelevant skill
```

Expected:

```text
little/no improvement
```

Test:

```text
Add already-present skill
```

Expected:

```text
no double counting
```

---

# 45. MODEL ABLATION STUDY

Run:

```text
Model A:
Keyword only

Model B:
Embedding only

Model C:
Skill matching only

Model D:
Hybrid
```

Compare:

```text
Precision@5
Recall@5
MRR
NDCG
```

This provides strong evidence that each component contributes.

---

# 46. ERROR ANALYSIS

Do not stop at metrics.

Inspect failures.

Categories:

```text
False skill extraction
Missed skill
Wrong normalization
Semantic false positive
Semantic false negative
Wrong role ranking
Wrong gap
Bad recommendation
```

For each failure record:

```text
input
prediction
expected
root cause
fix
```

---

# 47. CONFUSION MATRIX

For binary matching:

```text
                 Predicted
              Relevant  Not
Actual
Relevant        TP       FN
Not             FP       TN
```

Calculate:

```text
precision
recall
F1
accuracy
specificity
```

Do not rely on accuracy alone if classes are imbalanced.

---

# 48. CLASS IMBALANCE

If most candidate-job pairs are irrelevant:

```text
accuracy may look high
```

Example:

```text
95 irrelevant
5 relevant
```

A model predicting everything irrelevant gets:

```text
95% accuracy
```

but is useless.

Prefer:

```text
Precision
Recall
F1
PR-AUC where appropriate
ranking metrics
```

---

# 49. EVALUATION SPLIT

Where enough data exists:

```text
Train
Validation
Test
```

For a rule/embedding prototype without training:

```text
Development benchmark
Held-out evaluation benchmark
```

Do not tune rules repeatedly on the same test set and then claim unbiased test performance.

---

# 50. DATA LEAKAGE

Avoid leakage such as:

```text
same resume in tuning and test
same candidate in train/test
same near-duplicate job in train/test
ground-truth labels used during inference
```

Keep evaluation data isolated.

---

# 51. REPRODUCIBILITY

Record:

```text
model name
model version
embedding model
ontology version
dataset version
scoring weights
code commit
evaluation timestamp
```

Example:

```json
{
  "embeddingModel": "all-MiniLM-L6-v2",
  "ontologyVersion": "1.0.0",
  "matchingVersion": "1.0.0",
  "datasetVersion": "1.0.0"
}
```

---

# 52. EXPERIMENT TRACKING

Every experiment should record:

```text
experiment ID
date
dataset version
model
parameters
weights
metrics
notes
```

For the hackathon, a simple JSON/CSV experiment log is sufficient.

Do not introduce a complex MLOps platform unless needed.

---

# 53. THRESHOLD CALIBRATION

If using thresholds:

```text
skill extraction confidence threshold
match threshold
gap threshold
recommendation threshold
```

Do not choose arbitrary values without checking examples.

Test:

```text
0.30
0.50
0.70
0.80
```

and inspect precision/recall tradeoffs.

---

# 54. SCORE CALIBRATION

A score of:

```text
90%
```

should not imply:

```text
90% probability of getting hired
```

It means:

> High relative match according to the project's scoring model.

Use language:

```text
Match Score
```

not:

```text
Hiring Probability
```

---

# 55. EXPLAINABILITY CONSISTENCY

The explanation must be generated from the same evidence used by the score.

Bad:

```text
Score says 82%
Explanation invents "leadership strength"
```

Good:

```text
Score:
Python + SQL + ML overlap

Explanation:
Python + SQL + ML are shared requirements.
```

---

# 56. SCORE DECOMPOSITION

Return:

```json
{
  "finalScore": 81.5,
  "components": {
    "semantic": 82,
    "skills": 75,
    "experience": 90,
    "education": 80
  }
}
```

This enables debugging and explanation.

---

# 57. SKILL CONTRIBUTION

Optionally show:

```text
Python       +12
SQL          +10
ML           +14
Docker       missing
Kubernetes   missing
```

Do not expose misleading exact causal contributions unless mathematically derived from the scoring function.

---

# 58. ONTOLOGY VERSIONING

Never silently change the skill ontology.

Version:

```text
1.0.0
1.1.0
2.0.0
```

Record:

```text
skill additions
alias changes
relationship changes
role changes
```

---

# 59. JOB DATA VERSIONING

Record:

```text
job dataset version
created date
source type
last update
```

If using synthetic jobs:

```text
mark them synthetic
```

If using external occupational data:

```text
document source and usage conditions
```

---

# 60. O*NET / ESCO POSITIONING

If integrating external occupational taxonomies such as O*NET or ESCO:

Use them as:

```text
knowledge sources / ontology references
```

not as unexplained magic.

Document:

```text
which fields were used
how mappings were made
what version was used
```

Do not claim official affiliation unless one exists.

---

# 61. KNOWLEDGE BASE ARCHITECTURE

Recommended:

```text
Skill
Role
Skill Alias
Role Skill Requirement
Skill Relationship
Career Transition
Learning Resource
```

Graphically:

```text
Role
 │
 ├── requires → Skill
 │
 └── prefers → Skill

Skill
 │
 ├── alias → SkillAlias
 ├── related → Skill
 └── prerequisite → Skill
```

---

# 62. KNOWLEDGE BASE QUERY EXAMPLES

Support questions such as:

```text
What skills does ML Engineer require?

Which roles use Python?

What skills are missing for this candidate?

What skills connect Data Analyst to ML Engineer?

What prerequisite comes before Kubernetes?
```

---

# 63. RAG KNOWLEDGE GROUNDING

If RAG is implemented:

Retrieval corpus may include:

```text
role descriptions
skill definitions
career paths
skill relationships
approved learning resources
```

Pipeline:

```text
Candidate context
+
Target role
 ↓
Query construction
 ↓
Retriever
 ↓
Top-k evidence
 ↓
LLM
 ↓
Structured recommendation
```

The retrieved context must be traceable.

---

# 64. RAG EVALUATION

Measure:

```text
retrieval relevance
retrieval recall
groundedness
citation/evidence coverage
hallucination rate
```

If these cannot be evaluated reliably during the hackathon:

```text
keep RAG optional
```

---

# 65. HALLUCINATION TEST SET

Create prompts/resumes containing:

```text
missing education
ambiguous skill
contradictory dates
fake certification
negated skill
future learning goal
unrelated technology
```

Verify the system does not convert them into facts.

---

# 66. ADVERSARIAL RESUME TESTS

Examples:

```text
"I have never used Docker."

"Learning Python next month."

"Interested in Kubernetes."

"Python, Java, Go, Rust..." 
```

Check whether extraction incorrectly treats all statements as demonstrated skills.

---

# 67. ADVERSARIAL JOB TESTS

Test:

```text
extremely long job description
duplicate skills
irrelevant buzzwords
missing required skills
contradictory requirements
empty description
```

System must remain stable.

---

# 68. FAIRNESS EVALUATION

Where appropriate, construct controlled tests where irrelevant personal attributes differ while job-relevant content stays constant.

Expected:

```text
match should remain materially consistent
```

Do not collect sensitive personal attributes unnecessarily.

---

# 69. BIAS SOURCES

Document possible bias from:

```text
resume quality
language
institution names
career gaps
nontraditional careers
missing information
ontology coverage
job dataset
historical hiring data
```

Do not claim "bias-free."

Say:

```text
"Bias risks are recognized and mitigated through feature restrictions, explainability, and evaluation."
```

---

# 70. ROBUSTNESS

Test minor changes:

```text
Python
python
PYTHON
Python 3
Python programming
```

Expected:

```text
same canonical skill
```

Also test formatting changes:

```text
bullet list
paragraph
table
different resume ordering
```

---

# 71. LANGUAGE ROBUSTNESS

If multilingual resumes are not supported:

Say so.

Do not silently claim multilingual support.

If multilingual support is planned:

```text
future scope
```

unless actually implemented and evaluated.

---

# 72. OCR

OCR is optional.

If scanned PDFs are unsupported:

Return:

```text
"This document appears image-based and could not be parsed reliably."
```

Do not pretend extraction succeeded.

If OCR is implemented, evaluate it separately.

---

# 73. MISSING DATA

Never infer:

```text
degree
experience
skill
certification
```

from absence/presence alone.

Represent:

```text
unknown
```

when necessary.

---

# 74. CANDIDATE PROFILE SCHEMA

Recommended:

```json
{
  "candidate": {
    "name": null,
    "education": [],
    "experience": [],
    "projects": [],
    "certifications": []
  },
  "skills": [],
  "metadata": {
    "parserVersion": "1.0.0",
    "ontologyVersion": "1.0.0",
    "modelVersion": "1.0.0"
  }
}
```

---

# 75. MATCH RESPONSE SCHEMA

```json
{
  "jobId": "JOB001",
  "score": 81.5,
  "components": {
    "semantic": 82,
    "skills": 75,
    "experience": 90,
    "education": 80
  },
  "matchedSkills": [],
  "missingSkills": [],
  "evidence": [],
  "modelVersion": "1.0.0"
}
```

---

# 76. GAP RESPONSE SCHEMA

```json
{
  "jobId": "JOB001",
  "gaps": [
    {
      "skill": "Docker",
      "priority": 92,
      "required": true,
      "reason": "Required by target role"
    }
  ]
}
```

---

# 77. RECOMMENDATION RESPONSE SCHEMA

```json
{
  "targetRole": "Machine Learning Engineer",
  "steps": [
    {
      "skill": "Docker",
      "priority": 92,
      "reason": "Required for deployment workflow",
      "prerequisites": []
    }
  ]
}
```

---

# 78. MODEL OUTPUT VALIDATION

Every AI output must pass schema validation.

Reject:

```text
missing required fields
wrong types
invalid score ranges
unknown enum values
malformed arrays
```

Never blindly trust model JSON.

---

# 79. DETERMINISM

Where possible:

```text
temperature = low/controlled
fixed model version
fixed scoring weights
fixed ontology
fixed evaluation dataset
```

For deterministic rules:

```text
same input → same output
```

For stochastic models:

```text
record seed/configuration where supported
```

---

# 80. MODEL CHANGE POLICY

If changing:

```text
embedding model
NLP model
skill rules
ontology
matching weights
```

rerun evaluation.

Do not compare version 1 and version 2 without recording what changed.

---

# 81. REGRESSION SUITE

Maintain a fixed set of examples:

```text
resume_001
resume_002
...
```

Every model/rule change runs them.

Catch:

```text
new false positives
new false negatives
ranking regressions
normalization regressions
```

---

# 82. GOLDEN TEST CASES

Create at least:

```text
10 skill extraction cases
10 normalization cases
10 matching cases
10 skill-gap cases
5 roadmap cases
5 adversarial cases
```

Total:

```text
50+ golden cases
```

For a hackathon this is sufficient to demonstrate disciplined evaluation.

---

# 83. EVALUATION REPORT

Generate:

```text
evaluation/
├── summary.md
├── extraction_metrics.json
├── normalization_metrics.json
├── matching_metrics.json
├── gap_metrics.json
├── recommendation_scores.json
└── error_analysis.csv
```

---

# 84. FINAL METRICS DASHBOARD

Show:

```text
Skill Extraction
Precision: XX%
Recall: XX%
F1: XX%

Normalization
Accuracy: XX%

Matching
Precision@5: XX%
Recall@5: XX%
MRR: XX%

Skill Gap
F1: XX%
```

Only show metrics actually measured.

---

# 85. BASELINE COMPARISON TABLE

Create:

| Model | P@5 | R@5 | MRR |
|---|---:|---:|---:|
| Keyword | X | X | X |
| Embedding | X | X | X |
| Skill-only | X | X | X |
| Hybrid | X | X | X |

This is one of the strongest technical slides.

---

# 86. ERROR ANALYSIS TABLE

Create:

| Case | Expected | Predicted | Error | Cause | Fix |
|---|---|---|---|---|---|
| R01 | Docker | Docker | — | — | — |
| R02 | React | ReactJS | normalization | alias | alias mapping |
| R03 | Kubernetes absent | Kubernetes | false positive | weak context | context rule |

Do not hide failures.

---

# 87. ABLATION SLIDE

Show:

```text
Keyword only       → 58%
Embedding only     → 71%
Skill matching     → 74%
Hybrid             → 82%
```

Only use actual measured values.

The purpose is to show contribution of each layer.

---

# 88. SCIENTIFIC CLAIMS

Allowed:

```text
"Our prototype achieved X on our manually labeled benchmark."
```

Not allowed:

```text
"Our AI is 95% accurate in real-world hiring."
```

unless rigorously supported.

---

# 89. HACKATHON DATA LIMITATION

Always state:

```text
Evaluation uses a small prototype benchmark and should not be interpreted as production-scale hiring validation.
```

This increases credibility.

---

# 90. PRODUCTION DATA PLAN

Future production evaluation:

```text
larger resume corpus
diverse job corpus
expert annotations
inter-annotator agreement
temporal validation
industry-specific evaluation
fairness audits
drift monitoring
```

---

# 91. ANNOTATION GUIDELINES

Annotators must receive explicit instructions.

For skill annotation:

Mark a skill only if:

```text
explicitly demonstrated
clearly used
credibly supported by evidence
```

Do not mark:

```text
mere interest
future learning
negated skill
unrelated mention
```

---

# 92. ANNOTATOR AGREEMENT

If multiple annotators are available, compare labels.

Use:

```text
Cohen's Kappa
```

or an appropriate agreement statistic.

The goal:

```text
measure whether humans agree on labels
```

If only one annotator is available, document this limitation.

---

# 93. LABEL QUALITY

Before evaluating the model:

```text
review labels
resolve conflicts
standardize terminology
freeze benchmark
```

Do not modify ground truth merely to improve model metrics.

---

# 94. EVALUATION DATA LEAKAGE CHECK

Before final metrics:

```text
[ ] test resumes not used for rule tuning
[ ] test jobs not copied into development
[ ] aliases not created specifically from test errors without re-freezing
[ ] gold labels unavailable to inference
[ ] no manual score adjustment
```

---

# 95. RECOMMENDATION SAFETY

Recommendations must not say:

```text
"You will get this job."
"You are guaranteed to be hired."
```

Use:

```text
"Your profile currently shows strong alignment."
"Consider developing..."
"This may improve alignment with..."
```

---

# 96. USER TRUST

Expose:

```text
why matched
what is missing
what evidence was found
what is uncertain
what to do next
```

This is more valuable than displaying an opaque AI score.

---

# 97. EXPLANATION TRACE

Internally retain:

```text
input evidence
normalized skills
score components
retrieved knowledge if RAG
recommendation reason
model versions
```

This makes debugging possible.

---

# 98. PRIVACY IN EVALUATION

Do not include real personal data in the benchmark unless permitted.

Prefer:

```text
synthetic resumes
anonymized examples
public/licensed datasets where allowed
```

---

# 99. MODEL CARD

Create:

```text
docs/model-card.md
```

Include:

```text
model purpose
inputs
outputs
models
datasets
limitations
bias risks
failure modes
evaluation
version
```

---

# 100. DATA CARD

Create:

```text
docs/data-card.md
```

Include:

```text
dataset purpose
sources
size
schema
annotation
synthetic/real status
limitations
license
privacy
version
```

---

# 101. ONTOLOGY CARD

Create:

```text
docs/ontology.md
```

Include:

```text
skill categories
canonical naming
aliases
relationships
role mapping
versioning
source
limitations
```

---

# 102. EVALUATION CARD

Create:

```text
docs/evaluation.md
```

Include:

```text
benchmark
metrics
baselines
results
error analysis
limitations
reproduction commands
```

---

# 103. REPRODUCTION COMMAND

Provide one documented command sequence:

```bash
# install
# seed
# run evaluation
# generate metrics
```

Example:

```bash
npm run seed
python -m evaluation.run
```

Use the project's actual commands once implemented.

---

# 104. CONTINUOUS EVALUATION

Future:

```text
new model
 ↓
evaluation suite
 ↓
metrics
 ↓
regression check
 ↓
approve
 ↓
deploy
```

Do not deploy a new model merely because it is newer.

---

# 105. DRIFT MONITORING

Future production monitoring:

```text
skill vocabulary drift
job terminology drift
embedding distribution drift
role distribution drift
extraction confidence drift
```

Alert when distributions materially change.

---

# 106. MODEL RETRAINING POLICY

If using trained models:

Trigger reevaluation/retraining when:

```text
performance drops
taxonomy changes significantly
new domains are added
language distribution changes
job market changes materially
```

For a pretrained embedding model without fine-tuning, document that retraining is not part of the MVP.

---

# 107. COST AWARENESS

Track:

```text
CPU time
GPU usage if any
LLM/API calls if any
storage
database size
```

Avoid unnecessary external API calls.

Cache deterministic computations.

---

# 108. LATENCY BREAKDOWN

Measure:

```text
upload
parse
NLP
embedding
matching
database
response
```

Example:

```text
Upload: 100ms
Parsing: 500ms
NLP: 700ms
Embedding: 300ms
Matching: 80ms
DB: 100ms
```

Use actual measurements.

---

# 109. BATCH EMBEDDING

For many jobs:

```text
batch encode job descriptions
```

rather than encoding one at a time during every request.

---

# 110. VECTOR STORAGE

For hackathon:

```text
NumPy / serialized vectors
```

may be sufficient.

For larger systems:

```text
pgvector
vector database
```

may be considered.

Do not add a vector database just because embeddings exist.

---

# 111. SEMANTIC SEARCH

Support:

```text
candidate → jobs
```

and potentially:

```text
job → candidates
```

The second mode can support recruiter functionality later.

---

# 112. RECRUITER MODE

Optional.

Features:

```text
create job
define requirements
rank candidates
explain ranking
compare candidate gaps
```

Must not become the primary MVP if time is limited.

---

# 113. ROLE SIMILARITY

Calculate:

```text
Role A ↔ Role B
```

using:

```text
skill overlap
semantic similarity
```

This can power career transitions.

---

# 114. CAREER TRANSITION SCORE

Possible:

```text
Transition Score =
Current Skill Overlap
+
Target Skill Demand
-
Gap Severity
```

Normalize to:

```text
0–100
```

Document formula.

---

# 115. JOB MARKET DATA

If external market data is unavailable:

Use:

```text
curated/synthetic job data
```

Do not pretend it is live market data.

If live data is added:

```text
source
timestamp
retrieval method
```

must be documented.

---

# 116. LIVE SCRAPING WARNING

Do not make live scraping a critical dependency during the hackathon.

Problems:

```text
network failure
rate limits
robots restrictions
schema changes
authentication
unstable websites
```

Keep a local job dataset as the reliable core.

---

# 117. LEARNING RESOURCE MAPPING

Career roadmap may map:

```text
Skill
 ↓
Learning Resource
 ↓
Practice Project
```

Use curated links/resources only if permitted and stable.

Do not generate fake course URLs.

---

# 118. ROADMAP QUALITY

Each recommendation should include:

```text
why
priority
prerequisite
estimated difficulty
practice idea
target role relevance
```

Avoid generic:

```text
"Learn more AI."
```

Prefer:

```text
"Learn Docker fundamentals and containerize your FastAPI project because Docker is required by 3 of your selected target roles."
```

Only use the numerical claim if the dataset supports it.

---

# 119. WHAT-IF MULTI-SKILL SIMULATION

Optional advanced feature:

```text
Add:
Docker
AWS
Kubernetes
```

Then calculate:

```text
current
+ Docker
+ AWS
+ Kubernetes
```

Show marginal improvement.

Do not double-count related skills.

---

# 120. MARGINAL SKILL VALUE

Calculate:

```text
Value(skill) =
Projected Score(skill added)
-
Current Score
```

This helps answer:

> Which skill should I learn first?

---

# 121. SKILL PRIORITIZATION

Rank missing skills by:

```text
match impact
role importance
frequency
prerequisites
learning effort
```

Possible:

```text
Priority = Impact / Effort
```

Document the exact formula.

---

# 122. EVALUATION OF WHAT-IF

Use known target jobs.

For each candidate:

```text
simulate skill
observe score change
```

Check:

```text
does relevant skill increase alignment?
does irrelevant skill have little effect?
does duplicate skill avoid double counting?
```

---

# 123. TESTING ON EDGE CASES

Required:

```text
empty resume
one-line resume
very long resume
duplicate sections
tables
columns
unicode
special characters
multiple degrees
multiple jobs
career transition
no skills
many skills
ambiguous skills
negated skills
future skills
```

---

# 124. RESUME PARSER LIMITATIONS

Document:

```text
complex visual layouts may reduce extraction quality
image-only PDFs may require OCR
tables may be imperfect
columns may be reordered
icons may be ignored
```

Do not hide parser limitations.

---

# 125. EVALUATION SUMMARY FOR JUDGES

Use:

```text
We created a manually labeled prototype benchmark.

We evaluated:
1. skill extraction
2. normalization
3. job ranking
4. skill-gap detection

We compared:
keyword baseline
embedding model
hybrid model

We report:
Precision
Recall
F1
Precision@5
MRR
```

Only insert actual measured values.

---

# 126. 15-HOUR AI EVALUATION PLAN

## Hour 0–1

Freeze:

```text
ontology
schema
scoring formula
evaluation labels
```

## Hour 1–3

Create:

```text
skills
aliases
roles
jobs
demo resumes
```

## Hour 3–5

Implement extraction + normalization.

## Hour 5–7

Implement embeddings + matching.

## Hour 7–8

Create evaluation benchmark.

## Hour 8–9

Run baseline.

## Hour 9–10

Run hybrid model.

## Hour 10

Feature freeze.

## Hour 10–11

Error analysis.

## Hour 11–12

Fix highest-impact AI errors.

## Hour 12–13

Generate metrics/report.

## Hour 13–14

Prepare judge slides.

## Hour 14–15

Re-run final benchmark and demo.

---

# 127. P0 AI REQUIREMENTS

```text
[ ] parser works
[ ] skill extraction works
[ ] normalization works
[ ] candidate profile works
[ ] embeddings work
[ ] matching works
[ ] score is bounded
[ ] explanations are evidence-based
[ ] gaps work
[ ] roadmap works
```

---

# 128. P1 AI REQUIREMENTS

```text
[ ] evaluation benchmark
[ ] baseline comparison
[ ] error analysis
[ ] what-if simulator
[ ] ontology versioning
[ ] model versioning
[ ] regression tests
```

---

# 129. P2 AI REQUIREMENTS

```text
[ ] RAG
[ ] fine-tuning
[ ] OCR
[ ] multilingual NLP
[ ] graph neural networks
[ ] advanced agents
[ ] live labor-market intelligence
```

---

# 130. DO NOT OVERENGINEER

Do not add:

```text
Kafka
Kubernetes
Airflow
MLflow
complex agent frameworks
vector databases
microservices everywhere
```

unless a real requirement exists.

A hackathon system should be:

```text
simple
fast
testable
explainable
demoable
```

---

# 131. FINAL AI ARCHITECTURE

Recommended:

```text
                    Resume
                      │
                      ▼
              PDF/DOCX Parser
                      │
                      ▼
                 Text Layer
                      │
                      ▼
              NLP / Extraction
                      │
                      ▼
             Skill Normalizer
                      │
                      ▼
            Candidate Knowledge
                 Profile
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
    Skill Features           Text Embedding
          │                       │
          └───────────┬───────────┘
                      ▼
               Hybrid Matcher
                      │
          ┌───────────┼────────────┐
          ▼           ▼            ▼
       Ranking    Explanation    Gaps
          │           │            │
          └───────────┼────────────┘
                      ▼
              Career Planner
                      │
                      ▼
              What-If Engine
                      │
                      ▼
                 Dashboard
```

---

# 132. FINAL AI QUALITY GATE

The AI subsystem is considered ready only if:

```text
[ ] output is structured
[ ] output is reproducible
[ ] model versions are recorded
[ ] ontology is versioned
[ ] evaluation benchmark exists
[ ] baseline exists
[ ] metrics are calculated
[ ] errors are reviewed
[ ] limitations are documented
[ ] no fabricated claims are made
```

---

# 133. FINAL RESEARCH-QUALITY REVIEW PROMPT

Use this after all AI work is complete:

> Act as a skeptical ML reviewer.
>
> Inspect the complete AI pipeline:
>
> `Parsing → Extraction → Normalization → Profile → Embedding → Matching → Gap → Recommendation`
>
> Challenge every AI claim.
>
> Ask:
>
> - What is the ground truth?
> - How were labels created?
> - Is there data leakage?
> - What is the baseline?
> - What metrics are used?
> - Are the metrics appropriate?
> - Are the test examples representative?
> - Are false positives analyzed?
> - Are false negatives analyzed?
> - Does semantic matching outperform keyword matching?
> - Are scores calibrated?
> - Are explanations faithful to the score?
> - Are recommendations grounded?
> - Could protected attributes influence results?
> - What happens on ambiguous resumes?
> - What happens when evidence is missing?
>
> Identify unsupported claims.
>
> Never invent missing metrics.
>
> Return:
>
> 1. AI quality verdict
> 2. evaluation weaknesses
> 3. data weaknesses
> 4. model weaknesses
> 5. ontology weaknesses
> 6. fairness risks
> 7. top five fixes
> 8. exact experiments to run
> 9. final judge-ready explanation

---

# 134. FINAL JUDGE-READY AI STORY

Use this narrative:

```text
Traditional systems often depend on keyword overlap.

Our system first understands the resume,
extracts skills,
normalizes terminology,
builds a structured candidate profile,
represents candidate and jobs semantically,
combines semantic similarity with explicit skill evidence,
explains the resulting ranking,
identifies missing skills,
and converts those gaps into a personalized career path.

The what-if simulator then lets the candidate see
how acquiring a specific skill could change alignment
with a target role.
```

Do not claim that the system predicts hiring outcomes.

---

# 135. FINAL MASTER ACCEPTANCE CHECKLIST

## Data

```text
[ ] data sources documented
[ ] synthetic data labeled
[ ] ontology versioned
[ ] aliases documented
[ ] roles documented
[ ] job requirements documented
```

## NLP

```text
[ ] PDF parser
[ ] DOCX parser
[ ] preprocessing
[ ] section detection
[ ] extraction
[ ] normalization
[ ] evidence
[ ] ambiguity
[ ] negation
```

## ML

```text
[ ] embeddings
[ ] cosine similarity
[ ] hybrid score
[ ] score decomposition
[ ] ranking
[ ] caching
[ ] model version
```

## Evaluation

```text
[ ] gold labels
[ ] baseline
[ ] precision
[ ] recall
[ ] F1
[ ] Precision@5
[ ] Recall@5
[ ] MRR
[ ] error analysis
[ ] regression suite
```

## Recommendations

```text
[ ] gap detection
[ ] prioritization
[ ] prerequisites
[ ] roadmap
[ ] what-if
[ ] evidence
```

## Responsible AI

```text
[ ] no protected attributes in score
[ ] no fabricated candidate facts
[ ] uncertainty handled
[ ] limitations documented
[ ] privacy considered
[ ] fairness risks documented
```

---

# 136. FINAL COMMAND

After implementation, execute the following conceptual sequence:

```text
1. Build ontology
2. Build benchmark
3. Run parser
4. Evaluate extraction
5. Fix extraction errors
6. Run normalization
7. Evaluate normalization
8. Build embeddings
9. Run keyword baseline
10. Run embedding baseline
11. Run hybrid model
12. Evaluate ranking
13. Evaluate skill gaps
14. Evaluate roadmap
15. Run adversarial tests
16. Run regression suite
17. Generate metrics
18. Review failures
19. Freeze AI version
20. Integrate with backend
21. Run E2E
22. Prepare judge explanation
```

---

# 137. FINAL GOLDEN RULES

1. **No metric without a benchmark.**
2. **No benchmark without labels.**
3. **No labels without documented annotation rules.**
4. **No AI claim without evidence.**
5. **No score without an interpretable formula.**
6. **No explanation that contradicts the score.**
7. **No recommendation without a reason.**
8. **No normalization without canonical definitions.**
9. **No model comparison without controlling the evaluation set.**
10. **No test result should be silently changed to improve the story.**
11. **No sensitive attribute should influence matching.**
12. **No fabricated real-world accuracy.**
13. **No RAG merely for buzzwords.**
14. **No fine-tuning merely for buzzwords.**
15. **No unnecessary infrastructure.**
16. **Measure the baseline.**
17. **Measure the hybrid system.**
18. **Analyze failures, not only averages.**
19. **Document limitations.**
20. **Make every AI decision explainable enough for the user to understand.**
21. **A smaller validated AI system is stronger than a larger unvalidated one.**
22. **The final demo must show evidence, not just UI.**

---

# 138. FINAL DELIVERABLES

The completed AI workstream should produce:

```text
data/
├── ontology/
├── evaluation/
├── processed/
└── outputs/

docs/
├── model-card.md
├── data-card.md
├── ontology.md
└── evaluation.md
```

And a judge-ready AI slide containing:

```text
AI Pipeline
+
Ontology
+
Matching Formula
+
Baseline vs Hybrid
+
Evaluation Metrics
+
Explainability
+
Skill Gap
+
Career Roadmap
```

---

# 139. FINAL DEFINITION OF DONE

The AI system is **DONE** only when:

```text
A resume can be uploaded
        ↓
parsed reliably
        ↓
skills extracted
        ↓
skills normalized
        ↓
candidate profile created
        ↓
candidate represented semantically
        ↓
jobs ranked
        ↓
ranking explained
        ↓
skill gaps identified
        ↓
career path generated
        ↓
what-if skill tested
        ↓
outputs evaluated
        ↓
metrics reproduced
        ↓
limitations documented
```

The final system must be:

**Functional + Measurable + Explainable + Reproducible + Secure + Responsible + Demo-ready.**

---

# 140. FINAL PRINCIPAL AI REVIEW PROMPT

> You are the final Principal AI reviewer.
>
> Review this repository and its AI evaluation artifacts as if the project will be judged by senior ML engineers.
>
> Do not be impressed by terminology.
>
> Verify actual implementation.
>
> Verify actual datasets.
>
> Verify actual labels.
>
> Verify actual metrics.
>
> Verify actual baselines.
>
> Verify actual model versions.
>
> Verify actual scoring logic.
>
> Verify actual explanations.
>
> Verify actual error cases.
>
> Verify actual limitations.
>
> Search for:
>
> - fabricated metrics
> - hardcoded AI claims
> - leakage
> - invalid normalization
> - false skill extraction
> - unsupported recommendations
> - misleading percentages
> - score/explanation mismatch
> - hidden sensitive features
> - untested edge cases
> - unstable model behavior
> - undocumented data sources
> - unversioned ontology
> - missing regression tests
>
> Classify:
>
> `P0 BLOCKER`
> `P1 HIGH`
> `P2 MEDIUM`
> `P3 LOW`
>
> For every issue provide:
>
> - location
> - evidence
> - impact
> - fix
> - verification
>
> Finally answer:
>
> **"Would you trust this prototype's AI outputs enough to demonstrate them to a technical judging panel?"**
>
> Give a strict YES/NO and explain why.
>
> Do not invent evidence.
