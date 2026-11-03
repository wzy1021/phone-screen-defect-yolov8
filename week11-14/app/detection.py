# -*- coding: utf-8 -*-
"""检测模块：加载 YOLOv8 模型、推理、后处理、画框。

对外只暴露一个 DefectDetector 类：
    det = DefectDetector(model_path)
    out = det.detect(image_path, conf=0.25)
    out['defects']     # 缺陷列表（归一化坐标）
    out['annotated']   # 画好框的 PIL 图片
    out['cost_ms']     # 推理耗时
"""
from __future__ import annotations

import os
import threading
import time

from PIL import Image, ImageDraw, ImageFont, ImageOps

from config import Config, class_map

FONT_CANDIDATES = [
    r'C:\Windows\Fonts\msyh.ttc',
    r'C:\Windows\Fonts\msyhbd.ttc',
    r'C:\Windows\Fonts\simhei.ttf',
    '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
]


class ModelNotFoundError(RuntimeError):
    pass


def _load_font(size: int):
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return ImageFont.load_default()


class DefectDetector:
    """YOLOv8 推理封装。模型在第一次检测时加载，之后复用。"""

    def __init__(self, model_path: str, imgsz: int = 640, device: str | None = None):
        self.model_path = model_path
        self.imgsz = imgsz
        self.device = device
        self.model = None
        self.lock = threading.Lock()
        self.classes = class_map()

    # -------------------------------------------------------------- 模型
    def _ensure_model(self):
        if self.model is not None:
            return
        if not os.path.exists(self.model_path):
            raise ModelNotFoundError(
                f'模型文件不存在：{self.model_path}，请先运行 train/train.py 训练模型')
        try:
            from ultralytics import YOLO   # 延迟导入，加快网页启动
        except ImportError as exc:
            raise ModelNotFoundError(
                '当前 Python 环境没有安装 ultralytics/torch，无法加载模型。'
                '请用 启动系统.bat 启动（它会使用 conda 环境 diffusion-course），'
                '或在当前环境执行 pip install -r requirements.txt') from exc

        if self.device is None:
            try:
                import torch
                self.device = 0 if torch.cuda.is_available() else 'cpu'
            except Exception:
                self.device = 'cpu'
        self.model = YOLO(self.model_path)
        # 预热：第一张图通常比较慢，先用空白图跑一次
        try:
            import numpy as np
            self.model.predict(np.zeros((self.imgsz, self.imgsz, 3), dtype='uint8'),
                               imgsz=self.imgsz, verbose=False, device=self.device)
        except Exception:
            pass

    @property
    def loaded(self) -> bool:
        return self.model is not None

    # -------------------------------------------------------------- 推理
    def detect(self, image_path: str, conf: float | None = None,
               iou: float | None = None, use_roi: bool | None = None) -> dict:
        self._ensure_model()
        conf = Config.DEFAULT_CONF if conf is None else float(conf)
        iou = Config.DEFAULT_IOU if iou is None else float(iou)
        if use_roi is None:
            use_roi = getattr(Config, 'USE_ROI', True)

        with Image.open(image_path) as im:
            img = ImageOps.exif_transpose(im).convert('RGB')
        width, height = img.size

        # 先找手机区域再检测：背景里的水花/反光不参与推理，小缺陷相对变大
        roi = None
        if use_roi:
            try:
                from .roi import find_screen_bbox
                roi = find_screen_bbox(img)
            except Exception:
                roi = None
        proc = img.crop(roi) if roi else img
        off_x, off_y = (roi[0], roi[1]) if roi else (0, 0)

        with self.lock:
            t0 = time.perf_counter()
            result = self.model.predict(
                source=proc, imgsz=self.imgsz, conf=conf, iou=iou,
                device=self.device, verbose=False)[0]
            cost_ms = int((time.perf_counter() - t0) * 1000)

        defects = []
        boxes = getattr(result, 'boxes', None)
        if boxes is not None and len(boxes) > 0:
            xyxy = boxes.xyxy.cpu().numpy()
            confs = boxes.conf.cpu().numpy()
            clses = boxes.cls.cpu().numpy().astype(int)
            for (x0, y0, x1, y1), cf, cid in zip(xyxy, confs, clses):
                x0 = max(0.0, min(float(x0) + off_x, width - 1))
                y0 = max(0.0, min(float(y0) + off_y, height - 1))
                x1 = max(0.0, min(float(x1) + off_x, width - 1))
                y1 = max(0.0, min(float(y1) + off_y, height - 1))
                if x1 - x0 < 2 or y1 - y0 < 2:
                    continue
                info = self.classes.get(int(cid), {'name': str(cid), 'cn': str(cid), 'color': '#ffffff'})
                bw = (x1 - x0) / width
                bh = (y1 - y0) / height
                # 亮点/暗点是“坏点”，尺寸很小；大块亮斑多半是水珠或反光，过滤掉
                if info['name'] in ('bright_spot', 'dark_spot'):
                    limit = getattr(Config, 'MAX_SPOT_SIZE', 0.025)
                    if max(bw, bh) > limit:
                        continue
                defects.append({
                    'class_id': int(cid),
                    'class_name': info['name'],
                    'class_cn': info['cn'],
                    'color': info['color'],
                    'conf': round(float(cf), 4),
                    'x': round((x0 + x1) / 2 / width, 6),
                    'y': round((y0 + y1) / 2 / height, 6),
                    'w': round(bw, 6),
                    'h': round(bh, 6),
                })

        defects.sort(key=lambda d: d['conf'], reverse=True)
        annotated = self.annotate(img, defects)
        return {'defects': defects, 'width': width, 'height': height,
                'cost_ms': cost_ms, 'conf': conf, 'iou': iou,
                'annotated': annotated}

    # -------------------------------------------------------------- 画框
    def annotate(self, img: Image.Image, defects: list[dict]) -> Image.Image:
        if not defects:
            return img.copy()
        draw = ImageDraw.Draw(img, 'RGBA')
        width, height = img.size
        base = max(12, int(min(width, height) * 0.026))
        font = _load_font(base)
        font_small = _load_font(max(11, int(base * 0.82)))
        line_w = max(2, int(min(width, height) / 280))

        for d in defects:
            color = d.get('color', '#ff4d4f')
            rgb = tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))
            x0 = (d['x'] - d['w'] / 2) * width
            y0 = (d['y'] - d['h'] / 2) * height
            x1 = (d['x'] + d['w'] / 2) * width
            y1 = (d['y'] + d['h'] / 2) * height
            # 半透明外发光，暗背景上也能看清
            draw.rounded_rectangle([x0 - 2, y0 - 2, x1 + 2, y1 + 2], radius=4,
                                   outline=rgb + (70,), width=line_w + 3)
            draw.rounded_rectangle([x0, y0, x1, y1], radius=4,
                                   outline=rgb + (255,), width=line_w)
            label = f"{d['class_cn']} {d['conf']:.2f}"
            tb = draw.textbbox((0, 0), label, font=font)
            tw, th = tb[2] - tb[0], tb[3] - tb[1]
            ty = y0 - th - 8
            if ty < 0:
                ty = y1 + 4
            tx = min(max(0, x0), max(0, width - tw - 12))
            draw.rounded_rectangle([tx, ty, tx + tw + 12, ty + th + 8], radius=3,
                                   fill=rgb + (235,))
            draw.text((tx + 6, ty + 2), label, font=font, fill=(255, 255, 255, 255))

        # 左上角叠加一行统计，方便演示时一眼看结果
        summary = f'检出 {len(defects)} 处缺陷'
        tb = draw.textbbox((0, 0), summary, font=font_small)
        draw.rounded_rectangle([10, 10, 10 + (tb[2] - tb[0]) + 16, 10 + (tb[3] - tb[1]) + 12],
                               radius=4, fill=(0, 0, 0, 130))
        draw.text((18, 14), summary, font=font_small, fill=(255, 255, 255, 235))
        return img


def get_detector() -> DefectDetector:
    """按当前应用配置取得检测器（进程内只创建一个）。"""
    from flask import current_app

    det = current_app.extensions.get('detector')
    if det is None:
        det = DefectDetector(
            model_path=current_app.config['MODEL_PATH'],
            imgsz=current_app.config['IMG_SIZE'],
        )
        current_app.extensions['detector'] = det
    return det
