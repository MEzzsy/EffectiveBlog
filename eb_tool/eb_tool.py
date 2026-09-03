#!/usr/bin/env python3
"""EffectiveBlog 的目录与图片维护工具。"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import fnmatch
import hashlib
import html
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import stat
import sys
import tempfile
import threading
from typing import Callable, Iterable, Sequence
from urllib.parse import quote, unquote, urlsplit
import webbrowser


IMAGE_EXTENSIONS = {
    ".avif",
    ".bmp",
    ".gif",
    ".heic",
    ".heif",
    ".ico",
    ".jpeg",
    ".jpg",
    ".png",
    ".svg",
    ".tif",
    ".tiff",
    ".webp",
}

CONFIG_FILE_NAME = "eb_config.json"
TOOL_DIRECTORY = Path(__file__).resolve().parent
DEFAULT_ROOT = TOOL_DIRECTORY.parent
SUMMARY_FILE_NAME = "SUMMARY.md"
FORMATTED_IMAGE_RE = re.compile(
    r"^eb_(\d{5})(\.(?:avif|bmp|gif|heic|heif|ico|jpe?g|png|svg|tiff?|webp))$",
    re.IGNORECASE,
)

FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
REFERENCE_DEFINITION_RE = re.compile(
    r"^ {0,3}\[([^\]\n]+)\]:[ \t]*(.+)$", re.MULTILINE
)
LINK_RE = re.compile(r"(!?)\[([^\]\n]*)\]")
WIKI_IMAGE_RE = re.compile(r"!\[\[([^\]|\n]+)(?:\|[^\]\n]*)?\]\]")
CSS_URL_RE = re.compile(
    r"url\(\s*(?:\"([^\"]+)\"|'([^']+)'|([^)'\"\s][^)]*?))\s*\)",
    re.IGNORECASE,
)
TITLE_RE = re.compile(
    r"\s+(?:\"(?:\\.|[^\"])*\"|'(?:\\.|[^'])*'|\((?:\\.|[^()])*\))\s*$"
)
MARKDOWN_ESCAPE_RE = re.compile(r"\\([\\`*_{}\[\]()<>#+\-.! ])")


def _match_path_parts(pattern: Sequence[str], path: Sequence[str]) -> bool:
    """匹配以路径段为单位的 glob，让 ** 可以跨越目录。"""
    if not pattern:
        return not path
    if pattern[0] == "**":
        return _match_path_parts(pattern[1:], path) or (
            bool(path) and _match_path_parts(pattern, path[1:])
        )
    return bool(path) and fnmatch.fnmatchcase(path[0], pattern[0]) and _match_path_parts(
        pattern[1:], path[1:]
    )


class IgnoreRule:
    """一条简化的 gitignore 风格规则。"""

    def __init__(self, pattern: str) -> None:
        pattern = pattern.replace("\\", "/")
        self.directory_only = pattern.endswith("/")
        pattern = pattern.rstrip("/")
        self.anchored = pattern.startswith("/")
        self.pattern = pattern.lstrip("/")
        self.parts = tuple(part for part in self.pattern.split("/") if part)
        self.has_slash = "/" in self.pattern

    def matches(self, relative_path: str, is_directory: bool) -> bool:
        path_parts = tuple(part for part in relative_path.split("/") if part)
        if not path_parts or not self.parts:
            return False

        # 检查各级前缀，可以让已忽略目录下的所有内容都自动被忽略。
        last_directory_index = len(path_parts) if is_directory else len(path_parts) - 1
        prefixes = [path_parts[:index] for index in range(1, last_directory_index + 1)]

        if self.directory_only:
            candidates = prefixes
        else:
            candidates = prefixes + [path_parts]

        if not self.has_slash and not self.anchored:
            for candidate in candidates:
                if candidate and fnmatch.fnmatchcase(candidate[-1], self.pattern):
                    return True
            return False

        return any(_match_path_parts(self.parts, candidate) for candidate in candidates)


class IgnoreMatcher:
    def __init__(self, rules: Iterable[IgnoreRule]) -> None:
        self.rules = tuple(rules)

    def matches(self, relative_path: str, is_directory: bool) -> bool:
        relative_path = relative_path.replace(os.sep, "/")
        if relative_path.startswith("./"):
            relative_path = relative_path[2:]
        relative_path = relative_path.lstrip("/")
        return any(rule.matches(relative_path, is_directory) for rule in self.rules)


class ProgressDisplay:
    """在终端中刷新进度条，输出重定向时仅打印少量里程碑。"""

    BAR_WIDTH = 30

    def __init__(self, label: str, total: int, enabled: bool = True) -> None:
        self.label = label
        self.total = total
        self.enabled = enabled
        self.is_terminal = sys.stderr.isatty()
        self.last_milestone = -1
        self.line_finished = False
        self.update(0)

    def update(self, completed: int) -> None:
        if not self.enabled:
            return

        completed = min(max(completed, 0), self.total)
        percent = 100 if self.total == 0 else int(completed * 100 / self.total)

        if self.is_terminal:
            filled = self.BAR_WIDTH if self.total == 0 else int(
                completed * self.BAR_WIDTH / self.total
            )
            bar = "█" * filled + "░" * (self.BAR_WIDTH - filled)
            ending = "\n" if completed >= self.total else ""
            print(
                f"\r{self.label} [{bar}] {completed}/{self.total} ({percent:3d}%)",
                end=ending,
                file=sys.stderr,
                flush=True,
            )
            self.line_finished = bool(ending)
            return

        milestone = percent // 25
        if milestone != self.last_milestone:
            print(
                f"{self.label}：{completed}/{self.total}（{percent}%）",
                file=sys.stderr,
            )
            self.last_milestone = milestone

    def close(self) -> None:
        if self.enabled and self.is_terminal and not self.line_finished:
            print(file=sys.stderr)
            self.line_finished = True


class ImageHTMLParser(HTMLParser):
    """从 Markdown 内嵌 HTML 中收集可能指向图片的属性。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.targets: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        attributes = {name.casefold(): value for name, value in attrs if value}
        tag = tag.casefold()

        if tag in {"img", "source"}:
            if "src" in attributes:
                self.targets.append(attributes["src"])
            if "srcset" in attributes:
                self.targets.extend(parse_srcset(attributes["srcset"]))
        elif tag == "video" and "poster" in attributes:
            self.targets.append(attributes["poster"])
        elif tag == "a" and "href" in attributes:
            self.targets.append(attributes["href"])
        elif tag == "image":
            for attribute in ("href", "xlink:href"):
                if attribute in attributes:
                    self.targets.append(attributes[attribute])


def parse_srcset(value: str) -> list[str]:
    """解析常见的 HTML srcset（data URL 会在后续被过滤）。"""
    targets: list[str] = []
    for item in value.split(","):
        item = item.strip()
        if item:
            targets.append(item.split()[0])
    return targets


