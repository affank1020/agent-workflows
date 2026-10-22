#!/usr/bin/env python3
"""Build a deterministic skills-only ChatGPT plugin from tracked repository sources.

This script NEVER publishes a plugin or accesses ChatGPT credentials.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = "prepare-pr"
CONFIG_ROOT = ROOT / "packaging" / PLUGIN
INVENTORY = {
    "plugin.json": CONFIG_ROOT / "plugin.json",
    ".codex-plugin/plugin.json": CONFIG_ROOT / "plugin.json",
    "skills/prepare-pr/agents/openai.yaml": CONFIG_ROOT / "agents" / "openai.yaml",
    "skills/prepare-pr/SKILL.md": ROOT / "skills/prepare-pr/SKILL.md",
    "skills/prepare-pr/references/review-checklist.md": ROOT / "skills/prepare-pr/references/review-checklist.md",
    "workflows/development-lifecycle.md": ROOT / "workflows/development-lifecycle.md",
}
FIXED_DATE = (2024, 1, 1, 0, 0, 0)


def validate_source() -> None:
    for path in INVENTORY.values():
        resolved = path.resolve()
        if path.is_symlink() or not resolved.is_relative_to(ROOT) or not path.is_file():
            raise ValueError(f"Invalid or missing source file: {path}")
    manifest = json.loads((CONFIG_ROOT / "plugin.json").read_text(encoding="utf-8"))
    if manifest.get("name") != PLUGIN:
        raise ValueError("Plugin identity must remain prepare-pr")
    if manifest.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
        raise ValueError("Expected portable plugin schema")
    interface = manifest.get("extensions", {}).get("com.openai", {}).get("interface", {})
    if interface.get("displayName") != "Prepare PR":
        raise ValueError("Plugin display name must remain Prepare PR")
    if len(interface.get("shortDescription", "")) > 30:
        raise ValueError("Plugin subtitle exceeds 30 characters")


def source_sha() -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "--verify", "HEAD"],
        check=True, capture_output=True, text=True,
    )
    return result.stdout.strip()


def build(output: Path) -> dict:
    validate_source()
    output = output.resolve()
    if output.is_relative_to(ROOT):
        raise ValueError("Output archive must be outside the source checkout")
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for filename, src in sorted(INVENTORY.items()):
            # Prevent traversal if future contributors edit the inventory.
            target = PurePosixPath(filename)
            if target.is_absolute() or ".." in target.parts:
                raise ValueError(f"Unsafe archive path: {filename}")
            info = ZipInfo(filename, FIXED_DATE)
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, src.read_bytes(), compress_type=ZIP_DEFLATED, compresslevel=9)
    artifact = {
        "plugin": PLUGIN,
        "source_commit": source_sha(),
        "archive_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "files": sorted(INVENTORY),
        "note": "Build only. Publish through an authenticated plugin update after review.",
    }
    return artifact


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="ZIP output outside the repository")
    parser.add_argument("--report", type=Path, help="Optional JSON provenance report")
    args = parser.parse_args()
    try:
        report = build(args.output)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError, json.JSONDecodeError) as error:
        print(f"Plugin packaging failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
