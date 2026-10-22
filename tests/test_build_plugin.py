"""Test the reproducible Prepare PR package without publishing it."""
from pathlib import Path
import hashlib
import importlib.util
import json
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_plugin", ROOT / "scripts/build_plugin.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PackagingTests(unittest.TestCase):
    def test_includes_complete_plugin(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "build.zip"
            with patch.object(module, "source_sha", return_value="a" * 40):
                report = module.build(path)
            self.assertEqual(report["plugin"], "prepare-pr")
            self.assertEqual(report["source_commit"], "a" * 40)
            with ZipFile(path) as package:
                self.assertEqual(sorted(package.namelist()), sorted(module.INVENTORY))
                self.assertEqual(len(package.namelist()), len(set(package.namelist())))
                self.assertEqual(package.read("skills/prepare-pr/SKILL.md"), (ROOT / "skills/prepare-pr/SKILL.md").read_bytes())
                manifest = json.loads(package.read("plugin.json"))
                self.assertEqual(manifest["name"], "prepare-pr")
                self.assertEqual(manifest["extensions"]["com.openai"]["interface"]["displayName"], "Prepare PR")

    def test_reproducible_archive_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            first, second = Path(temp) / "a.zip", Path(temp) / "b.zip"
            with patch.object(module, "source_sha", return_value="b" * 40):
                module.build(first)
                module.build(second)
            self.assertEqual(hashlib.sha256(first.read_bytes()).digest(), hashlib.sha256(second.read_bytes()).digest())

    def test_output_must_be_outside_source_checkout(self):
        with self.assertRaisesRegex(ValueError, "outside"):
            module.build(ROOT / "build.zip")

    def test_rejects_missing_or_symlinked_sources(self):
        path = ROOT / "skills/prepare-pr/SKILL.md"
        with patch.dict(module.INVENTORY, {"fake": ROOT / "nonexistent.md"}):
            with self.assertRaisesRegex(ValueError, "Invalid or missing"):
                module.validate_source()


if __name__ == "__main__":
    unittest.main()
