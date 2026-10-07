# SkillGap AI Persistence Layer

## 1. Overview
The `database` package implements the PostgreSQL + Prisma persistence layer for the **SkillGap AI** platform. It provides the system-of-record schema supporting the complete talent intelligence lifecycle:

```text
User 
 ├── Resume 
 └── CandidateProfile 
       ├── CandidateSkill ── (canonical) Skill
       └── Match ──────────── Job ── JobSkill ── Skill
             └── SkillGap ── Skill
                   └── CareerPath
```

---

## 2. Technology Stack
- **Database Engine**: PostgreSQL 16
- **Object-Relational Mapping**: Prisma ORM (`@prisma/client` & `prisma` CLI v5.22.0)
- **Runtime & Scripting**: Node.js (>= 20), TypeScript, `tsx`
- **Development Service**: Embedded / Containerized PostgreSQL on port `5432`

---

## 3. Directory Layout
```text
database/
├── prisma/
│   ├── schema.prisma              # Complete 10-entity domain schema
│   ├── seed.ts                    # Idempotent database seeder
│   └── migrations/
│       ├── 20261007140857_init_skillgap_schema/
│       │   └── migration.sql      # Core tables, enums, FKs, and indexes
│       └── 20261007140934_add_score_constraints/
│           └── migration.sql      # Database-level CHECK constraints for scores
├── scripts/
│   ├── start_db.ts                # Starts development PostgreSQL instance
│   ├── stop_db.ts                 # Stops development PostgreSQL instance
│   └── validate_db.ts             # Comprehensive validation suite
├── tests/
│   ├── database.test.ts           # Integrity, uniqueness, and cascade tests
│   └── run_tests.ts               # Test suite runner
├── .env.example                   # Connection URL template
├── package.json                   # Dependency manifests and scripts
├── tsconfig.json                  # TypeScript compiler settings
└── README.md                      # Architecture and operational documentation
```

---

## 4. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Placeholder configuration:
```env
DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/skillgap
```
Default local development URL:
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/skillgap
```
> **Security Notice**: Never commit real database passwords or credentials to version control. The `.env` file is strictly gitignored.

---

## 5. Development Operations

### A. Start Database
```bash
npm run db:start
```

### B. Generate Prisma Client
```bash
npm run prisma:generate
```

### C. Run Migrations
To apply migrations in development:
```bash
npm run prisma:migrate
```
To deploy migrations in CI/production:
```bash
npm run prisma:deploy
```

### D. Seed Database
Seeds 91 canonical skills from `data/skills.json`, 100 representative jobs and 179 job-skill links from `data/processed/analytics_jobs/job_profiles.json`, and a synthetic development candidate (`demo.candidate@example.com`):
```bash
npm run prisma:seed
```
*The seed routine uses upsert operations and is 100% idempotent.*

### E. Validate Database
Runs the connection, table structure, row count, uniqueness, and foreign-key integrity checks:
```bash
npm run db:validate
```

### F. Run Test Suite
Executes the automated integrity tests (unique constraints, ownership isolation, score checks, cascade behavior):
```bash
npm test
```

### G. Database Reset (Development Only)
> ⚠️ **CAUTION**: Destructive command. Drops the database, reapplies all migrations, and runs seeds.
```bash
npx prisma migrate reset
```

---

## 6. Core Domain Models

| Model | Primary Key | Key Fields | Purpose |
| :--- | :--- | :--- | :--- |
| `User` | UUID (`id`) | `email` (unique), `role`, `status` | System accounts and authentication metadata |
| `Resume` | UUID (`id`) | `userId` (FK), `storedFilename`, `status` | Uploaded document metadata and storage references |
| `CandidateProfile` | UUID (`id`) | `userId` (FK), `summary`, `analysisVersion` | Normalized candidate professional profile |
| `Skill` | UUID (`id`) | `name`, `normalizedName` (unique), `category` | Canonical skills taxonomy |
| `CandidateSkill` | UUID (`id`) | `candidateProfileId`, `skillId`, `confidence` | Extracted candidate skills with confidence (0.0–1.0) |
| `Job` | String (`id`) | `title`, `normalizedTitle`, `location` | Preprocessed job postings (stable `job_id` keys) |
| `JobSkill` | UUID (`id`) | `jobId`, `skillId`, `isRequired`, `importance` | Normalized required/preferred job skill links |
| `Match` | UUID (`id`) | `candidateProfileId`, `jobId`, `finalScore` | Hybrid candidate-to-job match score & explainability |
| `SkillGap` | UUID (`id`) | `matchId`, `skillId`, `priority`, `reason` | Missing skills for candidate target role |
| `CareerPath` | UUID (`id`) | `jobId`, `title`, `sequenceOrder` | Recommended roadmap milestones and projects |

---

## 7. Integrity & Safety Guarantees
1. **Conservative Deletion**:
   - Deleting a `User` or `Resume` is protected via `onDelete: Restrict` when profiles or dependencies exist.
   - Child join tables (`CandidateSkill`, `JobSkill`, `SkillGap`) cascade safely upon parent deletion.
2. **Score Range CHECK Constraints**:
   - `matches.finalScore` CHECK `[0.0, 100.0]`.
   - `matches.skillOverlapScore` CHECK `[0.0, 1.0]`.
   - `matches.tfidfSimilarity` CHECK `[0.0, 1.0]`.
   - `matches.semanticSimilarity` CHECK `[0.0, 1.0]`.
   - `candidate_skills.confidence` CHECK `[0.0, 1.0]`.
3. **Multi-Tenant Ownership Isolation**:
   - All profile, resume, and match queries are scoped to the authenticated `userId`.
   - Client-provided identifiers are never trusted without backend ownership verification.
4. **No Secrets / Plaintext Passwords**:
   - The schema stores `passwordHash` only; plaintext passwords are never stored.
