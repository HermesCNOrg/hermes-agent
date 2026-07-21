#!/usr/bin/env python3
"""Maintain Simplified Chinese docs inside a full Hermes Agent fork.

The fork follows upstream through normal Git merges. This tool only tracks the
relationship between website/docs and Docusaurus' zh-Hans translation tree.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DOC_SUFFIXES = {".md", ".mdx"}
STATE_RELATIVE = Path("website/translation/zh-Hans-state.json")
QUEUE_RELATIVE = Path("website/translation/zh-Hans-queue.json")
ZH_RELATIVE = Path("website/i18n/zh-Hans/docusaurus-plugin-content-docs/current")
ACTIONABLE = {"missing", "needs_update", "needs_review", "draft"}
FENCE_RE = re.compile(r"^```", re.MULTILINE)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path, default: Any) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def docs_at(root: Path) -> dict[str, Path]:
    if not root.exists():
        return {}
    return {
        p.relative_to(root).as_posix(): p
        for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in DOC_SUFFIXES
    }


def refresh_state(repo_root: Path, upstream_commit: str) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    source_root = repo_root / "website/docs"
    zh_root = repo_root / ZH_RELATIVE
    state_path = repo_root / STATE_RELATIVE
    previous = read_json(state_path, {"documents": {}})
    previous_docs = previous.get("documents", {})
    source_docs = docs_at(source_root)
    translations = docs_at(zh_root)
    removed = sorted(set(previous_docs) - set(source_docs))

    for rel in removed:
        translation = translations.get(rel)
        if translation and translation.exists():
            archive = repo_root / "website/translation/archive" / upstream_commit / rel
            archive.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(translation), str(archive))

    documents: dict[str, dict[str, Any]] = {}
    changed: list[str] = []
    for rel, source in sorted(source_docs.items()):
        source_hash = digest(source)
        old = previous_docs.get(rel, {})
        old_source_hash = old.get("source_sha256")
        translation = zh_root / rel
        translation_hash = digest(translation) if translation.exists() else None
        if old_source_hash and old_source_hash != source_hash:
            changed.append(rel)

        if not translation_hash:
            status = "missing"
        elif not old:
            status = "needs_review"
        elif old_source_hash != source_hash:
            status = "needs_update"
        elif old.get("translation_sha256") != translation_hash:
            status = "draft"
        else:
            status = old.get("status", "needs_review")

        documents[rel] = {
            "source_sha256": source_hash,
            "translation_sha256": translation_hash,
            "status": status,
            "source_commit": upstream_commit,
        }
        if status == "approved":
            for key in ("reviewed_by", "reviewed_at"):
                if key in old:
                    documents[rel][key] = old[key]

    state = {
        "upstream": "NousResearch/hermes-agent",
        "upstream_commit": upstream_commit,
        "refreshed_at": datetime.now(timezone.utc).isoformat(),
        "documents": documents,
    }
    counts = dict(sorted(Counter(item["status"] for item in documents.values()).items()))
    report = {"upstream_commit": upstream_commit, "changed": changed, "removed": removed, "counts": counts}
    write_json(state_path, state)
    return report


def priority(path: str) -> tuple[int, str]:
    if "/skills/" in path or path.endswith(("skills-catalog.md", "skills-catalog.mdx")):
        return 3, "generated-skills"
    if path.startswith("getting-started/") or path in {
        "user-guide/cli.md", "user-guide/tui.md", "user-guide/configuration.md"
    }:
        return 0, "getting-started"
    if path.startswith(("user-guide/", "reference/")):
        return 1, "user-guide"
    return 2, "developer-and-guides"


def build_queue(state: dict[str, Any], include_generated: bool = False) -> list[dict[str, str]]:
    queue: list[dict[str, str]] = []
    for path, item in state.get("documents", {}).items():
        if item.get("status") not in ACTIONABLE:
            continue
        rank, tier = priority(path)
        if rank == 3 and not include_generated:
            continue
        queue.append({"path": path, "status": item["status"], "priority": f"P{rank}", "tier": tier})
    return sorted(queue, key=lambda item: (item["priority"], item["status"] != "needs_update", item["path"]))


def filter_queue(queue: list[dict[str, str]], changed_paths: list[str]) -> list[dict[str, str]]:
    """Keep only docs changed by the current upstream synchronization."""
    prefix = "website/docs/"
    normalized = {
        path.strip().replace("\\", "/")[len(prefix):]
        if path.strip().replace("\\", "/").startswith(prefix)
        else path.strip().replace("\\", "/")
        for path in changed_paths
        if path.strip()
    }
    return [item for item in queue if item["path"] in normalized]


def validate(repo_root: Path, strict: bool = False) -> int:
    state = read_json(repo_root / STATE_RELATIVE, {"documents": {}})
    source_root = repo_root / "website/docs"
    zh_root = repo_root / ZH_RELATIVE
    errors: list[str] = []
    warnings: list[str] = []
    for rel, item in state["documents"].items():
        source, target = source_root / rel, zh_root / rel
        status = item["status"]
        if not target.exists():
            warnings.append(f"{rel}: missing")
            continue
        source_text, target_text = source.read_text(encoding="utf-8"), target.read_text(encoding="utf-8")
        structural: list[str] = []
        if len(FENCE_RE.findall(source_text)) % 2 != len(FENCE_RE.findall(target_text)) % 2:
            structural.append("unbalanced fenced code blocks")
        if source_text.startswith("---\n") != target_text.startswith("---\n"):
            structural.append("front matter presence differs")
        for problem in structural:
            (errors if status in {"draft", "approved"} else warnings).append(f"{rel}: {problem}")
        if status in {"needs_update", "needs_review", "draft"}:
            warnings.append(f"{rel}: {status}")
    for item in errors:
        print(f"ERROR {item}")
    for item in warnings[:50]:
        print(f"WARN  {item}")
    if len(warnings) > 50:
        print(f"WARN  ... {len(warnings) - 50} additional warnings omitted")
    print(f"Checked {len(state['documents'])} documents: {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors or (strict and warnings) else 0


def git_upstream_commit(repo_root: Path) -> str:
    for ref in ("upstream/main", "HEAD"):
        result = subprocess.run(["git", "rev-parse", ref], cwd=repo_root, text=True, capture_output=True)
        if result.returncode == 0:
            return result.stdout.strip()
    raise RuntimeError("Cannot determine Git commit")


def hermes_subprocess_env(repo_root: Path) -> dict[str, str]:
    """Pin nested Hermes file and terminal tools to the requested repository."""
    env = os.environ.copy()
    env["TERMINAL_CWD"] = str(repo_root.resolve())
    return env


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    sub = parser.add_subparsers(dest="command", required=True)
    refresh = sub.add_parser("refresh")
    refresh.add_argument("--commit")
    queue_cmd = sub.add_parser("queue")
    queue_cmd.add_argument("--include-generated", action="store_true")
    queue_cmd.add_argument("--limit", type=int, default=0)
    queue_cmd.add_argument("--output", type=Path)
    mark = sub.add_parser("mark")
    mark.add_argument("--reviewer", required=True)
    mark.add_argument("paths", nargs="+")
    check = sub.add_parser("validate")
    check.add_argument("--strict", action="store_true")
    translate = sub.add_parser("translate")
    translate.add_argument("--limit", type=int, default=0, help="0 translates every selected document")
    translate.add_argument("--include-generated", action="store_true")
    translate.add_argument("--paths-file", type=Path, help="Only translate docs listed in this newline-delimited file")
    translate.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = args.repo.resolve()
    state_path = root / STATE_RELATIVE

    if args.command == "refresh":
        report = refresh_state(root, args.commit or git_upstream_commit(root))
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    if args.command == "queue":
        queue = build_queue(read_json(state_path, {"documents": {}}), args.include_generated)
        if args.limit:
            queue = queue[: args.limit]
        output = args.output or root / QUEUE_RELATIVE
        write_json(output, queue)
        print(json.dumps(queue, ensure_ascii=False, indent=2))
        return 0
    if args.command == "mark":
        state = read_json(state_path, {"documents": {}})
        now = datetime.now(timezone.utc).isoformat()
        for rel in args.paths:
            target = root / ZH_RELATIVE / rel
            if rel not in state["documents"] or not target.exists():
                raise SystemExit(f"Unknown or missing translation: {rel}")
            state["documents"][rel].update({
                "translation_sha256": digest(target), "status": "approved",
                "reviewed_by": args.reviewer, "reviewed_at": now,
            })
        write_json(state_path, state)
        print(f"Approved {len(args.paths)} translation(s).")
        return 0
    if args.command == "validate":
        return validate(root, args.strict)
    if args.command == "translate":
        queue = build_queue(read_json(state_path, {"documents": {}}), args.include_generated)
        if args.paths_file:
            changed_paths = args.paths_file.read_text(encoding="utf-8").splitlines()
            queue = filter_queue(queue, changed_paths)
        if args.limit:
            queue = queue[: args.limit]
        if not queue:
            print("No changed English documents require translation.")
            return 0
        for index, item in enumerate(queue, 1):
            rel = item["path"]
            print(f"[{index}/{len(queue)}] {rel} ({item['status']})")
            if args.dry_run:
                continue
            prompt = f"""Read website/TRANSLATING_ZH.md. Translate website/docs/{rel} into high-quality Simplified Chinese at website/i18n/zh-Hans/docusaurus-plugin-content-docs/current/{rel}. Preserve front matter keys, MDX/JSX, code, commands, URLs, anchors, admonitions, and structure. Compare the existing Chinese file when present. Edit the destination in place and verify Markdown fences before finishing."""
            subprocess.run(
                ["hermes", "--yolo", "chat", "--toolsets", "file", "--query", prompt],
                cwd=root,
                env=hermes_subprocess_env(root),
                check=True,
            )
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
