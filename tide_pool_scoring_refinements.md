# Tide Pool Scoring Refinements

Tracking scoring model failures, pattern analysis, and implemented fixes.

---

## Refinement #1: Pre-Scoring Function Classification Gate

**Date identified**: 2026-03-05
**Pipeline version**: v7 (implemented)
**Previous version**: v6

### Failure Case

**Role**: dbt Labs – Customer Advocacy Manager
**Pipeline score**: 45/moderate
**Correct verdict**: SKIP (function mismatch)

The role is a marketing function hire misclassified by the pipeline as CS-adjacent due to language overlap. "Customer Advocacy" in this JD means CAB governance, customer reference programs, analyst engagement pipelines, and content production — not VoC loops or support org leadership. Explicit requirement: 5+ years in customer marketing or customer advocacy roles.

### Root Cause

The pipeline had no mechanism to distinguish CS-flavored marketing roles from actual CS/support/CX hires. Scoring ran on all jobs that passed auto-disqualifiers, regardless of whether the role's function was actually in-scope.

Specific failures:
- Developer tools sector match inflated score
- Clean VC backing (a16z, Sequoia) — no PE penalty
- Title didn't trigger a function mismatch flag
- Pipeline can't distinguish CS-flavored marketing roles from actual CS/support hires

### Fix: Pre-Scoring Binary Gate

Added a **STEP 0** to the Claude evaluation prompt: a binary function classification gate that runs before weighted scoring.

**Gate question**: "Is this a CS/support/CX operations hire, or a marketing/advocacy/content/communications hire?"

**Marketing/advocacy signals that trigger disqualification**:
- Customer Advisory Board (CAB) management or governance
- Customer reference programs or reference databases
- Customer story/case study production
- Analyst relations or analyst engagement pipelines
- Speaking program coordination
- Customer marketing campaigns
- Advocacy content creation or content pipelines
- Event/conference speaker sourcing from customer base
- Review site management (G2, TrustRadius)
- Award/recognition program submissions
- "Customer advocacy" when deliverables are content, references, or analyst briefings

**CS/support/CX signals that confirm in-scope**:
- Support ticket operations, escalation management, SLA ownership
- Customer onboarding program design and delivery
- Customer success metrics ownership (CSAT, NPS, churn, health scores)
- Support team hiring, training, and management
- Support tooling and infrastructure (Zendesk, Intercom, etc.)
- Voice of Customer feedback loops TO product (not FROM customers for marketing)
- Customer retention through service quality (not through reference programs)

**Decision rule**: If the role's primary deliverables are CABs, reference databases, content pipelines, speaking programs, or analyst engagement — regardless of how customer-centric the title sounds — disqualify before weighted scoring runs.

### Impact

Prevents false positives on roles like:
- Customer Advocacy Manager (marketing function)
- Customer Marketing Manager
- Customer Reference Manager
- Customer Community Manager (when content/events-focused)
- Customer Storytelling Lead
- Voice of Customer Analyst (when marketing-facing)

### Configuration Changes

- `evaluation-config.json`: Added `FUNCTION_MISMATCH` disqualifier (priority 4.5)
- `Job Evaluation Pipeline v7.json`: Added STEP 0 function gate to Claude system prompt
- `CLAUDE.md`: Updated version references
