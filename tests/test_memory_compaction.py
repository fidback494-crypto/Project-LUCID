"""임시 SQLite 파일에서 대화 압축, 원문 검색, 초기 기억 이관을 검증한다."""

import os
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Barrier
from unittest.mock import patch

from lucid.memory import MemoryEngine, archive
from lucid.memory.facts import MemoryRecord
from lucid.memory.store import LongTermMemory


class MemoryCompactionTests(unittest.TestCase):
    """이 테스트가 만든 폴더 안에서만 DB를 열고 정리한다."""

    def setUp(self):
        """각 테스트의 활성 DB와 구형 DB를 분리한다."""
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name).resolve()
        change_env = patch.dict(os.environ, {"LUCID_DATA_DIR": directory.name})
        change_env.start()
        self.addCleanup(change_env.stop)
        self.memory = self.open_store()
        self.old = datetime.now(timezone.utc) - timedelta(days=20)

    def open_store(self):
        """별도의 연결을 열고 테스트가 끝날 때 반드시 닫는다."""
        store = LongTermMemory()
        self.addCleanup(store.close)
        return store

    def episode(self, user, reply, timestamp, intent="conversation"):
        """정확히 복원해야 할 ID와 원문을 기록해 반환한다."""
        stamp = timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp
        number = self.memory.store_conversation_episode(user, reply, intent, stamp)
        self.assertIsNotNone(number)
        return dict(
            id=number,
            user_text=user,
            assistant_text=reply,
            intent=intent,
            created_at=stamp,
        )

    def test_lossless_and_same_file_after_reopen(self):
        """줄바꿈·이모지·중복 원문과 ID를 보존하고 최근 대화와 사실을 그대로 둔다."""
        long_text = "봄에 기록한 대화\n별🌟  " * 220
        first = self.episode(long_text, "같은 응답\t\n", self.old)
        second = self.episode(
            long_text, "같은 응답\t\n", self.old + timedelta(minutes=30)
        )
        third = self.episode(
            "내용", "다시 만났어", self.old + timedelta(minutes=61, seconds=1)
        )
        recent = self.episode("오늘 기록", "최근 답", datetime.now())
        invalid = self.episode("옛 파일의 형식", "원본 유지", "날짜 미상")
        self.memory.store(
            MemoryRecord(
                "user", "사용자의 이름은 하늘", 0.9, predicate="name", value="하늘"
            )
        )
        self.assertEqual(self.memory.compact_conversations(), 3)
        self.assertEqual(self.memory.compact_conversations(), 0)
        after = self.open_store()
        sessions = after.session_summaries()
        self.assertEqual([s["turn_count"] for s in sessions], [1, 2])
        self.assertEqual(after.session_episodes(sessions[-1]["id"]), [first, second])
        self.assertEqual(after.session_episodes(sessions[0]["id"]), [third])
        self.assertEqual(after.session_episodes(-1), [])
        self.assertEqual(
            after.recent_conversation_episodes(),
            [first, second, third, recent, invalid],
        )
        self.assertEqual(after.all()[0]["value"], "하늘")
        rows = after.db.execute(
            "SELECT id FROM conversation_episodes ORDER BY id"
        ).fetchall()
        self.assertEqual([row[0] for row in rows], [recent["id"], invalid["id"]])
        self.assertLess(
            after.db.execute(
                "SELECT sum(length(payload)) FROM conversation_sessions"
            ).fetchone()[0],
            len(long_text.encode()),
        )
        self.assertEqual(
            {p.name for p in self.directory.iterdir()}, {"lucid_memory.db"}
        )

    def test_large_archive_reclaims_physical_file_space(self):
        """충분히 큰 원문을 압축하면 빈 SQLite 페이지를 회수해 실제 파일도 줄어든다."""
        text = "반복되는 합성 기록입니다. " * 5000
        for i in range(12):
            self.episode(f"{i} {text}", text, self.old + timedelta(seconds=i))
        before = self.memory.db_path.stat().st_size
        self.assertEqual(self.memory.compact_conversations(), 12)
        self.assertLess(self.memory.db_path.stat().st_size, before // 2)
        [session] = self.memory.session_summaries()
        self.assertEqual(
            self.memory.session_episodes(session["id"])[0]["assistant_text"], text
        )

    def test_summary_carries_middle_decision_and_open_work(self):
        """긴 턴의 중간 결정과 미해결 작업을 짧은 요약에서도 원문 근거와 함께 찾는다."""
        turns = [
            ("안녕", "반가워"),
            ("근황이야", "들려줘"),
            (
                "예전 이야기 " * 80 + "주 저장소는 청록색 상자로 결정했어.",
                "그곳에 넣을게.",
            ),
            ("조건은 종이 상자 필수야.", "알았어"),
            ("다음 작업은 은빛 라벨 만들기야.", "좋아"),
            ("무늬는 파란 줄무늬를 선호해.", "기억해 둘게"),
            ("오후엔 쉬자", "응"),
            ("또 봐", "잘 가"),
        ]
        for offset, (user, reply) in enumerate(turns):
            self.episode(user, reply, self.old + timedelta(minutes=offset))
        self.episode("별개 대화", "구름", self.old + timedelta(days=1))
        self.memory.compact_conversations()
        [related] = self.memory.session_summaries("청록색", 1)
        self.assertGreater(related["relevance"], 0)
        self.assertLessEqual(len(related["summary"]), archive.SUMMARY_LIMIT)
        for cue in ("청록색 상자", "은빛 라벨", "종이 상자", "파란 줄무늬"):
            self.assertIn(cue, related["summary"])
        [fallback] = self.memory.session_summaries("없는단어", 1)
        self.assertEqual(fallback["relevance"], 0)
        self.assertIn("별개 대화", fallback["summary"])

    def test_search_preserves_hits_and_skips_unpacking_for_normal_turns(self):
        """축약에서 생략된 발화도 직접 검색할 수 있고, 일반 턴에는 압축 원문을 열지 않는다."""
        old = self.episode("서랍에 주홍빛 리본이 있어", "맞아", self.old)
        for i in range(4):
            self.episode("일상", f"이야기 {i}", self.old + timedelta(minutes=i + 1))
        self.episode("서랍", "오늘도 살펴볼게", datetime.now())
        results = self.memory.search_conversation_episodes("주홍빛 서랍")
        self.assertEqual(self.memory.compact_conversations(), 5)
        self.assertEqual(
            self.memory.search_conversation_episodes("주홍빛 서랍"), results
        )
        self.assertEqual(results[0]["id"], old["id"])
        with patch(
            "lucid.memory.archive.zlib.decompress",
            side_effect=AssertionError("원문 복원 시도"),
        ):
            self.assertEqual(
                self.memory.search_conversation_episodes(
                    "주홍빛", include_archived=False
                ),
                [],
            )
            self.assertTrue(self.memory.session_summaries("주홍빛"))
            self.assertEqual(
                self.memory.last_conversation_gap()["source"], "conversation"
            )

    def test_old_only_last_contact_uses_episode_id_and_no_unpack(self):
        """행 번호와 시각 순서가 달라도 이전 API의 마지막 발화 판단을 보존한다."""
        self.episode("늦은 시각", "먼저 저장", self.old + timedelta(minutes=12))
        newest = self.episode("이른 시각", "나중 저장", self.old)
        expected = self.memory.last_conversation_gap()["last_at"]
        self.memory.compact_conversations()
        with patch(
            "lucid.memory.archive.zlib.decompress",
            side_effect=AssertionError("원문 복원 시도"),
        ):
            self.assertEqual(self.memory.last_conversation_gap()["last_at"], expected)
        self.assertEqual(self.memory.recent_conversation_episodes(1), [newest])

    def test_caps_session_length_without_duplicates_across_concurrent_connections(self):
        """두 연결이 같은 과거 행을 동시에 보관하더라도 원문 ID와 세션이 중복되지 않는다."""
        expected = [
            self.episode(f"발화 {i}", "응", self.old + timedelta(seconds=i))
            for i in range(65)
        ]
        # 다른 연결의 자동 정리 전에 원시 기록을 그대로 두고 두 명시적 호출을 맞춘다.
        with patch.object(LongTermMemory, "_maintain_archive"):
            other = self.open_store()
        barrier = Barrier(2)

        def compact(store):
            barrier.wait(timeout=3)
            return store.compact_conversations()

        with ThreadPoolExecutor(max_workers=2) as pool:
            moved = list(pool.map(compact, [self.memory, other]))
        self.assertEqual(sum(moved), len(expected))
        sessions = self.memory.session_summaries()
        self.assertEqual(sorted(s["turn_count"] for s in sessions), [15, 50])
        restored = [
            turn
            for s in reversed(sessions)
            for turn in self.memory.session_episodes(s["id"])
        ]
        self.assertEqual(restored, expected)

    def test_failed_move_rolls_back_and_retries(self):
        """원본 제거가 실패하면 요약과 원본이 함께 롤백되고 다음 실행에서 한 번만 옮겨진다."""
        expected = self.episode("보존", "대화", self.old)
        self.memory.db.execute("""CREATE TRIGGER fail_archive BEFORE DELETE ON conversation_episodes
                                 BEGIN SELECT RAISE(ABORT, 'test failure'); END""")
        with self.assertRaises(sqlite3.IntegrityError):
            self.memory.compact_conversations()
        self.assertEqual(self.memory.session_summaries(), [])
        self.assertEqual(self.memory.recent_conversation_episodes(), [expected])
        self.memory.db.execute("DROP TRIGGER fail_archive")
        reopened = self.open_store()
        self.assertEqual(
            reopened.session_episodes(reopened.session_summaries()[0]["id"]), [expected]
        )

    def test_legacy_ids_and_source_survive_reopen_and_new_writes_share_the_store(self):
        """기존 사실을 덮어쓰지 않고 구형 파일의 중복 원문·ID를 보관하며 두 API가 같은 DB를 쓴다."""
        self.memory.store(
            MemoryRecord(
                "user", "사용자의 이름은 하늘", 0.98, predicate="name", value="하늘"
            )
        )
        path = self.directory / "lucid.db"
        with closing(sqlite3.connect(path)) as legacy, legacy:
            legacy.execute(
                "CREATE TABLE memories(id INTEGER PRIMARY KEY, memory_type TEXT, content TEXT, importance REAL, created_at TEXT)"
            )
            legacy.executemany(
                "INSERT INTO memories VALUES(?,?,?,?,?)",
                [
                    (4, "name", "과거이름", 0.5, "2020-01-02 03:04:05"),
                    (6, "project", "별 실험", 0.8, "2020-01-03 03:04:05"),
                    (9, "project", "별 실험", 0.8, "2020-01-04 03:04:05"),
                ],
            )
        original = path.read_bytes()
        after = self.open_store()
        legacy = MemoryEngine()
        self.addCleanup(legacy.conn.close)
        self.assertEqual([r[0] for r in legacy.get_memories()], [9, 6, 4])
        self.assertEqual(legacy.get_name(), "과거이름")
        self.assertEqual(
            [row["value"] for row in after.all() if row["predicate"] == "name"],
            ["하늘"],
        )
        self.assertEqual(after.search("별 실험"), ["사용자의 프로젝트는 별 실험"])
        legacy.set_goal("이어 가기")
        self.assertEqual(after.search("이어 가기"), ["사용자의 목표는 이어 가기"])
        legacy.clear_goal()
        self.assertFalse(legacy.has_goal())
        self.assertEqual(after.search("이어 가기"), [])
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(
            after.db.execute("SELECT count(*) FROM legacy_imports").fetchone()[0], 3
        )
        self.assertEqual(
            legacy.conn.execute("PRAGMA database_list").fetchone()[2],
            str(self.directory / "lucid_memory.db"),
        )
        with closing(sqlite3.connect(path)) as source, source:
            source.execute(
                "INSERT INTO memories VALUES (10, 'favorite_animal', '고양이', .6, '2020-01-05')"
            )
        updated = self.open_store()
        self.assertEqual(updated.search("고양이"), ["사용자가 좋아하는 동물은 고양이"])
        self.assertEqual(
            updated.db.execute("SELECT count(*) FROM legacy_imports").fetchone()[0], 4
        )
