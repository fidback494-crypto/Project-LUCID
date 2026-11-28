"""구형 lucid.db의 원본 행과 출처를 보존하면서 현재 저장소로 이관한다."""

import hashlib
import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path

from lucid.log import Logger
from lucid.memory.facts import infer_legacy_memory, memory_key


def prepare_legacy(db):
    """초기 스키마의 행과 이관한 원본 ID를 보존할 테이블을 준비한다."""
    db.execute("""CREATE TABLE IF NOT EXISTS legacy_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT, memory_type TEXT, content TEXT,
        importance REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS legacy_imports (
        fingerprint TEXT PRIMARY KEY, source_id INTEGER NOT NULL, record_id INTEGER NOT NULL
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS legacy_source_files (
        path TEXT PRIMARY KEY, signature TEXT NOT NULL
    )""")


def _file_signature(path):
    """원본 또는 쓰기 전 로그가 바뀌었을 때만 행별 이관 여부를 다시 검사한다."""
    signature = []
    for candidate in (path, Path(str(path) + "-wal"), Path(str(path) + "-journal")):
        try:
            stat = candidate.stat()
        except FileNotFoundError:
            signature.append(None)
        else:
            signature.append(
                [stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns]
            )
    return json.dumps(signature)


def _normalized(kind, content):
    """초기 기억의 종류와 본문을 현재의 주체·관계·값·표시 본문·키로 변환한다."""
    if not isinstance(content, str) or not content.strip():
        return None
    value = content.strip()
    subject, predicate, inferred = infer_legacy_memory(kind, value)
    if predicate == "fact":
        predicate = str(kind or "fact")
    else:
        value = inferred
    description = {
        "name": "사용자의 이름은 ",
        "favorite_animal": "사용자가 좋아하는 동물은 ",
        "project": "사용자의 프로젝트는 ",
        "goal": "사용자의 목표는 ",
    }.get(predicate, "")
    display = description + value if description else content
    key = memory_key(subject, predicate, value)
    if predicate in {"favorite_animal", "project", "goal"}:
        key = f"{subject}:{predicate}"
    return subject, predicate, value, display, key


def project_legacy(db, kind, content, importance, created_at):
    """구형 행을 검색 가능한 사실로 반영한다. 현재 앱의 사실·삭제 상태가 우선한다."""
    fields = _normalized(kind, content)
    if fields is None:
        return
    subject, predicate, value, display, key = fields
    old = db.execute(
        "SELECT id, source, status FROM main.memories WHERE content = ?", (display,)
    ).fetchone()
    if old and (old[1] != "legacy_import" or old[2] != "superseded"):
        return
    current = db.execute(
        """SELECT id, source, created_at FROM main.memories WHERE memory_key = ? AND status = 'active'""",
        (key,),
    ).fetchone()
    stamp = str(created_at or "1970-01-01T00:00:00")
    status = "active"
    if current:
        if current[1] == "legacy_import" and str(current[2]) <= stamp:
            db.execute(
                "UPDATE main.memories SET status = 'superseded' WHERE id = ?",
                (current[0],),
            )
        else:
            status = "superseded"
    try:
        weight = max(0.0, min(1.0, float(importance)))
    except (TypeError, ValueError):
        weight = 0.5
    if old:
        if status == "active":
            db.execute(
                "UPDATE main.memories SET status = 'active', updated_at = ? WHERE id = ?",
                (stamp, old[0]),
            )
        return
    db.execute(
        """INSERT INTO main.memories(category, content, importance, created_at, subject,
           predicate, value, confidence, source, memory_key, status, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'legacy_import', ?, ?, ?)""",
        (
            str(kind or "fact"),
            display,
            weight,
            stamp,
            subject,
            predicate,
            value,
            weight,
            key,
            status,
            stamp,
        ),
    )


