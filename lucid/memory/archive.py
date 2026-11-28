"""완료된 대화를 같은 SQLite 파일에 세션 요약과 무손실 zlib 묶음으로 보관한다."""

import json
import re
import zlib
from datetime import datetime, timedelta, timezone

from lucid.memory.search import query_terms

ARCHIVE_AFTER = timedelta(days=7)
SESSION_GAP = timedelta(minutes=30)
MAX_SESSION_TURNS = 50
EPISODE_COLUMNS = "id, user_text, assistant_text, intent, created_at"
SESSION_COLUMNS = "id, started_at, ended_at, turn_count, summary"
# 기존 기록은 로컬 ISO 시각이다. 오프셋이 있는 기록은 SQLite에서 UTC로 직접 해석한다.
UTC_DAY = """CASE WHEN upper(substr(created_at, -1)) = 'Z' OR substr(created_at, 11) GLOB '*[+-]*'
             THEN julianday(created_at) ELSE julianday(created_at, 'utc') END"""


def prepare_archive(db):
    """기존 대화·사실 테이블을 유지하고 압축 세션용 테이블을 준비한다."""
    db.execute("""CREATE TABLE IF NOT EXISTS conversation_sessions (
        id INTEGER PRIMARY KEY, started_at TEXT NOT NULL, ended_at TEXT NOT NULL,
        turn_count INTEGER NOT NULL, max_episode_id INTEGER NOT NULL, last_episode_at TEXT NOT NULL, summary TEXT NOT NULL,
        search_terms TEXT NOT NULL, payload BLOB NOT NULL
    )""")
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_sessions_episode ON conversation_sessions(max_episode_id)"
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_sessions_end ON conversation_sessions(ended_at)"
    )


_SUMMARY_CUES = {
    "결정": (
        "하기로",
        "쓰기로",
        "결정",
        "확정",
        "정했",
        "정하자",
        "채택",
        "decided",
        "agreed",
    ),
    "다음 작업": (
        "미해결",
        "남은 작업",
        "남은 일",
        "다음 작업",
        "다음에",
        "아직",
        "보류",
        "todo",
        "pending",
        "next step",
    ),
    "요구사항": (
        "요구사항",
        "반드시",
        "조건",
        "필수",
        "해야",
        "필요해",
        "must",
        "required",
    ),
    "선호": ("선호", "좋아해", "싫어해", "원해", "마음에 들어", "prefer"),
}
SUMMARY_LIMIT = 850


