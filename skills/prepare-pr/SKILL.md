---
name: prepare-pr
description: Prepare the author's own branch or draft pull request for independent code review. Use when an agent has implemented, committed, updated, or is about to hand off its own PR; conduct a full-change adversarial preflight, fix credible defects, run available checks and record evidence. Not for an independent review of someone else's PR.
---

# Prepare PR: author-side adversarial preflight

**Role:** You are the author checking your own work. Be skeptical of it. This is **not** independent approval and does not replace any separate Code Reviewer.

Use whatever read-only comparison, file and testing tools the client actually grants. The skill is portable: no specific MCP service, repository, shell, host or CI provider is required. Repository instructions take precedence for project-specific checks without weakening safety.

## Procedure

1. **Identify target.** Confirm repository, intended base (often `main`), feature branch/draft PR and current commit SHA. Consult target-repository instructions. Don't adopt unrelated branches or silently switch repositories.
2. **Get the whole change set.** Prefer the draft PR's complete base-to-head diff **plus** a separately fetched changed-file inventory. Check number of files, changed statuses and patch coverage. A local staged/unstaged diff alone is insufficient. If no PR exists, use a safe supported base-to-head comparison (e.g. merge-base semantics). Include renamed, deleted and binary changes in coverage accounting.
3. **Read context.** Inspect code at the reviewed head, relevant prior behavior at base, callers, interfaces, config, migrations, deployment implications and test coverage. Do not rely on diff hunks alone. Report any file or patch that could not be inspected.
4. **Review adversarially.** Follow [review-checklist.md](references/review-checklist.md) for relevant failure modes. For each suspected bug, construct a concrete trigger, execution path and impact. Check whether surrounding code, invariants or tests already prevent it. Don't invent defects to satisfy a checklist.
5. **Fix and validate.** On the author's approved working branch, correct credible defects and add targeted regression coverage when feasible. Run owner-configured checks and any other explicitly authorized safe checks. Never introduce arbitrary shell execution as a workaround for missing tools; don't claim a check ran unless it did.
6. **Re-review the final head.** After fixes/commits, refresh base/head SHAs and the complete diff; check that evidence still describes the final commit. A changed head invalidates stale review/test claims. If coverage remains incomplete, report exactly which files/paths/checks are missing.
7. **Document and hand off.** Add or update the PR description's `Author preflight (not independent approval)` section using the [shared lifecycle template](../../workflows/development-lifecycle.md). Record base/head SHA, coverage, concrete risk areas, defects/fixes, locally executed checks, observed CI, limitations and handoff readiness.

## Decision and boundaries

- **Ready for independent review:** Full change inventory accounted for, no known unaddressed blocking defects, review evidence tied to the current head, important missing checks disclosed.
- **Blocked / incomplete:** No trustworthy comparison, material unreadable/truncated patches, unresolved blocking defect or uncertain Git operation. Explain the blocker and the safest next step; do not assert clean preflight.
- **Never:** Post an independent GitHub review, self-approve, issue `APPROVE`, merge, mark an independent reviewer as satisfied, forge test/CI evidence, suppress independent findings or edit other projects without authorization.
- **Independent-review request:** If asked to review someone else's PR as a separate reviewer, **do not invoke this author-side skill**; use that reviewer's own process.
- **No skill installation:** A developer can follow the published workflow without claiming this skill was loaded.

## Output

Brief author preflight summary: verdict (`ready` or `blocked/incomplete`), exact compared refs, complete/incomplete file coverage, defects fixed or unresolved, executed test results, limitations and a link to the draft PR if one exists. Do not confuse confidence with proof of correctness.
