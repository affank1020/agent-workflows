"""Regression coverage for reproducible, source-authenticated plugin packages."""
from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_plugin", ROOT / "scripts/build_plugin.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PackagingTests(unittest.TestCase):
    def test_includes_dual_manifests_and_canonical_skill(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "build.zip"
            report = module.build(path, installed_version="0.1.0")
            self.assertTrue(report["source_files_verified_against_head"])
            self.assertEqual(report["source_commit"], module.git("rev-parse", "HEAD").decode().strip())
            with ZipFile(path) as package:
                self.assertEqual(sorted(package.namelist()), report["files"])
                self.assertEqual(len(package.namelist()), len(set(package.namelist())))
                self.assertEqual(
                    package.read("skills/prepare-pr/SKILL.md"),
                    (ROOT / "skills/prepare-pr/SKILL.md").read_bytes(),
                )
                portable = json.loads(package.read("plugin.json"))
                legacy = json.loads(package.read(".codex-plugin/plugin.json"))
                self.assertEqual(portable["name"], "prepare-pr")
                self.assertEqual(portable["version"], "0.1.0")
                self.assertEqual(portable["extensions"]["com.openai"]["interface"]["displayName"], "Prepare PR")
                self.assertEqual(legacy["interface"]["displayName"], "Prepare PR")
                self.assertEqual(legacy["skills"], "./skills")
                self.assertNotIn("$schema", legacy)
                self.assertEqual(legacy["version"], portable["version"])

    def test_reproducible_archive_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            first, second = Path(temp) / "a.zip", Path(temp) / "b.zip"
            module.build(first, installed_version="0.1.1")
            module.build(second, installed_version="0.1.1")
            self.assertEqual(hashlib.sha256(first.read_bytes()).digest(), hashlib.sha256(second.read_bytes()).digest())

    def test_second_and_third_update_do_not_upload_lower_versions(self):
        # Plugin Creator auto-bumps an equal version to the next patch.
        current = "0.1.0"
        with tempfile.TemporaryDirectory() as temp:
            for round_no in range(2):
                archive = Path(temp) / f"update-{round_no}.zip"
                report = module.build(archive, installed_version=current)
                with ZipFile(archive) as package:
                    portable = json.loads(package.read("plugin.json"))
                    legacy = json.loads(package.read(".codex-plugin/plugin.json"))
                self.assertEqual(portable["version"], current)
                self.assertEqual(legacy["version"], current)
                self.assertEqual(report["installed_version_at_build"], current)
                major, minor, patch = module.version_parts(current)
                current = f"{major}.{minor}.{patch + 1}"  # simulated Creator response
            self.assertEqual(current, "0.1.2")

    def test_respects_higher_canonical_baseline(self):
        self.assertEqual(module.publish_version("1.2.0", "1.1.9"), "1.2.0")
        self.assertEqual(module.publish_version("1.2.0", "1.3.0"), "1.3.0")

    def test_rejects_unexpected_version_syntax(self):
        for value in ["v1.2.3", "0.1.0-rc.1", "01.2.3", "", "0.1.0+build"]:
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "stable"):
                module.publish_version("0.1.0", value)

    def test_output_must_be_outside_checkout(self):
        with self.assertRaisesRegex(ValueError, "outside"):
            module.build(ROOT / "build.zip")

    def create_test_checkout(self, root: Path) -> tuple[Path, Path]:
        checkout = root / "checkout"
        skill = checkout / "skills" / "prepare-pr" / "SKILL.md"
        manifest = checkout / "packaging" / "prepare-pr" / "plugin.json"
        skill.parent.mkdir(parents=True)
        manifest.parent.mkdir(parents=True)
        skill.write_text("---\nname: prepare-pr\ndescription: Temporary test skill fixture\n---\n# Sample\n", encoding="utf-8")
        manifest.write_text((ROOT / "packaging/prepare-pr/plugin.json").read_text(encoding="utf-8"))
        commands = [
            ["git", "init", "-q", str(checkout)],
            ["git", "-C", str(checkout), "config", "user.email", "test@example.org"],
            ["git", "-C", str(checkout), "config", "user.name", "Test User"],
            ["git", "-C", str(checkout), "add", "."],
            ["git", "-C", str(checkout), "commit", "-q", "-m", "fixture"],
        ]
        for args in commands:
            subprocess.run(args, check=True, capture_output=True)
        return checkout, skill

    def test_modified_tracked_file_cannot_claim_head_commit(self):
        with tempfile.TemporaryDirectory() as temp:
            checkout, skill = self.create_test_checkout(Path(temp))
            skill.write_text(skill.read_text() + "UNREVIEWED EDIT\n", encoding="utf-8")
            inventory = {"skills/prepare-pr/SKILL.md": skill}
            with patch.object(module, "ROOT", checkout), patch.object(module, "INVENTORY", inventory):
                with self.assertRaisesRegex(ValueError, "differs from recorded HEAD"):
                    module.commit_sources()

    def test_untracked_substituted_file_cannot_claim_head_commit(self):
        with tempfile.TemporaryDirectory() as temp:
            checkout, _ = self.create_test_checkout(Path(temp))
            other = checkout / "packaging" / "prepare-pr" / "untracked.yaml"
            other.write_text("not committed\n", encoding="utf-8")
            inventory = {"skills/prepare-pr/agents/openai.yaml": other}
            with patch.object(module, "ROOT", checkout), patch.object(module, "INVENTORY", inventory):
                with self.assertRaisesRegex(ValueError, "not a file tracked by HEAD"):
                    module.commit_sources()


if __name__ == "__main__":
    unittest.main()
