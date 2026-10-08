#!/usr/bin/env python3
"""Standard-library helpers for lecture state, snapshots, and experiment reuse."""
import argparse
import difflib
import hashlib
import json
import re
import shutil
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

STAGES = ("计划中", "草稿", "内容已核对", "排版已核对", "已交付")
ASSETS = Path(__file__).resolve().parent.parent / "assets"


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                     delete=False) as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        temporary = Path(stream.name)
    temporary.replace(path)


def read_json(path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def project_file(root, name, required=True):
    rel = Path(name)
    if rel.is_absolute() or ".." in rel.parts or not rel.parts or rel.parts[0] == ".lecture":
        raise ValueError("文件须为项目内的相对路径，不能指向内部快照")
    path = root / rel
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("文件解析后位于项目之外")
    if required and not path.is_file():
        raise ValueError(f"文件不存在：{name}")
    return path


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def hashes(root, names):
    return {name: digest(project_file(root, name)) for name in names}


def state_path(root):
    return root / ".lecture" / "state.json"


def load_state(root):
    return read_json(state_path(root), {"schema_version": 1, "chapters": {}, "caches": {}})


def manifest(root, snapshot):
    if not re.fullmatch(r"[a-f0-9]{12}", snapshot):
        raise ValueError("快照编号格式错误")
    folder = root / ".lecture" / "snapshots" / snapshot
    if not (folder / "manifest.json").is_file():
        raise ValueError("找不到该快照")
    data = read_json(folder / "manifest.json")
    for name, expected in data["files"].items():
        project_file(root, name, required=False)
        saved = folder / "files" / name
        if not saved.is_file() or digest(saved) != expected:
            raise ValueError(f"快照文件损坏：{name}")
    return folder, data


def run(args):
    root = Path(args.project).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    if args.command == "init":
        copied = []
        for asset, output in (("project-brief.md", "讲义编写约定.md"),
                              ("style-preferences.md", "排版偏好.md")):
            target = root / output
            if not target.exists():
                shutil.copyfile(ASSETS / asset, target)
                copied.append(output)
        if not state_path(root).exists():
            write_json(state_path(root), load_state(root))
        return {"project": str(root), "created": copied, "existing_files_preserved": True}

    state = load_state(root)
    if args.command == "progress":
        if args.chapter:
            if not args.stage:
                raise ValueError("更新章节需要提供阶段")
            previous = state["chapters"].get(args.chapter, {})
            state["chapters"][args.chapter] = {
                "title": args.title or previous.get("title", args.chapter),
                "stage": args.stage, "next": args.next or "", "updated_at": timestamp(),
                "evidence": args.evidence or "未附证据；状态由操作者按实际检查记录",
            }
            write_json(state_path(root), state)
        elif args.stage:
            raise ValueError("更新阶段需要指定章节")
        return state["chapters"]

    if args.command == "checkpoint":
        entries = hashes(root, args.files)
        snapshot = uuid.uuid4().hex[:12]
        folder = root / ".lecture" / "snapshots" / snapshot
        for name in entries:
            dest = folder / "files" / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(project_file(root, name), dest)
        data = {"id": snapshot, "created_at": timestamp(), "note": args.note, "files": entries}
        write_json(folder / "manifest.json", data)
        return data

    if args.command in ("diff", "restore-preview"):
        folder, saved = manifest(root, args.snapshot)
        if args.command == "restore-preview":
            dest_root = root / ("恢复预览-" + args.snapshot)
            if dest_root.exists():
                raise ValueError("恢复预览已存在，请先检查已有预览")
            for name in saved["files"]:
                dest = dest_root / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(folder / "files" / name, dest)
            return {"preview": str(dest_root), "current_files_unchanged": True}
        output = []
        for name, old_hash in saved["files"].items():
            now = project_file(root, name, required=False)
            if now.is_file() and digest(now) == old_hash:
                continue
            old = (folder / "files" / name).read_bytes()
            new = now.read_bytes() if now.is_file() else b""
            try:
                if b"\0" in old or b"\0" in new:
                    raise UnicodeError()
                changes = "".join(difflib.unified_diff(
                    old.decode("utf-8").splitlines(True), new.decode("utf-8").splitlines(True),
                    fromfile="快照/" + name, tofile="当前/" + name))
            except UnicodeError:
                changes = f"二进制文件变化：{name}（{len(old)} → {len(new)}字节）"
            output.append({"file": name, "diff": changes, "deleted": not now.exists()})
        return output

    if args.command == "cache-record":
        record = {"inputs": hashes(root, args.files), "outputs": hashes(root, args.outputs),
                  "environment": args.environment, "recorded_at": timestamp()}
        state["caches"][args.name] = record
        write_json(state_path(root), state)
        return {"name": args.name, "record": record}
    if args.command == "cache-check":
        record = state["caches"].get(args.name)
        if not record:
            return {"reusable": False, "reason": "尚无已运行结果记录"}
        if record["environment"] != args.environment:
            return {"reusable": False, "reason": "环境标识已变化"}
        for kind in ("inputs", "outputs"):
            for name, expected in record[kind].items():
                path = project_file(root, name, required=False)
                if not path.is_file() or digest(path) != expected:
                    return {"reusable": False, "reason": f"{kind}文件缺失或变化：{name}"}
        return {"reusable": True, "reason": "所记录输入、输出与环境标识一致"}
    raise ValueError("未知操作")


def main():
    parser = argparse.ArgumentParser(description="讲义状态、快照与实验结果复用")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "progress", "checkpoint", "diff", "restore-preview",
                 "cache-record", "cache-check"):
        cmd = commands.add_parser(name)
        cmd.add_argument("--project", required=True)
        if name == "progress":
            cmd.add_argument("--chapter")
            cmd.add_argument("--title")
            cmd.add_argument("--stage", choices=STAGES)
            cmd.add_argument("--next")
            cmd.add_argument("--evidence")
        elif name == "checkpoint":
            cmd.add_argument("--files", nargs="+", required=True)
            cmd.add_argument("--note", default="")
        elif name in ("diff", "restore-preview"):
            cmd.add_argument("--snapshot", required=True)
        elif name in ("cache-record", "cache-check"):
            cmd.add_argument("--name", required=True)
            cmd.add_argument("--environment", required=True)
            if name == "cache-record":
                cmd.add_argument("--files", nargs="+", required=True)
                cmd.add_argument("--outputs", nargs="+", required=True)
    try:
        print(json.dumps(run(parser.parse_args()), ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f"未完成：{error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