def load_config() -> dict[str, list[str]]:
    """配置始终与脚本同目录，与工作目录和 --root 无关。"""
    config_file = TOOL_DIRECTORY / CONFIG_FILE_NAME
    try:
        raw_config = json.loads(config_file.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as error:
        raise ValueError(f"配置文件不存在：{config_file}") from error
    except OSError as error:
        raise ValueError(f"无法读取配置文件 {config_file}：{error}") from error
    except json.JSONDecodeError as error:
        raise ValueError(
            f"配置文件 JSON 格式错误（第 {error.lineno} 行，第 {error.colno} 列）："
            f"{error.msg}"
        ) from error

    if not isinstance(raw_config, dict):
        raise ValueError("配置文件根节点必须是 JSON 对象")

    config: dict[str, list[str]] = {}
    for key in ("img_ignore", "gen_ignore"):
        value = raw_config.get(key)
        if not isinstance(value, list) or any(
            not isinstance(item, str) for item in value
        ):
            raise ValueError(f"配置字段 {key!r} 必须是字符串数组")
        config[key] = value
    return config


def load_ignore_matcher(configured_patterns: Iterable[str]) -> IgnoreMatcher:
    """将 img_ignore 转为与旧 imgIgnoredFile 相同的匹配器。"""
    # 版本控制元数据和 Python 缓存永远不应当成为扫描或修改目标。
    patterns = [".git/", ".hg/", ".svn/", "__pycache__/"]
    for raw_pattern in configured_patterns:
        pattern = raw_pattern.strip()
        if not pattern or pattern.startswith("#"):
            continue
        if pattern.startswith("!"):
            raise ValueError(
                f"img_ignore 暂不支持取反规则：{pattern!r}；请删除该配置项"
            )
        patterns.append(pattern)

    return IgnoreMatcher(IgnoreRule(pattern) for pattern in patterns)


def iter_repository_files(root: Path, ignores: IgnoreMatcher) -> Iterable[Path]:
    def raise_walk_error(error: OSError) -> None:
        raise error

    for current_dir, dir_names, file_names in os.walk(
        root, topdown=True, onerror=raise_walk_error, followlinks=False
    ):
        current = Path(current_dir)
        relative_dir = current.relative_to(root)

        kept_directories: list[str] = []
        for name in dir_names:
            relative = (relative_dir / name).as_posix()
            if not ignores.matches(relative, is_directory=True):
                kept_directories.append(name)
        dir_names[:] = kept_directories

        for name in file_names:
            path = current / name
            relative = path.relative_to(root).as_posix()
            if not ignores.matches(relative, is_directory=False):
                yield path


def strip_fenced_code(markdown: str) -> str:
    """移除 fenced code block，避免把示例代码误判为真实引用。"""
    result: list[str] = []
    fence_character: str | None = None
    fence_length = 0

    for line in markdown.splitlines(keepends=True):
        match = FENCE_RE.match(line)
        if fence_character is None and match:
            marker = match.group(1)
            fence_character = marker[0]
            fence_length = len(marker)
            result.append("\n" if line.endswith("\n") else "")
            continue

        if fence_character is not None:
            closing_re = rf"^ {{0,3}}{re.escape(fence_character)}{{{fence_length},}}\s*$"
            if re.match(closing_re, line.rstrip("\r\n")):
                fence_character = None
                fence_length = 0
            result.append("\n" if line.endswith("\n") else "")
            continue

        result.append(line)

    return "".join(result)


def normalize_reference_label(label: str) -> str:
    return " ".join(label.split()).casefold()


def parse_destination(raw_destination: str) -> str:
    destination = raw_destination.strip()
    if destination.startswith("<"):
        closing = destination.find(">", 1)
        if closing != -1:
            return destination[1:closing].strip()
    return TITLE_RE.sub("", destination).strip()


def find_parenthesized(markdown: str, opening_index: int) -> tuple[str, int] | None:
    """读取 Markdown 链接的 (...)，并支持路径中的嵌套括号。"""
    depth = 0
    quote: str | None = None
    index = opening_index

    while index < len(markdown):
        character = markdown[index]
        if character == "\\":
            index += 2
            continue
        if quote is not None:
            if character == quote:
                quote = None
            index += 1
            continue
        if character in {'"', "'"}:
            quote = character
        elif character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth == 0:
                return markdown[opening_index + 1 : index], index + 1
        index += 1
    return None


def extract_markdown_targets(markdown: str) -> set[str]:
    markdown = strip_fenced_code(markdown)
    targets: set[str] = set()
    definitions: dict[str, str] = {}

    for match in REFERENCE_DEFINITION_RE.finditer(markdown):
        label = normalize_reference_label(match.group(1))
        destination = parse_destination(match.group(2))
        if destination:
            definitions[label] = destination

    for match in LINK_RE.finditer(markdown):
        is_image = bool(match.group(1))
        label_text = match.group(2)
        index = match.end()

        if index < len(markdown) and markdown[index] == "(":
            parsed = find_parenthesized(markdown, index)
            if parsed:
                destination, _ = parsed
                destination = parse_destination(destination)
                if destination:
                    targets.add(destination)
            continue

        if index < len(markdown) and markdown[index] == "[":
            reference_end = markdown.find("]", index + 1)
            if reference_end != -1:
                reference_label = markdown[index + 1 : reference_end] or label_text
                destination = definitions.get(normalize_reference_label(reference_label))
                if destination:
                    targets.add(destination)
            continue

        if is_image:
            destination = definitions.get(normalize_reference_label(label_text))
            if destination:
                targets.add(destination)

    # 保留定义中出现的图片更安全，即使该定义暂时未在正文中展开。
    targets.update(definitions.values())

    for match in WIKI_IMAGE_RE.finditer(markdown):
        target = match.group(1).split("#", 1)[0].strip()
        if target:
            targets.add(target)

    for match in CSS_URL_RE.finditer(markdown):
        target = next((group for group in match.groups() if group is not None), "").strip()
        if target:
            targets.add(target)

    parser = ImageHTMLParser()
    try:
        parser.feed(markdown)
        parser.close()
    except Exception:
        # HTMLParser 通常会容忍不完整 HTML；即使极端输入失败，也不影响 Markdown 引用。
        pass
    targets.update(parser.targets)

    return targets


def clean_local_target(raw_target: str) -> str | None:
    target = html.unescape(raw_target.strip())
    if not target or target.startswith("#") or target.startswith("//"):
        return None

    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc:
        return None

    target = target.split("#", 1)[0].split("?", 1)[0].strip()
    target = unquote(target)
    target = MARKDOWN_ESCAPE_RE.sub(r"\1", target)
    target = target.replace("\\", "/")
    return target or None


def is_image_target(target: str) -> bool:
    return Path(target).suffix.casefold() in IMAGE_EXTENSIONS


def resolve_target(root: Path, markdown_file: Path, target: str) -> Path:
    if target.startswith("/"):
        path = root / target.lstrip("/")
    else:
        path = markdown_file.parent / target
    return Path(os.path.abspath(os.path.normpath(path)))


def relative_if_inside(path: Path, root: Path) -> str | None:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return None


def scan_repository(
    root: Path, ignores: IgnoreMatcher, show_progress: bool = False
) -> tuple[list[Path], set[Path], set[Path], set[Path]]:
    if show_progress:
        print("正在索引文件……", file=sys.stderr)
    repository_files = list(iter_repository_files(root, ignores))
    markdown_files = sorted(
        path for path in repository_files if path.suffix.casefold() == ".md"
    )
    image_files = {
        path for path in repository_files if path.suffix.casefold() in IMAGE_EXTENSIONS
    }
    local_references: set[Path] = set()
    progress = ProgressDisplay("扫描 Markdown", len(markdown_files), show_progress)

    try:
        for completed, markdown_file in enumerate(markdown_files, start=1):
            try:
                markdown = markdown_file.read_text(encoding="utf-8-sig", errors="replace")
            except OSError as error:
                raise RuntimeError(
                    f"无法读取 Markdown 文件 {markdown_file}: {error}"
                ) from error

            for raw_target in extract_markdown_targets(markdown):
                target = clean_local_target(raw_target)
                if target is None or not is_image_target(target):
                    continue
                resolved = resolve_target(root, markdown_file, target)
                relative = relative_if_inside(resolved, root)
                if relative is None:
                    continue
                if ignores.matches(relative, is_directory=False):
                    continue
                local_references.add(resolved)
            progress.update(completed)
    finally:
        progress.close()

    referenced_images = image_files & local_references
    unused_images = image_files - local_references
    missing_references = local_references - image_files
    return markdown_files, referenced_images, unused_images, missing_references


def display_paths(title: str, paths: Iterable[Path], root: Path) -> None:
    paths = sorted(paths, key=lambda path: path.relative_to(root).as_posix())
    print(f"\n{title}（{len(paths)}）：")
    if not paths:
        print("  无")
        return
    for path in paths:
        print(f"  {path.relative_to(root).as_posix()}")


def collect_file_sizes(paths: Iterable[Path]) -> dict[Path, int]:
    sizes: dict[Path, int] = {}
    for path in paths:
        try:
            # 使用 lstat，删除符号链接时只统计链接本身，不统计链接目标。
            sizes[path] = path.lstat().st_size
        except OSError as error:
            raise RuntimeError(f"无法获取图片大小 {path}: {error}") from error
    return sizes


def format_file_size(size: int) -> str:
    value = float(size)
    units = ("B", "KB", "MB", "GB", "TB")
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{size} B"


def confirm_deletion() -> bool:
    if not sys.stdin.isatty():
        print(
            "未检测到交互终端，本次不会删除；如需非交互删除，请添加 --delete。"
        )
        return False

    try:
        answer = input("确认立即删除以上未引用图片吗？[y/N]：").strip().casefold()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    return answer in {"y", "yes"}


def escape_markdown_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def summary_link(label: str, path: Path, root: Path) -> str:
    relative_path = path.relative_to(root).as_posix()
    return f"[{escape_markdown_label(label)}](./{encode_local_path(relative_path)})"


def collect_summary_entries(
    root: Path,
    directory: Path,
    ignored_names: set[str],
    depth: int,
) -> list[str]:
    """按名称排序生成一个目录中的 SUMMARY 条目。"""
    try:
        entries = sorted(os.scandir(directory), key=lambda entry: entry.name)
    except OSError as error:
        raise RuntimeError(f"无法遍历目录 {directory}：{error}") from error

    lines: list[str] = []
    for entry in entries:
        if entry.name in ignored_names or entry.name in {
            ".git",
            ".hg",
            ".svn",
            "__pycache__",
            SUMMARY_FILE_NAME,
        }:
            continue

        path = Path(entry.path)
        try:
            is_directory = entry.is_dir(follow_symlinks=False)
            is_file = entry.is_file(follow_symlinks=False)
        except OSError as error:
            raise RuntimeError(f"无法检查路径 {path}：{error}") from error

        if is_directory:
            readme = path / "README.md"
            has_readme = readme.is_file() and not readme.is_symlink()
            if has_readme:
                lines.append(
                    f"{'  ' * depth}- {summary_link(entry.name, readme, root)}"
                )
            child_depth = depth + 1 if has_readme else depth
            lines.extend(
                collect_summary_entries(root, path, ignored_names, child_depth)
            )
        elif (
            is_file
            and path.suffix.casefold() == ".md"
            and entry.name != "README.md"
        ):
            lines.append(
                f"{'  ' * depth}- {summary_link(path.stem, path, root)}"
            )
    return lines


def build_summary_content(root: Path, configured_ignores: Iterable[str]) -> str:
    ignored_names = {name for name in configured_ignores if name}
    lines = ["# Summary", ""]
    root_readme = root / "README.md"
    if root_readme.is_file() and not root_readme.is_symlink():
        # 保留现有 SUMMARY.md 对根 README 的展示名称。
        lines.append(f"- {summary_link('00 介绍', root_readme, root)}")
    lines.extend(collect_summary_entries(root, root, ignored_names, 0))
    return "\n".join(lines).rstrip() + "\n"


def generate_summary(root: Path, configured_ignores: Iterable[str]) -> None:
    content = build_summary_content(root, configured_ignores)

    summary_file = root / SUMMARY_FILE_NAME
    try:
        summary_file.write_text(content, encoding="utf-8")
    except OSError as error:
        raise RuntimeError(f"无法写入 {summary_file}：{error}") from error
    entry_count = sum(1 for line in content.splitlines() if line.lstrip().startswith("- "))
    print(f"已生成 {summary_file}，共 {entry_count} 个条目。")


def fenced_code_ranges(markdown: str) -> list[tuple[int, int]]:
    """返回 fenced code block 的字符区间。"""
    ranges: list[tuple[int, int]] = []
    opening_start: int | None = None
    fence_character: str | None = None
    fence_length = 0
    offset = 0

    for line in markdown.splitlines(keepends=True):
        line_without_ending = line.rstrip("\r\n")
        match = FENCE_RE.match(line_without_ending)
        if fence_character is None and match:
            marker = match.group(1)
            opening_start = offset
            fence_character = marker[0]
            fence_length = len(marker)
        elif fence_character is not None:
            closing_re = rf"^ {{0,3}}{re.escape(fence_character)}{{{fence_length},}}\s*$"
            if re.match(closing_re, line_without_ending):
                ranges.append(
                    (
                        opening_start if opening_start is not None else offset,
                        offset + len(line),
                    )
                )
                opening_start = None
                fence_character = None
                fence_length = 0
        offset += len(line)

    if fence_character is not None:
        ranges.append(
            (opening_start if opening_start is not None else offset, len(markdown))
        )
    return ranges


def is_in_ranges(position: int, ranges: Sequence[tuple[int, int]]) -> bool:
    return any(start <= position < end for start, end in ranges)


def is_escaped(markdown: str, position: int) -> bool:
    backslashes = 0
    position -= 1
    while position >= 0 and markdown[position] == "\\":
        backslashes += 1
        position -= 1
    return backslashes % 2 == 1


class ImageNameAllocator:
    """为根 assets 目录分配 eb_00001 格式的图片名。"""

    def __init__(self, assets_directory: Path) -> None:
        self.assets_directory = assets_directory
        self.used_numbers: set[int] = set()
        if assets_directory.is_dir():
            for path in assets_directory.iterdir():
                match = FORMATTED_IMAGE_RE.fullmatch(path.name)
                if match:
                    self.used_numbers.add(int(match.group(1)))
        self.next_number = 1

    def allocate(self, suffix: str) -> Path:
        while self.next_number in self.used_numbers:
            self.next_number += 1
        if self.next_number > 99999:
            raise RuntimeError("根目录 assets 中的 eb 图片编号已经用尽")
        number = self.next_number
        self.used_numbers.add(number)
        self.next_number += 1
        return self.assets_directory / f"eb_{number:05d}{suffix.casefold()}"


def relative_image_path(markdown_file: Path, image_file: Path) -> str:
    return os.path.relpath(image_file, markdown_file.parent).replace(os.sep, "/")


def image_target_replacement(
    raw_target: str,
    root: Path,
    markdown_file: Path,
    allocator: ImageNameAllocator,
    image_moves: dict[Path, Path],
) -> tuple[str, str | None]:
    """返回 (状态, 新路径)：skip、missing 或 replace。"""
    target = clean_local_target(raw_target)
    if target is None or target.startswith("/") or not is_image_target(target):
        return "skip", None

    if FORMATTED_IMAGE_RE.fullmatch(Path(target).name):
        return "skip", None

    source = resolve_target(root, markdown_file, target)
    if relative_if_inside(source, root) is None:
        return "skip", None

    destination = image_moves.get(source)
    if destination is None:
        if not source.is_file():
            return "missing", None
        destination = allocator.allocate(source.suffix)
        image_moves[source] = destination

    return "replace", relative_image_path(markdown_file, destination)


def destination_title(raw_destination: str) -> str:
    """保留 Markdown inline image 目标后的可选 title。"""
    stripped = raw_destination.strip()
    if stripped.startswith("<"):
        closing = stripped.find(">", 1)
        return stripped[closing + 1 :] if closing != -1 else ""
    match = TITLE_RE.search(stripped)
    return match.group(0) if match else ""


INLINE_IMAGE_RE = re.compile(r"!\[([^\]\n]*)\]")
REFERENCE_IMAGE_RE = re.compile(
    r"!\[([^\]\n]*)\](?:\[([^\]\n]*)\])?"
)
HTML_IMAGE_RE = re.compile(
    r"<img\b[^>]*?\bsrc\s*=\s*([\"'])(.*?)\1[^>]*>",
    re.IGNORECASE | re.DOTALL,
)
WIKI_LINK_RE = re.compile(r"!?\[\[([^\]\n]+)\]\]")
HTML_LINK_RE = re.compile(
    r"<a\b[^>]*?\bhref\s*=\s*([\"'])(.*?)\1[^>]*>",
    re.IGNORECASE | re.DOTALL,
)


def rewrite_markdown_images(
    markdown: str,
    root: Path,
    markdown_file: Path,
    allocator: ImageNameAllocator,
    image_moves: dict[Path, Path],
) -> tuple[str, int, int]:
    """规划一个 Markdown 文件中的图片迁移与引用修改。"""
    code_ranges = fenced_code_ranges(markdown)
    replacements: list[tuple[int, int, str]] = []
    replaced_count = 0
    missing_count = 0

    definitions: dict[str, re.Match[str]] = {}
    for definition in REFERENCE_DEFINITION_RE.finditer(markdown):
        if is_in_ranges(definition.start(), code_ranges):
            continue
        label = normalize_reference_label(definition.group(1))
        definitions.setdefault(label, definition)

    reference_occurrences: dict[str, list[re.Match[str]]] = {}
    for match in REFERENCE_IMAGE_RE.finditer(markdown):
        if is_escaped(markdown, match.start()) or is_in_ranges(
            match.start(), code_ranges
        ):
            continue
        if match.group(1).startswith("["):
            # wiki 图片由下面的专用逻辑处理。
            continue
        if match.group(2) is None:
            if match.end() < len(markdown) and markdown[match.end()] == "(":
                continue
            label_text = match.group(1)
        else:
            label_text = match.group(2) or match.group(1)
        label = normalize_reference_label(label_text)
        if label in definitions:
            reference_occurrences.setdefault(label, []).append(match)

    for label, occurrences in reference_occurrences.items():
        definition = definitions[label]
        raw_destination = definition.group(2)
        raw_target = parse_destination(raw_destination)
        status, new_target = image_target_replacement(
            raw_target, root, markdown_file, allocator, image_moves
        )
        if status == "replace" and new_target is not None:
            title = destination_title(raw_destination)
            start, end = definition.span(2)
            replacements.append((start, end, f"{new_target}{title}"))
            replaced_count += len(occurrences)
        elif status == "missing":
            replacements.extend(
                (match.start(), match.end(), "") for match in occurrences
            )
            missing_count += len(occurrences)

    for match in INLINE_IMAGE_RE.finditer(markdown):
        if is_escaped(markdown, match.start()) or is_in_ranges(match.start(), code_ranges):
            continue
        opening_index = match.end()
        if opening_index >= len(markdown) or markdown[opening_index] != "(":
            continue
        parsed = find_parenthesized(markdown, opening_index)
        if parsed is None:
            continue
        raw_destination, end = parsed
        raw_target = parse_destination(raw_destination)
        status, new_target = image_target_replacement(
            raw_target, root, markdown_file, allocator, image_moves
        )
        if status == "replace" and new_target is not None:
            title = destination_title(raw_destination)
            replacements.append(
                (match.start(), end, f"![{match.group(1)}]({new_target}{title})")
            )
            replaced_count += 1
        elif status == "missing":
            replacements.append((match.start(), end, ""))
            missing_count += 1

    for match in WIKI_IMAGE_RE.finditer(markdown):
        if is_escaped(markdown, match.start()) or is_in_ranges(
            match.start(), code_ranges
        ):
            continue
        raw_target = match.group(1).split("#", 1)[0].strip()
        status, new_target = image_target_replacement(
            raw_target, root, markdown_file, allocator, image_moves
        )
        if status == "replace" and new_target is not None:
            pipe = markdown[match.start() : match.end()].find("|")
            suffix = ""
            if pipe != -1:
                original = markdown[match.start() : match.end()]
                suffix = original[pipe:-2]
            replacements.append((match.start(), match.end(), f"![[{new_target}{suffix}]]"))
            replaced_count += 1
        elif status == "missing":
            replacements.append((match.start(), match.end(), ""))
            missing_count += 1

    for match in HTML_IMAGE_RE.finditer(markdown):
        if is_in_ranges(match.start(), code_ranges):
            continue
        raw_target = match.group(2)
        status, new_target = image_target_replacement(
            raw_target, root, markdown_file, allocator, image_moves
        )
        if status == "replace" and new_target is not None:
            target_start, target_end = match.span(2)
            replacements.append((target_start, target_end, new_target))
            replaced_count += 1
        elif status == "missing":
            replacements.append((match.start(), match.end(), ""))
            missing_count += 1

    # 同一位置不会同时属于上述三种语法；逆序修改可保持原始索引有效。
    for start, end, replacement in sorted(replacements, reverse=True):
        markdown = markdown[:start] + replacement + markdown[end:]
    return markdown, replaced_count, missing_count


def local_target_suffix(raw_target: str) -> str:
    """返回本地链接目标中的查询参数和锚点，并保持原始顺序。"""
    suffix_indexes = [
        index for marker in ("?", "#") if (index := raw_target.find(marker)) != -1
    ]
    return raw_target[min(suffix_indexes) :] if suffix_indexes else ""


def replace_destination_target(raw_destination: str, new_target: str) -> str:
    """只替换 Markdown destination 的路径，保留尖括号、标题与空白。"""
    raw_target = parse_destination(raw_destination)
    target_start = raw_destination.find(raw_target)
    if not raw_target or target_start == -1:
        return raw_destination
    target_end = target_start + len(raw_target)
    return raw_destination[:target_start] + new_target + raw_destination[target_end:]


def relative_markdown_path(markdown_file: Path, target: Path) -> str:
    return os.path.relpath(target, markdown_file.parent).replace(os.sep, "/")


def rewritten_reference_destination(
    raw_destination: str,
    root: Path,
    markdown_file: Path,
    source: Path,
    destination: Path,
) -> str | None:
    """当 destination 指向待移动文件时，返回新的相对引用。"""
    raw_target = parse_destination(raw_destination)
    target = clean_local_target(raw_target)
    if target is None or resolve_target(root, markdown_file, target) != source:
        return None

    new_target = relative_markdown_path(markdown_file, destination)
    new_target += local_target_suffix(raw_target)
    return replace_destination_target(raw_destination, new_target)


def rewritten_moved_document_destination(
    raw_destination: str,
    root: Path,
    source: Path,
    destination: Path,
) -> str | None:
    """重定位被移动文档自身的相对链接，使其仍指向移动前的目标。"""
    raw_target = parse_destination(raw_destination)
    target = clean_local_target(raw_target)
    if target is None or target.startswith("/"):
        return None

    original_target = resolve_target(root, source, target)
    if relative_if_inside(original_target, root) is None:
        return None
    target_after_move = destination if original_target == source else original_target
    new_target = relative_markdown_path(destination, target_after_move)
    new_target += local_target_suffix(raw_target)
    rewritten = replace_destination_target(raw_destination, new_target)
    return rewritten if rewritten != raw_destination else None


def rewrite_markdown_file_reference(
    markdown: str,
    root: Path,
    markdown_file: Path,
    source: Path,
    destination: Path,
    preserve_moved_document_targets: bool = False,
) -> tuple[str, int]:
    """改写入站引用，或重定位被移动文档自身的相对引用。"""
    def rewrite_destination(raw_destination: str) -> str | None:
        if preserve_moved_document_targets:
            return rewritten_moved_document_destination(
                raw_destination, root, source, destination
            )
        return rewritten_reference_destination(
            raw_destination, root, markdown_file, source, destination
        )

    return rewrite_markdown_destinations(markdown, rewrite_destination)


def markdown_code_ranges(markdown: str) -> list[tuple[int, int]]:
    """保护围栏、缩进代码块和行内代码，避免改写文档中的示例。"""
    ranges = fenced_code_ranges(markdown)
    offset = 0
    indented = False
    previous_blank = True
    for line in markdown.splitlines(keepends=True):
        blank = not line.strip()
        has_indent = line.startswith("    ") or line.startswith("\t")
        if has_indent and (previous_blank or indented):
            ranges.append((offset, offset + len(line)))
            indented = True
        elif not blank:
            indented = False
        previous_blank = blank
        offset += len(line)
    ticks = list(re.finditer(r"`+", markdown))
    index = 0
    while index < len(ticks):
        opening = ticks[index]
        if is_escaped(markdown, opening.start()) or is_in_ranges(opening.start(), ranges):
            index += 1
            continue
        closing_index = index + 1
        while closing_index < len(ticks):
            closing = ticks[closing_index]
            if is_in_ranges(closing.start(), ranges):
                break
            if len(closing.group()) == len(opening.group()):
                ranges.append((opening.start(), closing.end()))
                index = closing_index
                break
            closing_index += 1
        index += 1
    return ranges


def rewrite_markdown_destinations(
    markdown: str, rewrite_destination: Callable[[str], str | None]
) -> tuple[str, int]:
    """各入口共用原位置替换器；只替换目标，不重新序列化整篇 Markdown。"""
    code_ranges = markdown_code_ranges(markdown)
    replacements: list[tuple[int, int, str]] = []

    for definition in REFERENCE_DEFINITION_RE.finditer(markdown):
        if is_in_ranges(definition.start(), code_ranges):
            continue
        raw_destination = definition.group(2)
        rewritten = rewrite_destination(raw_destination)
        if rewritten is not None:
            start, end = definition.span(2)
            replacements.append((start, end, rewritten))

    for match in LINK_RE.finditer(markdown):
        if is_escaped(markdown, match.start()) or is_in_ranges(
            match.start(), code_ranges
        ):
            continue
        opening_index = match.end()
        if opening_index >= len(markdown) or markdown[opening_index] != "(":
            continue
        parsed = find_parenthesized(markdown, opening_index)
        if parsed is None:
            continue
        raw_destination, end = parsed
        rewritten = rewrite_destination(raw_destination)
        if rewritten is not None:
            replacements.append((opening_index + 1, end - 1, rewritten))

    for match in WIKI_LINK_RE.finditer(markdown):
        if is_escaped(markdown, match.start()) or is_in_ranges(
            match.start(), code_ranges
        ):
            continue
        wiki_value = match.group(1)
        raw_destination = wiki_value.split("|", 1)[0]
        target = raw_destination.strip()
        rewritten = rewrite_destination(target)
        if rewritten is not None:
            target_start = match.start(1) + raw_destination.find(target)
            replacements.append(
                (target_start, target_start + len(target), rewritten)
            )

    for match in HTML_LINK_RE.finditer(markdown):
        if is_in_ranges(match.start(), code_ranges):
            continue
        raw_destination = match.group(2)
        rewritten = rewrite_destination(raw_destination)
        if rewritten is not None:
            start, end = match.span(2)
            replacements.append((start, end, rewritten))

    for match in HTML_IMAGE_RE.finditer(markdown):
        if is_in_ranges(match.start(), code_ranges):
            continue
        rewritten = rewrite_destination(match.group(2))
        if rewritten is not None:
            start, end = match.span(2)
            replacements.append((start, end, rewritten))

    for match in CSS_URL_RE.finditer(markdown):
        if is_in_ranges(match.start(), code_ranges):
            continue
        group_index = next(
            (index for index in range(1, 4) if match.group(index) is not None),
            None,
        )
        if group_index is None:
            continue
        rewritten = rewrite_destination(match.group(group_index))
        if rewritten is not None:
            start, end = match.span(group_index)
            replacements.append((start, end, rewritten))

    # 对嵌套 HTML / Markdown 匹配也只应用互不重叠的区间。
    unique_replacements = sorted(set(replacements), reverse=True)
    boundary = len(markdown)
    applied = 0
    for start, end, replacement in unique_replacements:
        if end > boundary:
            continue
        markdown = markdown[:start] + replacement + markdown[end:]
        boundary = start
        applied += 1
    return markdown, applied


def repository_argument_path(root: Path, path: Path) -> Path:
    path = path.expanduser()
    if not path.is_absolute():
        path = root / path
    path = Path(os.path.abspath(os.path.normpath(path)))
    # 规范化父目录（例如 macOS 的 /var -> /private/var），但不跟随参数本身
    # 可能指向的符号链接，便于后续明确拒绝移动符号链接文件。
    return path.parent.resolve() / path.name


NUMBERED_TITLE_RE = re.compile(r"^([0-9]{1,2})[ -]+(.*)$")


def unnumbered_name(name: str, kind: str) -> str:
    """提取标题，保留 Markdown 扩展名；README 是不编号的特殊名称。"""
    suffix = Path(name).suffix if kind == "file" else ""
    stem = name[:-len(suffix)] if suffix else name
    match = NUMBERED_TITLE_RE.match(stem)
    title = (match[2] if match else stem).strip()
    if not title:
        raise ValueError("请在序号后填写名称")
    if kind == "file" and title.casefold() == "readme":
        return "README.md"
    return title + suffix


def move_markdown_file(
    root: Path,
    ignores: IgnoreMatcher,
    source_argument: Path,
    destination_argument: Path,
) -> None:
    """CLI 与 UI 共用编号、路径映射和事务，CLI 不额外生成 SUMMARY。"""
    root = root.resolve()
    source = repository_argument_path(root, source_argument)
    destination = repository_argument_path(root, destination_argument)
    if relative_if_inside(source, root) is None or relative_if_inside(destination, root) is None:
        raise ValueError("源文件和目标路径必须位于扫描根目录内")
    if source.suffix.casefold() != ".md":
        raise ValueError("源文件必须是 Markdown 文件")
    manager = FileManager(root, load_config())
    manager.ignores = ignores
    payload = {"revision": manager.state()["revision"]}
    source_relative = source.relative_to(root).as_posix()
    if destination.is_dir():
        payload.update(paths=[source_relative], target=destination.relative_to(root).as_posix())
        if destination == root:
            payload["target"] = ""
        action = "move"
    else:
        payload.update(path=source_relative, name=destination.name)
        if destination.parent != source.parent:
            payload["target"] = destination.parent.relative_to(root).as_posix()
            if destination.parent == root:
                payload["target"] = ""
        action = "rename"
    result = manager.operate(action, payload, regenerate=False)
    print(f"Markdown 整理完成：{source_relative} -> {result['focusPaths'][0]}；"
          f"更新引用 {result['summary']['updatedReferences']} 处。")


def format_images(root: Path, ignores: IgnoreMatcher) -> None:
    repository_files = list(iter_repository_files(root, ignores))
    markdown_files = sorted(
        path for path in repository_files if path.suffix.casefold() == ".md"
    )
    assets_directory = root / "assets"
    allocator = ImageNameAllocator(assets_directory)
    image_moves: dict[Path, Path] = {}
    changed_files: dict[Path, tuple[bytes, bytes]] = {}
    replaced_count = 0
    missing_count = 0

    for markdown_file in markdown_files:
        try:
            original_bytes = markdown_file.read_bytes()
            has_bom = original_bytes.startswith(b"\xef\xbb\xbf")
            markdown = original_bytes.decode("utf-8-sig")
        except (OSError, UnicodeError) as error:
            raise RuntimeError(f"无法读取 Markdown 文件 {markdown_file}：{error}") from error

        rewritten, replaced, missing = rewrite_markdown_images(
            markdown, root, markdown_file, allocator, image_moves
        )
        replaced_count += replaced
        missing_count += missing
        if rewritten != markdown:
            prefix = b"\xef\xbb\xbf" if has_bom else b""
            changed_files[markdown_file] = (
                original_bytes,
                prefix + rewritten.encode("utf-8"),
            )

    assets_created = False
    moved_images: list[tuple[Path, Path]] = []
    written_files: list[Path] = []
    try:
        if image_moves and not assets_directory.exists():
            assets_directory.mkdir(parents=True)
            assets_created = True
        for source, destination in image_moves.items():
            if destination.exists():
                raise RuntimeError(f"目标图片已经存在：{destination}")
            source.rename(destination)
            moved_images.append((source, destination))
        for markdown_file, (_, rewritten_bytes) in changed_files.items():
            markdown_file.write_bytes(rewritten_bytes)
            written_files.append(markdown_file)
    except (OSError, RuntimeError) as error:
        for markdown_file in reversed(written_files):
            original_bytes = changed_files[markdown_file][0]
            try:
                markdown_file.write_bytes(original_bytes)
            except OSError:
                pass
        for source, destination in reversed(moved_images):
            try:
                destination.rename(source)
            except OSError:
                pass
        if assets_created:
            try:
                assets_directory.rmdir()
            except OSError:
                pass
        raise RuntimeError(f"图片格式化失败，已尝试回滚：{error}") from error

    print(
        f"图片格式化完成：扫描 Markdown {len(markdown_files)} 个，"
        f"修改 {len(changed_files)} 个，移动图片 {len(image_moves)} 张，"
        f"更新引用 {replaced_count} 处，删除缺失引用 {missing_count} 处。"
    )


class OperationConflict(ValueError):
    """文件状态已改变或操作与现有路径冲突。"""


def map_moved_path(path: Path, moves: Sequence[tuple[Path, Path]]) -> Path:
    # 父目录和子项目可能同时改号，最具体的映射已经包含最终父目录路径。
    for source, destination in sorted(moves, key=lambda move: len(move[0].parts), reverse=True):
        if path == source or source in path.parents:
            return destination / path.relative_to(source)
    return path


def encode_local_path(path: str, original: str = "") -> str:
    if re.search(r"%[0-9a-fA-F]{2}", original):
        return quote(path, safe="/-._~")
    # 保持中文、空格可读，避免文件名中的 URL / HTML 分隔符改变链接含义。
    return "".join(quote(char, safe="") if char in '%#?<>\"\'()' else char for char in path)


def rewrite_mapped_destination(
    raw_destination: str,
    root: Path,
    document: Path,
    moves: Sequence[tuple[Path, Path]],
) -> str | None:
    raw_target = parse_destination(raw_destination)
    target = clean_local_target(raw_target)
    if target is None:
        return None
    old_target = resolve_target(root, document, target)
    if relative_if_inside(old_target, root) is None:
        return None
    new_document = map_moved_path(document, moves)
    new_target = map_moved_path(old_target, moves)
    if target.startswith("/"):
        if new_target == old_target:
            return None
        replacement = "/" + new_target.relative_to(root).as_posix()
    else:
        before = relative_markdown_path(document, old_target)
        replacement = relative_markdown_path(new_document, new_target)
        if before == replacement:
            return None
        if target.startswith("./") and not replacement.startswith("."):
            replacement = "./" + replacement
    replacement = encode_local_path(replacement, raw_target) + local_target_suffix(raw_target)
    return replace_destination_target(raw_destination, replacement)


@dataclass
class UndoRecord:
    moves: list[tuple[Path, Path]]
    changes: dict[Path, tuple[bytes | None, bytes | None]]
    created_directory: Path | None
    after: dict
    label: str
    focus: list[Path]


class FileManager:
    """UI 的全部文件访问、变更、回滚与撤销；前端只传递操作意图。"""

    def __init__(self, root: Path, config: dict[str, list[str]]) -> None:
        self.root = root.resolve()
        if not self.root.is_dir():
            raise ValueError(f"管理根目录不存在：{self.root}")
        self.config = config
        self.ignores = load_ignore_matcher([*config["img_ignore"], "/eb_tool/"])
        self.hidden_names = (set(config["gen_ignore"]) - {"README.md"}) | {
            "assets", "img", "eb_tool", "AGENTS.md", SUMMARY_FILE_NAME,
        }
        self.lock = threading.RLock()
        self.undo_record: UndoRecord | None = None

    def _snapshot(self) -> dict:
        result = {}

        def visit(directory: Path) -> None:
            with os.scandir(directory) as entries:
                for entry in entries:
                    if entry.name.startswith("."):
                        continue
                    path = Path(entry.path)
                    relative = path.relative_to(self.root).as_posix()
                    info = entry.stat(follow_symlinks=False)
                    kind = ("directory" if stat.S_ISDIR(info.st_mode) else
                            "file" if stat.S_ISREG(info.st_mode) else "special")
                    if self.ignores.matches(relative, kind == "directory"):
                        continue
                    if kind == "directory":
                        result[relative] = (kind, info.st_mode)
                        visit(path)
                    else:
                        result[relative] = (
                            kind, info.st_size, info.st_mtime_ns,
                            info.st_ctime_ns, info.st_ino, info.st_mode,
                        )

        visit(self.root)
        return result

    @staticmethod
    def _revision(snapshot: dict) -> str:
        return hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()

    def _visible(self, relative: str, kind: str) -> bool:
        path = Path(relative)
        if any(part.startswith(".") or part in self.hidden_names for part in path.parts):
            return False
        if relative == "README.md":
            return False
        return kind == "directory" or (kind == "file" and path.suffix.casefold() == ".md")

    def _state(self, snapshot: dict) -> dict:
        entries = [
            {
                "path": relative, "name": Path(relative).name,
                "parent": "" if Path(relative).parent == Path(".") else Path(relative).parent.as_posix(),
                "kind": value[0],
            }
            for relative, value in sorted(snapshot.items())
            if self._visible(relative, value[0])
        ]
        return {
            "rootName": self.root.name, "rootPath": str(self.root), "entries": entries,
            "revision": self._revision(snapshot),
            "undo": {"available": self.undo_record is not None,
                     "label": self.undo_record.label if self.undo_record else ""},
        }

    def state(self) -> dict:
        with self.lock:
            return self._state(self._snapshot())

    def _path(self, value: str, snapshot: dict, allow_root: bool = False) -> Path:
        if not isinstance(value, str) or "\\" in value or "\0" in value:
            raise ValueError("路径必须是仓库内的相对路径")
        if value == "" and allow_root:
            return self.root
        if not value or value.startswith("/") or any(part in {"", ".", ".."} for part in value.split("/")):
            raise ValueError("不允许绝对路径、空路径或上级目录")
        path = self.root
        for part in value.split("/"):
            path = path / part
            if path.is_symlink():
                raise ValueError("不支持操作符号链接")
        info = snapshot.get(value)
        if info is None or not self._visible(value, info[0]):
            raise ValueError(f"项目不存在或不可管理：{value}")
        return path

    @staticmethod
    def _name(name: str) -> str:
        if (not isinstance(name, str) or not name or name != name.strip()
                or name in {".", ".."} or name.startswith(".")
                or any(char in "/\\" or ord(char) < 32 or ord(char) == 127 for char in name)):
            raise ValueError("名称不能为空，不能包含路径分隔符、控制字符或首尾空白，也不能以点开头")
        if len(name.encode("utf-8")) > 255:
            raise ValueError("名称过长，请缩短后重试")
        return name

    @staticmethod
    def _case_alias(source: Path, destination: Path) -> bool:
        return (
            source.parent == destination.parent
            and source.name != destination.name
            and source.name.casefold() == destination.name.casefold()
            and destination.exists()
            and source.samefile(destination)
            and destination.name not in os.listdir(destination.parent)
        )

    def _check_scope(self, destination: Path, kind: str) -> None:
        relative = destination.relative_to(self.root).as_posix()
        if not self._visible(relative, kind) or self.ignores.matches(relative, kind == "directory"):
            raise ValueError("目标名称或目录属于忽略范围")

    def _validate_moves(
        self, moves: list, create: Path | None = None, remove: Path | None = None,
        snapshot: dict | None = None,
    ) -> None:
        destinations = set()
        for source, destination in [*moves, *([(None, create)] if create else [])]:
            self._name(destination.name)
            self._check_scope(destination, "directory" if source is None or source.is_dir() else "file")
            key = str(destination).casefold()
            if key in destinations:
                raise OperationConflict("所选项目在目标目录中名称重复")
            destinations.add(key)
            if source is not None:
                self._assert_regular_tree(source)
            # 已占用的路径只有在本批操作中会腾出、或由撤销移除时才可使用。
            if os.path.lexists(destination) and destination != source and destination != remove:
                if map_moved_path(destination, moves) == destination and not (
                    source is not None and self._case_alias(source, destination)
                ):
                    raise OperationConflict(f"目标已存在，不会覆盖：{destination.relative_to(self.root)}")
        sources = {source for source, _ in moves}
        for relative in snapshot or {}:
            original = self.root / relative
            if original in sources or (remove and (original == remove or remove in original.parents)):
                continue
            # 目录整体移动携带的后代也会占用最终路径，需在写入前一起预检。
            destination = map_moved_path(original, moves)
            if str(destination).casefold() in destinations:
                raise OperationConflict(f"目标已存在，不会覆盖：{destination.relative_to(self.root)}")

    def _plan(self, action: str, payload: dict, snapshot: dict) -> tuple:
        # 原始路径作为稳定身份；父目录改名不会影响子项目或移动目标的身份。
        nodes = {
            self.root / relative: {"name": Path(relative).name, "kind": info[0],
                                   "parent": (self.root / relative).parent}
            for relative, info in snapshot.items() if self._visible(relative, info[0])
        }
        affected = set()
        if action == "rename":
            source = self._path(payload.get("path"), snapshot)
            name = self._name(payload.get("name"))
            if nodes[source]["kind"] == "file" and Path(name).suffix.casefold() != ".md":
                raise ValueError("Markdown 文件必须保留 .md 扩展名")
            parent = (self._path(payload["target"], snapshot, allow_root=True)
                      if "target" in payload else source.parent)
            if not parent.is_dir():
                raise ValueError("目标必须是目录")
            if source == parent or source in parent.parents:
                raise ValueError("不能将目录移动到自身或子目录中")
            self._check_scope(parent / name, nodes[source]["kind"])
            nodes[source].update(name=name, parent=parent)
            affected.update([source.parent, parent])
            focus = [source]
            label = f"重命名「{source.name}」"
        elif action == "move":
            values = payload.get("paths")
            if not isinstance(values, list) or not values:
                raise ValueError("请选择需要移动的项目")
            sources = set(self._path(value, snapshot) for value in values)
            sources = sorted(source for source in sources if not any(parent in sources for parent in source.parents))
            target = self._path(payload.get("target"), snapshot, allow_root=True)
            if not target.is_dir():
                raise ValueError("移动目标必须是目录")
            for source in sources:
                if source == target or source in target.parents:
                    raise ValueError("不能将目录移动到自身或子目录中")
                if source.parent == target:
                    raise OperationConflict("项目已经位于目标目录")
                nodes[source]["parent"] = target
                affected.update([source.parent, target])
            focus = sources
            label = f"移动 {len(sources)} 个项目"
        elif action == "mkdir":
            parent = self._path(payload.get("parent"), snapshot, allow_root=True)
            if not parent.is_dir():
                raise ValueError("父目录必须是目录")
            name = self._name(payload.get("name"))
            self._check_scope(parent / name, "directory")
            nodes[None] = {"name": name, "kind": "directory", "parent": parent}
            affected.add(parent)
            focus = [None]
            label = "新建目录"
        else:
            raise ValueError("不支持的操作")

        def order(key):
            node = nodes[key]
            old_name = key.name if key is not None else node["name"]
            number = NUMBERED_TITLE_RE.match(old_name)
            incoming = key is None or key.parent != node["parent"]
            return (incoming, int(number[1]) if number else 100,
                    old_name.casefold(), str(key))

        for parent in affected:
            for kind in ("directory", "file"):
                children = [key for key, node in nodes.items()
                            if node["parent"] == parent and node["kind"] == kind]
                numbered = []
                for key in children:
                    title = unnumbered_name(nodes[key]["name"], kind)
                    if kind == "file" and title == "README.md":
                        nodes[key]["name"] = title
                    else:
                        numbered.append((key, title))
                if len(numbered) > 99:
                    raise ValueError("每个目录最多支持 99 个同类编号项目，请选择其他目录")
                for number, (key, title) in enumerate(sorted(numbered, key=lambda item: order(item[0])), 1):
                    nodes[key]["name"] = f"{number:02d} {title}"

        final_paths = {self.root: self.root}
        def final_path(key):
            if key not in final_paths:
                node = nodes[key]
                final_paths[key] = final_path(node["parent"]) / node["name"]
            return final_paths[key]

        moves = [(source, final_path(source)) for source, node in nodes.items()
                 if source is not None and (node["name"] != source.name or node["parent"] != source.parent)]
        create = final_path(None) if None in nodes else None
        if not moves and create is None:
            raise OperationConflict("项目名称和编号没有变化")
        if create:
            label = f"新建「{create.name}」"
        return moves, create, [final_path(key) for key in focus], label, focus

    def _assert_regular_tree(self, source: Path) -> None:
        # 隐藏文件也会随目录移动，必须检查被 UI 隐藏或被扫描忽略的后代。
        if source.is_symlink():
            raise ValueError("不支持操作符号链接")
        if source.is_dir():
            for current, directories, files in os.walk(source, followlinks=False):
                for name in directories + files:
                    path = Path(current) / name
                    mode = path.lstat().st_mode
                    if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                        raise ValueError(f"目录包含符号链接或特殊文件：{path.relative_to(self.root)}")

    def _tree_signature(self, source: Path) -> dict:
        """完整移动子树（包括隐藏文件和资源）用于撤销的外部修改校验。"""
        result = {}
        paths = [source]
        if source.is_dir():
            for current, directories, files in os.walk(source, followlinks=False):
                paths.extend(Path(current) / name for name in directories + files)
        for path in paths:
            info = path.lstat()
            if stat.S_ISDIR(info.st_mode):
                value = ("directory", info.st_mode)
            else:
                value = (info.st_mode, info.st_size, info.st_mtime_ns, info.st_ctime_ns, info.st_ino)
            result[path.relative_to(self.root).as_posix()] = value
        return result

    @staticmethod
    def _read_optional(path: Path) -> bytes | None:
        if path.is_symlink():
            raise ValueError(f"不支持读取或写入符号链接：{path}")
        if path.exists():
            if not path.is_file():
                raise ValueError(f"预期普通文件：{path}")
            return path.read_bytes()
        return None

    def _write_atomic(self, path: Path, expected: bytes | None, content: bytes | None) -> None:
        if self._read_optional(path) != expected:
            raise OperationConflict(f"文件已被外部修改：{path.relative_to(self.root)}")
        if content is None:
            if path.exists():
                path.unlink()
            return
        mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
        descriptor, temporary = tempfile.mkstemp(prefix=".eb-write-", dir=path.parent)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                os.fchmod(stream.fileno(), mode)
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            if self._read_optional(path) != expected:
                raise OperationConflict(f"文件已被外部修改：{path.relative_to(self.root)}")
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def _relocate(self, source: Path, destination: Path) -> None:
        if self._case_alias(source, destination):
            holder = Path(tempfile.mkdtemp(prefix=".eb-rename-", dir=source.parent))
            intermediate = holder / source.name
            try:
                source.rename(intermediate)
                if os.path.lexists(destination):
                    raise OperationConflict(f"目标已存在：{destination}")
                intermediate.rename(destination)
            except BaseException:
                if intermediate.exists() and not os.path.lexists(source):
                    intermediate.rename(source)
                elif intermediate.exists():
                    raise RuntimeError(f"大小写重命名失败；原内容保留在：{intermediate}")
                raise
            finally:
                if not any(holder.iterdir()):
                    holder.rmdir()
        else:
            if os.path.lexists(destination):
                raise OperationConflict(f"目标已存在：{destination.relative_to(self.root)}")
            source.rename(destination)

    @staticmethod
    def _summary_bytes(content: str, original: bytes | None) -> bytes:
        if original and b"\r\n" in original:
            content = content.replace("\n", "\r\n")
        prefix = b"\xef\xbb\xbf" if original and original.startswith(b"\xef\xbb\xbf") else b""
        return prefix + content.encode("utf-8")

    def _commit(
        self, moves: list[tuple[Path, Path]],
        changes: dict[Path, tuple[bytes | None, bytes | None]],
        create: Path | None = None, remove: Path | None = None,
        regenerate: bool = True,
    ) -> tuple[dict, dict]:
        journal = []
        written = set()
        changes = dict(changes)
        undo_was_valid = self._record_unchanged(self.undo_record)
        summary_path = self.root / SUMMARY_FILE_NAME
        original_summary = self._read_optional(summary_path) if regenerate else None

        def write(path, original, updated):
            journal.append(("write", path, (original, updated)))
            written.add(path)
            self._write_atomic(path, original, updated)

        def relocate(source, destination):
            self._relocate(source, destination)
            journal.append(("move", source, destination))

        staging = None
        try:
            # 撤销新建目录时先腾出位置；该位置可能正是旧编号要恢复的位置。
            if remove:
                readme = remove / "README.md"
                original, updated = changes[readme]
                write(readme, original, updated)
                remove.rmdir()
                journal.append(("rmdir", remove, None))
            if moves:
                staging = Path(tempfile.mkdtemp(prefix=".eb-stage-", dir=self.root))
                journal.append(("mkdir", staging, None))
                staged = []
                # 先取出后代，再取出父目录，避免路径覆盖及父子同时改名丢失定位。
                for index, (source, destination) in enumerate(sorted(moves, key=lambda item: len(item[0].parts), reverse=True)):
                    temporary = staging / str(index)
                    relocate(source, temporary)
                    staged.append((temporary, destination))
                # 最终父目录先就位，子项目再放入；编号互换不会覆盖原文件。
                for temporary, destination in sorted(staged, key=lambda item: len(item[1].parts)):
                    relocate(temporary, destination)
            if create:
                create.mkdir()
                journal.append(("mkdir", create, None))
                readme = create / "README.md"
                changes[readme] = (None, b"")
                write(readme, None, b"")
            if regenerate:
                generated = self._summary_bytes(
                    build_summary_content(self.root, self.config["gen_ignore"]), original_summary,
                )
                if generated != original_summary:
                    changes[summary_path] = (original_summary, generated)
            for path, (original, updated) in changes.items():
                if path not in written:
                    write(path, original, updated)
            after = self._snapshot()
            signatures = {
                str(path): self._tree_signature(path)
                for path in [*(destination for _, destination in moves), *([create] if create else [])]
            }
            if staging:
                staging.rmdir()
            return changes, {"snapshot": after, "trees": signatures}
        except BaseException as error:
            failures = []
            for action, path, data in reversed(journal):
                try:
                    if action == "write":
                        original, updated = data
                        current = self._read_optional(path)
                        if current == original:
                            continue
                        if current != updated:
                            raise OperationConflict("恢复前检测到外部修改，保留当前文件")
                        self._write_atomic(path, current, original)
                    elif action == "move":
                        self._relocate(data, path)
                    elif action == "mkdir":
                        path.rmdir()
                    elif action == "rmdir":
                        path.mkdir()
                except (OSError, ValueError, RuntimeError) as rollback_error:
                    failures.append(f"{path}: {rollback_error}")
            if failures:
                self.undo_record = None
                raise RuntimeError(
                    f"操作失败：{error}；以下项目未能恢复，请保留现场并检查："
                    + "；".join(failures)
                ) from error
            # 回滚中的原子写入会改变 inode / ctime。内容已恢复时刷新指纹，
            # 使用户仍能重试撤销；原本已被外部修改的记录不得重新变为有效。
            if undo_was_valid and self.undo_record:
                try:
                    self.undo_record.after = {
                        "snapshot": self._snapshot(),
                        "trees": {path: self._tree_signature(Path(path))
                                  for path in self.undo_record.after["trees"]},
                    }
                except OSError:
                    self.undo_record = None
            if isinstance(error, (KeyboardInterrupt, SystemExit)):
                raise
            raise RuntimeError(f"操作失败，已回滚：{error}") from error

    def _record_unchanged(self, record: UndoRecord | None) -> bool:
        if record is None:
            return False
        try:
            return all(
                Path(path).exists() and not Path(path).is_symlink()
                and self._tree_signature(Path(path)) == signature
                for path, signature in record.after["trees"].items()
            ) and all(self._read_optional(path) == updated
                      for path, (_, updated) in record.changes.items())
        except (OSError, ValueError):
            return False

    def _prepare_references(self, snapshot: dict, moves: list, include_summary: bool = False) -> tuple[dict, int]:
        changes = {}
        references = 0
        documents = {
            self.root / relative for relative, info in snapshot.items()
            if info[0] == "file" and Path(relative).suffix.casefold() == ".md"
            and (include_summary or relative != SUMMARY_FILE_NAME) and Path(relative).name != "AGENTS.md"
        }
        # 移动的子树可能含有被扫描规则隐藏的 Markdown，也需保留其链接。
        for source, _ in moves:
            if source.is_dir():
                documents.update(path for path in source.rglob("*") if path.is_file()
                                 and path.suffix.casefold() == ".md" and path.name != "AGENTS.md")
        for document in sorted(documents):
            original = document.read_bytes()
            try:
                markdown = original.decode("utf-8-sig")
            except UnicodeError as error:
                raise ValueError(f"Markdown 不是 UTF-8，未执行操作：{document.relative_to(self.root)}") from error
            rewritten, count = rewrite_markdown_destinations(
                markdown, lambda raw: rewrite_mapped_destination(raw, self.root, document, moves),
            )
            if rewritten != markdown:
                prefix = b"\xef\xbb\xbf" if original.startswith(b"\xef\xbb\xbf") else b""
                changes[map_moved_path(document, moves)] = (original, prefix + rewritten.encode("utf-8"))
                references += count
        return changes, references

    def operate(self, action: str, payload: dict, regenerate: bool = True) -> dict:
        with self.lock:
            before = self._snapshot()
            if payload.get("revision") != self._revision(before):
                raise OperationConflict("目录或文件已被外部修改，请刷新后重试")
            if action == "undo":
                return self._undo(before)
            moves, create, focus, label, originals = self._plan(action, payload, before)
            self._validate_moves(moves, create=create, snapshot=before)
            source_signatures = {source: self._tree_signature(source) for source, _ in moves}
            changes, references = self._prepare_references(before, moves, include_summary=not regenerate) if moves else ({}, 0)
            if self._snapshot() != before or any(
                self._tree_signature(path) != signature for path, signature in source_signatures.items()
            ):
                raise OperationConflict("准备操作期间文件发生变化，请刷新后重试")
            committed, after = self._commit(moves, changes, create=create, regenerate=regenerate)
            self.undo_record = UndoRecord(moves, committed, create, after, label,
                                          [path for path in originals if path is not None])
            result = self._state(after["snapshot"])
            result.update({
                "focusPaths": [path.relative_to(self.root).as_posix() for path in focus],
                "summary": {"message": f"{label}完成", "updatedReferences": references,
                            "changedFiles": len(committed), "movedItems": len(originals) if not create else 0,
                            "renumberedItems": sum(source not in originals for source, _ in moves)},
            })
            return result

    def _undo(self, before: dict) -> dict:
        record = self.undo_record
        if record is None:
            raise OperationConflict("没有可撤销的操作")
        for path_string, signature in record.after["trees"].items():
            path = Path(path_string)
            if not path.exists() or path.is_symlink() or self._tree_signature(path) != signature:
                raise OperationConflict("操作后的文件或目录已被外部修改，无法安全撤销")
        for path, (_, expected) in record.changes.items():
            if self._read_optional(path) != expected:
                raise OperationConflict(f"文件已被外部修改，无法撤销：{path.relative_to(self.root)}")
        reverse = [(destination, source) for source, destination in reversed(record.moves)]
        self._validate_moves(reverse, remove=record.created_directory, snapshot=before)
        readme = record.created_directory / "README.md" if record.created_directory else None
        changes = {
            (path if path == readme else map_moved_path(path, reverse)): (updated, original)
            for path, (original, updated) in record.changes.items()
        }
        if self._snapshot() != before:
            raise OperationConflict("准备撤销期间文件发生变化，请刷新后重试")
        _, after = self._commit(reverse, changes, remove=record.created_directory, regenerate=False)
        self.undo_record = None
        result = self._state(after["snapshot"])
        result.update({
            "focusPaths": [path.relative_to(self.root).as_posix() for path in record.focus],
            "summary": {"message": f"已撤销：{record.label}", "updatedReferences": 0,
                        "changedFiles": len(changes), "movedItems": len(reverse)},
        })
        return result


def create_ui_server(root: Path, config: dict[str, list[str]], port: int = 8765) -> ThreadingHTTPServer:
    manager = FileManager(root, config)
    token = secrets.token_urlsafe(32)
    static_files = {
        "/": ("index.html", "text/html; charset=utf-8"),
        "/index.html": ("index.html", "text/html; charset=utf-8"),
        "/app.js": ("app.js", "text/javascript; charset=utf-8"),
        "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    }

    class Handler(BaseHTTPRequestHandler):
        server_version = "EffectiveBlog"

        def log_message(self, format: str, *args) -> None:
            # 不记录令牌、文件名或请求正文。
            pass

        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy",
                             "default-src 'self'; script-src 'self'; style-src 'self'; "
                             "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; "
                             "base-uri 'none'; form-action 'self'")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, status: int, value: dict) -> None:
            self._send(status, json.dumps(value, ensure_ascii=False).encode(), "application/json; charset=utf-8")

        def _authorized(self, api: bool = False, write: bool = False) -> bool:
            authority = f"127.0.0.1:{self.server.server_port}"
            if self.headers.get("Host") != authority:
                self._json(403, {"error": "仅允许通过本机地址访问"})
                return False
            origin = self.headers.get("Origin")
            if (origin is not None and origin != f"http://{authority}") or (write and origin is None):
                self._json(403, {"error": "请求来源不受信任"})
                return False
            if self.headers.get("Sec-Fetch-Site") == "cross-site":
                self._json(403, {"error": "不允许跨站访问"})
                return False
            supplied = self.headers.get("X-EB-Token", "")
            if api and (not supplied.isascii() or not secrets.compare_digest(supplied, token)):
                self._json(403, {"error": "会话已失效，请重新打开页面"})
                return False
            return True

        def do_GET(self) -> None:
            path = urlsplit(self.path).path
            if not self._authorized(api=path.startswith("/api/")):
                return
            try:
                if path == "/api/state":
                    self._json(200, manager.state())
                elif path in static_files:
                    name, mime = static_files[path]
                    content = (TOOL_DIRECTORY / "ui" / name).read_bytes()
                    if name == "index.html":
                        content = content.replace(b"__EB_SESSION_TOKEN__", token.encode())
                    self._send(200, content, mime)
                else:
                    self._json(404, {"error": "页面不存在"})
            except (OSError, ValueError, RuntimeError) as error:
                self._json(500, {"error": str(error)})

        def do_POST(self) -> None:
            if not self._authorized(api=True, write=True):
                return
            path = urlsplit(self.path).path
            if path not in {"/api/rename", "/api/move", "/api/mkdir", "/api/undo"}:
                self._json(404, {"error": "操作不存在"})
                return
            try:
                if self.headers.get_content_type() != "application/json":
                    raise ValueError("请求必须使用 application/json")
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 1024 * 1024:
                    raise ValueError("请求正文为空或超过 1 MB")
                if self.headers.get("Transfer-Encoding"):
                    raise ValueError("不支持分块请求")
                self.connection.settimeout(10)
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(payload, dict):
                    raise ValueError("请求正文必须是 JSON 对象")
                self._json(200, manager.operate(path.rsplit("/", 1)[-1], payload))
            except OperationConflict as error:
                self._json(409, {"error": str(error)})
            except (ValueError, UnicodeError) as error:
                self._json(400, {"error": str(error)})
            except (OSError, RuntimeError) as error:
                self._json(500, {"error": str(error)})

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    # 关闭时等待进行中的事务完成，不在写文件途中结束工作线程。
    server.daemon_threads = False
    server.manager = manager
    return server


