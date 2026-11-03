# -*- coding: utf-8 -*-
"""打印 data.db 的概况，供测试报告引用。"""
import sqlite3
from pathlib import Path

db = Path(__file__).resolve().parents[2] / 'week11-14' / 'data.db'
conn = sqlite3.connect(db)
print('tables:', [r[0] for r in conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")])
print('records:', conn.execute(
    'SELECT COUNT(*), ROUND(AVG(cost_ms),1), SUM(total) FROM t_record').fetchone())
print('users:', conn.execute('SELECT id, username, role FROM t_user').fetchall())
print('by class:', conn.execute(
    'SELECT class_name, COUNT(*) FROM t_defect GROUP BY class_name ORDER BY 2 DESC').fetchall())
print('time range:', conn.execute(
    'SELECT MIN(created_at), MAX(created_at) FROM t_record').fetchone())
print('per user:', conn.execute(
    'SELECT user_id, COUNT(*), SUM(total) FROM t_record GROUP BY user_id').fetchall())
print('config:', conn.execute('SELECT name, value FROM t_config').fetchall())
conn.close()
