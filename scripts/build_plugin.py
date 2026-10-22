#!/usr/bin/env python3
"""Build a reproducible skills-only plugin from commit-verified repository files.

This script NEVER publishes a plugin or accesses ChatGPT credentials.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = "prepare-pr"
CONFIG_ROOT = ROOT / "packaging" / PLUGIN
INVENTORY = {
    "plugin.json": CONFIG_ROOT / "plugin.json",
    "skills/prepare-pr/agents/openai.yaml": CONFIG_ROOT / "agents" / "openai.yaml",
    "skills/prepare-pr/SKILL.md": ROOT / "skills/prepare-pr/SKILL.md",
    "skills/prepare-pr/references/review-checklist.md": ROOT / "skills/prepare-pr/references/review-checklist.md",
    "workflows/development-lifecycle.md": ROOT / "workflows/development-lifecycle.md",
}
FIXED_DATE = (2024, 1, 1, 0, 0, 0)
VERSION_PATTERN = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)\Z")


def version_parts(value: str) -> tuple[int, int, int]:
    if not isinstance(value, str) or not VERSION_PATTERN.fullmatch(value):
        raise ValueError("Plugin version must use stable MAJOR.MINOR.PATCH (no prerelease/build metadata)")
    return tuple(int(x) for x in value.split("."))


def publish_version(baseline: str, installed: str | None = None) -> str:
    """An equal version auto-bumps on Plugin Creator update; lower versions fail."""
    base = version_parts(baseline)
    if installed is None:
        return baseline  # Offline CI builds a non-publishable preview.
    current = version_parts(installed)
    return baseline if base > current else installed


def git(*args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=True, capture_output=True,
    ).stdout


def commit_sources() -> tuple[str, dict[str, bytes]]:
    """Snapshot included files, requiring byte-for-byte equality to HEAD blobs."""
    sha = git("rev-parse", "--verify", "HEAD^{commit}").decode("ascii").strip()
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("Cannot identify full Git commit SHA")
    content = {}
    for dest, path in sorted(INVENTORY.items()):
        target = PurePosixPath(dest)
        if target.is_absolute() or ".." in target.parts:
            raise ValueError(f"Unsafe archive path: {dest}")
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Invalid or missing source file: {path}")
        relative = path.relative_to(ROOT).as_posix()
        try:
            original = git("show", f"{sha}:{relative}")
        except subprocess.CalledProcessError as error:
            raise ValueError(f"Source is not a file tracked by HEAD: {relative}") from error
        data = path.read_bytes()
        if data != original:
            raise ValueError(f"Source differs from recorded HEAD: {relative}")
        content[dest] = data
    if git("rev-parse", "--verify", "HEAD^{commit}").decode("ascii").strip() != sha:
        raise ValueError("HEAD changed while packaging; retry from a stable checkout")
    return sha, content


def prepare_files(sources: dict[str, bytes], installed_version: str | None) -> tuple[dict[str, bytes], str]:
    manifest = json.loads(sources["plugin.json"])
    if not isinstance(manifest, dict):
        raise ValueError("Plugin manifest must be a JSON object")
    if manifest.get("name") != PLUGIN:
        raise ValueError("Plugin identity must remain prepare-pr")
    if manifest.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
        raise ValueError("Expected portable plugin schema")
    interface = manifest.get("extensions", {}).get("com.openai", {}).get("interface", {})
    if interface.get("displayName") != "Prepare PR":
        raise ValueError("Plugin display name must remain Prepare PR")
    if not 1 <= len(interface.get("shortDescription", "")) <= 30:
        raise ValueError("Plugin subtitle must be 1-30 characters")
    version = publish_version(manifest.get("version"), installed_version)
    manifest["version"] = version
    # The portable manifest owns presentation metadata. Derive a true legacy
    # Codex-compatible overlay rather than copying the portable schema there.
    legacy = {k: manifest[k] for k in ("name", "version", "description", "author", "repository") if k in manifest}
    legacy["interface"] = interface
    legacy["skills"] = "./skills"
    encode = lambda obj: (json.dumps(obj, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    files = dict(sources)
    files["plugin.json"] = encode(manifest)
    files[".codex-plugin/plugin.json"] = encode(legacy)
    return files, version


def build(output: Path, installed_version: str | None = None) -> dict:
    output = output.resolve()
    if output.is_relative_to(ROOT):
        raise ValueError("Output archive must be outside the source checkout")
    sha, sources = commit_sources()
    files, version = prepare_files(sources, installed_version)
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for filename, data in sorted(files.items()):
            info = ZipInfo(filename, FIXED_DATE)
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compress_type=ZIP_DEFLATED, compresslevel=9)
    return {
        "plugin": PLUGIN,
        "source_commit": sha,
        "source_files_verified_against_head": True,
        "installed_version_at_build": installed_version,
        "package_version": version,
        "archive_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "files": sorted(files),
        "note": "Build only. Publishing requires a fresh installed version and release ID.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="ZIP output outside the repository")
    parser.add_argument("--report", type=Path, help="Optional JSON provenance report")
    parser.add_argument(
        "--installed-version", help="Current version from Plugin Creator (required for a real update)"
    )
    args = parser.parse_args()
    try:
        result = build(args.output, args.installed_version)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError, json.JSONDecodeError) as error:
        print(f"Plugin packaging failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
