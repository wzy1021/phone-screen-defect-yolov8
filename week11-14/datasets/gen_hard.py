# -*- coding: utf-8 -*-
"""生成“困难版”手机屏幕缺陷数据集（低对比度、微小目标、强反光/水花干扰）。

和 gen_dataset.py 的区别：
    1. 屏幕更亮、对比度更低，缺陷线宽只有 1~3 像素；
    2. 裂纹改成从撞击点发散的“蜘蛛网”，带同心连接线，接近真实碎屏；
    3. 划痕、亮点、暗点、污渍、崩缺的尺寸都缩小，颜色贴近背景；
    4. 随机加大量水珠、反光、散景光斑，这些是“不标注”的干扰物，
       专门用来压误检（模型要学会不把水花当亮点）。

输出：datasets_hard/images|labels/{train,val,test}、data_hard.yaml、dataset_stats.json
用法：python datasets/gen_hard.py --train 600 --val 100 --test 100
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_dataset as G  # noqa: E402

SIZE = 640
SS = 2
W = SIZE * SS
CLASSES = G.CLASSES
CLASS_IDS = G.CLASS_IDS


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def make_bokeh_background(rng):
    """深色散景背景：像隔着玻璃/水面拍手机。"""
    base = np.array([rng.randint(20, 55), rng.randint(28, 65), rng.randint(35, 75)], dtype=np.float32)
    top = np.linspace(0, 1, W)[:, None, None]
    arr = np.repeat(np.repeat(base[None, None, :], W, 0), W, 1) * (0.65 + 0.5 * top)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert('RGBA')
    layer = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(rng.randint(20, 40)):
        x, y = rng.randint(-100, W + 100), rng.randint(-100, W + 100)
        r = rng.randint(20, 160)
        color = rng.choice([(180, 200, 220), (150, 180, 210), (220, 210, 190), (120, 160, 190)])
        d.ellipse([x - r, y - r, x + r, y + r], fill=color + (rng.randint(8, 26),))
    layer = layer.filter(ImageFilter.GaussianBlur(rng.uniform(12, 30)))
    img = Image.alpha_composite(img, layer).convert('RGB')
    img = G.add_noise(img, rng.uniform(3, 6))
    return img


def make_screen_hard(rng, geo):
    """亮屏或暗屏，整体对比度偏低，带反光。"""
    sw = int(geo['sx1']) - int(geo['sx0'])
    sh = int(geo['sy1']) - int(geo['sy0'])
    bright = rng.random() < 0.65
    if bright:
        c1 = np.array(G.rand_color(rng, 70, 150), dtype=np.float32)
        c2 = np.array(G.rand_color(rng, 90, 180), dtype=np.float32)
    else:
        c1 = np.array(G.rand_color(rng, 25, 55), dtype=np.float32)
        c2 = np.array(G.rand_color(rng, 40, 80), dtype=np.float32)
    yy, xx = np.mgrid[0:sh, 0:sw]
    w = np.clip(0.5 * yy / max(sh, 1) + 0.5 * xx / max(sw, 1), 0, 1)[..., None]
    arr = c1 * (1 - w) + c2 * w
    screen = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    # 低频纹理，避免纯色
    noise = np.random.normal(0, rng.uniform(3, 7), (sh, sw, 1))
    screen = Image.fromarray(np.clip(np.asarray(screen) + noise, 0, 255).astype(np.uint8))
    # 反光带 + 高光
    refl = Image.new('RGBA', (sw, sh), (0, 0, 0, 0))
    rd = ImageDraw.Draw(refl)
    for _ in range(rng.randint(2, 4)):
        bx = rng.randint(-sw, sw)
        bw = rng.randint(sw // 5, sw // 2)
        rd.polygon([(bx, 0), (bx + bw, 0), (bx + bw + sh * 0.5, sh), (bx + sh * 0.5, sh)],
                   fill=(230, 240, 255, rng.randint(20, 45)))
    refl = refl.filter(ImageFilter.GaussianBlur(rng.uniform(15, 35)))
    screen = Image.alpha_composite(screen.convert('RGBA'), refl)
    screen = Image.alpha_composite(
        screen, G.radial_glow((sw, sh), (rng.randint(0, sw), rng.randint(0, sh // 2)),
                              sw * 0.8, (255, 255, 255), 20))
    return screen.convert('RGB'), bright


def add_water_drops(layer, rng, n=None):
    """在手机/背景上画水珠，不标注，作为困难负样本。"""
    d = ImageDraw.Draw(layer, 'RGBA')
    for _ in range(n if n is not None else rng.randint(12, 30)):
        x, y = rng.randint(-20, W + 20), rng.randint(-20, W + 20)
        r = rng.randint(2, 11)
        alpha = rng.randint(40, 110)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(210, 225, 245, alpha // 2))
        d.ellipse([x - r, y - r, x + r, y + r], outline=(240, 250, 255, alpha), width=1)
        d.ellipse([x - r * 0.45, y - r * 0.45, x - r * 0.1, y - r * 0.1],
                  fill=(255, 255, 255, min(220, alpha + 60)))
        d.arc([x - r * 0.7, y - r * 0.7, x + r * 0.7, y + r * 0.7], 200, 320,
              fill=(255, 255, 255, min(200, alpha + 40)), width=1)
    return layer


def draw_crack_web(draw, rng, screen_box, bright):
    """从撞击点发散的蜘蛛网裂纹 + 同心连接线。"""
    sx0, sy0, sx1, sy1 = screen_box
    sw, sh = sx1 - sx0, sy1 - sy0
    ox = rng.uniform(sx0 + 0.2 * sw, sx1 - 0.2 * sw)
    oy = rng.uniform(sy0 + 0.2 * sh, sy1 - 0.2 * sh)
    n = rng.randint(10, 16)
    max_len = rng.uniform(0.30, 0.60) * min(sw, sh)
    if bright:
        color = (rng.randint(15, 55), rng.randint(15, 55), rng.randint(20, 60))
    else:
        color = (rng.randint(190, 240), rng.randint(190, 240), rng.randint(195, 245))
    alpha = rng.randint(130, 210)
    width = rng.randint(2, 4)
    pts_all = []
    ends = []
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.25, 0.25)
        length = max_len * rng.uniform(0.55, 1.0)
        x, y = ox, oy
        pts = [(x, y)]
        for _ in range(rng.randint(4, 9)):
            a += rng.uniform(-0.28, 0.28)
            step = length / 5 * rng.uniform(0.5, 1.1)
            x += math.cos(a) * step
            y += math.sin(a) * step
            x = clamp(x, sx0 + 3, sx1 - 3)
            y = clamp(y, sy0 + 3, sy1 - 3)
            pts.append((x, y))
        draw.line(pts, fill=color + (alpha,), width=width, joint='curve')
        # 子裂纹
        if len(pts) > 3 and rng.random() < 0.7:
            bx, by = pts[rng.randint(2, len(pts) - 1)]
            ba = a + rng.choice([-1, 1]) * rng.uniform(0.5, 1.3)
            bl = max_len * rng.uniform(0.15, 0.4)
            bpts = [(bx, by)]
            for _ in range(rng.randint(2, 4)):
                bx += math.cos(ba) * bl / 3
                by += math.sin(ba) * bl / 3
                ba += rng.uniform(-0.4, 0.4)
                bpts.append((clamp(bx, sx0 + 2, sx1 - 2), clamp(by, sy0 + 2, sy1 - 2)))
            draw.line(bpts, fill=color + (alpha - 20,), width=max(1, width - 1), joint='curve')
            pts_all += bpts
        pts_all += pts
        ends.append(pts[-1])
    # 同心连接线：相邻分支末端/中段连起来
    for frac in (0.3, 0.45, 0.6, 0.75, 0.9):
        for i in range(len(ends)):
            if rng.random() < 0.6:
                p1 = (ox + (ends[i][0] - ox) * frac, oy + (ends[i][1] - oy) * frac)
                j = (i + 1) % len(ends)
                p2 = (ox + (ends[j][0] - ox) * frac, oy + (ends[j][1] - oy) * frac)
                draw.line([p1, p2], fill=color + (max(40, alpha - 40),), width=max(1, width - 1))
                pts_all += [p1, p2]
    return G._bbox_of_points(pts_all, pad=5)


def draw_tiny_scratch(draw, rng, screen_box, bright):
    sx0, sy0, sx1, sy1 = screen_box
    sw, sh = sx1 - sx0, sy1 - sy0
    length = rng.uniform(8, 34) * SS
    cx = rng.uniform(sx0 + 0.12 * sw, sx1 - 0.12 * sw)
    cy = rng.uniform(sy0 + 0.12 * sh, sy1 - 0.12 * sh)
    a = rng.uniform(0, math.pi)
    n = rng.randint(2, 4)
    pts = [(cx + math.cos(a) * length * (i / (n - 1) - 0.5) + rng.uniform(-1, 1),
            cy + math.sin(a) * length * (i / (n - 1) - 0.5) + rng.uniform(-1, 1)) for i in range(n)]
    if bright:
        color = (rng.randint(200, 245),) * 3
    else:
        color = (rng.randint(20, 60),) * 3
    draw.line(pts, fill=color + (rng.randint(80, 150),), width=rng.randint(1, 2), joint='curve')
    return G._bbox_of_points(pts, pad=4)


def draw_tiny_spot(draw, rng, screen_box, bright):
    sx0, sy0, sx1, sy1 = screen_box
    sw, sh = sx1 - sx0, sy1 - sy0
    cx = rng.uniform(sx0 + 0.1 * sw, sx1 - 0.1 * sw)
    cy = rng.uniform(sy0 + 0.1 * sh, sy1 - 0.1 * sh)
    r = rng.uniform(2, 5) * SS
    if bright:
        color = (rng.randint(200, 255),) * 3
    else:
        color = (rng.randint(5, 35),) * 3
    boxes = []
    for _ in range(rng.randint(1, 3)):
        ox = cx + rng.uniform(-2, 2) * r
        oy = cy + rng.uniform(-2, 2) * r
        draw.ellipse([ox - r, oy - r, ox + r, oy + r], fill=color + (rng.randint(110, 190),))
        boxes.append([ox - r, oy - r, ox + r, oy + r])
    return [min(b[0] for b in boxes) - 3, min(b[1] for b in boxes) - 3,
            max(b[2] for b in boxes) + 3, max(b[3] for b in boxes) + 3]


def draw_faint_stain(draw, rng, screen_box):
    sx0, sy0, sx1, sy1 = screen_box
    sw, sh = sx1 - sx0, sy1 - sy0
    cx = rng.uniform(sx0 + 0.15 * sw, sx1 - 0.15 * sw)
    cy = rng.uniform(sy0 + 0.15 * sh, sy1 - 0.15 * sh)
    r = rng.uniform(0.03, 0.07) * sw
    pts = []
    for i in range(rng.randint(6, 10)):
        a = 2 * math.pi * i / 8
        pts.append((cx + math.cos(a) * r * rng.uniform(0.6, 1.2),
                    cy + math.sin(a) * r * rng.uniform(0.6, 1.2)))
    draw.polygon(pts, fill=(rng.randint(150, 210),) * 3 + (rng.randint(25, 60),))
    return G._bbox_of_points(pts, pad=4)


def draw_small_chip(draw, rng, screen_box):
    sx0, sy0, sx1, sy1 = screen_box
    sw = sx1 - sx0
    side = rng.choice(['left', 'right', 'top', 'bottom'])
    depth = rng.uniform(0.012, 0.04) * sw
    length = rng.uniform(0.04, 0.11) * sw
    if side in ('left', 'right'):
        x = sx0 if side == 'left' else sx1
        sgn = 1 if side == 'left' else -1
        cy = rng.uniform(sy0 + 0.15 * (sy1 - sy0), sy1 - 0.15 * (sy1 - sy0))
        pts = [(x, cy - length / 2), (x + sgn * depth * 0.6, cy),
               (x + sgn * depth, cy + length * 0.2), (x, cy + length / 2)]
    else:
        y = sy0 if side == 'top' else sy1
        sgn = 1 if side == 'top' else -1
        cx = rng.uniform(sx0 + 0.15 * sw, sx1 - 0.15 * sw)
        pts = [(cx - length / 2, y), (cx, y + sgn * depth * 0.6),
               (cx + length * 0.2, y + sgn * depth), (cx + length / 2, y)]
    draw.polygon(pts, fill=(10, 10, 14, rng.randint(160, 220)))
    draw.line(pts[:3], fill=(220, 225, 235, rng.randint(90, 150)), width=1)
    return G._bbox_of_points(pts, pad=4)


def generate_one(seed):
    rng = random.Random(seed)
    np.random.seed(seed % (2 ** 32))
    bg = make_bokeh_background(rng)
    geo = G.phone_geometry(rng)
    screen, bright = make_screen_hard(rng, geo)
    phone = G.draw_phone(geo, screen, rng)
    mask = G.screen_mask(geo)

    def_layer = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(def_layer)
    box = (geo['sx0'] + 6, geo['sy0'] + 6, geo['sx1'] - 6, geo['sy1'] - 6)

    negative = rng.random() < 0.15
    labels, boxes = [], []
    if not negative:
        n = rng.choices(range(1, 5), weights=[0.25, 0.4, 0.25, 0.1])[0]
        tries = 0
        while len(labels) < n and tries < 60:
            tries += 1
            name = rng.choices([c[0] for c in CLASSES], weights=G.CLASS_WEIGHTS)[0]
            if name == 'crack':
                b = draw_crack_web(d, rng, box, bright)
            elif name == 'scratch':
                b = draw_tiny_scratch(d, rng, box, bright)
            elif name == 'bright_spot':
                b = draw_tiny_spot(d, rng, box, True)
            elif name == 'dark_spot':
                b = draw_tiny_spot(d, rng, box, False)
            elif name == 'stain':
                b = draw_faint_stain(d, rng, box)
            else:
                b = draw_small_chip(d, rng, box)
            b = [clamp(b[0], 0, W), clamp(b[1], 0, W), clamp(b[2], 0, W), clamp(b[3], 0, W)]
            if b[2] - b[0] < 6 or b[3] - b[1] < 6:
                continue
            if any(G.iou(b, x) > 0.1 for x in boxes):
                continue
            boxes.append(b)
            labels.append(CLASS_IDS[name])

    clipped = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    clipped.paste(def_layer, (0, 0), mask)
    phone = Image.alpha_composite(phone, clipped)
    # 水珠画在手机之上
    phone = add_water_drops(phone, rng)

    angle = rng.uniform(-10, 10)
    phone = phone.rotate(angle, resample=Image.BICUBIC, center=(geo['cx'], geo['cy']))
    th = math.radians(angle)

    shadow = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    ds = ImageDraw.Draw(shadow)
    ds.rounded_rectangle([geo['x0'] + 12, geo['y0'] + 20, geo['x1'] + 16, geo['y1'] + 24],
                         radius=geo['radius'], fill=(0, 0, 0, 110))
    shadow = shadow.filter(ImageFilter.GaussianBlur(24))
    bg = Image.alpha_composite(bg.convert('RGBA'), shadow).convert('RGBA')
    bg = Image.alpha_composite(bg, phone).convert('RGB')
    bg = add_water_drops(bg.convert('RGBA'), rng, n=rng.randint(8, 22)).convert('RGB')

    out_boxes = []
    for b in boxes:
        pts = []
        for px, py in [(b[0], b[1]), (b[2], b[1]), (b[2], b[3]), (b[0], b[3])]:
            dx, dy = px - geo['cx'], py - geo['cy']
            pts.append((geo['cx'] + dx * math.cos(th) + dy * math.sin(th),
                        geo['cy'] - dx * math.sin(th) + dy * math.cos(th)))
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        nb = [max(0, min(xs) - 2), max(0, min(ys) - 2), min(W, max(xs) + 2), min(W, max(ys) + 2)]
        if nb[2] - nb[0] >= 4 and nb[3] - nb[1] >= 4:
            out_boxes.append(nb)
    labels = labels[:len(out_boxes)]

    img = bg.resize((SIZE, SIZE), Image.LANCZOS)
    img = img.filter(ImageFilter.GaussianBlur(rng.uniform(0.3, 0.9)))
    arr = np.asarray(img).astype(np.float32) * rng.uniform(0.85, 1.10)
    arr = np.clip(arr + np.random.normal(0, rng.uniform(2, 5), arr.shape), 0, 255)
    img = Image.fromarray(arr.astype(np.uint8))

    norm = []
    for b in out_boxes:
        x0, y0, x1, y1 = [v / W * SIZE for v in b]
        cx, cy = (x0 + x1) / 2 / SIZE, (y0 + y1) / 2 / SIZE
        w, h = (x1 - x0) / SIZE, (y1 - y0) / SIZE
        if 0 < w <= 1 and 0 < h <= 1:
            norm.append((cx, cy, w, h))
    return img, list(zip(labels, norm))


def write_split(out_root, split, count, start_seed):
    img_dir = os.path.join(out_root, 'images', split)
    lbl_dir = os.path.join(out_root, 'labels', split)
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(lbl_dir, exist_ok=True)
    stats = {name: 0 for name, _ in CLASSES}
    empty = 0
    t0 = time.time()
    for i in range(count):
        img, labels = generate_one(start_seed + i)
        stem = f'{split}_{i:05d}'
        img.save(os.path.join(img_dir, stem + '.jpg'), quality=rng_quality(i))
        if not labels:
            empty += 1
        with open(os.path.join(lbl_dir, stem + '.txt'), 'w', encoding='utf-8') as f:
            for cid, (cx, cy, w, h) in labels:
                stats[CLASSES[cid][0]] += 1
                f.write(f'{cid} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n')
        if (i + 1) % 100 == 0:
            print(f'  {split}: {i + 1}/{count} ({time.time() - t0:.0f}s)', flush=True)
    print(f'{split} 完成：{count} 张，空图 {empty}，框 {sum(stats.values())}，'
          f'用时 {time.time() - t0:.0f}s', flush=True)
    return {'images': count, 'empty': empty, 'boxes': sum(stats.values()), 'classes': stats}


def rng_quality(i):
    return 88 + (i * 7) % 7


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.dirname(os.path.abspath(__file__)) + '/../datasets_hard')
    ap.add_argument('--train', type=int, default=600)
    ap.add_argument('--val', type=int, default=100)
    ap.add_argument('--test', type=int, default=100)
    ap.add_argument('--seed', type=int, default=20261110)
    args = ap.parse_args()

    out_root = os.path.abspath(args.out)
    os.makedirs(out_root, exist_ok=True)
    result = {'seed': args.seed, 'size': SIZE, 'classes': CLASSES}
    result['train'] = write_split(out_root, 'train', args.train, args.seed)
    result['val'] = write_split(out_root, 'val', args.val, args.seed + 100000)
    result['test'] = write_split(out_root, 'test', args.test, args.seed + 200000)

    with open(os.path.join(out_root, 'data_hard.yaml'), 'w', encoding='utf-8') as f:
        f.write(f'path: {out_root.replace(os.sep, "/")}\n')
        f.write('train: images/train\nval: images/val\ntest: images/test\nnc: 6\nnames:\n')
        for i, (name, _) in enumerate(CLASSES):
            f.write(f'  {i}: {name}\n')
    with open(os.path.join(out_root, 'dataset_stats.json'), 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print('done:', out_root)


if __name__ == '__main__':
    main()

