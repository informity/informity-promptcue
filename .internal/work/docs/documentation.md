# PromptCue — Document Style Guide

**Status:** 🔄 ACTIVE
**Version:** 1.0
**Last updated:** 2026-03-23
**Scope:** Working documents for features, refactoring, fixes, planning, and contracts

---

## Purpose

Define consistent structure and conventions for internal working documents (improvement
plans, refactoring specs, fix proposals, backlog items, contracts). Use this guide when
creating new documents in `.internal/work/` so structure and status tracking remain
uniform across the project.

---

## Folder Map

```
.internal/
  tests/                   — test query sets and run outputs
    queries/               — queries-N.json files
    runs/                  — run_vN.json outputs
  work/
    active/                — active or near-term multi-day work
    backlog/               — deferred ideas with substantial prior planning
    contracts/             — normative behavior and API specs
    docs/                  — persistent reference (architecture, build guide, etc.)
```

---

## Which Document Type?

- **Normative behavior, API contract, or schema spec?** → `contracts/`
- **Raw idea, not yet committed to?** → entry in the relevant `backlog/` file
- **Complex deferred idea with planning?** → new file in `work/backlog/`
- **Active or near-term implementation, multi-day?** → `work/active/` doc, full phased format
- **Small change: same-day, 1–3 files?** → `work/active/` doc, lightweight format
- **Persistent reference (architecture, build instructions, etc.)?** → `work/docs/`

---

## Document Types

| Type | Location | Use Case |
|------|----------|----------|
| **Feature / Refactor (full)** | `work/active/` | Active or near-term multi-day work, phased plans |
| **Feature / Refactor (lightweight)** | `work/active/` | Same-day changes, 1–3 files; minimal format |
| **Backlog detail file** | `work/backlog/` | Deferred idea with substantial planning |
| **Contract / Spec** | `work/contracts/` | Normative behavior, API shape, schema rules |
| **Reference doc** | `work/docs/` | Architecture notes, build guide, style guides |

---

## Required Elements by Document Type

| Document Type | Header | Problem Statement | Phases | Implementation Notes |
|---------------|--------|-------------------|--------|----------------------|
| **Feature / Refactor (full)** | Required | Required | Required | At least one |
| **Feature / Refactor (lightweight)** | None | Required (1 paragraph) | None | Files + exit criteria only |
| **Backlog detail file** | Required | Required | Optional | Constraints + acceptance criteria |
| **Contract** | Required | Required (as Purpose) | N/A | Optional |

---

## Required Elements (Minimum)

Feature and refactor plans must include:

### 1. Header

- **Title:** `# PromptCue — [Topic]` or `# [Topic] Plan`
- **Status:** Always use `[ICON] [CAPITALIZED_STATUS]` — must align with phase status when the document has phases.
- **Version:** Document version (e.g. `1.0`).
- **Date:** `Last updated: YYYY-MM-DD`
- **Scope:** One line describing what the document covers

#### Document Status

| Document State | Format | When to Use |
|----------------|--------|-------------|
| All phases done | `✅ COMPLETED` | Work is finished |
| Work in progress | `🔄 IN PROGRESS` | Some phases done, some not |
| Not started | `⏳ NOT STARTED` | All phases planned but none begun |
| Partially done | `⚠️ PARTIAL` | Some scope done, some deferred |
| Deferred | `⏸️ DEFERRED` | Work postponed |
| Active (no phases) | `🔄 ACTIVE` | Living doc in use (contracts, guides, backlogs) |

Example:

```markdown
# PromptCue — [Feature Name]

**Status:** 🔄 IN PROGRESS
**Version:** 1.0
**Last updated:** 2026-03-23
**Scope:** [One-line scope]
```

---

### 2. Problem Statement / Description

One paragraph that answers:

- **What** is the problem or goal?
- **Why** does it matter?
- **What** is the desired outcome?

Place this immediately after the header block, before phases.

---

### 3. Phase-Based Structure

Organize implementation as **Phase 1**, **Phase 2**, etc. For small, single-scope work a
single phase is fine. Each phase must have:

- **Phase title** with status indicator
- **Goal** (1–2 sentences)
- **Scope** (bullet list of in-scope items)
- **Exit criteria** (how you know the phase is done)

#### Phase Status Indicators

| Status | Format | When to Use |
|--------|--------|-------------|
| Not started | `⏳ NOT STARTED` | Phase is planned but work has not begun |
| In progress | `🔄 IN PROGRESS` | Work is underway |
| Completed | `✅ COMPLETED` | Phase is done; optionally add date |
| Partial | `⚠️ PARTIAL` | Some scope done, some deferred |
| Deferred | `⏸️ DEFERRED` | Phase postponed |

**Format:** Place status immediately after the phase title.

```markdown
### Phase 1 — [Phase Name] ⏳ NOT STARTED

- **Goal:** [1–2 sentences]
- **Scope:** [bullets]
- **Exit criteria:** [bullets]
```

