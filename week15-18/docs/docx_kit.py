# -*- coding: utf-8 -*-
"""week15-18 三份 Word 文档共用的排版工具与数据加载。

排版与 week11-14/docs/make_doc.py 保持一致：A4、宋体正文、黑体标题、
1.5 倍行距、页脚页码、打开时自动更新目录域。
"""
from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = Path(__file__).resolve().parent
BASE = HERE.parent                      # week15-18
ROOT = BASE.parent                      # 项目根目录
W1114 = ROOT / 'week11-14'
FIG11 = W1114 / 'docs' / 'figures'
SHOT = W1114 / 'screenshots'
FIG15 = BASE / 'docs' / 'figures'
FIG15.mkdir(parents=True, exist_ok=True)

BODY_EAST = '宋体'
HEAD_EAST = '黑体'
ASCII_FONT = 'Times New Roman'
CODE_FONT = 'Consolas'
DOC_DATE = '2026 年 12 月 20 日'

# ---------------------------------------------------------------- 数据
def _json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return default if default is not None else {}


STATS = _json(W1114 / 'datasets' / 'dataset_stats.json')
STATS_HARD = _json(W1114 / 'datasets_hard' / 'dataset_stats.json')
METRICS = _json(W1114 / 'models' / 'metrics.json')
METRICS_MIX = _json(W1114 / 'models' / 'metrics_mix.json')
try:
    ABL = json.loads((W1114 / 'docs' / 'ablation.json').read_text(encoding='utf-8-sig'))
except (OSError, ValueError):
    ABL = {}
PERF = _json(W1114 / 'docs' / 'perf.json')
TEST_OUT = (W1114 / 'docs' / 'test_output.txt').read_text(encoding='utf-8') \
    if (W1114 / 'docs' / 'test_output.txt').exists() else '（没有找到测试输出）'

M = METRICS.get('test', {})
MM = METRICS_MIX.get('test', {})
PC = {c['class_name']: c for c in METRICS_MIX.get('per_class', [])}
PC1 = {c['class_name']: c for c in METRICS.get('per_class', [])}
CLASS_CN = {c[0]: c[1] for c in STATS.get('classes', [])}
CLASS_ORDER = ['scratch', 'crack', 'bright_spot', 'dark_spot', 'stain', 'edge_chip']
CLASS_COLOR = {'scratch': '#ff7a45', 'crack': '#ff4d4f', 'bright_spot': '#52c41a',
               'dark_spot': '#722ed1', 'stain': '#faad14', 'edge_chip': '#13c2c2'}


def _db_overview():
    path = W1114 / 'data.db'
    out = {'records': 0, 'defects': 0, 'avg_cost': 0.0, 'users': [], 'by_class': [],
           'first': '—', 'last': '—'}
    if not path.exists():
        return out
    try:
        conn = sqlite3.connect(path)
        row = conn.execute('SELECT COUNT(*), COALESCE(SUM(total),0), '
                           'COALESCE(AVG(cost_ms),0) FROM t_record').fetchone()
        out['records'], out['defects'], out['avg_cost'] = row[0], row[1], row[2]
        out['users'] = conn.execute('SELECT username, role FROM t_user ORDER BY id').fetchall()
        out['by_class'] = conn.execute(
            'SELECT class_name, COUNT(*) FROM t_defect GROUP BY class_name '
            'ORDER BY COUNT(*) DESC').fetchall()
        out['first'], out['last'] = conn.execute(
            'SELECT MIN(created_at), MAX(created_at) FROM t_record').fetchone()
        conn.close()
    except sqlite3.Error:
        pass
    return out


DB = _db_overview()


def best_epoch():
    path = W1114 / 'train' / 'runs' / 'phonescreen_yolov8n' / 'results.csv'
    if not path.exists():
        return None, None
    rows = list(csv.DictReader(path.open(encoding='utf-8')))
    if not rows:
        return None, None
    key = 'metrics/mAP50(B)'
    best = max(rows, key=lambda r: float(r[key]))
    return int(best['epoch']), float(best[key])


BEST_EPOCH, BEST_MAP50 = best_epoch()


# ---------------------------------------------------------------- 排版
def set_run_font(run, east=BODY_EAST, ascii_f=ASCII_FONT):
    run.font.name = ascii_f
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.append(rFonts)
    rFonts.set(qn('w:eastAsia'), east)


def set_style_east(style, east):
    rPr = style.element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.append(rFonts)
    rFonts.set(qn('w:eastAsia'), east)


