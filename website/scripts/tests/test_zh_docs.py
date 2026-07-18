import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "zh_docs.py"
spec = importlib.util.spec_from_file_location("zh_docs", MODULE_PATH)
zh_docs = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(zh_docs)


class ZhDocsStateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "website/docs").mkdir(parents=True)
        (self.root / "website/i18n/zh-Hans/docusaurus-plugin-content-docs/current").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def source(self, rel: str, text: str):
        path = self.root / "website/docs" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def translation(self, rel: str, text: str):
        path = self.root / "website/i18n/zh-Hans/docusaurus-plugin-content-docs/current" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def state(self):
        return json.loads((self.root / "website/translation/zh-Hans-state.json").read_text())

    def test_initial_refresh_classifies_existing_and_missing_translations(self):
        self.source("a.md", "# A\n")
        self.source("b.md", "# B\n")
        self.translation("a.md", "# 甲\n")

        report = zh_docs.refresh_state(self.root, "commit-one")

        self.assertEqual(self.state()["documents"]["a.md"]["status"], "needs_review")
        self.assertEqual(self.state()["documents"]["b.md"]["status"], "missing")
        self.assertEqual(report["counts"], {"missing": 1, "needs_review": 1})

    def test_upstream_source_change_marks_approved_translation_needs_update(self):
        self.source("a.md", "# A\n")
        self.translation("a.md", "# 甲\n")
        zh_docs.refresh_state(self.root, "one")
        state_path = self.root / "website/translation/zh-Hans-state.json"
        state = json.loads(state_path.read_text())
        state["documents"]["a.md"]["status"] = "approved"
        state_path.write_text(json.dumps(state))

        self.source("a.md", "# A changed\n")
        zh_docs.refresh_state(self.root, "two")

        self.assertEqual(self.state()["documents"]["a.md"]["status"], "needs_update")
        self.assertEqual((self.root / "website/i18n/zh-Hans/docusaurus-plugin-content-docs/current/a.md").read_text(), "# 甲\n")

    def test_deleted_upstream_doc_archives_translation(self):
        self.source("old.md", "# Old\n")
        self.translation("old.md", "# 旧\n")
        zh_docs.refresh_state(self.root, "one")
        (self.root / "website/docs/old.md").unlink()

        report = zh_docs.refresh_state(self.root, "two")

        self.assertEqual(report["removed"], ["old.md"])
        self.assertFalse((self.root / "website/i18n/zh-Hans/docusaurus-plugin-content-docs/current/old.md").exists())
        self.assertTrue((self.root / "website/translation/archive/two/old.md").exists())

    def test_queue_prioritizes_getting_started_and_excludes_generated_skills(self):
        state = {"documents": {
            "user-guide/skills/bundled/x.md": {"status": "missing"},
            "guides/x.md": {"status": "missing"},
            "getting-started/quickstart.md": {"status": "needs_review"},
        }}

        queue = zh_docs.build_queue(state)

        self.assertEqual([x["path"] for x in queue], ["getting-started/quickstart.md", "guides/x.md"])

    def test_filter_queue_only_keeps_paths_changed_in_this_upstream_sync(self):
        queue = [
            {"path": "getting-started/quickstart.md", "status": "needs_update"},
            {"path": "guides/new.md", "status": "missing"},
            {"path": "reference/old.md", "status": "needs_review"},
        ]

        selected = zh_docs.filter_queue(
            queue,
            ["website/docs/guides/new.md", "getting-started/quickstart.md", "README.md"],
        )

        self.assertEqual(
            [item["path"] for item in selected],
            ["getting-started/quickstart.md", "guides/new.md"],
        )


if __name__ == "__main__":
    unittest.main()
