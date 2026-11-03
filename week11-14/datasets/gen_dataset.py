# -*- coding: utf-8 -*-
"""生成手机屏幕缺陷检测数据集（YOLO 格式）。

背景：
    课程设计期间很难收集到上千张带标注的真实屏幕缺陷照片，因此本项目用
    程序化渲染的方式合成数据集：随机生成桌面背景、手机外壳、玻璃屏幕和
    反光，再把六类缺陷按真实外观画到屏幕上。缺陷的画框由绘制时的几何位置
    直接换算，因此标签是准确的，不依赖人工标注。

    合成数据与真实照片之间存在“域差异”，这一点在《详细设计说明书》的数据集
    章节中有专门说明；真实照片的接入流程（LabelImg 标注 -> 放入同一目录结构）
    也已经预留。

输出结构：
    datasets/
      images/train/*.jpg   images/val/*.jpg   images/test/*.jpg
      labels/train/*.txt   labels/val/*.txt   labels/test/*.txt
      data.yaml
      dataset_stats.json

用法：
    python gen_dataset.py                 # 默认 800/140/140
    python gen_dataset.py --train 20 --val 4 --test 4 --out _demo
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# ------------------------------------------------------------------ 基本参数
SIZE = 640          # 最终图片边长
SS = 2              # 超采样倍数，先按 1280 画再缩小，边缘更自然
W = SIZE * SS

CLASSES = [
    ('scratch', '划痕'),
    ('crack', '裂纹'),
    ('bright_spot', '亮点'),
    ('dark_spot', '暗点'),
    ('stain', '污渍'),
    ('edge_chip', '边缘崩缺'),
]
CLASS_IDS = {name: i for i, (name, _) in enumerate(CLASSES)}
CLASS_WEIGHTS = [0.24, 0.18, 0.17, 0.14, 0.16, 0.11]

DEFECT_COUNT_P = [0.10, 0.25, 0.35, 0.20, 0.10]   # 0~4 个缺陷的概率


# ------------------------------------------------------------------ 小工具
def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def rand_color(rng, lo, hi):
    return tuple(rng.randint(lo, hi) for _ in range(3))


def add_noise(img: Image.Image, sigma: float) -> Image.Image:
    """给图片叠加高斯噪声。"""
    arr = np.asarray(img).astype(np.float32)
    noise = np.random.normal(0, sigma, arr.shape[:2])[..., None]
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def radial_glow(size, center, radius, color, alpha):
    """生成一张径向渐变的光斑图层。"""
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt((xx - center[0]) ** 2 + (yy - center[1]) ** 2)
    a = np.clip(1.0 - d / max(radius, 1), 0, 1) ** 2 * alpha
    layer = np.zeros((h, w, 4), dtype=np.uint8)
    layer[..., 0] = color[0]
    layer[..., 1] = color[1]
    layer[..., 2] = color[2]
    layer[..., 3] = a.astype(np.uint8)
    return Image.fromarray(layer, 'RGBA')


# ------------------------------------------------------------------ 背景
def make_background(rng) -> Image.Image:
    """桌面背景：渐变 + 纹理 + 暗角。"""
    mode = rng.choice(['wood', 'matte', 'fabric'])
    if mode == 'wood':
        base = (rng.randint(90, 130), rng.randint(70, 100), rng.randint(50, 75))
        c2 = (base[0] - 25, base[1] - 20, base[2] - 15)
    elif mode == 'matte':
        base = (rng.randint(40, 70), rng.randint(45, 75), rng.randint(50, 80))
        c2 = (base[0] - 15, base[1] - 15, base[2] - 12)
    else:
        base = (rng.randint(55, 90), rng.randint(60, 95), rng.randint(70, 105))
        c2 = (base[0] + 10, base[1] + 10, base[2] + 12)

    top = np.linspace(0, 1, W)[:, None, None]
    arr = np.zeros((W, W, 3), dtype=np.float32)
    for i in range(3):
        arr[..., i] = base[i] * (1 - top[..., 0] * 0.35) + c2[i] * top[..., 0] * 0.35

    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    draw = ImageDraw.Draw(img, 'RGBA')

    if mode == 'wood':
        # 木纹：一组略微弯曲的细线
        for _ in range(rng.randint(18, 30)):
            y0 = rng.randint(-100, W + 100)
            amp = rng.randint(4, 18)
            pts = [(x, y0 + amp * math.sin(x / rng.randint(90, 200) + rng.random() * 6))
                   for x in range(-50, W + 50, 40)]
            draw.line(pts, fill=(base[0] - 20, base[1] - 18, base[2] - 12, rng.randint(20, 45)),
                      width=rng.randint(1, 4))
    elif mode == 'matte':
        # 磨砂桌面：随机小斑点
        for _ in range(rng.randint(1200, 2200)):
            x, y = rng.randint(0, W), rng.randint(0, W)
            r = rng.randint(0, 2)
            draw.ellipse([x, y, x + r, y + r], fill=(255, 255, 255, rng.randint(5, 18)))
    else:
        # 布料：交叉斜纹
        step = rng.randint(26, 42)
        for k in range(-W, W * 2, step):
            draw.line([(k, 0), (k - W, W)], fill=(255, 255, 255, 10), width=2)
            draw.line([(k, 0), (k + W, W)], fill=(0, 0, 0, 12), width=2)

    # 光从左上角来
    img = Image.alpha_composite(
        img.convert('RGBA'),
        radial_glow((W, W), (rng.randint(0, W // 2), 0), W * 0.8, (255, 250, 235), 26)
    ).convert('RGB')
    # 暗角
    yy, xx = np.mgrid[0:W, 0:W]
    d = np.sqrt((xx - W / 2) ** 2 + (yy - W / 2) ** 2) / (W * 0.72)
    vig = np.clip(1 - 0.45 * d ** 2, 0.55, 1.0)[..., None]
    arr = np.asarray(img).astype(np.float32) * vig
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    return add_noise(img, rng.uniform(2.0, 4.5))


# ------------------------------------------------------------------ 手机和屏幕
def phone_geometry(rng):
    # 手机整体要完整落在画面里，长宽比按 2.05 左右，最大高度不超过画布 92%
    body_w = rng.uniform(0.34, 0.43) * W
    body_h = body_w * rng.uniform(2.00, 2.12)
    cx = W / 2 + rng.uniform(-0.025, 0.025) * W
    cy = W / 2 + rng.uniform(-0.020, 0.020) * W
    x0, y0 = cx - body_w / 2, cy - body_h / 2
    x1, y1 = cx + body_w / 2, cy + body_h / 2
    rim = body_w * rng.uniform(0.016, 0.026)
    sx0, sy0, sx1, sy1 = x0 + rim, y0 + rim * 1.4, x1 - rim, y1 - rim * 1.4
    return dict(cx=cx, cy=cy, x0=x0, y0=y0, x1=x1, y1=y1,
                sx0=sx0, sy0=sy0, sx1=sx1, sy1=sy1,
                radius=body_w * 0.11, screen_radius=body_w * 0.075)


def screen_mask(geo):
    m = Image.new('L', (W, W), 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([geo['sx0'], geo['sy0'], geo['sx1'], geo['sy1']],
                        radius=geo['screen_radius'], fill=255)
    return m


def draw_screen_background(geo, rng):
    """屏幕底色：息屏（深色玻璃 + 反光）或亮屏（彩色壁纸）。"""
    sw = int(geo['sx1']) - int(geo['sx0'])
    sh = int(geo['sy1']) - int(geo['sy0'])
    on = rng.random() < 0.45

    if not on:
        top = np.array(rand_color(rng, 8, 22), dtype=np.float32)
        bottom = np.array(rand_color(rng, 18, 38), dtype=np.float32)
        t = np.linspace(0, 1, sh)[:, None, None]
        arr = top + (bottom - top) * t
        arr = np.repeat(arr, sw, axis=1)
        screen = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        # 斜向玻璃反光：先画在单独图层上再模糊，避免出现生硬的斜条
        refl = Image.new('RGBA', (sw, sh), (0, 0, 0, 0))
        rd = ImageDraw.Draw(refl)
        for _ in range(rng.randint(2, 3)):
            bx = rng.randint(-sw, sw)
            bw = rng.randint(sw // 6, sw // 3)
            rd.polygon([(bx, 0), (bx + bw, 0), (bx + bw + sh * 0.45, sh), (bx + sh * 0.45, sh)],
                       fill=(235, 242, 255, rng.randint(26, 52)))
        refl = refl.filter(ImageFilter.GaussianBlur(rng.uniform(18, 34)))
        screen = Image.alpha_composite(screen.convert('RGBA'), refl)
        # 高光
        screen = Image.alpha_composite(
            screen, radial_glow((sw, sh), (rng.randint(0, sw), rng.randint(0, sh // 2)),
                                sw * 0.7, (255, 255, 255), 16))
        screen = screen.convert('RGB')
    else:
        # 亮屏：双色渐变 + 低频波浪 + 模糊色块，接近真实壁纸
        yy, xx = np.mgrid[0:sh, 0:sw]
        u, v = xx / max(sw - 1, 1), yy / max(sh - 1, 1)
        wave = 0.5 + 0.5 * np.sin((u * 1.4 + v * 0.7) * math.pi * 2 + rng.uniform(0, 6))
        c1 = np.array(rand_color(rng, 25, 170), dtype=np.float32)
        c2 = np.array(rand_color(rng, 40, 200), dtype=np.float32)
        w = np.clip(0.55 * v + 0.35 * u + 0.10 * wave, 0, 1)[..., None]
        arr = c1 * (1 - w) + c2 * w
        screen = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        blobs = Image.new('RGBA', (sw, sh), (0, 0, 0, 0))
        bd = ImageDraw.Draw(blobs)
        for _ in range(rng.randint(1, 3)):
            ex, ey = rng.randint(0, sw), rng.randint(0, sh)
            er = rng.randint(sw // 4, sw // 2)
            bd.ellipse([ex - er, ey - er, ex + er, ey + er],
                       fill=rand_color(rng, 80, 255) + (rng.randint(18, 36),))
        blobs = blobs.filter(ImageFilter.GaussianBlur(70))
        screen = Image.alpha_composite(screen.convert('RGBA'), blobs)
        # 亮屏也会反光
        screen = Image.alpha_composite(
            screen, radial_glow((sw, sh), (rng.randint(0, sw), rng.randint(-sh // 4, sh // 4)),
                                sw * 0.9, (255, 255, 255), 18))
        screen = screen.convert('RGB')

    return screen, on


def draw_phone(geo, screen, rng):
    """手机外壳 + 屏幕 + 摄像头，返回 RGBA 图层。"""
    layer = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # 外壳
    body_color = rand_color(rng, 8, 30)
    d.rounded_rectangle([geo['x0'], geo['y0'], geo['x1'], geo['y1']],
                        radius=geo['radius'], fill=body_color + (255,))
    # 金属边框高光
    d.rounded_rectangle([geo['x0'] + 2, geo['y0'] + 2, geo['x1'] - 2, geo['y1'] - 2],
                        radius=geo['radius'], outline=(120, 125, 135, 180), width=max(2, int(W * 0.003)))
    # 屏幕
    mask = screen_mask(geo)
    sx, sy = int(geo['sx0']), int(geo['sy0'])
    sub_mask = mask.crop((sx, sy, sx + screen.width, sy + screen.height))
    layer.paste(screen, (sx, sy), sub_mask)
    # 摄像头（挖孔）和听筒
    d = ImageDraw.Draw(layer, 'RGBA')
    hole_x = geo['cx']
    hole_y = geo['sy0'] + (geo['sy1'] - geo['sy0']) * 0.018
    hole_r = (geo['sx1'] - geo['sx0']) * 0.014
    d.ellipse([hole_x - hole_r, hole_y - hole_r, hole_x + hole_r, hole_y + hole_r],
              fill=(5, 5, 8, 255), outline=(70, 75, 85, 200), width=2)
    # 屏幕内侧的黑色边框（让屏幕和外壳过渡自然）
    d.rounded_rectangle([geo['sx0'] - 2, geo['sy0'] - 2, geo['sx1'] + 2, geo['sy1'] + 2],
                        radius=geo['screen_radius'] + 2, outline=(0, 0, 0, 220), width=3)
    return layer


# ------------------------------------------------------------------ 缺陷绘制
def _bbox_of_points(points, pad=4):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return [min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad]


def draw_scratch(draw, rng, screen_box):
    sx0, sy0, sx1, sy1 = screen_box
    sw, sh = sx1 - sx0, sy1 - sy0
    length = rng.uniform(0.10, 0.32) * sw
    angle = rng.uniform(0, math.pi)
    cx = rng.uniform(sx0 + sw * 0.12, sx1 - sw * 0.12)
    cy = rng.uniform(sy0 + sh * 0.12, sy1 - sh * 0.12)
    n = rng.randint(3, 6)
    pts = []
    for i in range(n):
        t = i / (n - 1)
        x = cx + math.cos(angle) * length * (t - 0.5)
        y = cy + math.sin(angle) * length * (t - 0.5)
        # 轻微弯曲
        y += math.sin(t * math.pi * rng.uniform(0.8, 1.6)) * rng.uniform(-4, 4)
        pts.append((x, y))
    bright = rng.randint(190, 255)
    alpha = rng.randint(150, 230)
    width = rng.randint(3, 6)
    draw.line(pts, fill=(bright, bright, min(255, bright + 5), alpha), width=width, joint='curve')
    # 一条偏冷的伴线，模拟玻璃折射
    draw.line([(x + 2, y + 2) for x, y in pts],
              fill=(150, 190, 235, rng.randint(40, 90)), width=max(1, width // 2))
    return _bbox_of_points(pts, pad=width + 6)


def draw_crack(draw, rng, screen_box):
    sx0, sy0, sx1, sy1 = screen_box
    sw, sh = sx1 - sx0, sy1 - sy0
    # 裂缝起点：更靠近屏幕边缘或角落
    ox = rng.choice([rng.uniform(sx0 + 0.02 * sw, sx0 + 0.3 * sw),
                     rng.uniform(sx0 + 0.7 * sw, sx1 - 0.02 * sw)])
    oy = rng.uniform(sy0 + 0.05 * sh, sy1 - 0.05 * sh)
    all_pts = [(ox, oy)]
    for _ in range(rng.randint(3, 6)):
        a = rng.uniform(0, 2 * math.pi)
        x, y = ox, oy
        segs = rng.randint(3, 7)
        for _ in range(segs):
            a += rng.uniform(-0.6, 0.6)
            step = rng.uniform(0.015, 0.045) * sw
            x += math.cos(a) * step
            y += math.sin(a) * step
            x = clamp(x, sx0 + 4, sx1 - 4)
            y = clamp(y, sy0 + 4, sy1 - 4)
            all_pts.append((x, y))
        # 主裂缝线
        pts = all_pts[-(segs + 1):]
        w = rng.randint(2, 5)
        draw.line(pts, fill=(245, 248, 255, rng.randint(190, 235)), width=w, joint='curve')
        draw.line(pts, fill=(170, 200, 255, 70), width=w + 4, joint='curve')
    return _bbox_of_points(all_pts, pad=8)


def draw_bright_spot(draw, rng, screen_box):
    sx0, sy0, sx1, sy1 = screen_box
    sw, sh = sx1 - sx0, sy1 - sy0
    cx = rng.uniform(sx0 + 0.1 * sw, sx1 - 0.1 * sw)
    cy = rng.uniform(sy0 + 0.1 * sh, sy1 - 0.1 * sh)
    color = rng.choice([(255, 255, 255), (220, 255, 220), (255, 225, 220), (210, 230, 255)])
    r = rng.uniform(0.008, 0.020) * sw
    n = rng.randint(1, 3)
    boxes = []
    for i in range(n):
        ox = cx + rng.uniform(-1.6, 1.6) * r * 1.5
        oy = cy + rng.uniform(-1.6, 1.6) * r * 1.5
        rr = r * rng.uniform(0.7, 1.2)
        # 光晕
        draw.ellipse([ox - rr * 2.2, oy - rr * 2.2, ox + rr * 2.2, oy + rr * 2.2],
                     fill=color + (rng.randint(30, 60),))
        draw.ellipse([ox - rr, oy - rr, ox + rr, oy + rr], fill=color + (rng.randint(190, 240),))
        if i == 0:
            draw.ellipse([ox - rr * 2.2, oy - rr * 2.2, ox + rr * 2.2, oy + rr * 2.2],
                         outline=color + (120,), width=2)
        boxes.append([ox - rr, oy - rr, ox + rr, oy + rr])
    return [min(b[0] for b in boxes) - 8, min(b[1] for b in boxes) - 8,
            max(b[2] for b in boxes) + 8, max(b[3] for b in boxes) + 8]


def draw_dark_spot(draw, rng, screen_box):
    sx0, sy0, sx1, sy1 = screen_box
    sw, sh = sx1 - sx0, sy1 - sy0
    cx = rng.uniform(sx0 + 0.1 * sw, sx1 - 0.1 * sw)
    cy = rng.uniform(sy0 + 0.1 * sh, sy1 - 0.1 * sh)
    r = rng.uniform(0.010, 0.024) * sw
    n = rng.randint(1, 3)
    boxes = []
    for _ in range(n):
        ox = cx + rng.uniform(-2.0, 2.0) * r
        oy = cy + rng.uniform(-2.0, 2.0) * r
        rr = r * rng.uniform(0.7, 1.3)
        draw.ellipse([ox - rr, oy - rr, ox + rr, oy + rr], fill=(8, 10, 14, rng.randint(170, 235)))
        draw.ellipse([ox - rr, oy - rr, ox + rr, oy + rr],
                     outline=(90, 95, 105, rng.randint(30, 70)), width=2)
        boxes.append([ox - rr, oy - rr, ox + rr, oy + rr])
    return [min(b[0] for b in boxes) - 6, min(b[1] for b in boxes) - 6,
            max(b[2] for b in boxes) + 6, max(b[3] for b in boxes) + 6]


def draw_stain(draw, rng, screen_box):
    sx0, sy0, sx1, sy1 = screen_box
    sw, sh = sx1 - sx0, sy1 - sy0
    cx = rng.uniform(sx0 + 0.12 * sw, sx1 - 0.12 * sw)
    cy = rng.uniform(sy0 + 0.12 * sh, sy1 - 0.12 * sh)
    r = rng.uniform(0.035, 0.085) * sw
    tone = rng.choice([(205, 195, 175), (180, 180, 185), (215, 205, 190)])
    a = rng.randint(35, 85)
    pts = []
    k = rng.randint(7, 11)
    for i in range(k):
        ang = 2 * math.pi * i / k
        rad = r * rng.uniform(0.65, 1.15)
        pts.append((cx + math.cos(ang) * rad, cy + math.sin(ang) * rad * rng.uniform(0.7, 1.2)))
    draw.polygon(pts, fill=tone + (a,))
    for _ in range(rng.randint(2, 4)):
        ox = cx + rng.uniform(-1, 1) * r * 0.7
        oy = cy + rng.uniform(-1, 1) * r * 0.7
        rr = r * rng.uniform(0.2, 0.45)
        draw.ellipse([ox - rr, oy - rr, ox + rr, oy + rr], fill=tone + (a + 15,))
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return [min(xs) - 4, min(ys) - 4, max(xs) + 4, max(ys) + 4]


def draw_edge_chip(draw, rng, screen_box):
    sx0, sy0, sx1, sy1 = screen_box
    sw, sh = sx1 - sx0, sy1 - sy0
    side = rng.choice(['left', 'right', 'top', 'bottom'])
    depth = rng.uniform(0.015, 0.055) * sw
    length = rng.uniform(0.06, 0.18) * sw
    if side in ('left', 'right'):
        edge_x = sx0 if side == 'left' else sx1
        sign = 1 if side == 'left' else -1
        cy = rng.uniform(sy0 + 0.1 * sh, sy1 - 0.1 * sh)
        y0, y1 = cy - length / 2, cy + length / 2
        pts = [(edge_x, y0), (edge_x + sign * depth * rng.uniform(0.5, 1.0), y0 + length * 0.2),
               (edge_x + sign * depth, cy), (edge_x + sign * depth * 0.8, y1 - length * 0.25),
               (edge_x, y1)]
    else:
        edge_y = sy0 if side == 'top' else sy1
        sign = 1 if side == 'top' else -1
        cx = rng.uniform(sx0 + 0.1 * sw, sx1 - 0.1 * sw)
        x0, x1 = cx - length / 2, cx + length / 2
        pts = [(x0, edge_y), (x0 + length * 0.2, edge_y + sign * depth * rng.uniform(0.5, 1.0)),
               (cx, edge_y + sign * depth), (x1 - length * 0.25, edge_y + sign * depth * 0.8),
               (x1, edge_y)]
    draw.polygon(pts, fill=(6, 7, 10, rng.randint(200, 245)))
    draw.line(pts[:3], fill=(230, 235, 245, rng.randint(150, 210)), width=3)
    return _bbox_of_points(pts, pad=6)


DEFECT_FUNCS = {
    'scratch': draw_scratch,
    'crack': draw_crack,
    'bright_spot': draw_bright_spot,
    'dark_spot': draw_dark_spot,
    'stain': draw_stain,
    'edge_chip': draw_edge_chip,
}


def iou(a, b):
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, x1 - x0) * max(0, y1 - y0)
    if inter <= 0:
        return 0.0
    area = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / max(area, 1e-6)


# ------------------------------------------------------------------ 单张合成
def generate_one(seed:int):
    rng = random.Random(seed)
    np.random.seed(seed % (2 ** 32))

    bg = make_background(rng)
    geo = phone_geometry(rng)
    screen, screen_on = draw_screen_background(geo, rng)
    phone = draw_phone(geo, screen, rng)
    mask = screen_mask(geo)

    # 缺陷画在单独图层上，再用屏幕形状裁剪，保证不会画到边框外
    def_layer = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(def_layer)
    screen_box = (geo['sx0'] + 8, geo['sy0'] + 8, geo['sx1'] - 8, geo['sy1'] - 8)

    n = rng.choices(range(5), weights=DEFECT_COUNT_P)[0]
    # 暗点在息屏上几乎看不见，所以息屏时减少暗点、增加亮点和裂纹
    pool = list(CLASSES)
    weights = list(CLASS_WEIGHTS)
    if not screen_on:
        for i, (name, _) in enumerate(pool):
            if name == 'dark_spot':
                weights[i] *= 0.35
            if name in ('scratch', 'crack'):
                weights[i] *= 1.25

    labels, boxes = [], []
    tries = 0
    while len(labels) < n and tries < 80:
        tries += 1
        name = rng.choices([c[0] for c in pool], weights=weights)[0]
        box = DEFECT_FUNCS[name](d, rng, screen_box)
        box = [clamp(box[0], 0, W), clamp(box[1], 0, W), clamp(box[2], 0, W), clamp(box[3], 0, W)]
        if box[2] - box[0] < 18 or box[3] - box[1] < 18:
            continue
        if any(iou(box, b) > 0.12 for b in boxes):
            continue
        if len(labels) > 0 and any(iou(box, b) > 0.35 for b in boxes):
            continue
        boxes.append(box)
        labels.append(CLASS_IDS[name])

    # 裁剪到屏幕圆角内
    clipped = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    clipped.paste(def_layer, (0, 0), mask)
    phone = Image.alpha_composite(phone, clipped)

    # 旋转整部手机
    angle = rng.uniform(-7, 7)
    phone = phone.rotate(angle, resample=Image.BICUBIC, center=(geo['cx'], geo['cy']))
    th = math.radians(angle)

    # 阴影
    shadow = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    ds = ImageDraw.Draw(shadow)
    ds.rounded_rectangle([geo['x0'] + 10, geo['y0'] + 18, geo['x1'] + 14, geo['y1'] + 22],
                         radius=geo['radius'], fill=(0, 0, 0, 110))
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    bg = Image.alpha_composite(bg.convert('RGBA'), shadow).convert('RGBA')
    bg = Image.alpha_composite(bg, phone).convert('RGB')

    # 把框的四个角按同样角度旋转，再取外接矩形
    out_boxes = []
    for box in boxes:
        pts = []
        for px, py in [(box[0], box[1]), (box[2], box[1]), (box[2], box[3]), (box[0], box[3])]:
            dx, dy = px - geo['cx'], py - geo['cy']
            rx = geo['cx'] + dx * math.cos(th) + dy * math.sin(th)
            ry = geo['cy'] - dx * math.sin(th) + dy * math.cos(th)
            pts.append((rx, ry))
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        nb = [max(0, min(xs) - 3), max(0, min(ys) - 3), min(W, max(xs) + 3), min(W, max(ys) + 3)]
        if nb[2] - nb[0] < 4 or nb[3] - nb[1] < 4:
            continue
        out_boxes.append(nb)
    labels = labels[:len(out_boxes)]

    # 缩放到 640，加轻微模糊/噪声/亮度变化，模拟真实拍摄
    img = bg.resize((SIZE, SIZE), Image.LANCZOS)
    img = img.filter(ImageFilter.GaussianBlur(rng.uniform(0.2, 0.7)))
    arr = np.asarray(img).astype(np.float32)
    arr = arr * rng.uniform(0.88, 1.10) + rng.uniform(-8, 8)
    arr = np.clip(arr + np.random.normal(0, rng.uniform(1.5, 4.0), arr.shape), 0, 255)
    img = Image.fromarray(arr.astype(np.uint8))

    # 归一化标签
    norm = []
    for box in out_boxes:
        x0, y0, x1, y1 = [b / W * SIZE for b in box]
        cx, cy = (x0 + x1) / 2 / SIZE, (y0 + y1) / 2 / SIZE
        w, h = (x1 - x0) / SIZE, (y1 - y0) / SIZE
        if not (0 < w <= 1 and 0 < h <= 1 and 0 <= cx <= 1 and 0 <= cy <= 1):
            continue
        norm.append((cx, cy, w, h))
    return img, list(zip(labels, norm)), screen_on


# ------------------------------------------------------------------ 数据集
def write_split(out_root, split, count, start_seed, rng):
    img_dir = os.path.join(out_root, 'images', split)
    lbl_dir = os.path.join(out_root, 'labels', split)
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(lbl_dir, exist_ok=True)
    stats = {name: 0 for name, _ in CLASSES}
    empty = 0
    t0 = time.time()
    for i in range(count):
        seed = start_seed + i
        img, labels, _ = generate_one(seed)
        stem = f'{split}_{i:05d}'
        img.save(os.path.join(img_dir, stem + '.jpg'), quality=rng.randint(88, 95))
        if not labels:
            empty += 1
        with open(os.path.join(lbl_dir, stem + '.txt'), 'w', encoding='utf-8') as f:
            for cid, (cx, cy, w, h) in labels:
                stats[CLASSES[cid][0]] += 1
                f.write(f'{cid} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n')
        if (i + 1) % 100 == 0:
            print(f'  {split}: {i + 1}/{count}  ({time.time() - t0:.0f}s)', flush=True)
    print(f'{split} 完成：{count} 张，空图 {empty} 张，缺陷框 {sum(stats.values())} 个，'
          f'用时 {time.time() - t0:.0f}s', flush=True)
    return {'images': count, 'empty': empty, 'boxes': sum(stats.values()), 'classes': stats}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument('--train', type=int, default=800)
    ap.add_argument('--val', type=int, default=140)
    ap.add_argument('--test', type=int, default=140)
    ap.add_argument('--seed', type=int, default=20261104)
    args = ap.parse_args()

    out_root = os.path.abspath(args.out)
    rng = random.Random(args.seed)
    print(f'输出目录：{out_root}')
    result = {'seed': args.seed, 'size': SIZE, 'classes': CLASSES}
    # 三个划分用不同的种子段，避免图片重复
    result['train'] = write_split(out_root, 'train', args.train, args.seed, rng)
    result['val'] = write_split(out_root, 'val', args.val, args.seed + 100000, rng)
    result['test'] = write_split(out_root, 'test', args.test, args.seed + 200000, rng)

    yaml_path = os.path.join(out_root, 'data.yaml')
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write(f'path: {out_root.replace(os.sep, "/")}\n')
        f.write('train: images/train\n')
        f.write('val: images/val\n')
        f.write('test: images/test\n')
        f.write('nc: %d\n' % len(CLASSES))
        f.write('names:\n')
        for i, (name, _) in enumerate(CLASSES):
            f.write(f'  {i}: {name}\n')

    with open(os.path.join(out_root, 'dataset_stats.json'), 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print('\n数据集统计：')
    for split in ('train', 'val', 'test'):
        s = result[split]
        print(f'  {split}: {s["images"]} 张 / {s["boxes"]} 框 / 空图 {s["empty"]}')
        print('    ' + '  '.join(f'{k}={v}' for k, v in s['classes'].items()))
    print(f'\ndata.yaml: {yaml_path}')


if __name__ == '__main__':
    main()

