#!/usr/bin/env python3
"""EffectiveBlog 的目录与图片维护工具。"""

from __future__ import annotations

import argparse
import fnmatch
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sys
from typing import Iterable, Sequence
from urllib.parse import unquote, urlsplit


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


def load_config(root: Path) -> dict[str, list[str]]:
    """读取并校验根目录中的工具配置。"""
    config_file = root / CONFIG_FILE_NAME
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
    return f"[{escape_markdown_label(label)}](./{relative_path})"


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
            has_readme = readme.is_file()
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


def generate_summary(root: Path, configured_ignores: Iterable[str]) -> None:
    ignored_names = {name for name in configured_ignores if name}
    lines = ["# Summary", ""]
    root_readme = root / "README.md"
    if root_readme.is_file():
        # 保留现有 SUMMARY.md 对根 README 的展示名称。
        lines.append(f"- {summary_link('00 介绍', root_readme, root)}")
    lines.extend(collect_summary_entries(root, root, ignored_names, 0))
    content = "\n".join(lines).rstrip() + "\n"

    summary_file = root / SUMMARY_FILE_NAME
    try:
        summary_file.write_text(content, encoding="utf-8")
    except OSError as error:
        raise RuntimeError(f"无法写入 {summary_file}：{error}") from error
    entry_count = sum(1 for line in lines if line.lstrip().startswith("- "))
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


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="生成 EffectiveBlog 目录，并维护 Markdown 使用的本地图片。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例：
  python3 eb_tool.py --clean_img --dry-run
  python3 eb_tool.py --clean_img --delete
  python3 eb_tool.py --gen
  python3 eb_tool.py --format_img

配置：
  工具读取扫描根目录下的 eb_config.json。
  - img_ignore：--clean_img 和 --format_img 使用的忽略规则数组
  - gen_ignore：--gen 按名称过滤的字符串数组
""",
    )
    actions = parser.add_mutually_exclusive_group(required=True)
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
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="扫描根目录（默认：本工具所在目录）",
    )
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

    if not args.clean_img and (
        args.show_referenced or args.delete or args.dry_run or args.no_progress
    ):
        parser.error(
            "--show-referenced、--delete、--dry-run 和 --no-progress 只能与 "
            "--clean_img 一起使用"
        )

    try:
        config = load_config(root)
        if args.gen:
            generate_summary(root, config["gen_ignore"])
            return 0

        ignores = load_ignore_matcher(config["img_ignore"])
        if args.format_img:
            format_images(root, ignores)
            return 0
        return clean_images(root, ignores, args)
    except (OSError, RuntimeError, ValueError) as error:
        print(f"错误：{error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
