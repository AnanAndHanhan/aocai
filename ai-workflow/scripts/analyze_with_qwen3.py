#!/usr/bin/env python3
"""Analyze Vision extraction results with the local Qwen3 main model."""

from __future__ import annotations

import argparse
import copy
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local Qwen3 analysis for Aucai Vision results.")
    parser.add_argument("--run-id", required=True, help="Run id created by vision_extract.py.")
    parser.add_argument("--vision-json", default=None, help="Optional path to vision_extract.json.")
    parser.add_argument("--note", default="", help="Optional user note, period info, or extra instruction.")
    parser.add_argument("--note-file", default=None, help="Optional UTF-8 text file with extra instruction.")
    return parser.parse_args()


def load_vision_result(run_id: str, explicit_path: str | None) -> dict:
    path = Path(explicit_path).expanduser().resolve() if explicit_path else PROJECT_ROOT / "ai-workflow/cache" / run_id / "vision_extract.json"
    if not path.exists():
        fail(f"Vision result not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_extra_note(note: str, note_file: str | None) -> str:
    parts = []
    if note:
        parts.append(note.strip())
    if note_file:
        path = Path(note_file).expanduser().resolve()
        if not path.exists():
            fail(f"Note file not found: {path}")
        parts.append(path.read_text(encoding="utf-8").strip())
    return "\n\n".join(part for part in parts if part)


def _as_text_list(value) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if value is None:
        return []
    return [str(value)]


def _unique_nonempty(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _region_has_manual_marker(region: dict) -> bool:
    region_text = str(region.get("region", "")).lower()
    visual_marker = str(region.get("visual_marker", "")).strip().lower()
    notes = str(region.get("notes", "")).strip().lower()
    marker_text = " ".join([region_text, visual_marker, notes])
    precise_region_keywords = [
        "框选",
        "矩形框",
        "方框",
        "边框",
        "箭头",
        "手绘",
        "黄色框",
        "荧光框",
        "outline",
        "box",
        "circle",
        "arrow",
    ]
    annotation_keywords = ["红框", "圈注", "圆圈", "标注", "框", "圈"]
    if any(keyword in marker_text for keyword in precise_region_keywords):
        return True
    if (visual_marker or notes) and any(keyword in marker_text for keyword in annotation_keywords):
        return True
    return False


def _manual_marked_regions(marked_regions: list) -> list[dict]:
    manual_regions: list[dict] = []
    for region in marked_regions:
        if isinstance(region, dict) and _region_has_manual_marker(region):
            manual_regions.append(region)
    return manual_regions


def _detect_decision_type(parsed: dict, ocr_text: list[str]) -> str:
    text = "\n".join([str(parsed.get("image_type", ""))] + ocr_text)
    if "管家婆" in text or "一句话赢大钱" in text:
        return "管家婆一句话赢大钱"
    if "澳门跑狗" in text or "跑狗图" in text or "跑狗" in text:
        return "跑狗图/澳门跑狗"
    if "跑马" in text:
        return "跑马图"
    if "澳门传真" in text:
        return "澳门传真"
    if "九肖" in text and ("30码" in text or "三十码" in text):
        return "九肖30码"
    return str(parsed.get("image_type", "unknown") or "unknown")


def _extract_guanjiapo_sentence(lines: list[str]) -> str:
    stop_pattern = re.compile(
        r"(管家婆平特玄机|平特玄机|上期回放|解[:：]|解码|号码|本期|开[:：]|第\d+期|$)"
    )
    for line in lines:
        if "一句话赢大钱" not in line:
            continue
        parts = re.split(r"一句话赢大钱\s*[:：]", line, maxsplit=1)
        if len(parts) < 2:
            continue
        candidate = parts[1].strip()
        stop = stop_pattern.search(candidate)
        if stop:
            candidate = candidate[: stop.start()].strip()
        candidate = candidate.strip(" ，,。；;：:")
        if candidate:
            return candidate
    joined = "\n".join(lines)
    match = re.search(r"一句话赢大钱\s*[:：]\s*([^\n]+)", joined)
    if not match:
        return ""
    candidate = match.group(1).strip()
    stop = stop_pattern.search(candidate)
    if stop:
        candidate = candidate[: stop.start()].strip()
    return candidate.strip(" ，,。；;：:")


def _remove_default_excluded_segments(lines: list[str]) -> tuple[list[str], list[str]]:
    kept: list[str] = []
    excluded_reasons: list[str] = []
    for line in lines:
        text = str(line).strip()
        if not text:
            continue
        if "暗码" in text:
            before = re.split(r"暗码", text, maxsplit=1)[0].strip(" ，,。；;")
            if before:
                kept.append(before)
            excluded_reasons.append("暗码默认不纳入分析")
            continue
        kept.append(text)
    return _unique_nonempty(kept), _unique_nonempty(excluded_reasons)


def _strip_period_prefix(line: str) -> str:
    text = re.sub(r"^\s*\d{4}\s*[-—－]\s*\d+\s*", "", line)
    text = re.sub(r"^\s*第?\d+期\s*", "", text)
    return text.strip(" ，,。；;")


def _extract_period_context(lines: list[str]) -> dict:
    zodiac_chars = "鼠牛虎兔龙蛇马羊猴鸡狗猪"
    context = {
        "lines": [],
        "current_clash_text": "",
        "previous_result_text": "",
        "previous_period": "",
        "previous_first_number": "",
        "previous_special_number": "",
        "previous_special_zodiac": "",
    }
    for line in lines:
        text = str(line).strip()
        if not text:
            continue
        is_context = bool(
            re.search(r"\[[^]]*冲[^]]*\]", text)
            or "上期回放" in text
            or re.search(r"\d+期\s*[:：].*特", text)
            or re.search(r"\d+期\d+月\d+日", text)
        )
        if is_context:
            context["lines"].append(text)
        clash = re.search(rf"\[?([{zodiac_chars}]冲[{zodiac_chars}])\]?", text)
        if clash:
            context["current_clash_text"] = clash.group(1)
        previous = re.search(
            rf"(\d+)期\s*[:：]\s*([0-9\s]+?)\s*特\s*[:：]?\s*(\d{{1,2}})([{zodiac_chars}])?",
            text,
        )
        if previous:
            numbers = previous.group(2).split()
            context["previous_result_text"] = previous.group(0)
            context["previous_period"] = previous.group(1)
            context["previous_first_number"] = numbers[0] if numbers else ""
            context["previous_special_number"] = previous.group(3)
            context["previous_special_zodiac"] = previous.group(4) or ""
    context["lines"] = _unique_nonempty(context["lines"])
    return context


def _split_running_scope(lines: list[str]) -> tuple[list[str], list[str], dict, list[str]]:
    cleaned_lines, excluded_reasons = _remove_default_excluded_segments(lines)
    period_context = _extract_period_context(cleaned_lines)
    context_lines = set(period_context.get("lines", []))
    primary_lines: list[str] = []
    weak_auxiliary_lines: list[str] = []
    for line in cleaned_lines:
        if line in context_lines:
            continue
        if "解九肖" in line or "解肖" in line or "九肖" in line:
            parts = re.split(r"(解九肖|解肖|九肖)", line, maxsplit=1)
            if len(parts) >= 3:
                primary_part = _strip_period_prefix(parts[0])
                if primary_part:
                    primary_lines.append(primary_part)
                weak_auxiliary_lines.append("".join(parts[1:]).strip())
            else:
                weak_auxiliary_lines.append(line)
            continue
        primary = _strip_period_prefix(line)
        if primary:
            primary_lines.append(primary)
    if weak_auxiliary_lines:
        excluded_reasons.append("解肖/九肖只作弱辅助候选池，不作主线权重")
    if period_context.get("lines"):
        excluded_reasons.append("上期开奖结果和对冲信息只作降权上下文，不作本期数字线")
    return (
        _unique_nonempty(primary_lines),
        _unique_nonempty(weak_auxiliary_lines),
        period_context,
        _unique_nonempty(excluded_reasons),
    )


def _extract_nine_zodiac_scope(lines: list[str]) -> list[str]:
    zodiac_chars = "鼠牛虎兔龙蛇马羊猴鸡狗猪"
    scoped: list[str] = []
    for line in lines:
        if "九肖" in line:
            found = [char for char in line if char in zodiac_chars]
            if found:
                scoped.append("九肖：" + "".join(dict.fromkeys(found)))
    return _unique_nonempty(scoped)


def _numbers_in_scope(numbers: list, scope_text: list[str]) -> list:
    joined_scope = "\n".join(scope_text)
    return [number for number in numbers if str(number) in joined_scope]


def build_analysis_scope(vision: dict) -> dict:
    scoped = {
        "run_id": vision.get("run_id"),
        "project_root": vision.get("project_root"),
        "analysis_scope_policy": (
            "Manual marked regions are prioritized. If no manual region is present, scope is selected "
            "by PROJECT_HANDOFF.md, 基础资料.md, and 决策记录.md decision rules before calling Qwen3."
        ),
        "analysis_mode": "normal",
        "results": [],
    }
    for item in vision.get("results", []):
        parsed = copy.deepcopy(item.get("parsed", {}))
        ocr_text = _unique_nonempty(_as_text_list(parsed.get("ocr_text")))
        marked_regions = parsed.get("marked_regions") if isinstance(parsed.get("marked_regions"), list) else []
        manual_regions = _manual_marked_regions(marked_regions)
        marked_text: list[str] = []
        for region in manual_regions:
            marked_text.extend(_as_text_list(region.get("text")))
        marked_text = _unique_nonempty(marked_text)
        has_marked_text = bool(marked_text)
        decision_type = _detect_decision_type(parsed, ocr_text)
        scope_source = "ocr_full_fallback"
        scope_text: list[str]
        weak_auxiliary_text: list[str] = []
        period_context: dict = {}
        excluded_reasons: list[str] = []

        if decision_type == "管家婆一句话赢大钱":
            source_lines = marked_text + ocr_text if has_marked_text else ocr_text
            sentence = _extract_guanjiapo_sentence(source_lines)
            scope_text = [f"一句话赢大钱：{sentence}"] if sentence else marked_text
            scope_source = "decision_record: 管家婆只分析一句话赢大钱冒号后的红字"
            excluded_reasons = [
                "管家婆平特玄机默认忽略",
                "上期回放默认忽略",
                "解码和号码默认忽略",
                "其他非一句话赢大钱内容默认忽略",
            ]
        elif decision_type in {"跑狗图/澳门跑狗", "跑马图"}:
            if has_marked_text:
                scope_text, weak_auxiliary_text, period_context, excluded_reasons = _split_running_scope(marked_text)
                scope_source = "manual_marked_region_with_default_exclusions"
            else:
                scope_text, weak_auxiliary_text, period_context, excluded_reasons = _split_running_scope(ocr_text)
                scope_source = f"decision_record: {decision_type} 无人工红框时按资料类型有效区域自动取全图事实，暗码默认排除"
        elif decision_type == "澳门传真":
            if has_marked_text:
                scope_text, excluded_reasons = _remove_default_excluded_segments(marked_text)
                scope_source = "manual_marked_region"
            else:
                scope_text = []
                scope_source = "decision_record: 澳门传真需要用户红框或指定区域，未自动纳入全图"
                excluded_reasons = ["澳门传真未见人工红框或指定区域"]
        elif decision_type == "九肖30码":
            scope_text = _extract_nine_zodiac_scope(marked_text if has_marked_text else ocr_text)
            scope_source = "decision_record: 九肖30码只取九肖本身"
            excluded_reasons = ["六肖、四肖、一肖和30码号码列表默认忽略"]
        elif has_marked_text:
            scope_text, excluded_reasons = _remove_default_excluded_segments(marked_text)
            scope_source = "manual_marked_region"
        else:
            scope_text, excluded_reasons = _remove_default_excluded_segments(ocr_text)

        original_numbers = parsed.get("numbers") if isinstance(parsed.get("numbers"), list) else []
        scope_numbers = _numbers_in_scope(original_numbers, scope_text)
        excluded_count = max(0, len(ocr_text) - len(scope_text))
        test_text = "\n".join(ocr_text + [str(parsed.get("image_type", ""))])
        if any(token in test_text for token in ["测试图", "流程验证", "OCR 验证", "本地图像识别"]):
            scoped["analysis_mode"] = "workflow_test_no_prediction"
        scoped["results"].append(
            {
                "image_index": item.get("image_index"),
                "image_path": item.get("image_path"),
                "metadata": item.get("metadata", {}),
                "image_type": parsed.get("image_type", "unknown"),
                "decision_type": decision_type,
                "analysis_scope_source": scope_source,
                "analysis_scope_text": scope_text,
                "weak_auxiliary_scope_text": weak_auxiliary_text,
                "period_context": period_context,
                "analysis_scope_marked_regions": manual_regions if has_marked_text else [],
                "analysis_scope_numbers": scope_numbers,
                "uncertain": parsed.get("uncertain", []),
                "excluded_non_scope_ocr_count": excluded_count,
                "excluded_non_scope_reasons": excluded_reasons,
            }
        )
    return scoped


def build_prompt(vision: dict, extra_note: str) -> str:
    workflow = load_workflow_config()
    analysis_prompt = read_prompt("main_analysis.md")
    scoped_vision = build_analysis_scope(vision)
    sections = [
        "# 系统任务",
        analysis_prompt,
        "",
        "# 项目文档",
    ]
    for relative in workflow["handoff_files"]:
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
            "# Vision 模型事实提取结果（已按决策记录确定有效范围）",
            "```json",
            json.dumps(scoped_vision, ensure_ascii=False, indent=2),
            "```",
            "",
            "注意：只能使用 analysis_scope_text 和 analysis_scope_numbers 做候选主权重；weak_auxiliary_scope_text 只能作弱辅助；period_context 只用于降权和期数核验；excluded_non_scope_reasons 中的内容边界不得反向用于分析。",
            "",
        ]
    )
    if extra_note:
        sections.extend(["# 用户补充说明", extra_note, ""])
    sections.extend(
        [
            "# 输出要求",
            "请严格按项目规则输出中文分析。",
            "人工红框/指定区域优先；没有人工红框时，按 analysis_scope_source 指明的决策记录口径执行。",
            "红框外、非指定区域、规则默认排除、或被图片文字明确标为非重点的内容，不得进入候选权重。",
            "上期开奖结果、上期回放、末尾特码和当期对冲只用于降权或风险提示，不能当作本期数字线来抬高生肖。",
            "解肖和九肖只作弱辅助候选池，不能压过正文、图画、诗句、成语和号码级主线。",
            "如果 analysis_scope_source 已经写明按决策记录自动取范围，禁止在输出中要求用户补充红框或指定区域。",
            "资料类型只能依据用户说明、图片可见标题或 analysis_scope 中的 image_type；未知或测试图不得强套任何项目资料模板。",
            "如果 Vision 结果存在 OCR 不确定或可能误读，必须列为不确定项，不要强行当作事实。",
            "如果 analysis_mode 是 workflow_test_no_prediction，只能输出流程验证结果、识别事实、规则执行检查和不确定项；禁止输出候选生肖权重、主六肖、强防或开奖倾向。",
            "不要输出内部思考过程。",
        ]
    )
    return "\n".join(sections)


