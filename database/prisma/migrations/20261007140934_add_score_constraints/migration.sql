-- Score and Confidence Validation Constraints
ALTER TABLE "matches" ADD CONSTRAINT "matches_finalScore_check" CHECK ("finalScore" >= 0.0 AND "finalScore" <= 100.0);
ALTER TABLE "matches" ADD CONSTRAINT "matches_skillOverlapScore_check" CHECK ("skillOverlapScore" >= 0.0 AND "skillOverlapScore" <= 1.0);
ALTER TABLE "matches" ADD CONSTRAINT "matches_tfidfSimilarity_check" CHECK ("tfidfSimilarity" >= 0.0 AND "tfidfSimilarity" <= 1.0);
ALTER TABLE "matches" ADD CONSTRAINT "matches_semanticSimilarity_check" CHECK ("semanticSimilarity" >= 0.0 AND "semanticSimilarity" <= 1.0);
ALTER TABLE "candidate_skills" ADD CONSTRAINT "candidate_skills_confidence_check" CHECK ("confidence" >= 0.0 AND "confidence" <= 1.0);