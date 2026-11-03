# -*- coding: utf-8 -*-
"""SQLite 数据访问层。

统一在这里建表、增删改查，其他模块不直接写 SQL。
数据库文件默认是项目根目录下的 data.db。
"""
from __future__ import annotations

import sqlite3
from datetime import datetime

from flask import current_app, g

from config import Config, class_map

SCHEMA = """
CREATE TABLE IF NOT EXISTS t_user (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT    NOT NULL UNIQUE,
    password    TEXT    NOT NULL,
    role        TEXT    NOT NULL DEFAULT 'user',
    nickname    TEXT,
    avatar      TEXT,
    created_at  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS t_record (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    image_path  TEXT    NOT NULL,
    result_path TEXT,
    total       INTEGER NOT NULL DEFAULT 0,
    status      TEXT    NOT NULL DEFAULT 'done',
    conf        REAL    NOT NULL,
    cost_ms     INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL,
    FOREIGN KEY (user_id) REFERENCES t_user (id)
);

CREATE TABLE IF NOT EXISTS t_defect (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id   INTEGER NOT NULL,
    class_id    INTEGER NOT NULL,
    class_name  TEXT    NOT NULL,
    conf        REAL    NOT NULL,
    x           REAL    NOT NULL,
    y           REAL    NOT NULL,
    w           REAL    NOT NULL,
    h           REAL    NOT NULL,
    FOREIGN KEY (record_id) REFERENCES t_record (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS t_config (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT NOT NULL UNIQUE,
    value   TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_record_created ON t_record (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_record_user    ON t_record (user_id);
CREATE INDEX IF NOT EXISTS idx_defect_record  ON t_defect (record_id);
"""

DEFAULT_CONFIG = {
    'conf_threshold': '0.25',
    'iou_threshold': '0.45',
    'model_name': 'best.pt',
}


def get_db() -> sqlite3.Connection:
    """取得当前请求的数据库连接（每个请求一个）。"""
    if 'db' not in g:
        conn = sqlite3.connect(current_app.config['DB_PATH'])
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        g.db = conn
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def now_str() -> str:
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def init_db():
    """建表并写入默认账号、默认参数。可重复执行。"""
    from .auth import hash_password

    db = get_db()
    db.executescript(SCHEMA)
    # 老版本数据库没有 nickname / avatar，启动时自动补列
    cols = {row[1] for row in db.execute('PRAGMA table_info(t_user)')}
    if 'nickname' not in cols:
        db.execute('ALTER TABLE t_user ADD COLUMN nickname TEXT')
    if 'avatar' not in cols:
        db.execute('ALTER TABLE t_user ADD COLUMN avatar TEXT')
    db.execute("UPDATE t_user SET nickname = username WHERE nickname IS NULL OR nickname = ''")
    for u in Config.DEMO_USERS:
        db.execute(
            'INSERT OR IGNORE INTO t_user (username, password, role, created_at) VALUES (?, ?, ?, ?)',
            (u['username'], hash_password(u['password']), u['role'], now_str()))
    for name, value in DEFAULT_CONFIG.items():
        db.execute('INSERT OR IGNORE INTO t_config (name, value) VALUES (?, ?)', (name, value))
    db.commit()


def init_app(app):
    with app.app_context():
        init_db()
    app.teardown_appcontext(close_db)


# ------------------------------------------------------------------ 用户
def get_user_by_name(username: str):
    row = get_db().execute('SELECT * FROM t_user WHERE username = ?', (username,)).fetchone()
    return dict(row) if row else None


def create_user(username: str, password_hash: str, role: str = 'user') -> int:
    """新建用户；用户名重复时抛 sqlite3.IntegrityError。"""
    db = get_db()
    cur = db.execute(
        'INSERT INTO t_user (username, password, role, nickname, created_at) '
        'VALUES (?, ?, ?, ?, ?)',
        (username, password_hash, role, username, now_str()))
    db.commit()
    return cur.lastrowid


def get_user_by_id(user_id: int):
    row = get_db().execute('SELECT * FROM t_user WHERE id = ?', (user_id,)).fetchone()
    return dict(row) if row else None


def list_users() -> list[dict]:
    """管理员的用户列表：基本信息 + 检测次数/缺陷数/最近检测时间。"""
    rows = get_db().execute(
        'SELECT u.id, u.username, '
        "COALESCE(NULLIF(u.nickname, ''), u.username) AS nickname, "
        'u.role, u.avatar, u.created_at, '
        'COUNT(r.id) AS records, COALESCE(SUM(r.total), 0) AS defects, '
        'MAX(r.created_at) AS last_at '
        'FROM t_user u LEFT JOIN t_record r ON r.user_id = u.id '
        'GROUP BY u.id ORDER BY u.id').fetchall()
    return [dict(r) for r in rows]


def update_user_profile(user_id: int, nickname=None, avatar=None):
    fields, args = [], []
    if nickname is not None:
        fields.append('nickname = ?')
        args.append(nickname)
    if avatar is not None:
        fields.append('avatar = ?')
        args.append(avatar)
    if not fields:
        return
    db = get_db()
    db.execute(f'UPDATE t_user SET {", ".join(fields)} WHERE id = ?', args + [user_id])
    db.commit()


def get_user_summary(user_id: int) -> dict:
    row = get_db().execute(
        'SELECT COUNT(*) AS records, COALESCE(SUM(total), 0) AS defects, '
        'MAX(created_at) AS last_at FROM t_record WHERE user_id = ?', (user_id,)).fetchone()
    return dict(row)