```markdown
### Phase 2 — [Phase Name] ✅ COMPLETED (2026-03-23)

- **Goal:** [1–2 sentences]
- **Scope:** [bullets]
- **Exit criteria:** [bullets]
```

---

### 4. Additional Implementation Notes

Include at least one of:

- **Implementation targets:** Files/modules to change
- **Technical notes:** Constraints, dependencies, design decisions
- **Risks and mitigations:** Table of risk → mitigation
- **Success criteria:** Overall pass/fail for the work
- **Non-goals:** Explicitly out of scope

---

## Recommended Additions

### Implementation Summary Table

For multi-phase work, add a quick-reference table immediately after the header:

```markdown
## Implementation Summary

| Phase | Scope | Status |
|-------|-------|--------|
| Phase 1 | [Brief scope] | ✅ COMPLETED |
| Phase 2 | [Brief scope] | ⏳ NOT STARTED |
```

---

### Document Role

When the document relates to others (e.g. implementation plan vs. contract), state its role:

```markdown
## Document Role

- This document is the **implementation plan** for [X].
- The normative contract lives in `contracts/[name].md`.
- Contract rules are referenced, not redefined here.
```

---

### Exit Criteria Per Phase

```markdown
**Exit criteria**
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] All existing tests pass
```

---

### Risks and Mitigations Table

```markdown
## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| [Risk description] | [How to mitigate] |
```

---

## Document Templates

### Feature / Refactor Plan (Phased)

For small, single-scope work use one phase only.

```markdown
# PromptCue — [Feature Name]

**Status:** ⏳ NOT STARTED
**Version:** 1.0
**Last updated:** YYYY-MM-DD
**Scope:** [One-line scope]

---

## Goal

[1 paragraph: problem, why it matters, desired outcome]

---

## Implementation Summary

| Phase | Scope | Status |
|-------|-------|--------|
| Phase 1 | [Scope] | ⏳ NOT STARTED |
| Phase 2 | [Scope] | ⏳ NOT STARTED |

---

## Phase 1 — [Name] ⏳ NOT STARTED

- **Goal:** [1–2 sentences]
- **Scope:** [bullets]
- **Exit criteria:** [bullets]

---

## Phase 2 — [Name] ⏳ NOT STARTED

- **Goal:** [1–2 sentences]
- **Scope:** [bullets]
- **Exit criteria:** [bullets]

---

## Implementation Notes

- [Targets, constraints, design decisions]

---

## Success Criteria

- [Overall pass/fail criteria]
```

---

### Feature / Refactor Plan (Lightweight)

Use for same-day changes touching 1–3 files. No header block, no phases, no status tracking.

```markdown
# [Short Title]

## Problem

[1 paragraph: what is wrong or missing and why it matters]

## Files

- `path/to/file.py` — [what changes]
- `path/to/other.py` — [what changes]

## Exit criteria

- [ ] [Specific, verifiable criterion]
- [ ] [Specific, verifiable criterion]
- [ ] Zero behavior changes / existing tests pass
```

---

### Backlog Detail File (in `work/backlog/`)

Use when a deferred idea already has substantial prior planning worth preserving.

```markdown
# PromptCue — [Topic] (Backlog)

**Last updated:** YYYY-MM-DD

---

## What

[What it is and the problem it solves]

---

## Constraints

- [Must preserve / must not break]

---

## Phases (outline)

1. [Phase 1 name — brief description]
2. [Phase 2 name — brief description]

---

## Decision Gate

Implement only when: [conditions]

---

## Acceptance Criteria

- [Measurable success criteria]
```

---

### Contract / Spec Document (in `work/contracts/`)

```markdown
# PromptCue — [Contract Name]

**Status:** 🔄 ACTIVE
**Version:** 1.0
**Last updated:** YYYY-MM-DD
**Scope:** [What this contract governs]

---

## Document Role

- This document is the **normative contract** for [X].
- If planning docs conflict with this file, this contract takes precedence.

---

## Purpose

[What the contract defines]

---

## [Section 1]

[Contract rules, invariants, allowed/not-allowed]
```

---

## Consistency Rules

- Use **kebab-case** for filenames: `http-api-plan.md`, `classifier-refactor.md`.
- Use **Title Case** for document titles and phase names.
- Use **sentence case** for body text and descriptions.
- Use `---` horizontal rules to separate major sections.
- Header **Status** and phase status both use `[ICON] [CAPITALIZED_STATUS]`.
- When a phase completes, add the date: `✅ COMPLETED (YYYY-MM-DD)`.
- Update `Last updated` when phases change, scope changes, or the doc is revisited.
- Reference related docs by path relative to the repo root:
  `.internal/work/contracts/promptcue-contract.md`.

---

## Quick Reference: Status Icons

| Icon | Meaning | Use in |
|------|---------|--------|
| ⏳ | NOT STARTED | Phase or document |
| 🔄 | IN PROGRESS / ACTIVE | Phase or document |
| ✅ | COMPLETED | Phase or document |
| ⚠️ | PARTIAL | Phase or document |
| ⏸️ | DEFERRED | Phase or document |
