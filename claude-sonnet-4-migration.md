# Claude Model Migration Plan

**Deprecation Notice:** `claude-sonnet-4-20250514` was deprecated. Migrate to the appropriate model below.

---

## Model Selection Guide

| Model | Use Case | Files to Update |
|-------|----------|-----------------|
| `claude-opus-4-7` | Heavy reasoning (complex scoring, architectural decisions) | Scoring APIs, dimension extraction |
| `claude-sonnet-4-6` | General synthesis (lens generation, discovery conversations) | Discover, synthesize, chat routes |
| `claude-haiku-4-5-20251001` | Fast/cheap operations (validation, simple transforms) | Validation, merge operations |

---

## Migration Status

### Lens Project — API Routes (Critical)

| File | Current | Target | Status |
|------|---------|--------|--------|
| `app/api/discover/route.js` | ~~sonnet-4-20250514~~ | `claude-sonnet-4-6` | ✅ Migrated 2026-04-22 |
| `app/api/rc-discover/route.js` | ~~sonnet-4-20250514~~ | `claude-sonnet-4-6` | ✅ Migrated 2026-04-22 |
| `app/api/synthesize/route.js` | ~~sonnet-4-20250514~~ | `claude-sonnet-4-6` | ✅ Migrated 2026-04-22 |
| `app/api/rc-synthesize/route.js` | ~~sonnet-4-20250514~~ | `claude-sonnet-4-6` | ✅ Migrated 2026-04-22 |
| `app/api/team-synthesize/route.js` | ~~sonnet-4-20250514~~ | `claude-sonnet-4-6` | ✅ Migrated 2026-04-22 |
| `app/api/chat/route.js` | ~~sonnet-4-20250514~~ | `claude-sonnet-4-6` | ✅ Migrated 2026-04-22 |
| `app/api/generate-session/route.js` | ~~sonnet-4-20250514~~ | `claude-opus-4-7` | ✅ Migrated 2026-04-22 |
| `app/api/score/route.js` | ~~sonnet-4-20250514~~ | `claude-opus-4-7` | ✅ Migrated 2026-04-22 |
| `app/api/extract-dimensions/route.js` | ~~sonnet-4-20250514~~ | `claude-opus-4-7` | ✅ Migrated 2026-04-22 |
| `app/api/merge/route.js` | ~~sonnet-4-20250514~~ | `claude-haiku-4-5-20251001` | ✅ Migrated 2026-04-22 |
| `app/api/_prompts/generate-session.js` | ~~sonnet-4-20250514~~ | `claude-sonnet-4-6` | ✅ Migrated 2026-04-22 |
| `config/route.js` | sonnet-4-20250514 | `claude-sonnet-4-6` | ⚠️ File not found |
| `components/role-lens-scorer/api/score.js` | sonnet-4-20250514 | `claude-opus-4-7` | ⏳ Pending (standalone) |

### Lens Project — Components

| File | Current | Target | Status |
|------|---------|--------|--------|
| `components/lens-scorer.jsx` | sonnet-4-20250514 | `claude-opus-4-7` | ⏳ Pending |
| `components/lens-scorer-compare.jsx` | sonnet-4-20250514 | `claude-opus-4-7` | ⏳ Pending |
| `components/role-lens-scorer.jsx` | sonnet-4-20250514 | `claude-opus-4-7` | ⏳ Pending |
| `components/lens-scorer-compare/public/index.html` | sonnet-4-20250514 | `claude-opus-4-7` | ⏳ Pending |
| `app/components/LensExperience.jsx` | sonnet-4-20250514 | `claude-sonnet-4-6` | ⏳ Pending |

### Lens Project — Documentation (Low Priority)

| File | Status |
|------|--------|
| `CLAUDE.md` | ✅ Updated 2026-04-16 |
| `code-review.mjs` | ✅ Migrated 2026-04-16 |
| `review-profiles/scoring.md` | ✅ Migrated 2026-04-16 |
| `review-profiles/form.md` | ✅ Migrated 2026-04-16 |
| `docs/lens-serverless-proxy-architecture-v1.1.md` | ✅ Migrated 2026-04-16 |
| `specs/lens-validation-prompt-v1.0.md` | ✅ Migrated 2026-04-16 |
| `specs/rc-role-input-form-brief.md` | ✅ Migrated 2026-04-16 |
| `specs/rc-session-generation-brief.md` | ✅ Migrated 2026-04-16 |
| `CHANGELOG.md` | ⏸️ Keep historical refs |

### Job Search Project

| File | Current | Target | Status |
|------|---------|--------|--------|
| `CLAUDE.md` | sonnet-4-20250514 | Update to model table | ⏳ Pending |
| `code-review-skill-v2.md` | sonnet-4-20250514 | `claude-sonnet-4-6` | ⏳ Pending |
| `code-review.mjs` | sonnet-4-20250514 | `claude-sonnet-4-6` | ⏳ Pending |
| `Feedback Loop - Applied.json` | sonnet-4-20250514 | `claude-sonnet-4-6` | ⏳ Pending |
| `Feedback Loop - Not a Fit.json` | sonnet-4-20250514 | `claude-sonnet-4-6` | ⏳ Pending |

---

## Summary

| Category | Pending | Completed |
|----------|---------|-----------|
| Lens API Routes | 1 | 11 |
| Lens Components | 5 | 0 |
| Lens Docs | 0 | 8 |
| Job Search | 5 | 0 |
| **Total** | **11** | **19** |

---

## Migration Process

1. **API Routes first** — These are production-critical
2. **Test each route** — Verify responses are consistent
3. **Components second** — Test UI scoring flows
4. **Documentation last** — Update references
5. **Deploy** — Push to Vercel

---

*Last updated: 2026-04-22 by Claude Code*
