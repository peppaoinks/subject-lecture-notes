#!/usr/bin/env python3
"""Build a local, dependency-free reader from structured chapter data."""
import argparse
import json
import re
from pathlib import Path


def validate(data):
    if not isinstance(data, dict) or not isinstance(data.get("title"), str):
        raise ValueError("阅读版需要字符串title")
    chapters = data.get("chapters")
    if not isinstance(chapters, list) or not chapters:
        raise ValueError("阅读版至少包含一个章节")
    seen = set()
    for chapter in chapters:
        if not isinstance(chapter, dict):
            raise ValueError("章节需要对象")
        ident = chapter.get("id", "")
        if not isinstance(ident, str) or not re.fullmatch(r"[a-z0-9-]+", ident) or ident in seen:
            raise ValueError("章节id必须唯一且只含小写字母、数字、连字符")
        seen.add(ident)
        if not isinstance(chapter.get("title"), str):
            raise ValueError("章节需要title")
        for key in ("source", "previous", "revision_note"):
            if key in chapter and not isinstance(chapter[key], str):
                raise ValueError(f"{key}需要字符串")
        sections = chapter.get("sections")
        if not isinstance(sections, list) or not sections:
            raise ValueError("章节至少包含一节")
        for section in sections:
            if not isinstance(section, dict) or not isinstance(section.get("title"), str):
                raise ValueError("小节需要title")
            for key in ("equation", "source", "code"):
                if key in section and not isinstance(section[key], str):
                    raise ValueError(f"{key}需要字符串")
            paragraphs = section.get("paragraphs", [])
            if not isinstance(paragraphs, list) or not all(isinstance(x, str) for x in paragraphs):
                raise ValueError("paragraphs需要字符串列表")
            exercises = section.get("exercises", [])
            if not isinstance(exercises, list):
                raise ValueError("exercises需要列表")
            for exercise in exercises:
                if not isinstance(exercise, dict) or not all(
                    isinstance(exercise.get(k), str) for k in ("question", "answer")
                ):
                    raise ValueError("习题需要question和answer字符串")


def build(input_path, output_path):
    data = json.loads(Path(input_path).read_text(encoding="utf-8"))
    validate(data)
    target = Path(output_path)
    if target.resolve() == Path(input_path).resolve():
        raise ValueError("不能用HTML覆盖输入资料")
    template = Path(__file__).resolve().parent.parent / "assets" / "reader-template.html"
    payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(template.read_text(encoding="utf-8").replace("__LECTURE_DATA__", payload),
                      encoding="utf-8")
    return target


def main():
    parser = argparse.ArgumentParser(description="生成单文件讲义阅读版")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        print(build(args.input, args.output))
    except (ValueError, OSError, TypeError) as error:
        parser.exit(1, f"未生成：{error}\n")


if __name__ == "__main__":
    main()
