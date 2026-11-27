"""학습 목표 문구의 길이와 JSONL 분할 시의 파일 보존을 검증한다."""

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from training.corpus import validate_row
from training.split_dialogue_data import main as split_corpus


class CorpusValidationTests(unittest.TestCase):
    """실제 학습에 사용하는 세 텍스트 필드의 경계값을 검사한다."""

    def test_target_length_boundaries(self):
        """각 필드는 지정한 글자 수까지 유효하고 한 글자 더 길면 오류 위치를 알려준다."""
        target = {
            "reply": "안녕.",
            "experience": "반가움",
            "meaning": "인사를 받았다.",
            "intent": "greeting",
            "speech_style": "warm",
        }
        for field, limit in (("reply", 500), ("experience", 60), ("meaning", 100)):
            with self.subTest(field=field):
                reply = {**target, field: "별" * limit}
                completion = {"role": "assistant", "content": json.dumps(reply)}
                row = {
                    "prompt": [{"role": "user", "content": "안녕"}],
                    "completion": [completion],
                }
                validate_row(row, "data.jsonl", 7)
                reply[field] += "별"
                completion["content"] = json.dumps(reply)
                with self.assertRaisesRegex(
                    ValueError, rf"data\.jsonl:7: {field}.*{limit}"
                ):
                    validate_row(row, "data.jsonl", 7)


class SplitPathTests(unittest.TestCase):
    """경로 별칭을 통해 원본이나 기존 분할 결과가 덮어써지지 않는지 확인한다."""

    def setUp(self):
        """임시 디렉터리에 유효한 입력과 기존 출력 두 개를 준비한다."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        seed = Path(__file__).resolve().parents[1] / "training/dialogue/seed.jsonl"
        self.source = self.directory / "input.jsonl"
        shutil.copyfile(seed, self.source)
        self.train = self.directory / "train.jsonl"
        self.validation = self.directory / "validation.jsonl"
        self.train.write_bytes(b"previous train")
        self.validation.write_bytes(b"previous validation")

    def _assert_collision_preserves_files(self, source):
        """일반 CLI 경로에서 충돌 예외가 발생하고 세 파일의 내용이 유지되는지 검증한다."""
        paths = [self.source, self.train, self.validation]
        contents = [path.read_bytes() for path in paths]
        args = [
            "split_dialogue_data.py",
            "--input",
            str(source),
            "--output-dir",
            str(self.directory),
        ]
        with (
            patch.object(sys, "argv", args),
            self.assertRaisesRegex(ValueError, "경로가 겹쳐"),
        ):
            split_corpus()
        self.assertEqual([path.read_bytes() for path in paths], contents)

    def test_source_is_validation_output(self):
        """검증 출력 자체가 입력이면 이전 학습 출력도 보존된다."""
        shutil.copyfile(self.source, self.validation)
        self._assert_collision_preserves_files(self.validation)

    def test_outputs_are_hard_links(self):
        """두 출력이 같은 파일의 다른 이름이면 두 번째 쓰기 전에 중단한다."""
        self.validation.unlink()
        try:
            os.link(self.train, self.validation)
        except OSError as error:
            self.skipTest(f"임시 파일시스템에서 하드링크를 만들 수 없음: {error}")
        self._assert_collision_preserves_files(self.source)

    def test_outputs_are_symbolic_links(self):
        """한 출력이 다른 출력을 가리키면 기존 파일을 열기 전에 중단한다."""
        self.validation.unlink()
        try:
            self.validation.symlink_to(self.train)
        except OSError as error:
            self.skipTest(f"임시 파일시스템에서 심볼릭 링크를 만들 수 없음: {error}")
        self._assert_collision_preserves_files(self.source)
