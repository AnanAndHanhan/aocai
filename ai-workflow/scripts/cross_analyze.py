#!/usr/bin/env python3
"""Run Qwen3 multi-source cross analysis from brief.md."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from common import (
    PROJECT_ROOT,
    ensure_run_dirs,
    fail,
    load_models_config,
    load_workflow_config,
    log_line,
    ollama_generate,
    read_project_file,
    read_prompt,
    write_json,
    write_text,
)


PROJECT_DOCS = ["PROJECT_HANDOFF.md", "基础资料.md", "决策记录.md"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local Qwen3 multi-source analysis from brief.md.")
    parser.add_argument("--period", required=True, help="Period id, for example 2026-178.")
    parser.add_argument("--run-id", default=None, help="Run id. Defaults to --period.")
    parser.add_argument("--brief", default=None, help="Optional explicit brief.md path.")
    parser.add_argument("--note", default="", help="Optional user note.")
    return parser.parse_args()


def load_brief(run_id: str, explicit_path: str | None) -> tuple[Path, str]:
    path = Path(explicit_path).expanduser().resolve() if explicit_path else PROJECT_ROOT / "ai-workflow/cache" / run_id / "brief.md"
    if not path.exists():
        fail(f"brief.md not found: {path}")
    return path, path.read_text(encoding="utf-8")


def output_dir(period: str) -> Path:
    workflow = load_workflow_config()
    base = PROJECT_ROOT / workflow["directories"].get("output", "ai-workflow/output")
    path = base / period
    path.mkdir(parents=True, exist_ok=True)
    return path


def build_prompt(period: str, brief_path: Path, brief: str, note: str) -> str:
    sections = [
        "# 系统任务",
        read_prompt("multi_source_analysis.md"),
        "",
        "# 项目文档",
    ]
    for relative in PROJECT_DOCS:
        path = PROJECT_ROOT / relative
        if not path.exists():
            fail(f"Required project file not found: {path}")
        sections.extend(
            [
                f"## {relative}",
                "```markdown",
                read_project_file(relative).strip(),
                "```",
                "",
            ]
        )
    sections.extend(
        [
            "# brief.md",
            "",
            f"- 期号：{period}",
            f"- brief 路径：{brief_path}",
            "",
            "```markdown",
            brief.strip(),
            "```",
            "",
        ]
    )
    if note.strip():
        sections.extend(["# 用户补充说明", note.strip(), ""])
    sections.extend(
        [
            "# 输出要求",
            "输出完整中文分析，必须使用固定结构。",
            "必须分别写每张资料单独指向和多资料共同指向。",
            "必须单独写上期首号降权和对冲生肖降权；末尾特码不能当作首号。",
            "必须输出主六肖、强防三肖、关键号码线索和不确定项。",
            "最终答案直接写 Markdown 正文，不要包裹 ```markdown 代码围栏。",
            "不要输出内部思考过程。",
        ]
    )
    return "\n".join(sections)


def strip_outer_markdown_fence(text: str) -> str:
    stripped = text.strip()
    match = re.fullmatch(r"```(?:markdown)?\s*(.*?)\s*```", stripped, flags=re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else stripped


def main() -> None:
    args = parse_args()
    run_id = args.run_id or args.period
    models = load_models_config()
    run_dirs = ensure_run_dirs(run_id)
    log_path = run_dirs["logs"] / "cross_analyze.log"
    brief_path, brief = load_brief(run_id, args.brief)
    prompt = build_prompt(args.period, brief_path, brief, args.note)
    prompt_path = run_dirs["cache"] / "qwen3-prompt.md"
    write_text(prompt_path, prompt)
    payload = {
        "model": models["models"]["main"],
        "prompt": prompt,
        "stream": False,
        "think": models["defaults"].get("think", False),
        "options": {
            "temperature": models["defaults"].get("temperature", 0.2),
            "top_p": models["defaults"].get("top_p", 0.9),
            "num_ctx": models["defaults"].get("num_ctx_main", 32768),
            "num_predict": 4096,
        },
    }
    log_line(log_path, f"Cross analysis started: period={args.period}, run_id={run_id}")
    raw = ollama_generate(payload, timeout=1200)
    response = strip_outer_markdown_fence(raw.get("response", ""))
    result = {
        "period": args.period,
        "run_id": run_id,
        "project_root": str(PROJECT_ROOT),
        "brief_path": str(brief_path),
        "model": models["models"]["main"],
        "response": response,
        "raw": raw,
    }
    write_json(run_dirs["cache"] / "qwen3-raw.json", result)
    final_path = output_dir(args.period) / "当期分析.md"
    output = "\n".join(
        [
            f"# {args.period} 当期分析",
            "",
            f"- Model: {models['models']['main']}",
            f"- Brief: {brief_path}",
            f"- Project: {PROJECT_ROOT}",
            "",
            response or "(empty)",
            "",
        ]
    )
    write_text(final_path, output)
    log_line(log_path, f"Cross analysis finished: {final_path}")
    print(final_path)


if __name__ == "__main__":
    main()
