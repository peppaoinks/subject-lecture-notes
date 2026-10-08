import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "scripts" / "project_tools.py"


class ToolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "我的讲义"
        self.path.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def command(self, operation, *args, expect=0):
        result = subprocess.run([sys.executable, str(PROJECT), operation, "--project", str(self.path),
                                 *args], capture_output=True, text=True)
        self.assertEqual(result.returncode, expect, result.stderr)
        return json.loads(result.stdout) if expect == 0 else result.stderr

    def test_init_preserves_preferences_and_resume_state(self):
        original = "用户选择：只使用PPT，正文绿色。\n"
        (self.path / "讲义编写约定.md").write_text(original)
        self.command("init")
        self.assertEqual((self.path / "讲义编写约定.md").read_text(), original)
        self.command("progress", "--chapter", "ch01", "--stage", "草稿", "--next", "核对符号")
        self.command("init")
        state = self.command("progress")
        self.assertEqual(state["ch01"]["next"], "核对符号")
        self.assertEqual(state["ch01"]["stage"], "草稿")

    def test_snapshot_diff_restore_preserve_latest_work(self):
        (self.path / "chapter.md").write_text("原符号：ν。\n")
        saved = self.command("checkpoint", "--files", "chapter.md", "--note", "修改前")
        (self.path / "chapter.md").write_text("原符号：ν。\n增加解释。\n")
        changes = self.command("diff", "--snapshot", saved["id"])
        self.assertIn("+增加解释。", changes[0]["diff"])
        preview = self.command("restore-preview", "--snapshot", saved["id"])
        self.assertEqual((Path(preview["preview"]) / "chapter.md").read_text(), "原符号：ν。\n")
        self.assertIn("增加解释", (self.path / "chapter.md").read_text())
        self.command("restore-preview", "--snapshot", saved["id"], expect=1)

    def test_deleted_binary_and_corrupt_snapshot(self):
        (self.path / "chapter.md").write_text("删除前。\n")
        (self.path / "chart.bin").write_bytes(b"\0\1")
        saved = self.command("checkpoint", "--files", "chapter.md", "chart.bin")
        (self.path / "chapter.md").unlink()
        (self.path / "chart.bin").write_bytes(b"\0\2")
        changes = self.command("diff", "--snapshot", saved["id"])
        self.assertTrue(changes[0]["deleted"])
        self.assertIn("二进制文件变化", changes[1]["diff"])
        copied = self.path / ".lecture" / "snapshots" / saved["id"] / "files" / "chart.bin"
        copied.write_bytes(b"broken")
        error = self.command("restore-preview", "--snapshot", saved["id"], expect=1)
        self.assertIn("快照文件损坏", error)

    def test_cache_input_output_environment_and_missing_file(self):
        source, output = self.path / "experiment.py", self.path / "output.txt"
        source.write_text("print(2)\n")
        output.write_text("2\n")
        self.command("cache-record", "--name", "demo", "--files", "experiment.py",
                     "--outputs", "output.txt", "--environment", "stdlib-test")
        def check(environment="stdlib-test"):
            return self.command("cache-check", "--name", "demo", "--environment", environment)["reusable"]
        self.assertTrue(check())
        self.assertFalse(check("changed"))
        source.write_text("print(3)\n")
        self.assertFalse(check())
        source.write_text("print(2)\n")
        output.write_text("changed\n")
        self.assertFalse(check())
        output.unlink()
        self.assertFalse(check())

    def test_outside_project_paths_are_rejected(self):
        (self.path.parent / "outside.md").write_text("outside")
        self.command("checkpoint", "--files", "../outside.md", expect=1)
        (self.path / "link.md").symlink_to(self.path.parent / "outside.md")
        self.command("checkpoint", "--files", "link.md", expect=1)
        self.command("diff", "--snapshot", "../../outside", expect=1)

    def test_reader_safe_text_duplicate_ids_and_input_preservation(self):
        spec = importlib.util.spec_from_file_location("reader", ROOT / "scripts" / "build_reader.py")
        reader = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(reader)
        injection = "</script><script>window.injected=true</script>"
        data = {"title": "test", "chapters": [{"id": "ch01", "title": "ν不改名", "sections": [
            {"title": "资料", "paragraphs": [injection]}]}]}
        source, target = self.path / "data.json", self.path / "reader.html"
        source.write_text(json.dumps(data, ensure_ascii=False))
        reader.build(source, target)
        self.assertNotIn(injection, target.read_text())
        self.assertIn("ν不改名", target.read_text())
        data["chapters"].append(data["chapters"][0])
        with self.assertRaises(ValueError):
            reader.validate(data)
        with self.assertRaises(ValueError):
            reader.build(source, source)


if __name__ == "__main__":
    unittest.main()
