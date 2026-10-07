# Architecture Decision Record (ADR): Job Matching Engine

**Status**: Accepted  
**Date**: 2026-10-07  
**Decision**: Adopt the Tripartite Hybrid Matcher Architecture for SkillGap AI.

## Context
SkillGap AI requires a job matching engine that is:
1. **Deterministic and Explainable**: Candidates must see exactly which skills they possess, which skills they lack, and why a job was recommended.
2. **Context-Aware**: Lexical-only matching (TF-IDF) misses roles that use synonym expressions or broader role narratives.
3. **Fair and Unbiased**: Predictions from personality classification (SDS) or salary hike models (JDS) must never influence job suitability.
4. **Lightweight and Hackathon-Deployable**: Must run reliably on CPU without external API bills or complex distributed vector databases.

## Options Considered

### 1. TF-IDF Baseline Matcher
- **Pros**: Fast (~1.2 ms), 100% lexical precision on exact skill strings, zero neural dependency.
- **Cons**: Vocabulary mismatch; cannot capture semantic intent in summaries (e.g., "predictive modeling" vs "machine learning").

### 2. Dense Semantic Matcher (Sentence-Transformers Only)
- **Pros**: Strong contextual understanding of role descriptions and candidate summaries.
- **Cons**: Opaque black-box scoring. A candidate can be recommended a role they lack mandatory technical qualifications for, breaking the Skill Gap explainability requirement.

### 3. Tripartite Hybrid Matcher (Chosen)
- **Formula**:
  $$\text{Final Score} = 0.50 \times \text{Skill Overlap} + 0.20 \times \text{TF-IDF Similarity} + 0.30 \times \text{Semantic Similarity}$$
- **Pros**:
  - Explicit skill overlap holds the majority weight (50%) to guarantee transparent skill-gap visualization.
  - TF-IDF (20%) preserves exact technical tokens (`C++`, `.NET`, `Python`).
  - Dense embeddings (30%) elevate roles with semantic narrative affinity.
  - Sub-55ms CPU inference across 14,840 precomputed job embeddings.
- **Cons**: Requires storing precomputed embedding matrix (22.8 MB), which is trivial on modern hardware.

## Ethical Fairness Mandate
Personality classifications (SDS Big Five) and salary-hike forecasts (JDS) are **strictly isolated** from suitability matching. Matching decisions are grounded exclusively in job-relevant professional qualifications.

## Next Steps
Use the Hybrid Matcher as the core engine when implementing the upcoming FastAPI `/match` endpoints.
