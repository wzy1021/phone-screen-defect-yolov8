# -*- coding: utf-8 -*-
"""把 PPTX 粗略画成 PNG，用于检查版式（不是精确渲染器）。

只还原背景、矩形、图片和文本；图表画成占位框。用法：
python week15-18/docs/render_preview.py 1 2 7 12
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu

BASE = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / '_preview'
OUT.mkdir(exist_ok=True)
FONT_PATH = r'C:\Windows\Fonts\msyh.ttc'
FONT_BOLD = r'C:\Windows\Fonts\msyhbd.ttc'
DPI = 120
SCALE = DPI / 96.0


def font(size_pt, bold=False):
    px = max(int(round(size_pt * DPI / 72)), 6)
    return ImageFont.truetype(FONT_BOLD if bold else FONT_PATH, px)


def color_of(fmt, default=(255, 255, 255)):
    try:
        if fmt.type is None:
            return default
        rgb = fmt.fore_color.rgb
        return (rgb[0], rgb[1], rgb[2])
    except Exception:
        return default


def emu_in(v):
    return Emu(v).inches


def wrap_lines(text, fnt, max_w):
    lines = []
    for para in text.split('\n'):
        if not para:
            lines.append('')
            continue
        cur = ''
        for ch in para:
            if fnt.getlength(cur + ch) <= max_w or not cur:
                cur += ch
            else:
                lines.append(cur)
                cur = ch
        lines.append(cur)
    return lines


def draw_text(draw, shape, ox, oy):
    tf = shape.text_frame
    if not tf.text.strip():
        return
    l, t = emu_in(shape.left) * DPI, emu_in(shape.top) * DPI
    w, h = emu_in(shape.width) * DPI, emu_in(shape.height) * DPI
    # 取第一段字号（同一文本框内通常一致）
    size, bold, col, align = 14, False, (16, 26, 46), PP_ALIGN.LEFT
    for p in tf.paragraphs:
        for r in p.runs:
            if r.font.size:
                size = r.font.size.pt
            bold = bool(r.font.bold)
            try:
                col = (r.font.color.rgb[0], r.font.color.rgb[1], r.font.color.rgb[2])
            except Exception:
                pass
            align = p.alignment
            break
        break
    fnt = font(size, bold)
    lines = wrap_lines(tf.text, fnt, max(w, 10))
    lh = size * DPI / 72 * 1.3
    total = lh * len(lines)
    anchor = tf.vertical_anchor
    if anchor == MSO_ANCHOR.MIDDLE:
        y = t + (h - total) / 2
    elif anchor == MSO_ANCHOR.BOTTOM:
        y = t + h - total
    else:
        y = t
    for line in lines:
        tw = fnt.getlength(line)
        if align == PP_ALIGN.CENTER:
            x = l + (w - tw) / 2
        elif align == PP_ALIGN.RIGHT:
            x = l + w - tw
        else:
            x = l
        draw.text((ox + x, oy + y), line, font=fnt, fill=col)
        y += lh


def render(slide, idx, prs):
    W = int(emu_in(prs.slide_width) * DPI)
    H = int(emu_in(prs.slide_height) * DPI)
    img = Image.new('RGB', (W, H), 'white')
    draw = ImageDraw.Draw(img)
    try:
        bg = slide.background.fill
        img.paste(Image.new('RGB', (W, H), color_of(bg, (255, 255, 255))), (0, 0))
    except Exception:
        pass
    for shape in slide.shapes:
        l = emu_in(shape.left) * DPI
        t = emu_in(shape.top) * DPI
        w = emu_in(shape.width) * DPI
        h = emu_in(shape.height) * DPI
        if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
            try:
                pic = Image.open(io.BytesIO(shape.image.blob)).convert('RGB')
                pic = pic.resize((max(int(w), 1), max(int(h), 1)), Image.LANCZOS)
                img.paste(pic, (int(l), int(t)))
            except Exception:
                pass
            continue
        if shape.has_chart:
            draw.rectangle([l, t, l + w, t + h], outline=(220, 228, 240), width=2)
            draw.text((l + 10, t + 10), '[chart]', font=font(10), fill=(150, 160, 180))
            continue
        if shape.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE:
            fill = color_of(shape.fill, (255, 255, 255))
            try:
                line = color_of(shape.line.color, None)
            except Exception:
                line = None
            try:
                radius = int(min(w, h) * float(shape.adjustments[0]))
            except Exception:
                radius = 0
            if line is None:
                draw.rounded_rectangle([l, t, l + w, t + h], radius=radius, fill=fill)
            else:
                draw.rounded_rectangle([l, t, l + w, t + h], radius=radius,
                                       fill=fill, outline=line, width=1)
            draw_text(draw, shape, 0, 0)
        elif shape.has_text_frame:
            draw_text(draw, shape, 0, 0)
    path = OUT / f'slide_{idx:02d}.png'
    img.save(path)
    print('OK:', path)


if __name__ == '__main__':
    prs = Presentation(BASE / '答辩PPT.pptx')
    wanted = [int(x) for x in sys.argv[1:]] or list(range(1, len(prs.slides) + 1))
    for i in wanted:
        render(prs.slides[i - 1], i, prs)