# ------------------------------------------------------------------ 检测记录
def create_record(user_id: int, image_path: str, result_path: str, total: int,
                  status: str, conf: float, cost_ms: int, defects: list[dict]) -> int:
    db = get_db()
    cur = db.execute(
        'INSERT INTO t_record (user_id, image_path, result_path, total, status, conf, cost_ms, created_at) '
        'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (user_id, image_path, result_path, total, status, conf, cost_ms, now_str()))
    rid = cur.lastrowid
    for d in defects:
        db.execute(
            'INSERT INTO t_defect (record_id, class_id, class_name, conf, x, y, w, h) '
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (rid, d['class_id'], d['class_name'], d['conf'], d['x'], d['y'], d['w'], d['h']))
    db.commit()
    return rid


def _record_where(user_id, start=None, end=None, has_defect=None):
    where, args = [], []
    if user_id is not None:
        where.append('r.user_id = ?')
        args.append(user_id)
    if start:
        where.append('r.created_at >= ?')
        args.append(start + ' 00:00:00')
    if end:
        where.append('r.created_at <= ?')
        args.append(end + ' 23:59:59')
    if has_defect == 1:
        where.append('r.total > 0')
    elif has_defect == 0:
        where.append('r.total = 0')
    return (' WHERE ' + ' AND '.join(where)) if where else '', args


def list_records(user_id, page=1, size=10, start=None, end=None, has_defect=None):
    page = max(1, int(page))
    size = max(1, min(100, int(size)))
    clause, args = _record_where(user_id, start, end, has_defect)
    db = get_db()
    total = db.execute(f'SELECT COUNT(*) AS c FROM t_record r{clause}', args).fetchone()['c']
    rows = db.execute(
        f'SELECT r.*, u.username FROM t_record r JOIN t_user u ON u.id = r.user_id'
        f'{clause} ORDER BY r.id DESC LIMIT ? OFFSET ?',
        args + [size, (page - 1) * size]).fetchall()
    return {'total': total, 'page': page, 'size': size,
            'items': [dict(r) for r in rows]}


def get_record(record_id: int, user_id=None, is_admin=False):
    db = get_db()
    row = db.execute(
        'SELECT r.*, u.username FROM t_record r JOIN t_user u ON u.id = r.user_id WHERE r.id = ?',
        (record_id,)).fetchone()
    if not row:
        return None
    rec = dict(row)
    if not is_admin and user_id is not None and rec['user_id'] != user_id:
        return None      # 别人的记录当作不存在，避免越权
    defects = db.execute(
        'SELECT * FROM t_defect WHERE record_id = ? ORDER BY conf DESC', (record_id,)).fetchall()
    rec['defects'] = [dict(d) for d in defects]
    return rec


def delete_record(record_id: int, user_id=None, is_admin=False):
    db = get_db()
    rec = get_record(record_id, user_id, is_admin)
    if not rec:
        return None
    db.execute('DELETE FROM t_defect WHERE record_id = ?', (record_id,))
    db.execute('DELETE FROM t_record WHERE id = ?', (record_id,))
    db.commit()
    return rec


# ------------------------------------------------------------------ 统计
def get_stats(user_id, start=None, end=None):
    clause, args = _record_where(user_id, start, end)
    db = get_db()
    row = db.execute(
        f'SELECT COUNT(*) AS total_records, COALESCE(SUM(total), 0) AS total_defects, '
        f'COALESCE(AVG(cost_ms), 0) AS avg_cost_ms FROM t_record r{clause}',
        args).fetchone()

    today = datetime.now().strftime('%Y-%m-%d')
    tclause, targs = _record_where(user_id, start or today, end or today)
    today_count = db.execute(
        f'SELECT COUNT(*) AS c FROM t_record r{tclause}', targs).fetchone()['c']

    per_class = {c['name']: {'class_id': c['id'], 'class_name': c['name'], 'cn': c['cn'],
                             'color': c['color'], 'count': 0} for c in Config.CLASSES}
    rows = db.execute(
        f'SELECT d.class_id, COUNT(*) AS c FROM t_defect d '
        f'JOIN t_record r ON r.id = d.record_id{clause} GROUP BY d.class_id', args).fetchall()
    cmap = class_map()
    for r in rows:
        info = cmap.get(r['class_id'])
        if info:
            per_class[info['name']]['count'] = r['c']

    trend_rows = db.execute(
        f"SELECT substr(r.created_at, 1, 10) AS day, COUNT(*) AS c, "
        f"COALESCE(SUM(r.total), 0) AS d FROM t_record r{clause} "
        f"GROUP BY day ORDER BY day DESC LIMIT 7", args).fetchall()

    return {
        'total_records': row['total_records'],
        'total_defects': row['total_defects'],
        'today_records': today_count,
        'avg_cost_ms': round(row['avg_cost_ms'] or 0, 1),
        'per_class': list(per_class.values()),
        'trend': [dict(t) for t in reversed(trend_rows)],
    }


# ------------------------------------------------------------------ 参数
def get_settings() -> dict:
    rows = get_db().execute('SELECT name, value FROM t_config').fetchall()
    return {r['name']: r['value'] for r in rows}


def get_setting(name, default=None):
    row = get_db().execute('SELECT value FROM t_config WHERE name = ?', (name,)).fetchone()
    return row['value'] if row else default


def set_setting(name, value):
    db = get_db()
    db.execute('INSERT INTO t_config (name, value) VALUES (?, ?) '
               'ON CONFLICT(name) DO UPDATE SET value = excluded.value', (name, str(value)))
    db.commit()
