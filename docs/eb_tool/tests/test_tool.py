"""文件操作与 HTTP 测试均在临时仓库中执行。"""
import contextlib
import http.client
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import eb_tool as tool


class FileManagerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="eb-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.config = tool.load_config()
        self.put("README.md", "# 介绍\n")
        self.put("SUMMARY.md", "# 手工目录\n\n原始内容\n")
        self.put("01 基础/README.md", "# 基础\n")
        self.put("01 基础/01 文档.md", "# 文档\n\n![图片](../assets/image.png)\n")
        self.put("01 基础/02 同级.md", "[文档](<01 文档.md#章节>)\n")
        self.put("02 目标/.keep", "")
        self.put("03 引用/01 外部.md", '[文档](<../01 基础/01 文档.md?view=1#章节> "标题")\n')
        self.put("assets/image.png", b"\x89PNG\r\n\x1a\nfixture")
        self.manager = tool.FileManager(self.root, self.config)

    def put(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode() if isinstance(content, str) else content)
        return path

    def read(self, name):
        return (self.root / name).read_text()

    def contents(self):
        return {str(path.relative_to(self.root)): path.read_bytes() if path.is_file() else None
                for path in self.root.rglob("*")}

    def operate(self, action, **payload):
        return self.manager.operate(action, {**payload, "revision": self.manager.state()["revision"]})

    def test_rename_updates_references_summary_and_undo_restores_exact_bytes(self):
        before = self.contents()
        result = self.operate("rename", path="01 基础/01 文档.md", name="01 新名称.md")
        self.assertFalse((self.root / "01 基础/01 文档.md").exists())
        self.assertIn('../01 基础/01 新名称.md?view=1#章节> "标题"', self.read("03 引用/01 外部.md"))
        self.assertIn("01 新名称", self.read("SUMMARY.md"))
        self.assertEqual(result["summary"]["updatedReferences"], 2)
        self.operate("undo")
        self.assertEqual(before, self.contents())
        self.assertFalse(self.manager.state()["undo"]["available"])

    def test_file_move_preserves_bom_crlf_self_links_and_rebases_images(self):
        self.put("02 目标/01 深层/.keep", "")
        self.put("01 基础/01 文档.md", b"\xef\xbb\xbf" +
                 "# Test\r\n\r\n![image](../assets/image.png)\r\n[self](<01 文档.md#anchor>)\r\n".encode())
        before = self.contents()
        self.operate("move", paths=["01 基础/01 文档.md"], target="02 目标/01 深层")
        data = (self.root / "02 目标/01 深层/01 文档.md").read_bytes()
        self.assertTrue(data.startswith(b"\xef\xbb\xbf"))
        self.assertNotIn(b"\n", data.replace(b"\r\n", b""))
        self.assertIn(b"../../assets/image.png", data)
        self.assertIn("[self](<01 文档.md#anchor>)".encode(), data)
        self.operate("undo")
        self.assertEqual(before, self.contents())

    def test_directory_move_includes_assets_hidden_files_and_both_link_directions(self):
        self.put("01 基础/assets/local.png", b"local")
        self.put("01 基础/.note", "hidden")
        self.put("01 基础/01 文档.md", "![local](assets/local.png)\n![root](../assets/image.png)\n[peer](../03 引用/01 外部.md)\n")
        self.put("03 引用/02 图片引用.md", '![local](../01 基础/assets/local.png)\n[root](/01 基础/01 文档.md#x)\n')
        before = self.contents()
        result = self.operate("move", paths=["01 基础", "01 基础/01 文档.md"], target="02 目标")
        self.assertEqual(result["summary"]["movedItems"], 1)
        self.assertEqual((self.root / "01 目标/01 基础/assets/local.png").read_bytes(), b"local")
        self.assertTrue((self.root / "01 目标/01 基础/.note").exists())
        self.assertEqual(result["focusPaths"], ["01 目标/01 基础"])
        moved = self.read("01 目标/01 基础/01 文档.md")
        for expected in ["![local](assets/local.png)", "../../assets/image.png", "../../02 引用/01 外部.md"]:
            self.assertIn(expected, moved)
        incoming = self.read("02 引用/02 图片引用.md")
        self.assertIn("../01 目标/01 基础/assets/local.png", incoming)
        self.assertIn("/01 目标/01 基础/01 文档.md#x", incoming)
        self.operate("undo")
        self.assertEqual(before, self.contents())

    def test_batch_move_uses_one_mapping_for_cross_references(self):
        before = self.contents()
        result = self.operate("move", paths=["01 基础/01 文档.md", "01 基础/02 同级.md"], target="02 目标")
        self.assertEqual(result["summary"]["movedItems"], 2)
        self.assertEqual(self.read("02 目标/02 同级.md"), "[文档](<01 文档.md#章节>)\n")
        self.assertIn("../02 目标/01 文档.md", self.read("03 引用/01 外部.md"))
        self.operate("undo")
        self.assertEqual(before, self.contents())

    def test_move_fills_source_gaps_and_target_starts_at_one(self):
        self.put("02 目标/07 已有.md", "existing")
        before = self.contents()
        result = self.operate("move", paths=["01 基础/01 文档.md"], target="02 目标")
        self.assertEqual(result["focusPaths"], ["02 目标/02 文档.md"])
        self.assertEqual(self.read("02 目标/01 已有.md"), "existing")
        self.assertEqual(self.read("01 基础/01 同级.md"), "[文档](<../02 目标/02 文档.md#章节>)\n")
        self.assertFalse((self.root / "01 基础/02 同级.md").exists())
        self.assertEqual(result["summary"]["renumberedItems"], 2)
        self.operate("undo")
        self.assertEqual(before, self.contents())

    def test_move_parent_and_separate_descendant_with_renumbered_destination(self):
        before = self.contents()
        result = self.operate("move", paths=["01 基础", "03 引用/01 外部.md"], target="02 目标")
        self.assertEqual(set(result["focusPaths"]), {"01 目标/01 基础", "01 目标/01 外部.md"})
        self.assertIn("01 基础/01 文档.md?view=1#章节", self.read("01 目标/01 外部.md"))
        self.assertTrue((self.root / "02 引用").is_dir())
        self.operate("undo")
        self.assertEqual(before, self.contents())

    def test_number_reuse_preserves_distinct_contents_and_original_link_targets(self):
        for number, label in [(2, "first"), (3, "second"), (6, "third")]:
            self.put(f"02 目标/{number:02d} 同名.md", label)
        self.put("README.md", "[a](<02 目标/02 同名.md>) [b](<02 目标/03 同名.md>) [c](<02 目标/06 同名.md>)")
        before = self.contents()
        result = self.operate("rename", path="02 目标/06 同名.md", name="同名.md")
        self.assertEqual(result["focusPaths"], ["02 目标/03 同名.md"])
        for number, label in [(1, "first"), (2, "second"), (3, "third")]:
            self.assertEqual(self.read(f"02 目标/{number:02d} 同名.md"), label)
        self.assertEqual(self.read("README.md"), "[a](<02 目标/01 同名.md>) [b](<02 目标/02 同名.md>) [c](<02 目标/03 同名.md>)")
        self.operate("undo")
        self.assertEqual(before, self.contents())

    def test_created_directory_can_reuse_old_number_and_undo_restores_original_directory(self):
        self.put("02 目标/02 归档/README.md", "existing README")
        before = self.contents()
        self.operate("mkdir", parent="02 目标", name="归档")
        self.assertEqual(self.read("02 目标/01 归档/README.md"), "existing README")
        self.assertEqual(self.read("02 目标/02 归档/README.md"), "")
        self.operate("undo")
        self.assertEqual(before, self.contents())

    def test_renumbering_conflict_with_inherited_readme_is_preflighted(self):
        self.put("02 目标/README.md", "target")
        self.put("03 引用/README.md", "incoming")
        before = self.contents()
        with mock.patch.object(self.manager, "_relocate") as relocate:
            with self.assertRaises(tool.OperationConflict):
                self.operate("move", paths=["01 基础", "03 引用/README.md"], target="02 目标")
            relocate.assert_not_called()
        self.assertEqual(before, self.contents())

    def test_edits_to_automatically_renumbered_siblings_block_undo(self):
        self.operate("move", paths=["01 基础/01 文档.md"], target="02 目标")
        self.put("01 基础/01 同级.md", "external")
        before = self.contents()
        with self.assertRaises(tool.OperationConflict):
            self.operate("undo")
        self.assertEqual(before, self.contents())

    def test_staging_and_install_failures_restore_original_numbering(self):
        self.put("02 目标/07 已有.md", "existing")
        before = self.contents()
        relocate = self.manager._relocate
        for fail_at in [2, 5]:
            with self.subTest(fail_at=fail_at):
                count = 0
                def fail_once(*args):
                    nonlocal count
                    count += 1
                    if count == fail_at:
                        raise OSError("injected move failure")
                    return relocate(*args)
                with mock.patch.object(self.manager, "_relocate", side_effect=fail_once):
                    with self.assertRaisesRegex(RuntimeError, "已回滚"):
                        self.operate("move", paths=["01 基础/01 文档.md"], target="02 目标")
                self.assertEqual(before, self.contents())

    def test_directory_creation_adds_empty_readme_summary_and_is_undoable(self):
        before = self.contents()
        result = self.operate("mkdir", parent="02 目标", name="新目录")
        self.assertEqual(result["focusPaths"], ["02 目标/01 新目录"])
        directory = self.root / result["focusPaths"][0]
        self.assertEqual([path.name for path in directory.iterdir()], ["README.md"])
        self.assertEqual((directory / "README.md").read_bytes(), b"")
        self.assertIn("02 目标/01 新目录/README.md", self.read("SUMMARY.md"))
        self.operate("undo")
        self.assertEqual(before, self.contents())

    def test_only_last_success_is_undoable_failed_operation_preserves_record(self):
        self.operate("mkdir", parent="", name="04 新目录")
        self.operate("mkdir", parent="", name="05 新目录")
        with self.assertRaises(ValueError):
            self.operate("mkdir", parent="", name="invalid/name")
        self.operate("undo")
        self.assertTrue((self.root / "04 新目录").is_dir())
        self.assertFalse((self.root / "05 新目录").exists())
        with self.assertRaises(tool.OperationConflict):
            self.operate("undo")

    def test_missing_summary_removed_by_undo(self):
        (self.root / "SUMMARY.md").unlink()
        before = self.contents()
        self.operate("mkdir", parent="", name="04 新目录")
        self.assertTrue((self.root / "SUMMARY.md").exists())
        self.operate("undo")
        self.assertEqual(before, self.contents())

    def test_summary_preserves_bom_and_crlf(self):
        self.put("SUMMARY.md", b"\xef\xbb\xbf# Old\r\n\r\n")
        self.operate("mkdir", parent="", name="04 新目录")
        data = (self.root / "SUMMARY.md").read_bytes()
        self.assertTrue(data.startswith(b"\xef\xbb\xbf"))
        self.assertNotIn(b"\n", data.replace(b"\r\n", b""))

    def test_case_only_rename_and_undo(self):
        self.put("01 基础/03 Case.md", "case")
        before = self.contents()
        self.operate("rename", path="01 基础/03 Case.md", name="case.md")
        self.assertIn("03 case.md", os.listdir(self.root / "01 基础"))
        self.assertNotIn("03 Case.md", os.listdir(self.root / "01 基础"))
        self.operate("undo")
        self.assertEqual(before, self.contents())

    def test_name_conflict_aborts_entire_batch(self):
        self.put("02 目标/README.md", "existing")
        before = self.contents()
        with self.assertRaises(tool.OperationConflict):
            self.operate("move", paths=["01 基础/01 文档.md", "01 基础/README.md"], target="02 目标")
        self.assertEqual(before, self.contents())

    def test_duplicate_titles_get_distinct_numbers_without_overwriting(self):
        self.put("03 引用/01 文档.md", "duplicate")
        before = self.contents()
        result = self.operate("move", paths=["03 引用/01 文档.md", "01 基础/01 文档.md"], target="02 目标")
        self.assertEqual(result["focusPaths"], ["02 目标/01 文档.md", "02 目标/02 文档.md"])
        self.assertEqual(self.read("02 目标/02 文档.md"), "duplicate")
        self.assertEqual(self.read("02 目标/01 文档.md"), before["01 基础/01 文档.md"].decode())
        self.operate("undo")
        self.assertEqual(before, self.contents())

    def test_create_normalizes_files_and_directories_independently(self):
        self.put("99 高序号文档.md", "file")
        before = self.contents()
        result = self.operate("mkdir", parent="", name="01-新目录")
        self.assertEqual(result["focusPaths"], ["04 新目录"])
        self.assertEqual(self.read("04 新目录/README.md"), "")
        self.assertEqual(self.read("01 高序号文档.md"), "file")
        self.operate("undo")
        self.assertEqual(before, self.contents())

    def test_rename_numbers_from_one_and_repairs_missing_duplicate_and_gapped_numbers(self):
        cases = [
            ("01 基础/01 文档.md", "88 新标题.md", "01 基础/01 新标题.md", None),
            ("01 基础/随记.MD", "新标题.MD", "01 基础/03 新标题.MD", "notes"),
            ("01 基础/01 重复.md", "新标题.md", "01 基础/02 新标题.md", "duplicate"),
            ("01 基础/7-旧格式.md", "新标题.md", "01 基础/03 新标题.md", "legacy"),
            ("01 基础/随记.md", "2024 年度总结.md", "01 基础/03 2024 年度总结.md", "year"),
            ("未编号目录", "新标题", "04 新标题", b""),
            ("03 引用", "88 新标题", "03 新标题", None),
        ]
        for source, name, expected, content in cases:
            with self.subTest(source=source):
                if content is not None:
                    self.put(source + "/README.md" if "." not in Path(source).name else source, content)
                before = self.contents()
                result = self.operate("rename", path=source, name=name)
                self.assertEqual(result["focusPaths"], [expected])
                self.assertTrue((self.root / expected).exists())
                if source == "01 基础/01 文档.md":
                    self.assertIn("01 新标题.md#章节", self.read("01 基础/02 同级.md"))
                self.operate("undo")
                self.assertEqual(before, self.contents())
                if content is not None:
                    if "." not in Path(source).name:
                        (self.root / source / "README.md").unlink()
                        (self.root / source).rmdir()
                    else:
                        (self.root / source).unlink()

    def test_batch_numbers_files_and_directories_separately_and_updates_final_paths(self):
        self.put("02 目标/07 已有.md", "existing file")
        self.put("02 目标/04 已有目录/README.md", "existing directory")
        before = self.contents()
        result = self.operate("move", paths=["01 基础/02 同级.md", "03 引用", "01 基础/01 文档.md"], target="02 目标")
        self.assertEqual(set(result["focusPaths"]), {
            "02 目标/02 文档.md", "02 目标/03 同级.md", "02 目标/02 引用",
        })
        self.assertEqual(self.read("02 目标/01 已有.md"), "existing file")
        self.assertEqual(self.read("02 目标/03 同级.md"), "[文档](<02 文档.md#章节>)\n")
        self.assertIn("../02 文档.md?view=1#章节", self.read("02 目标/02 引用/01 外部.md"))
        self.assertIn("02 目标/02 文档.md", self.read("SUMMARY.md"))
        self.operate("undo")
        self.assertEqual(before, self.contents())

    def test_readme_is_not_numbered_and_move_to_current_parent_is_rejected(self):
        before = self.contents()
        result = self.operate("move", paths=["01 基础/README.md"], target="02 目标")
        self.assertEqual(result["focusPaths"], ["02 目标/README.md"])
        self.operate("undo")
        self.assertEqual(before, self.contents())
        with self.assertRaises(tool.OperationConflict):
            self.operate("move", paths=["01 基础/01 文档.md"], target="01 基础")
        self.assertEqual(before, self.contents())
        result = self.operate("rename", path="01 基础/README.md", name="目录说明.md")
        self.assertEqual(result["focusPaths"], ["01 基础/03 目录说明.md"])
        self.operate("undo")
        self.assertEqual(before, self.contents())

    def test_number_overflow_aborts_whole_batch_and_empty_title_is_rejected(self):
        for number in range(1, 99):
            self.put(f"02 目标/{number:02d} 已有.md", "existing")
        for number in range(4, 100):
            self.put(f"{number:02d} 已有目录/README.md", "")
        before = self.contents()
        with self.assertRaisesRegex(ValueError, "99"):
            self.operate("move", paths=["01 基础/01 文档.md", "01 基础/02 同级.md"], target="02 目标")
        with self.assertRaisesRegex(ValueError, "99"):
            self.operate("mkdir", parent="", name="新目录")
        with self.assertRaisesRegex(ValueError, "名称"):
            self.operate("rename", path="01 基础/01 文档.md", name="01 .md")
        self.assertEqual(before, self.contents())

    def test_invalid_paths_names_and_protected_files_are_rejected(self):
        before = self.contents()
        cases = [
            ("move", {"paths": ["01 基础"], "target": "01 基础"}),
            ("rename", {"path": "../outside.md", "name": "01 foo.md"}),
            ("rename", {"path": "/tmp/outside.md", "name": "01 foo.md"}),
            ("rename", {"path": "README.md", "name": "01 intro.md"}),
            ("rename", {"path": "01 基础/01 文档.md", "name": "file.txt"}),
            ("mkdir", {"parent": "", "name": "nested/name"}),
            ("mkdir", {"parent": "", "name": ".git"}),
            ("mkdir", {"parent": "", "name": "eb_tool"}),
            ("mkdir", {"parent": "", "name": "bad\nname"}),
            ("mkdir", {"parent": "assets", "name": "01 hidden"}),
            ("move", {"paths": [], "target": "02 目标"}),
        ]
        for action, payload in cases:
            with self.subTest(action=action, payload=payload):
                with self.assertRaises(ValueError):
                    self.operate(action, **payload)
                self.assertEqual(before, self.contents())

    def test_directory_cannot_move_into_descendant(self):
        self.put("01 基础/03 深层/.keep", "")
        with self.assertRaisesRegex(ValueError, "子目录"):
            self.operate("move", paths=["01 基础"], target="01 基础/03 深层")

    def test_symlinks_including_hidden_descendants_are_rejected(self):
        (self.root / "01 基础/.link").symlink_to(self.root / "02 目标", target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "符号链接"):
            self.operate("move", paths=["01 基础"], target="02 目标")
        (self.root / "link.md").symlink_to(self.root / "01 基础/01 文档.md")
        with self.assertRaisesRegex(ValueError, "符号链接"):
            self.operate("rename", path="link.md", name="other.md")

    def test_state_excludes_tools_resources_and_protected_files(self):
        self.put("eb_tool/01 使用说明.md", "# Test\n")
        self.put("docs/01 built.md", "generated")
        self.put("AGENTS.md", "# Rules\n")
        paths = {entry["path"] for entry in self.manager.state()["entries"]}
        self.assertIn("01 基础/README.md", paths)
        self.assertIn("02 目标", paths)
        for value in ["README.md", "SUMMARY.md", "AGENTS.md", "assets", "eb_tool", "docs"]:
            self.assertNotIn(value, paths)

    def test_stale_revision_prevents_operation(self):
        state = self.manager.state()
        self.put("01 基础/01 文档.md", "external")
        before = self.contents()
        with self.assertRaises(tool.OperationConflict):
            self.manager.operate("rename", {"path": "01 基础/01 文档.md", "name": "01 new.md", "revision": state["revision"]})
        self.assertEqual(before, self.contents())

    def test_external_edit_blocks_undo_and_is_preserved(self):
        self.operate("rename", path="01 基础/01 文档.md", name="01 new.md")
        self.put("01 基础/01 new.md", "external changes")
        before = self.contents()
        with self.assertRaises(tool.OperationConflict):
            self.operate("undo")
        self.assertEqual(before, self.contents())

    def test_hidden_file_in_new_directory_blocks_undo(self):
        self.operate("mkdir", parent="", name="04 新目录")
        self.put("04 新目录/.external", "keep")
        with self.assertRaises(tool.OperationConflict):
            self.operate("undo")
        self.assertEqual(self.read("04 新目录/.external"), "keep")

    def test_edited_generated_readme_blocks_undo(self):
        self.operate("mkdir", parent="", name="新目录")
        self.put("04 新目录/README.md", "user notes")
        before = self.contents()
        with self.assertRaises(tool.OperationConflict):
            self.operate("undo")
        self.assertEqual(before, self.contents())

    def test_creation_write_and_summary_failures_roll_back_readme_directory_and_summary(self):
        before = self.contents()
        write = self.manager._write_atomic
        for failure in ["README.md", "SUMMARY.md", "generation"]:
            with self.subTest(failure=failure):
                failed = False
                def fail_after_write(path, *args):
                    nonlocal failed
                    write(path, *args)
                    if path.name == failure and not failed:
                        failed = True
                        raise OSError("injected creation failure")
                summary = tool.build_summary_content
                def build(*args):
                    if failure == "generation":
                        raise OSError("injected generation failure")
                    return summary(*args)
                with mock.patch.object(self.manager, "_write_atomic", side_effect=fail_after_write), \
                     mock.patch.object(tool, "build_summary_content", side_effect=build):
                    with self.assertRaisesRegex(RuntimeError, "已回滚"):
                        self.operate("mkdir", parent="", name="新目录")
                self.assertEqual(before, self.contents())
                self.assertFalse(self.manager.state()["undo"]["available"])

    def test_failed_creation_undo_restores_readme_and_allows_retry(self):
        original = self.contents()
        self.operate("mkdir", parent="", name="新目录")
        after = self.contents()
        with mock.patch.object(Path, "rmdir", side_effect=OSError("directory removal failure")):
            with self.assertRaisesRegex(RuntimeError, "已回滚"):
                self.operate("undo")
        self.assertEqual(after, self.contents())
        self.operate("undo")
        self.assertEqual(original, self.contents())

    def test_unrelated_edit_allows_undo_after_refresh(self):
        self.operate("mkdir", parent="", name="04 新目录")
        self.put("01 基础/01 文档.md", "unrelated edit")
        self.operate("undo")
        self.assertEqual(self.read("01 基础/01 文档.md"), "unrelated edit")

    def test_generation_failure_rolls_back_directory_move(self):
        self.put("02 目标/04 已有目录/README.md", "existing")
        before = self.contents()
        with mock.patch.object(tool, "build_summary_content", side_effect=OSError("generation failure")):
            with self.assertRaisesRegex(RuntimeError, "已回滚"):
                self.operate("move", paths=["01 基础"], target="02 目标")
        self.assertEqual(before, self.contents())

    def test_second_write_failure_rolls_back_files_and_references(self):
        self.put("02 目标/07 已有.md", "existing")
        before = self.contents()
        original_write = self.manager._write_atomic
        count = 0
        def fail_second(*args):
            nonlocal count
            count += 1
            if count == 2:
                raise OSError("injected failure")
            return original_write(*args)
        with mock.patch.object(self.manager, "_write_atomic", side_effect=fail_second):
            with self.assertRaisesRegex(RuntimeError, "已回滚"):
                self.operate("move", paths=["01 基础/01 文档.md"], target="02 目标")
        self.assertEqual(before, self.contents())

    def test_summary_write_failure_rolls_back_all_changes(self):
        before = self.contents()
        original_write = self.manager._write_atomic
        failed = False
        def fail_summary(path, *args):
            nonlocal failed
            if path.name == "SUMMARY.md" and not failed:
                failed = True
                raise OSError("summary failure")
            return original_write(path, *args)
        with mock.patch.object(self.manager, "_write_atomic", side_effect=fail_summary):
            with self.assertRaisesRegex(RuntimeError, "已回滚"):
                self.operate("move", paths=["01 基础"], target="02 目标")
        self.assertEqual(before, self.contents())

    def test_undo_failure_rolls_back_to_post_operation_state(self):
        original = self.contents()
        self.operate("move", paths=["01 基础"], target="02 目标")
        before = self.contents()
        original_write = self.manager._write_atomic
        failed = False
        def fail_once(*args):
            nonlocal failed
            if not failed:
                failed = True
                raise OSError("undo failure")
            return original_write(*args)
        with mock.patch.object(self.manager, "_write_atomic", side_effect=fail_once):
            with self.assertRaisesRegex(RuntimeError, "已回滚"):
                self.operate("undo")
        self.assertEqual(before, self.contents())
        self.assertTrue(self.manager.state()["undo"]["available"])
        self.operate("undo")
        self.assertEqual(original, self.contents())

    def test_rollback_failure_reports_unrestored_paths(self):
        before = self.contents()
        relocate = self.manager._relocate
        count = 0
        def fail_rollback(*args):
            nonlocal count
            count += 1
            if count > 1:
                raise OSError("cannot restore")
            return relocate(*args)
        with mock.patch.object(self.manager, "_relocate", side_effect=fail_rollback), \
             mock.patch.object(tool, "build_summary_content", side_effect=OSError("build failed")):
            with self.assertRaisesRegex(RuntimeError, "未能恢复") as raised:
                self.operate("move", paths=["01 基础"], target="02 目标")
        staging = list(self.root.glob(".eb-stage-*"))
        self.assertEqual(len(staging), 1)
        self.assertIn(str(staging[0]), str(raised.exception))
        self.assertEqual(sorted(value for value in before.values() if value is not None),
                         sorted(value for value in self.contents().values() if value is not None))

    def test_link_syntax_special_characters_and_code_examples(self):
        code = "[code](../01 基础/01 文档.md)"
        ticks = chr(96)
        text = (
            '[inline](<../01 基础/01 文档.md?x=1#标题> "说明")\n'
            "[encoded](../01%20%E5%9F%BA%E7%A1%80/01%20%E6%96%87%E6%A1%A3.md)\n"
            "[reference][id]\n[id]: <../01 基础/01 文档.md#锚点> 'title'\n"
            "[[../01 基础/01 文档.md|别名]]\n"
            '<a href="../01 基础/01 文档.md">link</a>\n'
            '<img src="../01 基础/01 文档.md">\n'
            '<div style="background:url(../01 基础/01 文档.md)"></div>\n'
            "[external](https://example.com/01 文档.md)\n[anchor](#标题)\n\n"
            + ticks * 3 + "md\n" + code + "\n" + ticks * 3 + "\n"
            + ticks + code + ticks + "\n\n    " + code + "\n"
        )
        self.put("03 引用/01 外部.md", text)
        self.operate("rename", path="01 基础/01 文档.md", name="01 新 (示例)#名称.md")
        updated = self.read("03 引用/01 外部.md")
        self.assertIn("01 新 %28示例%29%23名称.md?x=1#标题", updated)
        self.assertIn("%E6%96%B0%20%28%E7%A4%BA%E4%BE%8B%29%23", updated)
        self.assertIn("01 新 %28示例%29%23名称.md)", self.read("SUMMARY.md"))
        for expected in [ticks + code + ticks, "    " + code, "[anchor](#标题)",
                         "[external](https://example.com/01 文档.md)",
                         "[[../01 基础/01 新 %28示例%29%23名称.md|别名]]"]:
            self.assertIn(expected, updated)

    def test_cli_config_and_defaults_independent_of_working_directory(self):
        with tempfile.TemporaryDirectory(prefix="eb-cwd-") as other:
            script = tool.TOOL_DIRECTORY / "eb_tool.py"
            for arguments in [["--gen"], ["--move_md", "01 基础/01 文档.md", "02 目标"]]:
                result = subprocess.run([sys.executable, "-B", str(script), "--root", str(self.root), *arguments],
                                        cwd=other, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("../02 目标/01 文档.md", self.read("03 引用/01 外部.md"))
        self.assertEqual(tool.build_argument_parser().parse_args(["--gen"]).root, tool.TOOL_DIRECTORY.parent)

    def test_cli_move_and_rename_apply_same_automatic_numbering(self):
        self.put("02 目标/07 已有.md", "existing")
        script = tool.TOOL_DIRECTORY / "eb_tool.py"
        for source, destination in [
            ("01 基础/01 文档.md", "02 目标"),
            ("02 目标/02 文档.md", "02 目标/42 新标题.md"),
        ]:
            result = subprocess.run([
                sys.executable, "-B", str(script), "--root", str(self.root),
                "--move_md", source, destination,
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root / "02 目标/02 新标题.md").exists())
        self.assertEqual(self.read("02 目标/01 已有.md"), "existing")
        self.assertIn("../02 目标/02 新标题.md", self.read("03 引用/01 外部.md"))

    def test_clean_images_dry_run_and_format_images_cli(self):
        self.put("01 基础/local.png", b"fixture image")
        self.put("01 基础/01 文档.md", "![local](local.png)\n")
        before = self.contents()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(tool.main(["--root", str(self.root), "--clean_img", "--dry-run", "--no-progress"]), 0)
            self.assertEqual(before, self.contents())
            self.assertEqual(tool.main(["--root", str(self.root), "--format_img"]), 0)
        self.assertIn("../assets/eb_", self.read("01 基础/01 文档.md"))
        self.assertFalse((self.root / "01 基础/local.png").exists())


class HTTPTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="eb-http-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "01 文档.md").write_text("# Test\n")
        self.server = tool.create_ui_server(self.root, tool.load_config(), 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop)
        self.origin = f"http://127.0.0.1:{self.server.server_port}"
        status, content = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.token = re.search(r'name="eb-token" content="([^"]+)"', content.decode()).group(1)

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def request(self, method, path, payload=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            connection.request(method, path, body=None if payload is None else json.dumps(payload), headers=headers or {})
            response = connection.getresponse()
            return response.status, response.read()
        finally:
            connection.close()

    def auth(self):
        return {"X-EB-Token": self.token, "Origin": self.origin, "Content-Type": "application/json"}

    def test_api_operations_and_static_allowlist(self):
        status, content = self.request("GET", "/api/state", headers=self.auth())
        self.assertEqual(status, 200)
        state = json.loads(content)
        for action, payload in [
            ("mkdir", {"parent": "", "name": "01 目录"}),
            ("rename", {"path": "01 文档.md", "name": "01 新文档.md"}),
            ("move", {"paths": ["01 新文档.md"], "target": "01 目录"}),
            ("undo", {}),
        ]:
            status, body = self.request("POST", "/api/" + action, {**payload, "revision": state["revision"]}, self.auth())
            self.assertEqual(status, 200, body)
            state = json.loads(body)
        self.assertTrue((self.root / "01 新文档.md").is_file())
        self.assertEqual((self.root / "01 目录/README.md").read_bytes(), b"")
        for path in ["/eb_config.json", "/eb_tool.py", "/../eb_tool.py", "/01%20test.md"]:
            self.assertEqual(self.request("GET", path)[0], 404)
        for path in ["/app.js", "/styles.css"]:
            self.assertEqual(self.request("GET", path)[0], 200)

    def test_token_origin_and_host_guards(self):
        self.assertEqual(self.request("GET", "/api/state")[0], 403)
        self.assertEqual(self.request("GET", "/", headers={"Host": "evil.example"})[0], 403)
        for override in [{"Origin": "https://evil.example"}, {"X-EB-Token": "invalid"},
                         {"Sec-Fetch-Site": "cross-site"}, {"Origin": "null"}]:
            self.assertEqual(self.request("POST", "/api/mkdir", {}, {**self.auth(), **override})[0], 403)
        no_origin = self.auth()
        no_origin.pop("Origin")
        self.assertEqual(self.request("POST", "/api/mkdir", {}, no_origin)[0], 403)
        self.assertFalse((self.root / "SUMMARY.md").exists())

    def test_invalid_json_shape_and_stale_revision(self):
        self.assertEqual(self.request("POST", "/api/mkdir", [], self.auth())[0], 400)
        self.assertEqual(self.request("POST", "/api/mkdir", {"revision": "stale"}, self.auth())[0], 409)


if __name__ == "__main__":
    unittest.main()