def serve_ui(root: Path, config: dict[str, list[str]], port: int, open_browser: bool) -> None:
    try:
        server = create_ui_server(root, config, port)
    except OSError as error:
        raise RuntimeError(f"无法启动本地服务：{error}。可使用 --port 指定其他端口。") from error
    url = f"http://127.0.0.1:{server.server_port}"
    print(f"Markdown 目录管理：{url}\n管理目录：{root}\n按 Ctrl+C 停止服务。", flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n正在停止服务，等待文件操作完成……", flush=True)
    finally:
        server.server_close()


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="生成 EffectiveBlog 目录，并维护 Markdown 文档与本地图片。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例：
  python3 eb_tool/eb_tool.py --ui
  python3 eb_tool/eb_tool.py --ui --port 8766 --no-browser
  python3 eb_tool/eb_tool.py --clean_img --dry-run
  python3 eb_tool/eb_tool.py --clean_img --delete
  python3 eb_tool/eb_tool.py --gen
  python3 eb_tool/eb_tool.py --format_img
  python3 eb_tool/eb_tool.py --move_md "旧目录/文档.md" "新目录"
  python3 eb_tool/eb_tool.py --move_md "目录/旧名称.md" "目录/新名称.md"

配置：
  工具始终读取脚本同目录下的 eb_config.json；--root 只改变管理目录。
  - img_ignore：--clean_img、--format_img 和 --move_md 使用的忽略规则数组
  - gen_ignore：--gen 按名称过滤的字符串数组
""",
    )
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--ui", action="store_true", help="启动本地 Markdown 目录管理界面")
    actions.add_argument(
        "--clean_img",
        action="store_true",
        help="扫描 Markdown 图片引用，并预览或删除未引用图片",
    )
    actions.add_argument(
        "--gen",
        action="store_true",
        help="递归生成根目录中的 SUMMARY.md",
    )
    actions.add_argument(
        "--format_img",
        action="store_true",
        help="集中、重命名本地图片并更新 Markdown 引用",
    )
    actions.add_argument(
        "--move_md",
        nargs=2,
        type=Path,
        metavar=("SOURCE", "DESTINATION"),
        help="移动或重命名 Markdown 文件，自动处理编号并更新文档引用",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="扫描根目录（默认：eb_tool 文件夹的上一级）",
    )
    parser.add_argument("--port", type=int, default=8765, help="--ui 本地端口（默认 8765）")
    parser.add_argument("--no-browser", action="store_true", help="--ui 启动后不自动打开浏览器")
    parser.add_argument(
        "--show-referenced",
        action="store_true",
        help="--clean_img 同时列出已被引用且实际存在的图片",
    )
    deletion_mode = parser.add_mutually_exclusive_group()
    deletion_mode.add_argument(
        "--delete",
        action="store_true",
        help="--clean_img 跳过交互确认，直接删除未引用图片",
    )
    deletion_mode.add_argument(
        "--dry-run",
        action="store_true",
        help="--clean_img 仅预览，不询问也不删除图片",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="--clean_img 关闭进度显示",
    )
    return parser


def clean_images(root: Path, ignores: IgnoreMatcher, args: argparse.Namespace) -> int:
    try:
        markdown_files, referenced_images, unused_images, missing_references = scan_repository(
            root, ignores, show_progress=not args.no_progress
        )
    except (OSError, RuntimeError) as error:
        print(f"错误：扫描未完成，不会删除任何文件：{error}", file=sys.stderr)
        return 2

    try:
        image_sizes = collect_file_sizes(unused_images)
    except RuntimeError as error:
        print(f"错误：统计未完成，不会删除任何文件：{error}", file=sys.stderr)
        return 2
    total_unused_size = sum(image_sizes.values())

    if args.show_referenced:
        display_paths("已引用图片", referenced_images, root)
    display_paths("未引用图片", unused_images, root)
    if missing_references:
        display_paths("引用存在但文件缺失", missing_references, root)

    print(
        f"\n扫描完成：Markdown {len(markdown_files)} 个，图片 {len(referenced_images) + len(unused_images)} 个，"
        f"已引用 {len(referenced_images)} 个，未引用 {len(unused_images)} 个，缺失引用 {len(missing_references)} 个。"
    )
    print(
        f"待删除：{len(unused_images)} 张图片，预计释放 {format_file_size(total_unused_size)}。"
    )

    if not unused_images:
        print("没有未引用图片，无需删除。")
        return 0

    if args.dry_run:
        print("当前为预览模式，不会删除任何图片。")
        return 0

    if not args.delete and not confirm_deletion():
        if sys.stdin.isatty():
            print("未确认，已取消删除。")
        return 0

    failures = 0
    deleted_size = 0
    deletion_errors: list[tuple[Path, OSError]] = []
    images_to_delete = sorted(unused_images)
    progress = ProgressDisplay("删除未引用图片", len(images_to_delete), not args.no_progress)
    for completed, image_file in enumerate(images_to_delete, start=1):
        try:
            image_file.unlink()
            deleted_size += image_sizes[image_file]
        except OSError as error:
            failures += 1
            deletion_errors.append((image_file, error))
        progress.update(completed)
    progress.close()

    for image_file, error in deletion_errors:
        print(f"删除失败：{image_file}: {error}", file=sys.stderr)

    deleted = len(unused_images) - failures
    print(
        f"删除完成：成功 {deleted} 张，释放约 {format_file_size(deleted_size)}，"
        f"失败 {failures} 张。"
    )
    return 1 if failures else 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    root = args.root.expanduser().resolve()
    if not root.is_dir():
        print(f"错误：扫描根目录不存在或不是目录：{root}", file=sys.stderr)
        return 2

    if not args.ui and (args.port != 8765 or args.no_browser):
        parser.error("--port 和 --no-browser 只能与 --ui 一起使用")
    if args.ui and not 0 <= args.port <= 65535:
        parser.error("--port 必须在 0 到 65535 之间（0 表示自动选择可用端口）")

    if not args.clean_img and (
        args.show_referenced or args.delete or args.dry_run or args.no_progress
    ):
        parser.error(
            "--show-referenced、--delete、--dry-run 和 --no-progress 只能与 "
            "--clean_img 一起使用"
        )

    try:
        config = load_config()
        if args.ui:
            serve_ui(root, config, args.port, not args.no_browser)
            return 0
        if args.gen:
            generate_summary(root, config["gen_ignore"])
            return 0

        ignores = load_ignore_matcher(config["img_ignore"])
        if args.format_img:
            format_images(root, ignores)
            return 0
        if args.move_md:
            move_markdown_file(root, ignores, args.move_md[0], args.move_md[1])
            return 0
        return clean_images(root, ignores, args)
    except (OSError, RuntimeError, ValueError) as error:
        print(f"错误：{error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
