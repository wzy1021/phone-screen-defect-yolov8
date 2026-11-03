# -*- coding: utf-8 -*-
"""生成演示用的检测记录（用真实模型跑 test 集图片）。

用途：答辩演示或截图时，历史记录页、统计页不是空的。
不会改动账号，只清理/写入检测记录和图片文件。

用法：
    python scripts/seed_demo.py --count 24 --reset
"""
from __future__ import annotations

import argparse
import os
import random
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from PIL import Image  # noqa: E402

from app import create_app  # noqa: E402
from app import db as dbm  # noqa: E402
from app.detection import DefectDetector  # noqa: E402
from app.utils import unique_name  # noqa: E402
from config import Config  # noqa: E402

DATA = BASE / 'datasets'


def pick_images(count, seed=20261105):
    rng = random.Random(seed)
    test_dir = DATA / 'images' / 'test'
    label_dir = DATA / 'labels' / 'test'
    buckets = {i: [] for i in range(len(Config.CLASSES))}
    clean = []
    for img in sorted(test_dir.glob('*.jpg')):
        lbl = label_dir / (img.stem + '.txt')
        ids = set()
        if lbl.exists():
            for line in lbl.read_text(encoding='utf-8').splitlines():
                if line.strip():
                    ids.add(int(line.split()[0]))
        if not ids:
            clean.append(img)
        for cid in ids:
            buckets[cid].append(img)

    chosen, used = [], set()
    # 每类轮着取，保证统计图每一类都有数据
    for _ in range(count - 2):
        for cid in range(len(Config.CLASSES)):
            if len(chosen) >= count - 2:
                break
            pool = [p for p in buckets[cid] if p not in used]
            if not pool:
                continue
            p = rng.choice(pool)
            chosen.append(p)
            used.add(p)
    # 加两张没有缺陷的，演示“未发现缺陷”
    for p in rng.sample(clean, min(2, len(clean))):
        if p not in used:
            chosen.append(p)
    return chosen[:count]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--count', type=int, default=24)
    ap.add_argument('--reset', action='store_true', help='先清空已有检测记录和图片')
    args = ap.parse_args()

    app = create_app()
    with app.app_context():
        db = dbm.get_db()
        if args.reset:
            db.execute('DELETE FROM t_defect')
            db.execute('DELETE FROM t_record')
            db.commit()
            for folder in (Path(app.config['UPLOAD_DIR']), Path(app.config['RESULT_DIR'])):
                for f in folder.glob('*'):
                    if f.is_file():
                        f.unlink()
            print('已清空原有记录')

        admin = dbm.get_user_by_name('admin')
        user = dbm.get_user_by_name('user')
        images = pick_images(args.count)
        if not images:
            sys.exit('test 集没有图片，请先运行 datasets/gen_dataset.py')

        det = DefectDetector(app.config['MODEL_PATH'], imgsz=app.config['IMG_SIZE'])
        now = datetime.now()
        total_defects = 0
        for i, src in enumerate(images):
            stem = os.path.splitext(unique_name('demo'))[0]
            image_rel = f'uploads/{stem}.jpg'
            result_rel = f'results/res_{stem}.jpg'
            shutil.copy2(src, Path(app.config['UPLOAD_DIR']) / f'{stem}.jpg')
            out = det.detect(str(src), conf=0.25)
            out['annotated'].save(Path(app.config['RESULT_DIR']) / f'res_{stem}.jpg', 'JPEG', quality=92)
            owner = admin if i % 3 else user
            rid = dbm.create_record(owner['id'], image_rel, result_rel,
                                    len(out['defects']), 'done', 0.25,
                                    out['cost_ms'], out['defects'])
            # 把时间打散到最近 7 天，统计页的趋势图才有内容
            day = i % 7
            ts = (now - timedelta(days=day, hours=(i * 3) % 20, minutes=(i * 7) % 60))
            db.execute('UPDATE t_record SET created_at = ? WHERE id = ?',
                       (ts.strftime('%Y-%m-%d %H:%M:%S'), rid))
            db.commit()
            total_defects += len(out['defects'])
            print(f'[{i + 1}/{len(images)}] #{rid} {src.name} 检出 {len(out["defects"])} 处')

        stats = dbm.get_stats(None)
        print(f'\n完成：{stats["total_records"]} 条记录，{stats["total_defects"]} 个缺陷框，'
              f'平均耗时 {stats["avg_cost_ms"]} ms')


if __name__ == '__main__':
    main()