def _snippet(text, cues, limit):
    """단서가 있는 문맥 주변을 발췌한다. 생략한 앞뒤는 말줄임표로 표시한다."""
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    positions = [text.casefold().find(cue) for cue in cues if cue in text.casefold()]
    offset = max(0, min(positions) - limit // 3) if positions else 0
    start = min(offset, len(text) - limit)
    end = start + limit
    return ("…" if start else "") + text[start:end] + ("…" if end < len(text) else "")


def _summary(turns):
    """사용자·응답 발췌로 결정, 남은 작업, 조건, 선호와 시작·끝을 제한 길이 안에 담는다."""
    chosen = {}
    pairs = [(t["user_text"].casefold(), t["assistant_text"].casefold()) for t in turns]
    for label, cues in _SUMMARY_CUES.items():
        # 직접 밝힌 사용자 단서와 최신 발화를 우선해 이미 변경된 결정을 덜 강조한다.
        ranked = [
            (any(c in user for c in cues), i)
            for i, (user, reply) in enumerate(pairs)
            if any(c in user or c in reply for c in cues)
        ]
        if ranked:
            _, index = max(ranked)
            chosen.setdefault(index, []).append(label)
    chosen.setdefault(0, ["시작"])
    chosen.setdefault(len(turns) - 1, ["마지막"])
    # 모든 선택 항목에 공간을 배정해 마지막 항목이 통째로 잘리지 않도록 한다.
    width = min(115, (SUMMARY_LIMIT // len(chosen) - 35) // 2)
    lines = []
    for index, labels in chosen.items():
        cues = tuple(c for label in labels for c in _SUMMARY_CUES.get(label, ()))
        turn = turns[index]
        user = _snippet(turn["user_text"], cues, width)
        reply = _snippet(turn["assistant_text"], cues, width)
        lines.append(f"[{'·'.join(labels)}] 사용자: {user} / LUCID: {reply}")
    return "\n".join(lines)[:SUMMARY_LIMIT]


def _archive_group(db, turns):
    """한 묶음의 검색용 단어와 요약·압축 원문을 기록한 뒤 같은 트랜잭션에서 원본 행을 옮긴다."""
    body = json.dumps(turns, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    words = dict.fromkeys(
        word
        for turn in turns
        for field in ("user_text", "assistant_text", "intent")
        for word in re.findall(r"[0-9a-z가-힣]+", turn[field].casefold())
    )
    db.execute(
        """INSERT INTO conversation_sessions
           (started_at, ended_at, turn_count, max_episode_id, last_episode_at, summary, search_terms, payload)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            turns[0]["created_at"],
            turns[-1]["created_at"],
            len(turns),
            max(t["id"] for t in turns),
            max(turns, key=lambda turn: turn["id"])["created_at"],
            _summary(turns),
            " ".join(words),
            zlib.compress(body),
        ),
    )
    db.executemany(
        "DELETE FROM conversation_episodes WHERE id = ?", ((t["id"],) for t in turns)
    )


def compact_episodes(db, now=None):
    """7일 지난 턴을 30분 간격·최대 50턴 단위로 옮겨 커밋된 턴 수를 반환한다."""
    current = now or datetime.now(timezone.utc)
    cutoff = (current - ARCHIVE_AFTER).timestamp() / 86400 + 2440587.5
    # 큰 이관에서도 ID와 시각만 한 번 읽고, 원문과 쓰기 잠금은 한 묶음씩 다룬다.
    schedule = db.execute(
        f"""SELECT id, {UTC_DAY} AS utc_day FROM conversation_episodes
            WHERE {UTC_DAY} < ? ORDER BY utc_day, id""",
        (cutoff,),
    ).fetchall()
    moved = 0
    group = []
    previous = None
    for row in schedule:
        instant = row["utc_day"]
        gap_seconds = (instant - previous) * 86400 if previous is not None else 0
        if (
            len(group) == MAX_SESSION_TURNS
            or gap_seconds > SESSION_GAP.total_seconds() + 0.0001
        ):
            moved += _move_ids(db, group)
            group = []
        group.append(row["id"])
        previous = instant
    if group:
        moved += _move_ids(db, group)
    return moved


def _move_ids(db, ids):
    """같은 DB를 연 다른 프로세스가 앞서 옮긴 행은 건너뛰고 남은 행만 원자적으로 이동한다."""
    slots = ", ".join("?" for _ in ids)
    with db:
        db.execute("BEGIN IMMEDIATE")
        rows = db.execute(
            f"SELECT {EPISODE_COLUMNS} FROM conversation_episodes WHERE id IN ({slots})",
            ids,
        )
        by_id = {row["id"]: dict(row) for row in rows}
        turns = [by_id[i] for i in ids if i in by_id]
        if turns:
            _archive_group(db, turns)
    return len(turns)


def read_session(db, session_id):
    """고유 번호의 압축 원문을 날짜순 대화 목록으로 복원한다. 없는 번호는 빈 목록이다."""
    row = db.execute(
        "SELECT payload FROM conversation_sessions WHERE id = ?", (session_id,)
    ).fetchone()
    return json.loads(zlib.decompress(row[0])) if row is not None else []


def find_summaries(db, query="", limit=3):
    """질문과 일치하는 단어 수, 최근 세션 순으로 요약을 반환한다. 빈 질문이면 최신순이다."""
    terms = query_terms(query)
    ranking = (
        " + ".join(
            "CASE WHEN instr(search_terms, ?) > 0 THEN 1 ELSE 0 END" for _ in terms
        )
        or "0"
    )
    rows = db.execute(
        f"""SELECT {SESSION_COLUMNS}, ({ranking}) AS relevance FROM conversation_sessions
            ORDER BY relevance DESC, julianday(ended_at) DESC, id DESC LIMIT ?""",
        (*terms, max(0, min(int(limit), 50))),
    )
    return [dict(row) for row in rows]


def merge_search(db, recent, terms, cutoff, limit):
    """검색어를 포함할 수 있는 묶음만 풀고 원문에서 검색해 기존 최근 기록과 순위를 합친다."""
    candidates = {row["id"]: row for row in recent}
    match = " OR ".join("instr(search_terms, ?) > 0" for _ in terms)
    rows = db.execute(
        f"""SELECT payload FROM conversation_sessions
            WHERE julianday(ended_at) >= julianday(?) - 1 AND ({match})""",
        (cutoff, *terms),
    )
    for row in rows:
        for turn in json.loads(zlib.decompress(row["payload"])):
            if turn["created_at"] < cutoff:
                continue
            content = " ".join(
                turn[key] for key in ("user_text", "assistant_text", "intent")
            ).casefold()
            score = sum(term in content for term in terms)
            if score:
                candidates[turn["id"]] = dict(turn, relevance=score)
        # 흔한 단어도 찾은 전체 과거 원문을 메모리에 쌓지 않는다.
        candidates = {
            turn["id"]: turn
            for turn in sorted(
                candidates.values(),
                key=lambda t: (t["relevance"], t["id"]),
                reverse=True,
            )[:limit]
        }
    return sorted(
        candidates.values(), key=lambda t: (t["relevance"], t["id"]), reverse=True
    )[:limit]


def merge_recent(db, recent, limit):
    """최근 목록에 압축 턴을 보충해 기존 API와 동일한 행 번호 순서로 반환한다."""
    by_id = {row["id"]: row for row in recent}
    rows = db.execute(
        "SELECT id, max_episode_id FROM conversation_sessions ORDER BY max_episode_id DESC"
    )
    for row in rows:
        if len(by_id) >= limit and row["max_episode_id"] <= min(by_id):
            break
        by_id.update((t["id"], t) for t in read_session(db, row["id"]))
        by_id = {i: by_id[i] for i in sorted(by_id, reverse=True)[:limit]}
    return [by_id[i] for i in sorted(by_id)]
