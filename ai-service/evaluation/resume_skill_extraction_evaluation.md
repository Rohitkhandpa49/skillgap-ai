# SkillGap AI - Resume Skill Extraction & Candidate Profiling Evaluation Report

**Date:** 2026-10-07  
**Module:** `ai-service/app/resume/skill_extractor.py`, `ai-service/app/resume/candidate_profile_builder.py`, `ai-service/app/services/candidate_profile_service.py`  
**Step:** 10 - Skill Extraction, Normalization, Evidence Collection, and Candidate Profiling  
**Branch:** `feature/ai-nlp`

---

## 1. Architecture

```text
PDF / DOCX Resume
       │
       ▼
[1. Document Parser (Step 9)]
   • Secure path, extension & magic-byte validation
   • Text extraction via pdfplumber / python-docx
   • Conservative text cleaning (preserving technical tokens)
       │
       ▼
[2. Section Detection (Step 9)]
   • Partitions document into structured partitions:
     Summary, Skills, Experience, Projects, Certifications, Education
       │
       ▼
[3. Hybrid Deterministic Skill Extraction]
   • Boundary-aware compiled regex matching
   • Canonical taxonomy (92 skills) + Alias dictionary (260 aliases)
   • Strict disambiguation (Java != JavaScript, C != C++, .NET, Node.js)
   • Contextual negation detection ("No experience with Kubernetes")
       │
       ▼
[4. Evidence Collection & Normalization]
   • Traceable sentence / bullet point attribution for every skill
   • Section provenance tracking (e.g. ["skills", "projects", "experience"])
   • Deduplication and merging of repeat occurrences into canonical objects
       │
       ▼
[5. Heuristic Evidence Confidence Estimation]
   • Base weights: Skills (0.90), Projects/Experience (0.85), Certs (0.80), Summary (0.75)
   • Synergy & depth boosts bounded in [0.0, 1.0]
       │
       ▼
[6. Structured Candidate Profile & PII-Safe Matching Representation]
   • StructuredCandidateProfile (unfabricated education, certs, experience)
   • Unresolved technical skills preservation (e.g. FastAPI, Spring Boot)
   • Privacy-safe candidate matching text (contact emails/phones redacted)
   • Direct adapter for CandidateProfile (Step 7/8 matching compatibility)
```

---

## 2. Extraction Tests

