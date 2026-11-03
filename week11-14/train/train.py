# -*- coding: utf-8 -*-
"""训练手机屏幕缺陷检测模型（YOLOv8n）。

流程：
    1. 用 COCO 预训练的 yolov8n.pt 做迁移学习；
    2. 在 datasets/data.yaml 上训练，验证集挑选最优权重；
    3. 训练结束后在 test 划分上做一次最终评估，把指标写成 metrics.json；
    4. 把 best.pt 复制到 models/best.pt，训练曲线复制到 docs/figures/。

用法：
    python train.py                       # 默认 80 轮，GPU 0
    python train.py --epochs 2 --device cpu --name smoke
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(BASE)
DEFAULT_DATA = os.path.join(PROJECT, 'datasets', 'data.yaml')


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default=DEFAULT_DATA)
    ap.add_argument('--model', default='yolov8n.pt', help='预训练权重，没有会自动下载')
    ap.add_argument('--epochs', type=int, default=80)
    ap.add_argument('--imgsz', type=int, default=640)
    ap.add_argument('--batch', type=int, default=16)
    ap.add_argument('--device', default='0', help='0 表示第一块显卡，cpu 表示用处理器')
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--patience', type=int, default=20)
    ap.add_argument('--name', default='phonescreen_yolov8n')
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--profile', choices=['default', 'cpu', 'small'], default='default',
                    help='cpu：CPU 训练参数（workers=0、batch=8、关 AMP）；small：小目标参数（960 输入、弱 Mosaic/缩放）')
    ap.add_argument('--mosaic', type=float, default=0.8)
    ap.add_argument('--scale', type=float, default=0.5)
    ap.add_argument('--close-mosaic', type=int, default=10)
    ap.add_argument('--freeze', type=int, default=None, help='冻结前 N 层，CPU 微调时可用 10')
    return ap.parse_args()


def apply_profile(args):
    """按训练场景调整参数。CPU 训练不是效果差的原因，但参数要相应改小。"""
    if args.profile == 'cpu':
        if args.device == '0':
            args.device = 'cpu'
        args.workers = 0          # Windows 上 CPU 多进程 DataLoader 容易卡住
        args.batch = min(args.batch, 8)
        args.epochs = min(args.epochs, 40)
        print('CPU 配置：device=cpu, workers=0, batch<=8, epochs<=40, AMP 关闭')
    elif args.profile == 'small':
        args.imgsz = 960
        args.mosaic = 0.2         # 微小目标不适合强 Mosaic
        args.scale = 0.2          # 不要把小缺陷再缩小
        args.close_mosaic = 0
        print('小目标配置：imgsz=960, mosaic=0.2, scale=0.2, close_mosaic=0')
    return args


def main():
    args = apply_profile(parse_args())
    from ultralytics import YOLO

    if not os.path.exists(args.data):
        sys.exit(f'找不到数据集配置：{args.data}，请先运行 datasets/gen_dataset.py')
    os.makedirs(os.path.join(BASE, 'runs'), exist_ok=True)
    t0 = time.time()

    model = YOLO(args.model)
    train_kwargs = dict(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        workers=args.workers,
        patience=args.patience,
        seed=args.seed,
        project=os.path.join(BASE, 'runs'),
        name=args.name,
        exist_ok=True,
        optimizer='AdamW',
        lr0=0.005,
        lrf=0.01,
        weight_decay=0.0005,
        warmup_epochs=3.0,
        cos_lr=True,
        amp=(args.profile != 'cpu'),
        # 数据增强：翻转、亮度、旋转、缩放、Mosaic、MixUp
        hsv_h=0.015,
        hsv_s=0.5,
        hsv_v=0.35,
        degrees=8.0,
        translate=0.10,
        scale=args.scale,
        shear=2.0,
        perspective=0.0005,
        fliplr=0.5,
        flipud=0.0,
        mosaic=args.mosaic,
        mixup=0.1,
        copy_paste=0.1,
        erasing=0.2,
        close_mosaic=args.close_mosaic,
        plots=True,
        verbose=True,
    )
    if args.freeze:
        train_kwargs['freeze'] = args.freeze
    model.train(**train_kwargs)

    run_dir = os.path.join(BASE, 'runs', args.name)
    best = os.path.join(run_dir, 'weights', 'best.pt')
    if not os.path.exists(best):
        sys.exit(f'训练没有产出 best.pt：{best}')

    # 在测试集上做最终评估
    print('\n=== 在 test 划分上评估 ===', flush=True)
    best_model = YOLO(best)
    val = best_model.val(data=args.data, split='test', imgsz=args.imgsz,
                         batch=args.batch, device=args.device, plots=True,
                         project=os.path.join(BASE, 'runs'), name=f'{args.name}_test')
    box = val.box

    names = val.names if isinstance(val.names, dict) else {i: n for i, n in enumerate(val.names)}
    per_class = []
    for i in range(len(names)):
        rec = {'class_id': i, 'class_name': names[i]}
        try:
            rec['precision'] = round(float(box.p[i]), 4)
            rec['recall'] = round(float(box.r[i]), 4)
            rec['map50'] = round(float(box.ap50[i]), 4)
            rec['map50_95'] = round(float(box.ap[i]), 4)
        except Exception:
            rec.update({'precision': None, 'recall': None, 'map50': None, 'map50_95': None})
        per_class.append(rec)

    metrics = {
        'model': os.path.basename(best),
        'train_seconds': round(time.time() - t0, 1),
        'epochs': args.epochs,
        'imgsz': args.imgsz,
        'batch': args.batch,
        'dataset': args.data,
        'test': {
            'precision': round(float(box.mp), 4),
            'recall': round(float(box.mr), 4),
            'map50': round(float(box.map50), 4),
            'map50_95': round(float(box.map), 4),
        },
        'per_class': per_class,
        'speed_ms': {k: round(float(v), 2) for k, v in
                     (val.speed.items() if isinstance(val.speed, dict) else [])},
    }

    # 归档模型和评估指标
    models_dir = os.path.join(PROJECT, 'models')
    os.makedirs(models_dir, exist_ok=True)
    shutil.copy2(best, os.path.join(models_dir, 'best.pt'))
    with open(os.path.join(PROJECT, 'models', 'metrics.json'), 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    with open(os.path.join(run_dir, 'metrics.json'), 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    # 把训练图复制到文档配图目录
    fig_dir = os.path.join(PROJECT, 'docs', 'figures')
    os.makedirs(fig_dir, exist_ok=True)
    for src, dst in [('results.png', 'train_results.png'),
                     ('confusion_matrix_normalized.png', 'train_confusion_matrix.png'),
                     ('PR_curve.png', 'train_pr_curve.png'),
                     ('labels.jpg', 'train_labels.jpg'),
                     ('val_batch0_pred.jpg', 'train_val_pred.jpg'),
                     ('val_batch0_labels.jpg', 'train_val_labels.jpg')]:
        p = os.path.join(run_dir, src)
        if os.path.exists(p):
            shutil.copy2(p, os.path.join(fig_dir, dst))
    test_run = os.path.join(BASE, 'runs', f'{args.name}_test')
    for src, dst in [('confusion_matrix_normalized.png', 'test_confusion_matrix.png'),
                     ('PR_curve.png', 'test_pr_curve.png')]:
        p = os.path.join(test_run, src)
        if os.path.exists(p):
            shutil.copy2(p, os.path.join(fig_dir, dst))

    print('\n=== 完成 ===')
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(f'模型：{os.path.join(models_dir, "best.pt")}')
    print(f'指标：{os.path.join(models_dir, "metrics.json")}')
    print(f'训练用时：{metrics["train_seconds"] / 60:.1f} 分钟')


if __name__ == '__main__':
    main()
