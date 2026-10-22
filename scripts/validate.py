#!/usr/bin/env python3
"""Validate the structure of portable AI skill packages.

Behavioral correctness and skill selection still require manual agent pilots.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

import yaml
from yaml.nodes import MappingNode

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
FRONTMATTER = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.S)


def fail(message: str) -> None:
    raise ValueError(message)


class UniqueKeySafeLoader(yaml.SafeLoader):
    """Safe YAML subset with duplicate mapping keys forbidden."""

    def construct_mapping(self, node: MappingNode, deep: bool = False) -> dict:
        if not isinstance(node, MappingNode):
            raise yaml.constructor.ConstructorError(None, None, "expected mapping", node.start_mark)
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                fail("YAML frontmatter keys must be strings")
            if key in result:
                fail(f"duplicate YAML key: {key}")
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def check_skills(root: Path = ROOT) -> None:
    skills = root / "skills"
    if not skills.is_dir():
        fail("Missing skills/ directory")
    directories = sorted(path for path in skills.iterdir() if path.is_dir() and not path.name.startswith("."))
    if not directories:
        fail("No skill directories found")
    for directory in directories:
        if directory.is_symlink():
            fail(f"Symlinked skill directory not allowed: {directory.name}")
        path = directory / "SKILL.md"
        display = path.relative_to(root)
        if not path.is_file():
            fail(f"{display}: missing entrypoint")
        value = path.read_text(encoding="utf-8")
        match = FRONTMATTER.match(value)
        if not match:
            fail(f"{display}: missing YAML frontmatter")
        try:
            metadata = yaml.load(match.group(1), Loader=UniqueKeySafeLoader)
        except yaml.YAMLError as error:
            fail(f"{display}: invalid YAML frontmatter: {error}")
        if not isinstance(metadata, dict):
            fail(f"{display}: frontmatter must be a YAML mapping")
        name = metadata.get("name")
        description = metadata.get("description")
        if not isinstance(name, str) or not SKILL_NAME.fullmatch(name) or name != directory.name:
            fail(f"{display}: name must be a string matching its directory")
        if not isinstance(description, str) or not 40 <= len(description) <= 1024:
            fail(f"{display}: description must be a string of 40-1024 characters")
        if not value[match.end():].strip():
            fail(f"{display}: missing skill procedure")


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
    print("OK: required files, valid YAML metadata, skill directories, Markdown links and scenarios")
    print("Note: agent behavior and review accuracy still require manual pilot evaluation")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        sys.exit(1)