def init_document():
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.top_margin = sec.bottom_margin = Cm(2.54)
    sec.left_margin, sec.right_margin = Cm(3.0), Cm(2.6)
    normal = doc.styles['Normal']
    normal.font.name = ASCII_FONT
    normal.font.size = Pt(12)
    set_style_east(normal, BODY_EAST)
    pf = normal.paragraph_format
    pf.line_spacing = 1.5
    pf.space_after = Pt(3)
    for name, size in [('Title', 26), ('Heading 1', 16), ('Heading 2', 14), ('Heading 3', 12)]:
        st = doc.styles[name]
        st.font.name = ASCII_FONT
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.color.rgb = RGBColor(0, 0, 0)
        set_style_east(st, HEAD_EAST)
    doc.styles['Heading 1'].paragraph_format.page_break_before = True
    doc.styles['Heading 1'].paragraph_format.space_before = Pt(14)
    doc.styles['Heading 1'].paragraph_format.space_after = Pt(8)
    doc.styles['Heading 2'].paragraph_format.space_before = Pt(10)
    doc.styles['Heading 2'].paragraph_format.space_after = Pt(6)
    doc.styles['Heading 3'].paragraph_format.space_before = Pt(8)
    doc.styles['Heading 3'].paragraph_format.space_after = Pt(4)
    footer = sec.footer
    fp = footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = fp.add_run()
    f1 = OxmlElement('w:fldChar'); f1.set(qn('w:fldCharType'), 'begin')
    it = OxmlElement('w:instrText'); it.set(qn('xml:space'), 'preserve'); it.text = 'PAGE'
    f2 = OxmlElement('w:fldChar'); f2.set(qn('w:fldCharType'), 'end')
    run._r.append(f1); run._r.append(it); run._r.append(f2)
    run.font.size = Pt(9)
    set_run_font(run)
    uf = OxmlElement('w:updateFields'); uf.set(qn('w:val'), 'true')
    doc.settings.element.append(uf)
    return doc


def add_cover(doc, doc_name, english='', note_text=''):
    for _ in range(4):
        doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('基于YOLOv8的手机屏幕外观缺陷\n智能检测系统')
    r.font.size = Pt(22); r.font.bold = True; set_run_font(r)
    for _ in range(1):
        doc.add_paragraph()
    if english:
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(english); r.font.size = Pt(11); r.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
        set_run_font(r)
    for _ in range(2):
        doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(doc_name); r.font.size = Pt(26); r.font.bold = True; set_run_font(r)
    if note_text:
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(note_text); r.font.size = Pt(12); r.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
        set_run_font(r)
    for _ in range(3):
        doc.add_paragraph()
    info = ['院    系：人工智能学院', '专    业：信息工程', '班    级：2025219106',
            '成    员：王周毅　林城于', f'日    期：{DOC_DATE}']
    for line in info:
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(line); r.font.size = Pt(14); set_run_font(r)
        p.paragraph_format.space_after = Pt(10)


def add_toc(doc):
    p = doc.add_paragraph()
    run = p.add_run()
    f1 = OxmlElement('w:fldChar'); f1.set(qn('w:fldCharType'), 'begin'); f1.set(qn('w:dirty'), 'true')
    it = OxmlElement('w:instrText'); it.set(qn('xml:space'), 'preserve')
    it.text = ' TOC \\o "1-2" \\h \\z \\u '
    f2 = OxmlElement('w:fldChar'); f2.set(qn('w:fldCharType'), 'separate')
    t = OxmlElement('w:t'); t.text = '（目录将在用 Word 打开时自动生成；若未显示，请右键此处选择“更新域”）'
    f3 = OxmlElement('w:fldChar'); f3.set(qn('w:fldCharType'), 'end')
    run._r.append(f1); run._r.append(it); run._r.append(f2); run._r.append(t); run._r.append(f3)


def h1(doc, text):
    p = doc.add_paragraph(text, style='Heading 1')
    p.paragraph_format.keep_with_next = True
    return p


def h2(doc, text):
    p = doc.add_paragraph(text, style='Heading 2')
    p.paragraph_format.keep_with_next = True
    return p


def h3(doc, text):
    p = doc.add_paragraph(text, style='Heading 3')
    p.paragraph_format.keep_with_next = True
    return p


