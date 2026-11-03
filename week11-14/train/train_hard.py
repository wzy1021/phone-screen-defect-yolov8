# -*- coding: utf-8 -*-
"""在“困难版”数据集上训练小目标模型（低对比度、微小缺陷、强干扰）。

和 train.py 的区别：Mosaic 更弱、缩放更小、copy-paste 更强，
避免把本来就只有几像素的缺陷再缩小。结果写到 train/runs_hard/，
不会覆盖原来的 v1 模型和指标。

用法：
    python train/train_hard.py --epochs 45 --device 0
    python train/train_hard.py --epochs 40 --device cpu --profile cpu
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(BASE)
DATA = os.path.join(PROJECT, 'datasets_hard', 'data_hard.yaml')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default=DATA)
    ap.add_argument('--model', default='yolov8n.pt')
    ap.add_argument('--epochs', type=int, default=45)
    ap.add_argument('--imgsz', type=int, default=640)
    ap.add_argument('--batch', type=int, default=16)
    ap.add_argument('--device', default='0')
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--name', default='hard_yolov8n')
    ap.add_argument('--profile', choices=['default', 'cpu'], default='default')
    ap.add_argument('--project', default=os.path.join(BASE, 'runs_hard'))
    ap.add_argument('--metrics', default=os.path.join(PROJECT, 'models', 'metrics_hard.json'))
    ap.add_argument('--mosaic', type=float, default=0.2)
    ap.add_argument('--scale', type=float, default=0.2)
    ap.add_argument('--lr0', type=float, default=0.003)
    ap.add_argument('--copy-paste', type=float, default=0.3)
    args = ap.parse_args()
    if args.profile == 'cpu':
        args.device = 'cpu'
        args.workers = 0
        args.batch = min(args.batch, 8)

    from ultralytics import YOLO
    t0 = time.time()
    model = YOLO(args.model)
    model.train(
        data=args.data, epochs=args.epochs, imgsz=args.imgsz, batch=args.batch,
        device=args.device, workers=args.workers, seed=0,
        project=args.project, name=args.name, exist_ok=True,
        optimizer='AdamW', lr0=args.lr0, lrf=0.01, weight_decay=0.0005,
        warmup_epochs=3.0, cos_lr=True, patience=15,
        # 微小目标：弱 Mosaic、不要缩小、增强 copy-paste
        mosaic=args.mosaic, close_mosaic=0, scale=args.scale, translate=0.05,
        degrees=5.0, shear=1.0, perspective=0.0,
        copy_paste=args.copy_paste, mixup=0.0, erasing=0.1,
        hsv_h=0.015, hsv_s=0.4, hsv_v=0.45, fliplr=0.5, flipud=0.0,
        plots=True, verbose=True,
    )

    run_dir = os.path.join(args.project, args.name)
    best = os.path.join(run_dir, 'weights', 'best.pt')
    best_model = YOLO(best)
    val = best_model.val(data=args.data, split='test', imgsz=args.imgsz,
                         batch=args.batch, device=args.device, plots=True,
                         project=os.path.join(BASE, 'runs_hard'), name=f'{args.name}_test')
    box = val.box
    names = val.names if isinstance(val.names, dict) else dict(enumerate(val.names))
    per_class = []
    for i in range(len(names)):
        rec = {'class_id': i, 'class_name': names[i]}
        try:
            rec.update({'precision': round(float(box.p[i]), 4),
                        'recall': round(float(box.r[i]), 4),
                        'map50': round(float(box.ap50[i]), 4),
                        'map50_95': round(float(box.ap[i]), 4)})
        except Exception:
            rec.update({'precision': None, 'recall': None, 'map50': None, 'map50_95': None})
        per_class.append(rec)
    metrics = {
        'model': 'best.pt',
        'train_seconds': round(time.time() - t0, 1),
        'epochs': args.epochs, 'imgsz': args.imgsz, 'batch': args.batch,
        'dataset': args.data,
        'test': {'precision': round(float(box.mp), 4), 'recall': round(float(box.mr), 4),
                 'map50': round(float(box.map50), 4), 'map50_95': round(float(box.map), 4)},
        'per_class': per_class,
        'speed_ms': {k: round(float(v), 2) for k, v in val.speed.items()} if isinstance(val.speed, dict) else {},
    }
    out = args.metrics
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    print(json.dumps(metrics['test'], ensure_ascii=False))
    print('model:', best)
    print('metrics:', out)


if __name__ == '__main__':
    main()

