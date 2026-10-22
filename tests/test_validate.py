"""Regression tests for skill package validation."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate import check_skills


class SkillMetadataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.skill = self.root / "skills" / "example-skill" / "SKILL.md"
        self.skill.parent.mkdir(parents=True)

    def write(self, frontmatter: str) -> None:
        self.skill.write_text("---\n" + frontmatter + "\n---\n\n# Procedure\nDo the work.\n", encoding="utf-8")

    def test_accepts_valid_plain_yaml(self):
        self.write("name: example-skill\ndescription: Prepare a pull request by checking the entire change set before review.")
        check_skills(self.root)

    def test_accepts_folded_description(self):
        self.write("name: example-skill\ndescription: >\n  Prepare a pull request by checking the entire\n  change set before review and handoff.")
        check_skills(self.root)

    def test_rejects_unquoted_colon(self):
        self.write("name: example-skill\ndescription: Prepare branch: check the complete diff before handoff.")
        with self.assertRaisesRegex(ValueError, "invalid YAML"):
            check_skills(self.root)

    def test_rejects_unterminated_quoted_string(self):
        self.write('name: example-skill\ndescription: "Prepare the complete change set before handoff.')
        with self.assertRaisesRegex(ValueError, "invalid YAML"):
            check_skills(self.root)

    def test_rejects_duplicate_keys(self):
        self.write("name: example-skill\nname: example-skill\ndescription: Prepare the entire diff to reduce defects before review.")
        with self.assertRaisesRegex(ValueError, "duplicate YAML key"):
            check_skills(self.root)

    def test_rejects_non_string_description(self):
        self.write("name: example-skill\ndescription: [one, two, three]")
        with self.assertRaisesRegex(ValueError, "description must be a string"):
            check_skills(self.root)

    def test_rejects_missing_skill_entrypoint(self):
        self.write("name: example-skill\ndescription: Prepare a pull request by checking the entire change set before review.")
        (self.root / "skills" / "future-skill" / "references").mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, "missing entrypoint"):
            check_skills(self.root)

    def test_rejects_missing_all_skills(self):
        self.write("name: example-skill\ndescription: Prepare the entire diff to reduce defects before review.")
        self.skill.unlink()
        with self.assertRaisesRegex(ValueError, "missing entrypoint"):
            check_skills(self.root)


if __name__ == "__main__":
    unittest.main()
