"""Validate reviewed conversation examples and create leak-aware JSONL splits."""

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", default=Path("training/dialogue/split"), type=Path)
    parser.add_argument("--validation-ratio", default=0.1, type=float)
    parser.add_argument("--seed", default=42, type=int)
    return parser.parse_args()


def read_examples(path):
    examples = []
    with path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {error}") from error
            validate_row(row, path, line_number)
            examples.append(row)
    if len(examples) < 2:
        raise ValueError("At least two reviewed examples are needed to create a split.")
    return examples


def validate_messages(messages, allowed_roles, label):
    if not isinstance(messages, list) or not messages:
        raise ValueError(f"{label} must be a non-empty message array.")
    for message in messages:
        if not isinstance(message, dict):
            raise ValueError(f"{label} contains a non-object message.")
        if message.get("role") not in allowed_roles:
            raise ValueError(f"{label} contains an unsupported role.")
        if not isinstance(message.get("content"), str) or not message["content"].strip():
            raise ValueError(f"{label} contains an empty or non-text message.")


def validate_row(row, path, line_number):
    location = f"{path}:{line_number}"
    if not isinstance(row, dict):
        raise ValueError(f"{location}: each JSONL row must be an object.")
    validate_messages(row.get("prompt"), {"system", "user", "assistant"}, f"{location} prompt")
    validate_messages(row.get("completion"), {"assistant"}, f"{location} completion")
    if row["prompt"][-1].get("role") != "user":
        raise ValueError(f"{location}: prompt must end with the current user message.")
    if len(row["completion"]) != 1:
        raise ValueError(f"{location}: completion must contain exactly one assistant message.")
    try:
        target = json.loads(row["completion"][0]["content"])
    except json.JSONDecodeError as error:
        raise ValueError(f"{location}: assistant completion must contain JSON.") from error
    required = {"reply", "intent", "experience", "meaning", "speech_style"}
    if not isinstance(target, dict) or set(target) != required:
        raise ValueError(f"{location}: completion JSON keys must be exactly {sorted(required)}.")
    if not all(isinstance(target[key], str) and target[key].strip() for key in required):
        raise ValueError(f"{location}: every completion value must be non-empty text.")
    if target["intent"] not in {"question", "greeting", "conversation", "request", "emotion", "exit"}:
        raise ValueError(f"{location}: intent is outside the response schema.")
    if target["speech_style"] not in {
        "neutral", "warm", "curious", "cheerful", "playful",
        "soothing", "concerned", "serious", "shy",
    }:
        raise ValueError(f"{location}: speech_style is outside the response schema.")


def split_groups(examples, validation_ratio, seed):
    groups = defaultdict(list)
    for index, example in enumerate(examples):
        # Add a shared scene_id when several rows come from the same conversation.
        # This keeps a scene from appearing in both training and validation.
        group_id = str(example.get("scene_id") or f"row-{index}")
        groups[group_id].append(example)
    if len(groups) < 2:
        raise ValueError("Need at least two distinct scenes/groups for validation.")

    group_ids = list(groups)
    random.Random(seed).shuffle(group_ids)
    validation_group_count = max(1, round(len(group_ids) * validation_ratio))
    validation_ids = set(group_ids[:validation_group_count])
    train = [row for group_id, rows in groups.items() if group_id not in validation_ids for row in rows]
    validation = [row for group_id, rows in groups.items() if group_id in validation_ids for row in rows]
    return train, validation


def write_jsonl(path, examples):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as output:
        for row in examples:
            # Keep grouping metadata out of the trainer's model columns.
            clean_row = {key: value for key, value in row.items() if key != "scene_id"}
            output.write(json.dumps(clean_row, ensure_ascii=False) + "\n")


def main():
    args = parse_args()
    if not 0.05 <= args.validation_ratio <= 0.4:
        raise ValueError("validation-ratio must be between 0.05 and 0.4.")
    examples = read_examples(args.input)
    train, validation = split_groups(examples, args.validation_ratio, args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output_dir / "train.jsonl", train)
    write_jsonl(args.output_dir / "validation.jsonl", validation)
    print(f"Wrote {len(train)} train and {len(validation)} validation examples to {args.output_dir}")
    if len(train) < 100 or len(validation) < 20:
        print("Warning: this is below the training script's minimum for a fine-tuning run.")


if __name__ == "__main__":
    main()
