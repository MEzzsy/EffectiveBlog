#!/usr/bin/env python3
"""扫描 Markdown 中的本地图片引用，并清理未被引用的图片文件。"""

from __future__ import annotations

import argparse
import fnmatch
import html
from html.parser import HTMLParser
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


def load_ignore_matcher(ignore_file: Path | None) -> IgnoreMatcher:
    # 版本控制元数据和 Python 缓存永远不应当成为扫描或删除目标。
    patterns = [".git/", ".hg/", ".svn/", "__pycache__/"]
    if ignore_file is not None:
        try:
            lines = ignore_file.read_text(encoding="utf-8-sig").splitlines()
        except OSError as error:
            raise ValueError(f"无法读取 ignore 文件 {ignore_file}: {error}") from error

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("!"):
                raise ValueError(
                    f"ignore 文件暂不支持取反规则：{line!r}；请直接删除该行"
                )
            patterns.append(line)

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


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="识别 Markdown 引用的本地图片，并预览或删除未引用的图片。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例：
  python3 clean_unused_images.py --ignore-file ignoredFile
  python3 clean_unused_images.py --ignore-file ignoredFile --show-referenced
  python3 clean_unused_images.py --ignore-file ignoredFile --dry-run
  python3 clean_unused_images.py --ignore-file ignoredFile --delete

ignore 文件说明：
  - 每行一条相对于扫描根目录的规则；空行和以 # 开头的行会被忽略
  - 可写文件、目录或 glob，例如 docs/、draft.md、**/generated/*.png
  - 暂不支持以 ! 开头的取反规则
""",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="扫描根目录（默认：本工具所在目录）",
    )
    parser.add_argument(
        "--ignore-file",
        type=Path,
        help="ignore 规则文件；相对路径按当前工作目录解析",
    )
    parser.add_argument(
        "--show-referenced",
        action="store_true",
        help="同时列出已被 Markdown 引用且实际存在的图片",
    )
    deletion_mode = parser.add_mutually_exclusive_group()
    deletion_mode.add_argument(
        "--delete",
        action="store_true",
        help="跳过交互确认，直接删除未引用图片",
    )
    deletion_mode.add_argument(
        "--dry-run",
        action="store_true",
        help="仅预览，不询问也不删除图片",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="关闭进度显示",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    root = args.root.expanduser().resolve()
    if not root.is_dir():
        print(f"错误：扫描根目录不存在或不是目录：{root}", file=sys.stderr)
        return 2

    ignore_file = args.ignore_file
    if ignore_file is not None:
        ignore_file = ignore_file.expanduser().resolve()
        if not ignore_file.is_file():
            print(f"错误：ignore 文件不存在或不是文件：{ignore_file}", file=sys.stderr)
            return 2

    try:
        ignores = load_ignore_matcher(ignore_file)
    except ValueError as error:
        print(f"错误：{error}", file=sys.stderr)
        return 2

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


if __name__ == "__main__":
    raise SystemExit(main())
