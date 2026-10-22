# Agent Workflows

Version-controlled, provider-neutral development workflows and optional AI agent skills.

This repository is the **source of truth for reusable workflow guidance**, not a background agent service, a GitHub review bot, or an MCP server. Skills help capable clients follow the guidance; agents without skill support can follow the Markdown procedures directly.

## Start here

- [Development lifecycle](workflows/development-lifecycle.md) — shared end-to-end process, from scope to independent review.
- [prepare-pr](skills/prepare-pr/SKILL.md) — author-side adversarial preflight before reviewer handoff.
- [Preflight checklist](skills/prepare-pr/references/review-checklist.md) — risk-oriented questions.
- [Pilot scenarios](evaluations/prepare-pr/scenarios.md) — manual behavior checks for Atlas, Benchmark and other clients.

## How the pieces fit

1. The **target repository** owns its technical conventions, commands and deployment constraints, usually documented in AGENTS.md and project docs.
2. This repository owns **portable development process guidance**. Where repository-specific instructions conflict with generic examples, follow the more specific, safe instructions.
3. An optional **installed skill** helps the agent execute part of the process using its available tools. Installing it does not grant tools, permissions or automatic enforcement.
4. The **independent reviewer** remains separate from the developer's own preflight review.

## Client adoption

- **ChatGPT:** install/package the skill into a supported ChatGPT skill environment or private skills-only plugin, if available, then verify that it actually loads for PR-preparation tasks. A GitHub clone alone does not install a ChatGPT skill.
- **Codex / Claude Code / other clients:** install or reference the skill using that client's supported mechanism, or point the agent at the workflow document. Do not assume the same discovery or instruction-file behavior across products or versions.
- **No skill available:** follow the development lifecycle and checklist directly. Never block solely because a named skill cannot be loaded.

Skills are instructions, **not CI gates**. Automation and reviewer analytics are out of scope. Changes to these instructions should be reviewed like code.

## Validation

Run `python3 scripts/validate.py` locally, or inspect the repository's `Validate workflow files` GitHub Actions check. This checks structural consistency, **not the correctness of AI reasoning**. Use the manual pilot scenarios to evaluate behavior.

## Rollout status

The initial `prepare-pr` workflow is a pilot. It is **not automatically enabled** in Atlas, Benchmark or any connected AI client by merging this repository. Existing development tracks remain unchanged until their adoption is explicitly agreed and validated.