def import_old_files(db, directory):
    """알려진 초기 저장 경로의 lucid.db를 읽기 전용으로 열어 아직 이관하지 않은 행을 복사한다."""
    sources = [directory / "lucid.db"]
    previous = (Path.cwd() / "data" / "lucid.db").resolve()
    if not os.getenv("LUCID_DATA_DIR") and previous != sources[0]:
        sources.append(previous)
    for path in sources:
        if not path.is_file():
            continue
        try:
            signature = _file_signature(path)
            synced = db.execute(
                "SELECT signature FROM legacy_source_files WHERE path = ?", (str(path),)
            ).fetchone()
            if synced and synced[0] == signature:
                continue
            with closing(
                sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
            ) as source:
                columns = {
                    row[1] for row in source.execute("PRAGMA table_info(memories)")
                }
                if (
                    not {"id", "memory_type", "content", "importance", "created_at"}
                    <= columns
                ):
                    Logger.notice(
                        f"구형 기억 파일 형식을 확인할 수 없어 이관을 건너뛰었습니다: {path}"
                    )
                    continue
                with db:
                    db.execute("BEGIN IMMEDIATE")
                    for row in source.execute(
                        """SELECT id, memory_type, content, importance, created_at FROM memories
                           ORDER BY created_at, id"""
                    ):
                        fingerprint = hashlib.sha256(
                            json.dumps(
                                row,
                                ensure_ascii=True,
                                default=lambda blob: {"blob": blob.hex()},
                            ).encode("ascii")
                        ).hexdigest()
                        if db.execute(
                            "SELECT 1 FROM legacy_imports WHERE fingerprint = ?",
                            (fingerprint,),
                        ).fetchone():
                            continue
                        original, kind, content, weight, stamp = row
                        occupied = db.execute(
                            "SELECT 1 FROM legacy_records WHERE id = ?", (original,)
                        ).fetchone()
                        cur = db.execute(
                            """INSERT INTO legacy_records(id, memory_type, content, importance, created_at)
                               VALUES (?, ?, ?, ?, ?)""",
                            (
                                None if occupied else original,
                                kind,
                                content,
                                weight,
                                stamp,
                            ),
                        )
                        db.execute(
                            "INSERT INTO legacy_imports VALUES (?, ?, ?)",
                            (fingerprint, original, cur.lastrowid),
                        )
                        project_legacy(db, kind, content, weight, stamp)
                    if signature == _file_signature(path):
                        db.execute(
                            "INSERT OR REPLACE INTO legacy_source_files VALUES (?, ?)",
                            (str(path), signature),
                        )
        except (OSError, sqlite3.Error, ValueError, TypeError) as error:
            Logger.notice(
                f"구형 기억 파일을 이관하지 못했습니다. 원본을 보존했습니다: {path}"
            )
            Logger.error(str(error))


def _retire_legacy(db, kind, content):
    """구형 마지막 원본이 삭제되면 그 원본에서 가져온 활성 사실만 이력으로 전환한다."""
    fields = _normalized(kind, content)
    if (
        fields
        and not db.execute(
            "SELECT 1 FROM legacy_records WHERE memory_type IS ? AND content IS ?",
            (kind, content),
        ).fetchone()
    ):
        db.execute(
            """UPDATE main.memories SET status = 'superseded' WHERE content = ?
               AND source = 'legacy_import' AND status = 'active'""",
            (fields[3],),
        )


def legacy_view(db):
    """구형 연결 한 개에서만 memories 이름을 호환 뷰로 제공하고 쓰기를 현재 DB에 전달한다."""
    db.create_function("lucid_legacy_fact", 4, lambda *args: project_legacy(db, *args))
    db.create_function(
        "lucid_retire_legacy", 2, lambda *args: _retire_legacy(db, *args)
    )
    db.executescript("""
        CREATE TEMP VIEW memories AS
            SELECT id, memory_type, content, importance, created_at FROM main.legacy_records;
        CREATE TEMP TRIGGER legacy_insert INSTEAD OF INSERT ON memories BEGIN
            INSERT INTO legacy_records(id, memory_type, content, importance, created_at)
            VALUES(NEW.id, NEW.memory_type, NEW.content, NEW.importance, COALESCE(NEW.created_at, CURRENT_TIMESTAMP));
        END;
        CREATE TEMP TRIGGER legacy_materialize AFTER INSERT ON main.legacy_records BEGIN
            SELECT lucid_legacy_fact(NEW.memory_type, NEW.content, NEW.importance, NEW.created_at);
        END;
        CREATE TEMP TRIGGER legacy_delete INSTEAD OF DELETE ON memories BEGIN
            DELETE FROM legacy_records WHERE id = OLD.id;
            SELECT lucid_retire_legacy(OLD.memory_type, OLD.content);
        END;
        CREATE TEMP TRIGGER legacy_update INSTEAD OF UPDATE ON memories BEGIN
            UPDATE legacy_records SET id = NEW.id, memory_type = NEW.memory_type,
                   content = NEW.content, importance = NEW.importance, created_at = NEW.created_at
            WHERE id = OLD.id;
            SELECT lucid_retire_legacy(OLD.memory_type, OLD.content);
            SELECT lucid_legacy_fact(NEW.memory_type, NEW.content, NEW.importance, NEW.created_at);
        END;
    """)
