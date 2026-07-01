#!/usr/bin/env python3
"""Shared helpers for the local Aucai AI workflow."""

from __future__ import annotations

import base64
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
WORKFLOW_ROOT = SCRIPT_DIR.parent
PROJECT_ROOT = WORKFLOW_ROOT.parent
CONFIG_DIR = WORKFLOW_ROOT / "config"
PROMPTS_DIR = WORKFLOW_ROOT / "prompts"


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_models_config() -> dict[str, Any]:
    return load_json(CONFIG_DIR / "models.json")


def load_workflow_config() -> dict[str, Any]:
    return load_json(CONFIG_DIR / "workflow.json")


def now_run_id() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def ensure_run_dirs(run_id: str) -> dict[str, Path]:
    workflow = load_workflow_config()
    dirs = workflow["directories"]
    paths = {
        "cache": PROJECT_ROOT / dirs["cache"] / run_id,
        "outputs": PROJECT_ROOT / dirs["outputs"] / run_id,
        "logs": PROJECT_ROOT / dirs["logs"] / run_id,
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def read_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8").strip()


def read_project_file(relative_path: str) -> str:
    path = PROJECT_ROOT / relative_path
    return path.read_text(encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data, encoding="utf-8")


def image_to_base64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def discover_inbox_images() -> list[Path]:
    workflow = load_workflow_config()
    inbox = PROJECT_ROOT / workflow["directories"]["inbox"]
    if not inbox.exists():
        return []
    return sorted(path for path in inbox.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS)


def image_metadata(path: Path) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "path": str(path),
        "name": path.name,
        "suffix": path.suffix.lower(),
        "size_bytes": path.stat().st_size,
    }
    try:
        result = subprocess.run(
            ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )
        width_match = re.search(r"pixelWidth:\s*(\d+)", result.stdout)
        height_match = re.search(r"pixelHeight:\s*(\d+)", result.stdout)
        if width_match:
            meta["pixel_width"] = int(width_match.group(1))
        if height_match:
            meta["pixel_height"] = int(height_match.group(1))
    except Exception as exc:
        meta["metadata_warning"] = str(exc)
    return meta


def ollama_generate(payload: dict[str, Any], timeout: int = 600) -> dict[str, Any]:
    base_url = load_models_config()["ollama_base_url"].rstrip("/")
    req = urllib.request.Request(
        f"{base_url}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama HTTP {exc.code}: {body}") from exc


def extract_json_object(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    if not stripped:
        return None
    candidates = [stripped]
    fenced = re.findall(r"```(?:json)?\s*(.*?)```", stripped, flags=re.DOTALL | re.IGNORECASE)
    candidates.extend(item.strip() for item in fenced)
    object_match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
    if object_match:
        candidates.append(object_match.group(0))
    repaired_candidates = [
        re.sub(
            r"(?<=[\[,:\s])0(\d+)(?=\s*[\],}])",
            lambda match: f'"0{match.group(1)}"',
            candidate,
        )
        for candidate in candidates
    ]
    candidates.extend(repaired_candidates)
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def log_line(path: Path, message: str) -> None:
    timestamp = datetime.now().isoformat(timespec="seconds")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"[{timestamp}] {message}\n")


def fail(message: str, code: int = 1) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)