def body(doc, text, indent=True, bold_prefix=None):
    p = doc.add_paragraph()
    if bold_prefix and text.startswith(bold_prefix):
        r = p.add_run(bold_prefix); r.font.bold = True; set_run_font(r)
        text = text[len(bold_prefix):]
    r = p.add_run(text)
    set_run_font(r)
    if indent:
        p.paragraph_format.first_line_indent = Cm(0.85)
    return p


def bullet(doc, text):
    p = doc.add_paragraph(style='List Bullet')
    r = p.add_run(text)
    set_run_font(r)
    p.paragraph_format.space_after = Pt(2)
    return p


def note(doc, text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.size = Pt(10.5)
    r.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
    set_run_font(r)
    p.paragraph_format.left_indent = Cm(0.6)
    return p


def shade_paragraph(p, fill='F5F7FA'):
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto'); shd.set(qn('w:fill'), fill)
    pPr.append(shd)


def code_block(doc, code, caption=None):
    if caption:
        p = doc.add_paragraph()
        r = p.add_run(caption)
        r.font.size = Pt(9.5); r.font.bold = True
        set_run_font(r)
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
    for line in code.strip('\n').split('\n'):
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.left_indent = Cm(0.45)
        shade_paragraph(p)
        r = p.add_run(line if line else ' ')
        r.font.name = CODE_FONT
        r.font.size = Pt(8.8)
        r.font.color.rgb = RGBColor(0x1f, 0x2d, 0x45)
        r._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), '宋体')
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def shade_cell(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear'); shd.set(qn('w:fill'), fill)
    tcPr.append(shd)


def _set_table_fixed_layout(table, widths_cm):
    tbl = table._tbl
    tblPr = tbl.tblPr
    total = sum(widths_cm)
    tblW = tblPr.find(qn('w:tblW'))
    if tblW is None:
        tblW = OxmlElement('w:tblW')
        tblPr.append(tblW)
    tblW.set(qn('w:w'), str(int(total * 567)))
    tblW.set(qn('w:type'), 'dxa')
    layout = OxmlElement('w:tblLayout')
    layout.set(qn('w:type'), 'fixed')
    tblPr.append(layout)
    grid = tbl.find(qn('w:tblGrid'))
    if grid is not None:
        for col, w in zip(grid.findall(qn('w:gridCol')), widths_cm):
            col.set(qn('w:w'), str(int(w * 567)))


def _mark_row_flags(table):
    for i, row in enumerate(table.rows):
        trPr = row._tr.get_or_add_trPr()
        cant = OxmlElement('w:cantSplit')
        trPr.append(cant)
        if i == 0:
            th = OxmlElement('w:tblHeader')
            trPr.append(th)


def add_table(doc, headers, rows, widths=None, font_size=10.5, center_cols=(),
              caption=None, header_fill='D9E2F3'):
    if caption:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(caption)
        r.font.size = Pt(9); r.font.bold = True
        set_run_font(r)
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, htxt in enumerate(headers):
        c = t.rows[0].cells[i]
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = c.paragraphs[0].add_run(htxt)
        r.font.bold = True; r.font.size = Pt(font_size); set_run_font(r)
        shade_cell(c, header_fill)
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            p0 = cells[i].paragraphs[0]
            if i in center_cols:
                p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p0.paragraph_format.line_spacing = 1.15
            r = p0.add_run(str(val))
            r.font.size = Pt(font_size); set_run_font(r)
    if widths:
        if len(widths) != len(headers):
            print(f'[WARN] 表格列宽数量不符：{caption} widths={len(widths)} headers={len(headers)}')
        if sum(widths) > 15.45:
            print(f'[WARN] 表格过宽：{caption} {sum(widths):.2f} cm')
        t.autofit = False
        for i, w in enumerate(widths):
            t.columns[i].width = Cm(w)
            for row in t.rows:
                row.cells[i].width = Cm(w)
        _set_table_fixed_layout(t, widths)
    _mark_row_flags(t)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def add_figure(doc, img_path, caption, width_cm=15.0):
    if not Path(img_path).exists():
        note(doc, f'（缺少图片：{Path(img_path).name}）')
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(img_path), width=Cm(width_cm))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = cap.add_run(caption)
    r.font.size = Pt(9); r.font.bold = True
    set_run_font(r)
    cap.paragraph_format.space_after = Pt(8)


def page_break(doc):
    from docx.enum.text import WD_BREAK
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def finish(doc, path, title, subject):
    cp = doc.core_properties
    cp.title = title
    cp.author = '王周毅、林城于'
    cp.subject = subject
    doc.save(path)
    print('OK:', path)
