# -*- coding: utf-8 -*-
"""week15-18 交付物的结构与排版自检。

不是渲染器：用字体度量估算文本框是否可能溢出，检查形状越界、表格列数、
图片缺失、备注缺失等。用法：python week15-18/docs/qa_check.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

from PIL import ImageFont
from pptx import Presentation
from pptx.util import Emu
from docx import Document

BASE = Path(__file__).resolve().parent.parent
FONT_PATH = r'C:\Windows\Fonts\msyh.ttc'
SCALE = 2.0          # 估算分辨率倍数
DPI = 96.0


def emu_in(v):
    return Emu(v).inches


def wrap_height(text, size_pt, width_in, spacing=1.15):
    if not text:
        return 0.0
    font = ImageFont.truetype(FONT_PATH, int(round(size_pt * DPI / 72 * SCALE)))
    max_px = width_in * DPI * SCALE
    lines = 0
    for para in text.split('\n'):
        if not para:
            lines += 1
            continue
        cur = 0.0
        n = 1
        for ch in para:
            w = font.getlength(ch)
            if cur + w > max_px and cur > 0:
                n += 1
                cur = 0.0
            cur += w
        lines += n
    return lines * size_pt * 1.35 * spacing / 72.0


def check_pptx(path):
    prs = Presentation(path)
    W, H = emu_in(prs.slide_width), emu_in(prs.slide_height)
    print(f'\n== {path.name}: {len(prs.slides)} slides, {W:.2f}x{H:.2f} in')
    issues = 0
    for idx, slide in enumerate(prs.slides, 1):
        for shape in slide.shapes:
            l, t = emu_in(shape.left), emu_in(shape.top)
            w, h = emu_in(shape.width), emu_in(shape.height)
            if l < -0.02 or t < -0.02 or l + w > W + 0.03 or t + h > H + 0.03:
                print(f'  [越界] slide {idx}: {shape.shape_type} '
                      f'({l:.2f},{t:.2f},{w:.2f},{h:.2f})')
                issues += 1
            if not shape.has_text_frame:
                continue
            tf = shape.text_frame
            full = tf.text.strip()
            if not full:
                continue
            # 估第一段字号
            sizes = []
            for p in tf.paragraphs:
                for r in p.runs:
                    if r.font.size:
                        sizes.append(r.font.size.pt)
            size = max(sizes) if sizes else 14
            spacing = 1.15
            est = wrap_height(full, size, max(w - 0.04, 0.2), spacing)
            if est > h * 1.12 and est - h > 0.06:
                print(f'  [可能溢出] slide {idx}: h={h:.2f} est={est:.2f} '
                      f'size={size:.0f} text={full[:34]!r}')
                issues += 1
        if not slide.has_notes_slide or not slide.notes_slide.notes_text_frame.text.strip():
            print(f'  [缺备注] slide {idx}')
            issues += 1
    print(f'  issues: {issues}')
    return issues


def check_docx(path):
    doc = Document(path)
    print(f'\n== {path.name}: {len(doc.paragraphs)} paragraphs, '
          f'{len(doc.tables)} tables, {len(doc.inline_shapes)} images')
    issues = 0
    heads = [p.text for p in doc.paragraphs if p.style.name.startswith('Heading 1')]
    print('  H1:', ' | '.join(heads))
    for ti, table in enumerate(doc.tables, 1):
        ncol = len(table.columns)
        for ri, row in enumerate(table.rows):
            if len(row.cells) != ncol:
                print(f'  [列数不符] table {ti} row {ri}: {len(row.cells)} vs {ncol}')
                issues += 1
        # 宽度和
        widths = [c.width.cm if c.width else 0 for c in table.columns]
        total = sum(widths)
        if total > 15.45:
            cap = ''
            # 表标题通常紧邻表格前的段落
            print(f'  [表过宽] table {ti}: {total:.2f} cm')
            issues += 1
    # 空标题 / 连续空段
    for p in doc.paragraphs:
        if p.style.name.startswith('Heading') and not p.text.strip():
            print('  [空标题]', p.style.name)
            issues += 1
    for si, shape in enumerate(doc.inline_shapes, 1):
        w, h = shape.width.cm, shape.height.cm
        if h > 23.0 or w > 15.5:
            print(f'  [图片过大] image {si}: {w:.2f} x {h:.2f} cm')
            issues += 1
    for p in doc.paragraphs:
        if '缺少图片' in p.text:
            print('  [缺图]', p.text)
            issues += 1
    print(f'  issues: {issues}')
    return issues


if __name__ == '__main__':
    total = 0
    for name in ['测试报告.docx', '用户使用手册.docx', '课程设计报告.docx']:
        total += check_docx(BASE / name)
    total += check_pptx(BASE / '答辩PPT.pptx')
    print('\nTOTAL ISSUES:', total)