def main() -> None:
    args = parse_args()
    models = load_models_config()
    run_dirs = ensure_run_dirs(args.run_id)
    log_path = run_dirs["logs"] / "qwen3_analysis.log"
    vision = load_vision_result(args.run_id, args.vision_json)
    extra_note = load_extra_note(args.note, args.note_file)
    prompt = build_prompt(vision, extra_note)
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
    log_line(log_path, f"Qwen3 analysis started: run_id={args.run_id}")
    raw = ollama_generate(payload, timeout=1200)
    response = raw.get("response", "").strip()
    result = {
        "run_id": args.run_id,
        "project_root": str(PROJECT_ROOT),
        "model": models["models"]["main"],
        "response": response,
        "raw": raw,
    }
    write_json(run_dirs["cache"] / "qwen3_analysis.json", result)
    output = "\n".join(
        [
            "# Qwen3 Analysis Result",
            "",
            f"- Run ID: {args.run_id}",
            f"- Model: {models['models']['main']}",
            f"- Project: {PROJECT_ROOT}",
            "",
            "## Analysis",
            "",
            response or "(empty)",
            "",
        ]
    )
    output_path = run_dirs["outputs"] / "final_analysis.md"
    write_text(output_path, output)
    log_line(log_path, f"Qwen3 analysis finished: {output_path}")
    print(output_path)


if __name__ == "__main__":
    main()
