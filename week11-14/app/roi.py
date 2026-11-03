# -*- coding: utf-8 -*-
"""自动找手机屏幕区域，供检测时聚焦，减少背景反光/水花的误检。

做法：Canny 边缘 -> 膨胀连成闭合轮廓 -> 取面积大、形状接近手机的轮廓的外接矩形。
找不到就返回 None，检测退回整张图，不会因为这一步失败而报错。
"""
from __future__ import annotations

import numpy as np
from PIL import Image


def find_screen_bbox(img: Image.Image, min_area_ratio=0.05, max_area_ratio=0.95):
    """返回手机区域 (x0, y0, x1, y1)，失败返回 None。"""
    try:
        import cv2
    except Exception:
        return None

    rgb = np.asarray(img.convert('RGB'))
    h, w = rgb.shape[:2]
    if max(h, w) > 1280:                       # 缩小后再找轮廓，速度快
        scale = 1280 / max(h, w)
        small = cv2.resize(rgb, (int(w * scale), int(h * scale)))
    else:
        scale = 1.0
        small = rgb
    gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(gray, 40, 120)
    edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=2)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    sh, sw = small.shape[:2]
    best, best_score = None, 0.0
    for c in contours:
        area = cv2.contourArea(c)
        ratio = area / (sw * sh)
        if not (min_area_ratio <= ratio <= max_area_ratio):
            continue
        x, y, bw, bh = cv2.boundingRect(c)
        if bw < 40 or bh < 40:
            continue
        aspect = bw / max(bh, 1)
        if not (0.35 <= aspect <= 2.2):        # 手机整体外接矩形不会太扁
            continue
        hull = cv2.convexHull(c)
        hull_area = cv2.contourArea(hull)
        solidity = area / max(hull_area, 1.0)
        if solidity < 0.55:
            continue
        score = ratio * solidity
        if score > best_score:
            best_score = score
            best = (x, y, x + bw, y + bh)

    if best is None:
        return None
    # 放大回原图，留一点边，避免切掉边缘崩缺
    x0, y0, x1, y1 = [int(v / scale) for v in best]
    pad_x = int((x1 - x0) * 0.04)
    pad_y = int((y1 - y0) * 0.04)
    return (max(0, x0 - pad_x), max(0, y0 - pad_y),
            min(w, x1 + pad_x), min(h, y1 + pad_y))
