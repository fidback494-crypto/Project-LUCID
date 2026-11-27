"""검수된 JSONL 대화를 장면 단위로 학습·검증 데이터로 나눈다."""

import argparse
import json
import random
from collections import defaultdict
from itertools import combinations
from pathlib import Path

if __package__:
    from .corpus import read_examples
else:
    from corpus import read_examples


def parse_args() -> argparse.Namespace:
    """콘솔에서 원본, 출력 폴더, 검증 비율과 시드를 읽어 반환한다."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument(
        "--output-dir", default=Path("training/dialogue/split"), type=Path
    )
    parser.add_argument("--validation-ratio", default=0.1, type=float)
    parser.add_argument("--seed", default=42, type=int)
    return parser.parse_args()


def split_groups(examples, validation_ratio: float, seed: int) -> tuple[list, list]:
    """시드와 검증 비율로 장면을 나눠 (학습 행, 검증 행)을 반환한다."""
    groups = defaultdict(list)
    for index, example in enumerate(examples):
        scene_id = example.get("scene_id")
        group_id = ("scene", str(scene_id)) if scene_id is not None else ("row", index)
        groups[group_id].append(example)
    if len(groups) < 2:
        raise ValueError("Need at least two distinct scenes/groups for validation.")

    group_ids = list(groups)
    random.Random(seed).shuffle(group_ids)
    validation_group_count = max(1, round(len(group_ids) * validation_ratio))
    validation_ids = set(group_ids[:validation_group_count])
    train = [
        row
        for group_id, rows in groups.items()
        if group_id not in validation_ids
        for row in rows
    ]
    validation = [
        row
        for group_id, rows in groups.items()
        if group_id in validation_ids
        for row in rows
    ]
    return train, validation


def write_jsonl(path: Path, examples: list) -> None:
    """훈련에 쓰지 않는 장면 ID를 빼고 examples를 UTF-8 JSONL로 저장한다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as output:
        for row in examples:
            clean_row = {key: value for key, value in row.items() if key != "scene_id"}
            output.write(json.dumps(clean_row, ensure_ascii=False) + "\n")


def main() -> None:
    """원본과 두 출력이 서로 다른 파일인지 확인한 뒤 장면 단위로 분할한다."""
    args = parse_args()
    if not 0.05 <= args.validation_ratio <= 0.4:
        raise ValueError("validation-ratio must be between 0.05 and 0.4.")
    train_path = args.output_dir / "train.jsonl"
    validation_path = args.output_dir / "validation.jsonl"
    for left, right in combinations((args.input, train_path, validation_path), 2):
        if left.resolve() == right.resolve() or (
            left.exists() and right.exists() and left.samefile(right)
        ):
            raise ValueError(f"원본 및 출력 파일의 경로가 겹쳐: {left}, {right}")
    examples = read_examples(args.input)
    train, validation = split_groups(examples, args.validation_ratio, args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(train_path, train)
    write_jsonl(validation_path, validation)
    print(
        f"Wrote {len(train)} train and {len(validation)} validation examples to {args.output_dir}"
    )
    if len(train) < 100 or len(validation) < 20:
        print(
            "Warning: this is below the training script's minimum for a fine-tuning run."
        )


if __name__ == "__main__":
    main()
