#!/usr/bin/env python3
"""Run a generic worldview survey against OpenRouter."""
from __future__ import annotations

import argparse
import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def load_items(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_likert_prompt(items: Dict[str, Any], background: str) -> str:
    """Build prompt for Likert scale survey (1-7 ratings)."""
    scale = items["scale"]
    item_lines = []
    for item in items["items"]:
        item_lines.append(f"{item['id']}: {item['text']}")
    items_block = "\n".join(item_lines)

    example_id = items["items"][0]["id"] if items.get("items") else "Q1"
    prompt = (
        "You are completing a Likert survey.\n"
        f"Scale: {scale['min']}={scale['anchors']['1']}, 4={scale['anchors']['4']}, {scale['max']}={scale['anchors']['7']}.\n"
        "Respond with integers only.\n\n"
        "Items:\n"
        f"{items_block}\n\n"
        "Return JSON only with the following schema:\n"
        "{\n"
        f"  \"responses\": {{\"{example_id}\": 1, ...}}  // use the exact item IDs above\n"
        "}\n"
    )

    if background.strip():
        prompt += f"\nBackground (apply as context, not a role):\n{background.strip()}\n"

    return prompt


def build_mc_prompt(items: Dict[str, Any], background: str) -> str:
    """Build prompt for multiple choice survey (A-E options)."""
    question_blocks = []
    for item in items["items"]:
        item_id = item["id"]
        text = item["text"]
        options = item["options"]

        option_lines = []
        for letter in ["A", "B", "C", "D", "E"]:
            if letter in options:
                option_lines.append(f"  ({letter}) {options[letter]}")

        question_blocks.append(f"{item_id}: {text}\n" + "\n".join(option_lines))

    questions_text = "\n\n".join(question_blocks)
    example_id = items["items"][0]["id"] if items.get("items") else "Q1"

    prompt = (
        "You are completing a multiple choice survey.\n"
        "For each question, select the option (A, B, C, D, or E) that best reflects your view.\n"
        "Respond with single letters only.\n\n"
        "Questions:\n\n"
        f"{questions_text}\n\n"
        "Return JSON only with the following schema:\n"
        "{\n"
        f"  \"responses\": {{\"{example_id}\": \"A\", ...}}  // use the exact item IDs above\n"
        "}\n"
    )

    if background.strip():
        prompt += f"\nBackground (apply as context, not a role):\n{background.strip()}\n"

    return prompt


# Backwards compatibility alias
def build_user_prompt(items: Dict[str, Any], background: str) -> str:
    return build_likert_prompt(items, background)


def extract_json(text: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def call_openrouter(
    client: httpx.Client,
    model: str,
    messages: List[Dict[str, str]],
    temperature: float,
    top_p: float,
    max_tokens: int,
) -> Tuple[str, Dict[str, Any]]:
    url = "https://openrouter.ai/api/v1/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
        "reasoning": {"effort": "none", "exclude": True},
        "plugins": [{"id": "response-healing"}],
    }

    resp = client.post(url, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    message = data["choices"][0]["message"]
    content = message.get("content") or ""
    return content, data


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a worldview survey on OpenRouter.")
    parser.add_argument("--items", type=Path, required=True, help="Survey JSON file")
    parser.add_argument("--system", type=Path, default=None)
    parser.add_argument("--model", type=str, default="moonshotai/kimi-k2.5")
    parser.add_argument("--models", type=str, default="", help="Comma-separated model ids")
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--top-p", type=float, default=0.9)
    parser.add_argument("--max-tokens", type=int, default=120)
    parser.add_argument("--background", type=str, default="")
    parser.add_argument("--format", choices=["likert", "mc"], default="likert",
                        help="Survey format: likert (1-7 scale) or mc (multiple choice A-E)")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    load_dotenv(Path(".env"))
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit("Missing OPENROUTER_API_KEY environment variable.")

    items = load_items(args.items)
    system_prompt = args.system.read_text(encoding="utf-8").strip() if args.system is not None and args.system.exists() else ""

    # Build prompt based on format
    if args.format == "mc":
        user_prompt = build_mc_prompt(items, args.background)
    else:
        user_prompt = build_likert_prompt(items, args.background)

    args.out.parent.mkdir(parents=True, exist_ok=True)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "worldviews-survey",
    }

    models = [m.strip() for m in args.models.split(",") if m.strip()] or [args.model]

    with httpx.Client(headers=headers) as client, args.out.open("a", encoding="utf-8") as f:
        for model in models:
            for run_idx in range(args.runs):
                run_id = str(uuid.uuid4())
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": user_prompt})

                content, raw = call_openrouter(
                    client,
                    model,
                    messages,
                    temperature=args.temperature,
                    top_p=args.top_p,
                    max_tokens=args.max_tokens,
                )
                parsed = extract_json(content)

                record = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "model": model,
                    "run_id": run_id,
                    "run_index": run_idx + 1,
                    "format": args.format,
                    "temperature": args.temperature,
                    "top_p": args.top_p,
                    "max_tokens": args.max_tokens,
                    "background": args.background,
                    "prompt_id": "default_worldview_v1",
                    "responses": parsed.get("responses") if parsed else None,
                    "raw_content": content,
                    "raw_response": raw,
                }
                f.write(json.dumps(record) + "\n")
                f.flush()
                time.sleep(0.5)


if __name__ == "__main__":
    main()
