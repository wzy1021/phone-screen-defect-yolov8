# -*- coding: utf-8 -*-
"""测量模型加载、接口端到端、页面响应等性能指标，写入 docs/perf.json。

运行前确保 models/best.pt 已训练好。脚本用临时数据库，不会污染 data.db；
测完会清理 static/uploads 和 static/results 里本次产生的文件。
"""
from __future__ import annotations

import io
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

from PIL import Image, ImageDraw

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
MODEL = BASE / 'models' / 'best.pt'
SAMPLE = next((BASE / 'datasets' / 'images' / 'test').glob('*.jpg'))

from app import create_app
from app.detection import DefectDetector


def image_bytes():
    img = Image.open(SAMPLE).convert('RGB').resize((960, 960))
    d = ImageDraw.Draw(img)
    d.line([(200, 300), (500, 500)], fill=(255, 255, 255), width=3)
    buf = io.BytesIO()
    img.save(buf, 'JPEG', quality=92)
    buf.seek(0)
    return buf


def cleanup():
    for folder in (BASE / 'static' / 'uploads', BASE / 'static' / 'results'):
        if folder.exists():
            for f in folder.iterdir():
                if f.is_file():
                    f.unlink()


def main():
    tmp = tempfile.mkdtemp(prefix='ps_perf_')
    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'perf',
        'DB_PATH': os.path.join(tmp, 'perf.db'),
    })

    t0 = time.perf_counter()
    det = DefectDetector(str(MODEL))
    det._ensure_model()
    load_s = time.perf_counter() - t0
    app.extensions['detector'] = det

    client = app.test_client()
    r = client.post('/api/login', json={'username': 'admin', 'password': '123456'})
    token = r.get_json()['data']['token']
    headers = {'X-Token': token}

    api_times, detect_ids = [], []
    for _ in range(10):
        t = time.perf_counter()
        r = client.post('/api/detect',
                        data={'file': (image_bytes(), 'perf.jpg'), 'conf': '0.25'},
                        headers=headers, content_type='multipart/form-data')
        api_times.append((time.perf_counter() - t) * 1000)
        if r.status_code == 200:
            detect_ids.append(r.get_json()['data']['record_id'])

    page_times = {}
    for path in ('/detect', '/history', '/stats'):
        ts = []
        for _ in range(5):
            t = time.perf_counter()
            r = client.get(path, headers=headers)
            ts.append((time.perf_counter() - t) * 1000)
        page_times[path] = round(sum(ts) / len(ts), 1)

    # 分页查询：在当前记录量下取一页
    t = time.perf_counter()
    client.get('/api/records?page=1&size=10', headers=headers)
    query_ms = (time.perf_counter() - t) * 1000

    perf = {
        'model_load_s': round(load_s, 2),
        'api_ms': round(sum(api_times) / len(api_times), 1),
        'api_min_ms': round(min(api_times), 1),
        'api_max_ms': round(max(api_times), 1),
        'page_ms': round(sum(page_times.values()) / len(page_times), 1),
        'page_detail': page_times,
        'batch10_s': round(sum(api_times) / 1000, 2),
        'query_ms': round(query_ms, 2),
        'records': len(detect_ids),
        'device': 'GPU' if det.device == 0 else 'CPU',
    }
    (BASE / 'docs' / 'perf.json').write_text(json.dumps(perf, ensure_ascii=False, indent=2),
                                             encoding='utf-8')
    print(json.dumps(perf, ensure_ascii=False, indent=2))

    # 清掉测量产生的记录和文件
    with app.app_context():
        from app import db as dbm
        db = dbm.get_db()
        db.execute('DELETE FROM t_defect')
        db.execute('DELETE FROM t_record')
        db.commit()
    cleanup()
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
