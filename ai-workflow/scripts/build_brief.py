#!/usr/bin/env python3
"""Build a multi-image brief from per-image Vision extraction results."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from analyze_with_qwen3 import build_analysis_scope
from common import PROJECT_ROOT, ensure_run_dirs, extract_json_object, fail, write_json, write_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build brief.md from Vision extraction JSON.")
    parser.add_argument("--period", required=True, help="Period id, for example 2026-178.")
    parser.add_argument("--run-id", default=None, help="Vision run id. Defaults to --period.")
    parser.add_argument("--vision-json", default=None, help="Optional explicit vision_extract.json path.")
    return parser.parse_args()


def load_vision(run_id: str, explicit_path: str | None) -> dict[str, Any]:
    path = Path(explicit_path).expanduser().resolve() if explicit_path else PROJECT_ROOT / "ai-workflow/cache" / run_id / "vision_extract.json"
    if not path.exists():
        fail(f"Vision result not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def repair_vision_parsed(vision: dict[str, Any]) -> dict[str, Any]:
    repaired = json.loads(json.dumps(vision, ensure_ascii=False))
    for item in repaired.get("results", []):
        parsed = item.get("parsed")
        uncertain = parsed.get("uncertain", []) if isinstance(parsed, dict) else []
        needs_repair = (
            not isinstance(parsed, dict)
            or parsed.get("image_type") == "unknown"
            and not parsed.get("ocr_text")
            and any("not valid JSON" in str(value) for value in uncertain)
        )
        if not needs_repair:
            continue
        recovered = extract_json_object(str(item.get("raw_response", "")))
        if recovered is not None:
            recovered.setdefault("uncertain", [])
            recovered["uncertain"].append("Recovered from raw_response while building brief.")
            item["parsed"] = recovered
    return repaired


def as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def render_json_block(value: Any) -> list[str]:
    if value in (None, [], {}, ""):
        return ["无"]
    return ["```json", json.dumps(value, ensure_ascii=False, indent=2), "```"]


def render_list(values: list[Any]) -> list[str]:
    items = [str(value).strip() for value in values if str(value).strip()]
    if not items:
        return ["- 无"]
    return [f"- {item}" for item in items]


def parsed_by_index(vision: dict[str, Any]) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for item in vision.get("results", []):
        index = item.get("image_index")
        if isinstance(index, int):
            result[index] = item
    return result


def render_brief(period: str, vision: dict[str, Any], scoped: dict[str, Any]) -> str:
    original_items = parsed_by_index(vision)
    lines: list[str] = [
        "# 当期资料 Brief",
        "",
        "## 基本信息",
        "",
        f"- 期号：{period}",
        f"- Project：{PROJECT_ROOT}",
        f"- Vision Run ID：{vision.get('run_id', period)}",
        f"- 图片数量：{len(scoped.get('results', []))}",
        f"- 范围策略：{scoped.get('analysis_scope_policy', '')}",
        "",
    ]

    period_contexts = []
    for scoped_item in scoped.get("results", []):
        context = scoped_item.get("period_context") or {}
        if context.get("lines") or context.get("current_clash_text") or context.get("previous_result_text"):
            period_contexts.append({"image_index": scoped_item.get("image_index"), **context})
    lines.extend(["## 期数与降权上下文", ""])
    lines.extend(render_json_block(period_contexts))
    lines.append("")

    for scoped_item in scoped.get("results", []):
        image_index = scoped_item.get("image_index")
        original = original_items.get(image_index, {})
        parsed = original.get("parsed", {})
        lines.extend(
            [
                f"## 资料 {image_index}：{Path(str(scoped_item.get('image_path', ''))).name}",
                "",
                "### 资料类型",
                "",
                f"- Vision 类型：{scoped_item.get('image_type', 'unknown')}",
                f"- 决策类型：{scoped_item.get('decision_type', 'unknown')}",
                f"- 有效范围来源：{scoped_item.get('analysis_scope_source', '')}",
                "",
                "### 用户红框/重点区域",
                "",
            ]
        )
        lines.extend(render_json_block(scoped_item.get("analysis_scope_marked_regions")))
        lines.extend(["", "### 有效分析原文", ""])
        lines.extend(render_list(as_list(scoped_item.get("analysis_scope_text"))))
        lines.extend(["", "### 弱辅助内容（可参与交叉，不能单独压过资料主线）", ""])
        lines.extend(render_list(as_list(scoped_item.get("weak_auxiliary_scope_text"))))
        lines.extend(["", "### 原文 OCR", ""])
        lines.extend(render_list(as_list(parsed.get("ocr_text"))))
        lines.extend(["", "### 图像主体", ""])
        visual_subjects = as_list(parsed.get("visual_subjects")) + as_list(parsed.get("visual_scene"))
        lines.extend(render_list(visual_subjects))
        lines.extend(["", "### 数字线索", ""])
        lines.extend(render_json_block({"analysis_scope_numbers": scoped_item.get("analysis_scope_numbers"), "vision_numbers": parsed.get("numbers")}))
        lines.extend(["", "### 生肖/外号/五行/家野/山水线索", ""])
        lines.extend(
            [
                "- 仅允许 Qwen3 基于“有效分析原文”“图像主体”“数字线索.analysis_scope_numbers”“弱辅助内容”和项目资料自行拆解。",
                "- Vision 原始 possible_clues、zodiac_clues、number_clues 可能来自默认排除区域，不写入 brief 主权重区。",
            ]
        )
        lines.extend(["", "### 默认排除内容", ""])
        lines.extend(render_list(as_list(scoped_item.get("excluded_non_scope_reasons"))))
        lines.extend(["", "### 不确定内容", ""])
        lines.extend(render_list(as_list(scoped_item.get("uncertain")) + as_list(parsed.get("uncertain"))))
        lines.append("")

    lines.extend(
        [
            "## Brief 使用边界",
            "",
            "- 本 brief 只合并 Vision 单图事实，不做最终主六肖判断。",
            "- Qwen3 只能把“有效分析原文”和“数字线索.analysis_scope_numbers”作为主权重输入。",
            "- “弱辅助内容”可以参与交叉验证；若与多张资料、正文、图像、数字、五行、家野、山水等形成强交叉，可以进入主六肖或强防。",
            "- “弱辅助内容”不能脱离资料主线单独压过有效分析原文。",
            "- “期数与降权上下文”只用于上期首号降权、末尾特码核验和对冲生肖降权。",
            "- “默认排除内容”不得反向进入候选权重。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    run_id = args.run_id or args.period
    run_dirs = ensure_run_dirs(run_id)
    vision = repair_vision_parsed(load_vision(run_id, args.vision_json))
    scoped = build_analysis_scope(vision)
    brief = render_brief(args.period, vision, scoped)
    brief_path = run_dirs["cache"] / "brief.md"
    write_text(brief_path, brief)
    write_json(run_dirs["cache"] / "brief_scope.json", scoped)
    print(brief_path)


if __name__ == "__main__":
    main()
