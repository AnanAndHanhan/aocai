#!/usr/bin/env python3
"""Extract OCR and visual facts from one or more images with Ollama Vision."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from common import (
    PROJECT_ROOT,
    discover_inbox_images,
    ensure_run_dirs,
    extract_json_object,
    fail,
    image_metadata,
    image_to_base64,
    load_models_config,
    log_line,
    now_run_id,
    ollama_generate,
    read_prompt,
    write_json,
    write_text,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local Vision extraction for Aucai images.")
    parser.add_argument("images", nargs="*", help="Image paths. If omitted, images in ai-workflow/inbox are used.")
    parser.add_argument("--run-id", default=None, help="Stable run id. Defaults to current timestamp.")
    return parser.parse_args()


def resolve_images(raw_paths: list[str]) -> list[Path]:
    if raw_paths:
        paths = [Path(item).expanduser().resolve() for item in raw_paths]
    else:
        paths = discover_inbox_images()
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        fail("Missing image file(s):\n" + "\n".join(missing))
    if not paths:
        fail("No images provided and ai-workflow/inbox has no image files.")
    return paths


def build_prompt(base_prompt: str, image_index: int, image_count: int, metadata: dict[str, Any]) -> str:
    return f"""{base_prompt}

请严格返回一个 JSON 对象，不要输出 Markdown 代码围栏，不要添加 JSON 以外的说明。

当前图片编号：{image_index}/{image_count}
图片文件名：{metadata["name"]}
图片尺寸：{metadata.get("pixel_width", "unknown")} x {metadata.get("pixel_height", "unknown")}
"""


def run_one(image_path: Path, run_id: str, image_index: int, image_count: int) -> dict[str, Any]:
    models = load_models_config()
    run_dirs = ensure_run_dirs(run_id)
    log_path = run_dirs["logs"] / "vision_extract.log"
    metadata = image_metadata(image_path)
    base_prompt = read_prompt("vision_extract.md")
    prompt = build_prompt(base_prompt, image_index, image_count, metadata)
    payload = {
        "model": models["models"]["vision"],
        "prompt": prompt,
        "images": [image_to_base64(image_path)],
        "stream": False,
        "options": {
            "temperature": 0,
            "top_p": models["defaults"].get("top_p", 0.9),
            "num_ctx": models["defaults"].get("num_ctx_vision", 8192),
            "num_predict": 2048,
        },
    }
    log_line(log_path, f"Vision extraction started: {image_path}")
    raw = ollama_generate(payload)
    response_text = raw.get("response", "").strip()
    parsed = extract_json_object(response_text)
    if parsed is None:
        parsed = {
            "image_type": "unknown",
            "ocr_text": [],
            "marked_regions": [],
            "visual_scene": [],
            "numbers": [],
            "possible_clues": [],
            "uncertain": ["Vision response was not valid JSON; raw_response contains the original model output."],
        }
    item = {
        "image_index": image_index,
        "image_path": str(image_path),
        "metadata": metadata,
        "parsed": parsed,
        "raw_response": response_text,
        "model": models["models"]["vision"],
    }
    stem = f"{image_index:02d}-{image_path.stem}"
    write_json(run_dirs["cache"] / f"{stem}.vision.json", item)
    log_line(log_path, f"Vision extraction finished: {image_path}")
    return item


def render_markdown(run_id: str, results: list[dict[str, Any]]) -> str:
    lines = [
        "# Vision Extract Result",
        "",
        f"- Run ID: {run_id}",
        f"- Project: {PROJECT_ROOT}",
        f"- Images: {len(results)}",
        "",
    ]
    for item in results:
        lines.extend(
            [
                f"## Image {item['image_index']}: {Path(item['image_path']).name}",
                "",
                "### Parsed JSON",
                "",
                "```json",
            ]
        )
        import json

        lines.append(json.dumps(item["parsed"], ensure_ascii=False, indent=2))
        lines.extend(["```", "", "### Raw Response", "", item["raw_response"] or "(empty)", ""])
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    args = parse_args()
    run_id = args.run_id or now_run_id()
    images = resolve_images(args.images)
    run_dirs = ensure_run_dirs(run_id)
    results = [run_one(path, run_id, index, len(images)) for index, path in enumerate(images, start=1)]
    summary = {"run_id": run_id, "project_root": str(PROJECT_ROOT), "results": results}
    write_json(run_dirs["cache"] / "vision_extract.json", summary)
    output_path = run_dirs["outputs"] / "vision_extract.md"
    write_text(output_path, render_markdown(run_id, results))
    print(output_path)


if __name__ == "__main__":
    main()