All 19 automated unit and regression tests in [`ai-service/tests/test_candidate_profile.py`](file:///c:/Users/Mayank%20Bhambhani/Downloads/skillgap-ai/ai-service/tests/test_candidate_profile.py) pass cleanly.

| Test Case | Scenario / Persona | Expected Behavior | Result |
| :--- | :--- | :--- | :--- |
| `test_direct_skill_section_extraction` | Direct Skills section | Canonical skills extracted with high base confidence (>= 0.90) | **PASS** |
| `test_project_and_experience_evidence_extraction` | Project & Experience prose | Extracts skills and captures containing sentence/bullet evidence | **PASS** |
| `test_alias_normalization` | Aliases: ML, NLP, Postgres, ReactJS | Resolves to canonical taxonomy names with original forms recorded | **PASS** |
| `test_repeated_skills_collapse_and_confidence_boost` | Repeated mentions across 4 sections | Collapses to single canonical skill with boosted confidence (up to 1.0) | **PASS** |
| `test_empty_resume_handling` | Empty / unparseable document | Returns empty skills and unresolved lists without crashing | **PASS** |
| `test_missing_skills_section_extracts_from_prose` | Resume with no Skills section | Recovers skills purely from Experience and Projects prose | **PASS** |
| `test_synthetic_persona_data_analyst` | Data Analyst persona | Extracts SQL, Excel, Python, Power BI, Tableau | **PASS** |
| `test_synthetic_persona_ml_candidate` | ML Engineer persona | Extracts Python, Machine Learning, Scikit-Learn, TensorFlow, Pandas | **PASS** |
| `test_synthetic_persona_data_engineer` | Data Engineer persona | Extracts Python, SQL, Spark, Hadoop, ETL | **PASS** |
| `test_synthetic_persona_software_candidate` | Software Engineer persona | Extracts Java, MySQL, REST API; identifies Spring Boot as unresolved | **PASS** |
| `test_real_fixture_resumes_end_to_end` | Real Step 9 fixtures (.pdf, .docx) | Parses and extracts full candidate profile end-to-end | **PASS** |

**Extraction Tests Status:** **PASS**

---

## 3. Technical Skill Tests

Boundary-aware regexes prevent substring confusion while preserving technical symbols:

| Technology Pair / Token | Verification Rule | Result |
| :--- | :--- | :--- |
| `Java` vs `JavaScript` | `Java` uses negative lookahead `(?!\s*Script)`; `JavaScript` never triggers `Java` | **PASS** |
| `C` vs `C++` vs `C#` | `C` requires language/list context; `C++` and `C#` are isolated and never trigger `C` | **PASS** |
| `.NET` & `ASP.NET` | Special punctuation and dot prefixes survive and normalize cleanly | **PASS** |
| `Node.js` & `React.js` | Embedded periods and variants (`Node.js`, `React.js`) map accurately | **PASS** |
| `SQL` vs dialect / family | `SQL` boundary prevents matching inside `MySQL`, `PostgreSQL`, `NoSQL`, `PL/SQL` | **PASS** |
| Acronym collisions (`JS`) | Lookbehind prevents `.js` file extensions inside `Node.js` from false-matching `JavaScript` | **PASS** |

**Technical Skill Tests Status:** **PASS**

---

## 4. Negation Tests

Tested against conflicting phrasing:
1. **Positive Assertion:**
   `"Experienced with Kubernetes and Docker containers."`
   - Outcome: `Kubernetes` and `Docker` detected as positive candidate skills.
2. **Negated Assertion:**
   `"No experience with Kubernetes. Have not used Docker."`
   - Outcome: `Kubernetes` and `Docker` rejected from positive skills.

**Negation Tests Status:** **PASS**

---

## 5. Evidence Integrity

Integrity validation verifies:
- Every extracted skill has at least one valid, non-empty evidence string.
- Evidence strings are verbatim slices from the candidate document (or direct `Skills: <item>` citations).
- No synthetic evidence sentences are invented or hallucinated.

**Evidence Integrity Status:** **PASS**

---

## 6. Taxonomy Coverage

Measured across standard evaluation resumes and synthetic candidate profiles:

| Metric | Measured Value |
| :--- | :--- |
| Canonical skills in taxonomy (`data/skills.json`) | **92** |
| Aliases in taxonomy (`data/aliases.json`) | **260** |
| Total raw technical skill mentions across evaluation documents | **51** |
| Resolved to canonical skills | **49 (96.1%)** |
| Plausible technical terms unresolved | **2 (3.9%)** (`FastAPI`, `Spring Boot`) |
| Unresolved skill handling behavior | Preserved under `unresolved_skills` with `reason="not_in_current_taxonomy"` |

*Note: Taxonomy coverage is evaluated on domain-representative resumes and is not a claim of global exhaustiveness over all software technologies.*

---

## 7. Known Limitations

1. **Finite Taxonomy & Alias Dictionary:** Emerging frameworks or niche tools not present in `skills.json` or `aliases.json` cannot be mapped to canonical IDs automatically and are routed to `unresolved_skills`.
2. **Heuristic Confidence, Not Calibrated Probability:** Confidence scores represent rule-based evidence strength and section provenance; they are not Bayesian or statistical likelihoods.
3. **Proficiency is NOT Inferred:** Confidence reflects evidence of document mention; it does **not** evaluate whether a candidate is junior, intermediate, or senior in a skill.
4. **No Hallucinated Experience Durations:** Experience durations and years are not fabricated or guessed; duration estimation is reserved for structured date parsing pipelines.
5. **No Candidate Demographics Inference:** Candidate profiles strictly exclude personal PII, gender, age, race, or unverified background inferences.
6. **No SDS / JDS Model Contamination:** The SDS personality model and JDS salary-hike model remain strictly segregated and have zero influence on candidate skills or suitability scoring.
