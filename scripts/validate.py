#!/usr/bin/env python3
"""Structural checks for portable skill files; no third-party dependencies.

This intentionally does NOT evaluate an AI agent's review quality.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "README.md",
    "AGENTS.md",
    "workflows/development-lifecycle.md",
    "skills/prepare-pr/SKILL.md",
    "skills/prepare-pr/references/review-checklist.md",
    "evaluations/prepare-pr/scenarios.json",
]
LINK = re.compile(r"\[[^]]+\]\(([^)]+)\)")
SKILL_NAME = re.compile(r"^[a-z][a-z0-9-]{0,63}$")


def fail(message: str) -> None:
    raise ValueError(message)


def check_skills() -> None:
    for path in sorted(ROOT.glob("skills/*/SKILL.md")):
        value = path.read_text(encoding="utf-8")
        match = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n", value, flags=re.S)
        if not match:
            fail(f"{path.relative_to(ROOT)}: missing YAML frontmatter")
        metadata: dict[str, str] = {}
        for line in match.group(1).splitlines():
            if ":" not in line:
                fail(f"{path.relative_to(ROOT)}: frontmatter must be simple key: value")
            key, field_value = line.split(":", 1)
            key, field_value = key.strip(), field_value.strip()
            if key in metadata or not key or not field_value:
                fail(f"{path.relative_to(ROOT)}: duplicate or empty field {key!r}")
            metadata[key] = field_value.strip("'\"")
        name = metadata.get("name", "")
        description = metadata.get("description", "")
        if not SKILL_NAME.fullmatch(name) or name != path.parent.name:
            fail(f"{path.relative_to(ROOT)}: name must match directory")
        if not 40 <= len(description) <= 1024:
            fail(f"{path.relative_to(ROOT)}: description must be 40-1024 characters")
        if not value[match.end():].strip():
            fail(f"{path.relative_to(ROOT)}: missing skill procedure")


def check_links() -> None:
    for path in ROOT.rglob("*.md"):
        if ".git" in path.parts:
            continue
        content = path.read_text(encoding="utf-8")
        for target in LINK.findall(content):
            href = target.split("#", 1)[0]
            if not href or href.startswith(("https://", "http://", "mailto:")):
                continue
            if href.startswith("/"):
                fail(f"{path.relative_to(ROOT)}: absolute link is not portable: {href}")
            resolved = (path.parent / href).resolve()
            if not resolved.is_relative_to(ROOT) or not resolved.exists():
                fail(f"{path.relative_to(ROOT)}: broken or escaping link: {href}")


def check_scenarios() -> None:
    cases = json.loads((ROOT / "evaluations/prepare-pr/scenarios.json").read_text(encoding="utf-8"))
    if not isinstance(cases, list) or len(cases) < 4:
        fail("Provide at least four manual pilot scenarios")
    seen: set[str] = set()
    decisions: set[bool] = set()
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("id"), str):
            fail("Every scenario must have a string id")
        if case["id"] in seen:
            fail(f"Duplicate scenario id: {case['id']}")
        seen.add(case["id"])
        decision = case.get("expect_prepare_pr")
        if type(decision) is not bool:
            fail(f"{case['id']}: expect_prepare_pr must be boolean")
        decisions.add(decision)
        if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            fail(f"{case['id']}: missing prompt")
        expectations = case.get("expectations")
        if not isinstance(expectations, list) or not expectations or any(
            not isinstance(item, str) or not item.strip() for item in expectations
        ):
            fail(f"{case['id']}: expectations must be nonempty strings")
    if decisions != {True, False}:
        fail("Manual cases must cover both skill-eligible and non-eligible requests")


def main() -> int:
    for file in REQUIRED:
        if not (ROOT / file).is_file():
            fail(f"Missing required file: {file}")
    check_skills()
    check_links()
    check_scenarios()
    print("OK: required files, skill metadata, Markdown links and scenario structure")
    print("Note: agent behavior and review accuracy still require manual pilot evaluation")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        sys.exit(1)
