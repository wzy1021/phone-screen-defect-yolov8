# -*- coding: utf-8 -*-
"""生成《详细设计说明书.docx》（课程设计第 11-14 周交付物）。

文档中的数据集统计、训练指标、测试结果都从项目里的实际文件读取：
    datasets/dataset_stats.json
    models/metrics.json
    train/runs/phonescreen_yolov8n/results.csv
    docs/test_output.txt
    docs/perf.json
图片来自 docs/figures/ 与 screenshots/。

用法：python docs/make_doc.py
"""
from __future__ import annotations

import csv
import json
import os
import sqlite3
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

BASE = Path(__file__).resolve().parent.parent
FIG = BASE / 'docs' / 'figures'
SHOT = BASE / 'screenshots'
OUT = BASE / '详细设计说明书.docx'

BODY_EAST = '宋体'
HEAD_EAST = '黑体'
ASCII_FONT = 'Times New Roman'
CODE_FONT = 'Consolas'

STATS = json.loads((BASE / 'datasets' / 'dataset_stats.json').read_text(encoding='utf-8'))
METRICS = json.loads((BASE / 'models' / 'metrics.json').read_text(encoding='utf-8'))
TEST_OUT = (BASE / 'docs' / 'test_output.txt').read_text(encoding='utf-8') \
    if (BASE / 'docs' / 'test_output.txt').exists() else '（测试输出未生成）'
PERF = json.loads((BASE / 'docs' / 'perf.json').read_text(encoding='utf-8')) \
    if (BASE / 'docs' / 'perf.json').exists() else {}

M = METRICS['test']
PC = {c['class_name']: c for c in METRICS['per_class']}
METRICS_MIX = json.loads((BASE / 'models' / 'metrics_mix.json').read_text(encoding='utf-8'))
STATS_HARD = json.loads((BASE / 'datasets_hard' / 'dataset_stats.json').read_text(encoding='utf-8'))
ABL = json.loads((BASE / 'docs' / 'ablation.json').read_text(encoding='utf-8-sig'))
CLASS_CN = {c[0]: c[1] for c in STATS['classes']}
CLASS_COLOR = {'scratch': '#ff7a45', 'crack': '#ff4d4f', 'bright_spot': '#52c41a',
               'dark_spot': '#722ed1', 'stain': '#faad14', 'edge_chip': '#13c2c2'}

DBS = BASE / 'data.db'
RECORD_COUNT = 0
AVG_COST = 0.0
if DBS.exists():
    try:
        conn = sqlite3.connect(DBS)
        row = conn.execute('SELECT COUNT(*), COALESCE(AVG(cost_ms),0) FROM t_record').fetchone()
        RECORD_COUNT, AVG_COST = row[0], row[1]
        conn.close()
    except sqlite3.Error:
        pass


def best_epoch():
    path = BASE / 'train' / 'runs' / 'phonescreen_yolov8n' / 'results.csv'
    if not path.exists():
        return None, None
    rows = list(csv.DictReader(path.open(encoding='utf-8')))
    key = 'metrics/mAP50(B)'
    best = max(rows, key=lambda r: float(r[key]))
    return int(best['epoch']), float(best[key])


BEST_EPOCH, BEST_MAP50 = best_epoch()


# ================================================================ 排版工具
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


def add_cover(doc, doc_name):
    for _ in range(5):
        doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('基于YOLOv8的手机屏幕外观缺陷\n智能检测系统')
    r.font.size = Pt(22); r.font.bold = True; set_run_font(r)
    for _ in range(2):
        doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(doc_name); r.font.size = Pt(26); r.font.bold = True; set_run_font(r)
    for _ in range(4):
        doc.add_paragraph()
    info = ['院    系：人工智能学院', '专    业：信息工程', '班    级：2025219106',
            '成    员：王周毅　林城于', '日    期：2026 年 11 月 20 日']
    for line in info:
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(line); r.font.size = Pt(14); set_run_font(r)
        p.paragraph_format.space_after = Pt(10)


def add_toc(doc):
    p = doc.add_paragraph()
    run = p.add_run()
    f1 = OxmlElement('w:fldChar'); f1.set(qn('w:fldCharType'), 'begin'); f1.set(qn('w:dirty'), 'true')
    it = OxmlElement('w:instrText'); it.set(qn('xml:space'), 'preserve')
    it.text = ' TOC \\o "1-3" \\h \\z \\u '
    f2 = OxmlElement('w:fldChar'); f2.set(qn('w:fldCharType'), 'separate')
    t = OxmlElement('w:t'); t.text = '（目录将在用 Word 打开时自动生成；若未显示，请右键此处选择“更新域”）'
    f3 = OxmlElement('w:fldChar'); f3.set(qn('w:fldCharType'), 'end')
    run._r.append(f1); run._r.append(it); run._r.append(f2); run._r.append(t); run._r.append(f3)


def h1(doc, text):
    p = doc.add_paragraph(text, style='Heading 1')
    p.paragraph_format.keep_with_next = True


def h2(doc, text):
    p = doc.add_paragraph(text, style='Heading 2')
    p.paragraph_format.keep_with_next = True


def h3(doc, text):
    p = doc.add_paragraph(text, style='Heading 3')
    p.paragraph_format.keep_with_next = True


def body(doc, text, indent=True):
    p = doc.add_paragraph()
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
    lines = code.strip('\n').split('\n')
    for i, line in enumerate(lines):
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


def add_table(doc, headers, rows, widths=None, font_size=10.5, center_cols=(), caption=None):
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
        shade_cell(c, 'D9E2F3')
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


# ================================================================ 正文
def build():
    doc = init_document()
    cp = doc.core_properties
    cp.title = '基于YOLOv8的手机屏幕外观缺陷智能检测系统——详细设计说明书'
    cp.author = '王周毅、林城于'
    cp.subject = '课程设计第 11-14 周实现阶段'
    add_cover(doc, '详细设计说明书')
    h1(doc, '目录')
    add_toc(doc)

    # ------------------------------------------------------------ 1 引言
    h1(doc, '1 引言')
    h2(doc, '1.1 编写目的')
    body(doc, '这份文档是课程设计第 11–14 周（实现阶段）的交付物。第 5–6 周我们写了'
              '《需求分析说明书》和《可行性分析报告》，弄清楚了系统要做什么；第 7–10 周的'
              '《概要设计说明书》定下了系统的总体架构、模块划分、4 张数据库表、8 个主要接口'
              '和 5 个页面。到了实现阶段，光有“分成哪几块”已经不够了：数据集怎么造、模型'
              '怎么训、每个类和方法具体做什么、接口的参数和返回值是什么、测试用例怎么设计，'
              '这些都要写清楚。')
    body(doc, '这份文档就是把这些细节固化下来，作为我们两个人写代码、联调、自测的依据，'
              '同时也作为第 15–18 周验收时的材料。文档的读者是课程老师和组内的两位同学，'
              '所以尽量写得具体，关键地方直接贴代码。')
    h2(doc, '1.2 项目背景与范围')
    body(doc, '手机屏幕是手机最容易出外观问题的部件。划痕、裂纹、亮点、暗点、污渍和边缘'
              '崩缺这六类缺陷，现在主要靠人眼在产线或门店检查，速度慢、容易看漏，不同人'
              '判断的标准也不完全一样。我们想用 YOLOv8 做一个网页系统：上传一张屏幕照片，'
              '系统自动把缺陷框出来，标出类别和置信度，并把这次检测记录存进数据库，方便'
              '以后查历史和看统计。')
    body(doc, '本阶段完成的是单机可运行版本，范围包括：登录与权限、图片上传、YOLOv8 检测、'
              '结果展示与下载、历史记录管理、数据统计、参数设置。不做的事情包括：多人'
              '协同和细粒度权限、在线训练、移动端 App、和产线设备对接。这些留到以后有'
              '需要再做，不占用课程设计的时间。')
    h2(doc, '1.3 术语定义')
    add_table(doc, ['术语', '说明'],
              [['YOLOv8', 'Ultralytics 开源的目标检测算法，一次前向就能输出所有目标的位置和类别'],
               ['迁移学习', '先用 COCO 大数据集训练好的权重初始化，再用自己的数据继续训练'],
               ['mAP50', 'IoU 阈值取 0.5 时的平均精度均值，衡量检测准不准的主要指标'],
               ['mAP50-95', 'IoU 从 0.5 到 0.95 每隔 0.05 取一次 mAP 再平均，比 mAP50 更严格'],
               ['NMS', '非极大值抑制，把同一个目标上重叠的多个预测框合并成一个'],
               ['归一化坐标', '框的中心点和宽高除以图片宽高，取值 0 到 1，换分辨率也不影响'],
               ['合成数据', '用程序渲染出来的图片和标注，不是真实拍摄的照片'],
               ['token', '登录成功后服务器签发的凭证，之后请求带上它表示已经登录'],
               ['PBKDF2', '一种加盐慢哈希算法，数据库里不存明文密码'],
               ['域差异', '合成图片和真实照片在光照、纹理、噪声上的分布差别']],
              widths=[3.2, 11.2], center_cols=(0,), caption='表1-1 术语说明')
    h2(doc, '1.4 参考资料')
    bullet(doc, '《需求分析说明书》《可行性分析报告》（第 5–6 周）')
    bullet(doc, '《概要设计说明书》（第 7–10 周）')
    bullet(doc, 'Ultralytics YOLOv8 官方文档：https://docs.ultralytics.com')
    bullet(doc, 'Flask 官方文档：https://flask.palletsprojects.com')
    bullet(doc, 'SQLite 官方文档：https://www.sqlite.org')
    bullet(doc, 'PyTorch 官方文档：https://pytorch.org/docs')
    h2(doc, '1.5 文档组织')
    body(doc, '第 2 章写数据集怎么构建、怎么标注、怎么划分；第 3 章写模型训练的环境、参数、'
              '过程和评估结果；第 4 章按模块写代码结构和关键实现；第 5 章写测试设计、'
              '测试用例和执行结果；第 6 章写系统怎么部署和运行；第 7 章写针对低对比度'
              '小目标的第二次迭代；第 8 章做总结。')

    # ------------------------------------------------------------ 2 数据集
    h1(doc, '2 数据集构建')
    h2(doc, '2.1 构建思路')
    body(doc, '目标检测模型的效果，七成看数据。按照概要设计的计划，第 11 周要完成'
              '“收集并标注数据、划分数据集”。真正开始做的时候，我们遇到了两个现实问题：'
              '一是网上能找到的手机屏幕缺陷照片很零散，六类缺陷凑不齐，很多还带水印；'
              '二是自己拍的话，划痕、裂纹这些缺陷在普通手机上不好制造，拍出来也不一定'
              '清楚，而且一张一张用 LabelImg 画框很费时间。')
    body(doc, '所以我们换了一个思路：写一个渲染程序，程序化地“造”出手机屏幕照片。'
              '背景、手机外壳、玻璃反光、屏幕壁纸都随机生成，六类缺陷按真实外观画到屏幕上，'
              '画框的位置在画的时候就知道，标签可以直接算出来，不需要人工标。这样做的好处'
              '是数据量不受限制、类别均衡可控、标签绝对准确、每次生成都能复现；缺点是'
              '合成图片和真实照片之间存在“域差异”，模型在真实照片上的表现需要用后面的'
              '实测来检验。这一点我们在 2.7 节单独说明。')
    body(doc, '整个数据集的构建流程是：运行 gen_dataset.py → 生成 images/ 和 labels/ → '
              '按 8:1:1 写到 train/val/test → 用测试脚本检查标签合法性和类别覆盖 → '
              '输出 dataset_stats.json 供训练和文档使用。')

    h2(doc, '2.2 合成方法')
    body(doc, '每张图片的生成过程分成 6 步：')
    body(doc, '1）画背景。随机选木纹桌面、磨砂桌面或布料三种材质之一，先铺一层上下渐变，'
              '再按材质画纹理（木纹曲线、细斑点或交叉斜纹），叠一层左上角来的柔光，'
              '最后加暗角和高斯噪声。')
    body(doc, '2）放手机。机身宽度取画面宽度的 34%–43%，长宽比 2.0–2.12，位置在画面'
              '中心附近随机偏移，圆角、金属边框、听筒和挖孔摄像头都画上。整机最后会绕'
              '中心随机旋转 ±7°，看起来更像随手拍的照片。')
    body(doc, '3）画屏幕。45% 的概率是亮屏：用两种随机颜色做渐变，叠低频波浪和模糊色块，'
              '模拟壁纸；其余是息屏：深色玻璃渐变，加 2–3 条模糊的斜向反光带和一块高光。'
              '两种模式都保留反光，因为真实拍摄时屏幕上几乎总有反光。')
    body(doc, '4）画缺陷。六类缺陷的绘制规则不一样，具体见表 2-1。缺陷先画在一个单独的'
              '图层上，再用屏幕圆角矩形做遮罩，保证不会画到边框外面。每张图随机放 0–4 个'
              '缺陷，放的时候检查框之间的 IoU，避免重叠在一起。')
    body(doc, '5）合成与退化。手机图层加阴影后贴到背景上，整图从 1280×1280 超采样缩小到'
              '640×640，再加轻微高斯模糊、亮度/对比度扰动、JPEG 压缩噪声，模拟手机拍摄'
              '和压缩的痕迹。')
    body(doc, '6）算标签。每个缺陷绘制时记录了外接矩形，按同样的旋转角度把四个角变换一次，'
              '取新的外接矩形，再除以图片边长归一化，写成 YOLO 格式的一行。')
    add_table(doc, ['编号', '名称', '中文名', '外观特征', '标注要点'],
              [['0', 'scratch', '划痕', '细长亮线，可轻微弯曲，常带一条偏冷的伴线', '框住整条线，两端各留 2–3 像素'],
               ['1', 'crack', '裂纹', '从一点向外分叉的亮线，常出现在边缘或角落', '框住所有分支，不能只框主干'],
               ['2', 'bright_spot', '亮点', '1–3 个发白或发绿的小圆点，周围有光晕', '框住整簇亮点'],
               ['3', 'dark_spot', '暗点', '暗色小圆斑，亮屏上明显，息屏上很淡', '框住整簇暗点'],
               ['4', 'stain', '污渍', '不规则的半透明斑块，边缘模糊，颜色偏灰黄', '框住整个斑块'],
               ['5', 'edge_chip', '边缘崩缺', '屏幕边缘的锯齿状缺口，一侧发亮', '框住缺口，包含屏幕边缘']],
              widths=[1.2, 2.6, 2.2, 6.4, 4.0], center_cols=(0, 1, 2), caption='表2-1 六类缺陷的定义')
    add_figure(doc, FIG / 'dataset_samples.png', '图2-1 数据集中带标注的样例（彩色框为标注框，颜色对应类别）', 16.0)
    body(doc, '图 2-1 是从测试集里挑出来的 8 张图，框的颜色和类别一一对应。可以看到'
              '亮屏和息屏、不同桌面材质、不同手机位置和角度都有覆盖，缺陷的尺度差别也比较大。')

    code_block(doc, '''
def draw_scratch(draw, rng, screen_box):
    sx0, sy0, sx1, sy1 = screen_box
    sw, sh = sx1 - sx0, sy1 - sy0
    length = rng.uniform(0.10, 0.32) * sw
    angle = rng.uniform(0, math.pi)
    cx = rng.uniform(sx0 + sw * 0.12, sx1 - sw * 0.12)
    cy = rng.uniform(sy0 + sh * 0.12, sy1 - sh * 0.12)
    pts = []
    for i in range(rng.randint(3, 6)):
        t = i / 5
        x = cx + math.cos(angle) * length * (t - 0.5)
        y = cy + math.sin(angle) * length * (t - 0.5)
        y += math.sin(t * math.pi * rng.uniform(0.8, 1.6)) * rng.uniform(-4, 4)
        pts.append((x, y))
    draw.line(pts, fill=(240, 240, 245, rng.randint(150, 230)),
              width=rng.randint(3, 6), joint='curve')
    return _bbox_of_points(pts, pad=6)
''', caption='代码2-1 划痕的绘制与候选框（gen_dataset.py）')
    body(doc, '代码 2-1 是划痕的绘制函数。先用随机长度、角度和中心点确定一条折线，'
              '每个点加一点正弦扰动让它不那么直，然后用不同宽度的亮色画出来，最后返回'
              '折线的外接矩形。其他五类缺陷的写法类似，只是几何形状和颜色不同。')

    code_block(doc, '''
# 把标注框的四个角按图片旋转角度变换，再取新的外接矩形
th = math.radians(angle)
for box in boxes:
    pts = []
    for px, py in [(box[0], box[1]), (box[2], box[1]),
                   (box[2], box[3]), (box[0], box[3])]:
        dx, dy = px - geo['cx'], py - geo['cy']
        rx = geo['cx'] + dx * math.cos(th) + dy * math.sin(th)
        ry = geo['cy'] - dx * math.sin(th) + dy * math.cos(th)
        pts.append((rx, ry))
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    nb = [min(xs), min(ys), max(xs), max(ys)]
''', caption='代码2-2 旋转后的标注框换算（gen_dataset.py 节选）')
    body(doc, '手机整机旋转之后，缺陷在图片上的位置也变了，所以标签不能直接用绘制时的坐标。'
              '代码 2-2 把框的四个角按同样的角度绕手机中心旋转，再取旋转后四个点的外接矩形，'
              '这样得到的框仍然是轴对齐的，符合 YOLO 的要求。')

    h2(doc, '2.3 标注规范')
    body(doc, '虽然标签是程序算出来的，但我们仍然按 YOLO 的标准格式组织，方便以后混入'
              '人工标注的真实照片。每张图片对应一个同名 txt，每行一个缺陷，格式是：')
    code_block(doc, 'class_id  center_x  center_y  width  height', caption='代码2-3 YOLO 标签格式')
    body(doc, '五个数之间用空格分开，坐标都是相对图片宽高的比例，取值 0–1；class_id 是'
              '0–5 的整数，顺序固定为 scratch、crack、bright_spot、dark_spot、stain、'
              'edge_chip。没有缺陷的图片也会有一个空的 txt 文件，训练时当作背景图使用。')
    body(doc, '标注规范有下面几条，后面接真实照片时也按这个来：')
    bullet(doc, '一个缺陷一个框，框要贴紧目标，边缘留 2–3 像素，不要框进大片正常区域；')
    bullet(doc, '划痕只框单条线，交叉的两条划痕算两个框；裂纹要把所有分支都框进去；')
    bullet(doc, '亮斑、暗斑按“簇”来框，一簇 2–3 个小点算一个目标；')
    bullet(doc, '边缘崩缺必须贴着屏幕边缘，框要包含缺口和一小段边缘；')
    bullet(doc, '宽或高小于 8 像素的目标不标，太小了模型也学不出来；')
    bullet(doc, '污渍和反光要区分开：反光是规则的亮带，污渍是不规则的暗色斑块。')
    body(doc, '因为图片是程序生成的，标注不会出现人手抖、漏标、类别点错的问题。为了确认'
              '标签和画面对得上，我们另外写了一个预览脚本，把框画回图片上抽查了几十张，'
              '没有发现框偏移或类别错位。')

    h2(doc, '2.4 数据划分与增强')
    body(doc, '数据集按 8:1:1 划分成训练集、验证集、测试集。三部分用不同的随机种子段生成，'
              '不会出现同一张图同时出现在训练集和测试集的情况。验证集在训练时用来挑最优'
              '权重，测试集只在最后评估时用一次，避免“拿考试题调参”。具体数量见表 2-2。')
    add_table(doc, ['划分', '图片数', '缺陷框数', '空图数', '占图片比例'],
              [['训练集 train', STATS['train']['images'], STATS['train']['boxes'], STATS['train']['empty'], '75.8%'],
               ['验证集 val', STATS['val']['images'], STATS['val']['boxes'], STATS['val']['empty'], '12.1%'],
               ['测试集 test', STATS['test']['images'], STATS['test']['boxes'], STATS['test']['empty'], '12.1%'],
               ['合计', STATS['train']['images'] + STATS['val']['images'] + STATS['test']['images'],
                STATS['train']['boxes'] + STATS['val']['boxes'] + STATS['test']['boxes'],
                STATS['train']['empty'] + STATS['val']['empty'] + STATS['test']['empty'], '100%']],
              widths=[4.2, 2.6, 3.0, 2.6, 2.8], center_cols=(0, 1, 2, 3, 4), caption='表2-2 数据集划分')
    body(doc, '训练时开了 ultralytics 自带的数据增强，参数见表 2-3。增强的目的不是把图片'
              '“变好看”，而是让模型见到更多样的光照、角度和遮挡，减少过拟合。因为手机'
              '在照片里基本是竖着的，所以没有开垂直翻转；水平翻转、±8° 旋转和缩放是'
              '符合实际拍摄情况的。')
    add_table(doc, ['参数', '取值', '作用'],
              [['mosaic', '0.8', '四张图拼成一张，增加小目标和背景多样性'],
               ['close_mosaic', '10', '最后 10 轮关闭 Mosaic，让模型在真实分布上收敛'],
               ['mixup', '0.1', '两张图按比例混合，提升抗干扰能力'],
               ['copy_paste', '0.1', '把一个图的缺陷复制到另一个图，增加缺陷组合'],
               ['hsv_h / hsv_s / hsv_v', '0.015 / 0.5 / 0.35', '色调、饱和度、亮度扰动'],
               ['degrees', '8', '随机旋转 ±8°'],
               ['translate', '0.1', '随机平移 10%'],
               ['scale', '0.5', '随机缩放 0.5–1.5 倍'],
               ['shear / perspective', '2 / 0.0005', '轻微错切和透视变形'],
               ['fliplr / flipud', '0.5 / 0', '水平翻转开，垂直翻转关'],
               ['erasing', '0.2', '随机擦除一小块，模拟遮挡']],
              widths=[4.6, 4.8, 6.0], center_cols=(0, 1), caption='表2-3 数据增强参数')
    note(doc, '说明：数据增强只在训练时生效，验证和测试用的是原图，保证评估结果可比较。')

    h2(doc, '2.5 数据集统计')
    add_figure(doc, FIG / 'dataset_distribution.png', '图2-2 各划分的类别数量与整体类别占比', 16.0)
    add_figure(doc, FIG / 'dataset_boxsize.png', '图2-3 六类缺陷标注框的尺寸分布', 13.5)
    body(doc, '从图 2-2 可以看到，训练集里划痕最多（538 个框），暗点最少（179 个框），'
              '整体比例大约 3:1，不算严重不平衡。暗点少是因为它在息屏画面上几乎看不见，'
              '生成器在息屏时会主动降低暗点的概率，这是有意为之：如果硬凑数量，模型会'
              '学到“暗点只出现在亮屏上”这种捷径，反而不利于泛化。')
    body(doc, '图 2-3 是标注框的宽高分布（相对图片尺寸）。划痕和裂纹偏细长，宽高比大；'
              '亮点、暗点集中在 1%–3% 的小尺寸区域；污渍和崩缺的框明显更大。这个分布'
              '和真实屏幕缺陷的直觉是一致的，也说明模型需要同时处理小目标和大目标。')
    add_table(doc, ['缺陷类别', '训练集', '验证集', '测试集', '合计', '占比'],
              [[CLASS_CN[c], STATS['train']['classes'][c], STATS['val']['classes'][c],
                STATS['test']['classes'][c],
                STATS['train']['classes'][c] + STATS['val']['classes'][c] + STATS['test']['classes'][c],
                f'{(STATS["train"]["classes"][c] + STATS["val"]["classes"][c] + STATS["test"]["classes"][c]) / 2552 * 100:.1f}%']
               for c in CLASS_CN],
              widths=[4.0, 2.4, 2.4, 2.4, 2.4, 2.4], center_cols=(0, 1, 2, 3, 4, 5),
              caption='表2-4 各类别缺陷框数量')
    body(doc, f'整个数据集共 {STATS["train"]["images"] + STATS["val"]["images"] + STATS["test"]["images"]} 张图片、'
              f'{STATS["train"]["boxes"] + STATS["val"]["boxes"] + STATS["test"]["boxes"]} 个缺陷框。'
              f'按本机的生成速度，训练集 1000 张大约 9 分钟，验证集和测试集各 1.5 分钟，'
              f'整套数据重新生成一次约 12 分钟。')

    h2(doc, '2.6 质量检查')
    body(doc, '数据生成完，我们用 tests/test_dataset.py 做了 6 项检查，都是自动跑的：')
    bullet(doc, '图片和标签一一对应，数量一致，没有“有图无标”或“有标无图”；')
    bullet(doc, '每行标签正好 5 个数，类别编号在 0–5 之间，坐标都在 0–1 之间；')
    bullet(doc, '每个框的宽高都大于 0.005，没有退化成一个点的框；')
    bullet(doc, 'train、val、test 三个划分里每一类都至少有 20 个样本；')
    bullet(doc, '抽查 8 张训练图，尺寸都是 640×640；')
    bullet(doc, 'data.yaml 里 nc=6，路径和类别名正确。')
    body(doc, '检查全部通过，结果见第 5 章。开发过程中我们也用肉眼抽查过几轮，发现并'
              '修掉了三个问题：')
    add_table(doc, ['发现的问题', '现象', '处理'],
              [['手机会被裁掉', '早期版本机身宽度取到画面的 66%，整机高度超出画布，上下被切', '把机身宽度改成 34%–43%，保证整机落在画面内'],
               ['壁纸太假', '亮屏用几个大色块模糊，看起来像气泡，不像壁纸', '改成双色渐变 + 低频波浪 + 低透明度模糊色块'],
               ['划痕太细', '640 像素下划痕只有 1–2 像素，肉眼都难看清', '线宽从 2–5 调到 3–6，并加一条偏冷的伴线']],
              widths=[4.6, 6.8, 4.0], caption='表2-5 数据检查中发现的问题')

    h2(doc, '2.7 真实数据接入方案')
    body(doc, '合成数据能把流程跑通，但要真正用于质检，必须补真实照片。我们预留了接入'
              '方式，不需要改代码：用 LabelImg 打开真实照片，按 2.3 节的规范画框、选类别，'
              '导出 YOLO 格式的 txt；把图片放进 datasets/images/train（或新建一个 real 目录），'
              'txt 放进 datasets/labels/train，在 data.yaml 里加上路径即可。')
    body(doc, '建议的做法是：先收集 200–300 张真实照片，覆盖六类缺陷和正常屏幕，按 8:1:1'
              '划分；用现在这个合成数据训好的 best.pt 做初始化，学习率降到 0.001 左右，'
              '再训练 20–30 轮。这样既利用了合成数据学到的通用特征，又能让模型适应真实'
              '照片的光照和纹理。真实数据越多，合成数据的权重就应该越小，最后可以完全'
              '用真实数据微调。')
    note(doc, '需要说明的是：本文第 3 章的 mAP 是在合成测试集上得到的，数值会偏高，'
              '不能直接当作真实产线精度。真实场景的指标要等第 15–18 周补拍数据后重新评估。')

    # ------------------------------------------------------------ 3 训练
    h1(doc, '3 模型训练设计')
    h2(doc, '3.1 训练环境')
    add_table(doc, ['项目', '配置'],
              [['操作系统', 'Windows 11 专业版 10.0.26300'],
               ['CPU', 'Intel Core i7-14650HX，16 核 24 线程'],
               ['内存', '16 GB'],
               ['显卡', 'NVIDIA GeForce RTX 4060 Laptop GPU，8 GB 显存'],
               ['显卡驱动 / CUDA', '616.64 / CUDA 12.6'],
               ['Python', '3.11.16（conda 环境 diffusion-course）'],
               ['PyTorch', '2.14.1+cu126'],
               ['ultralytics', '8.4.198'],
               ['Flask / SQLite', '3.1.3 / Python 内置 sqlite3'],
               ['其他', 'OpenCV 5.0、Pillow 12.3、NumPy 2.4、pandas 3.1、Matplotlib 3.11']],
              widths=[4.2, 10.2], center_cols=(0,), caption='表3-1 训练与运行环境')
    body(doc, '这台笔记本的 8 GB 显存跑 YOLOv8n、batch 24、640 输入时占用约 3.6 GB，'
              '还有余量；如果换更大的模型或更大的 batch，需要相应调小。')

    h2(doc, '3.2 模型选择')
    body(doc, 'YOLOv8 有 n、s、m、l、x 五个尺度。我们的数据量是 1320 张、6 个类别，'
              '目标不算特别复杂，而且最终要在一台普通笔记本上演示，所以优先考虑速度和'
              '显存占用。三个候选的对比见表 3-2。')
    add_table(doc, ['模型', '参数量', '计算量（640）', '显存占用', '适用情况'],
              [['yolov8n', '约 3.0 M', '8.2 GFLOPs', '约 3.6 GB（batch 24）', '数据量不大、要快、要能在笔记本上跑'],
               ['yolov8s', '约 11.2 M', '28.6 GFLOPs', '约 6 GB', '有显卡、追求更高精度'],
               ['yolov8m', '约 25.9 M', '78.9 GFLOPs', '8 GB 以上', '数据量大、精度优先']],
              widths=[2.6, 3.0, 4.0, 4.4, 6.4], center_cols=(0, 1, 2, 3), caption='表3-2 模型尺度对比')
    body(doc, '我们最终选的是 yolov8n，原因是：第一，六类缺陷的形态差别比较明显，'
              'n 的表达能力够用；第二，n 训练快，一轮十几秒，方便反复调；第三，'
              '演示用的笔记本只有 8 GB 显存，n 更稳。如果后面加了真实数据发现精度不够，'
              '再换成 yolov8s 重新训练，代码不用改。')
    body(doc, '训练方式是迁移学习：加载 COCO 上预训练的 yolov8n.pt，把检测头换成 6 类，'
              '再用我们的数据继续训练。预训练权重里已经有边缘、纹理这些通用特征，'
              '比从头训练收敛快很多，也不容易过拟合。')

    h2(doc, '3.3 训练参数')
    add_table(doc, ['参数', '取值', '说明'],
              [['预训练权重', 'yolov8n.pt', 'COCO 预训练，首次运行自动下载'],
               ['epochs', '60', '最多 60 轮，验证集 20 轮不提升就提前停止'],
               ['batch', '24', '每批 24 张，显存占用约 3.6 GB'],
               ['imgsz', '640', '输入图片边长，和概要设计一致'],
               ['optimizer', 'AdamW', '自适应学习率优化器'],
               ['lr0 / lrf', '0.005 / 0.01', '初始学习率 / 最终学习率比例'],
               ['weight_decay', '0.0005', '权重衰减，抑制过拟合'],
               ['warmup_epochs', '3', '前 3 轮预热，避免一开始学习率过大'],
               ['cos_lr', 'True', '余弦退火，学习率平滑下降'],
               ['patience', '20', '验证集指标 20 轮不提升就停止'],
               ['seed', '0', '固定随机种子，结果可复现'],
               ['workers', '4', 'DataLoader 线程数'],
               ['amp', 'True', '混合精度训练，省显存、提速'],
               ['close_mosaic', '10', '最后 10 轮关闭 Mosaic']],
              widths=[3.4, 3.2, 8.4], center_cols=(0, 1), caption='表3-3 训练参数')
    body(doc, '学习率没有用默认值，而是取了 0.005。因为数据量不大，太大的学习率会让'
              '损失来回震荡；0.005 配合余弦退火，前几轮下降快，后面慢慢收，比较稳。'
              'Mosaic 放在最后 10 轮关闭，是为了让模型在训练后期见到“正常”的图片分布，'
              '收敛到更真实的检测能力。')

    h2(doc, '3.4 训练过程')
    minutes = METRICS['train_seconds'] / 60
    body(doc, f'训练在本机 GPU 上完成，60 轮一共用了约 {minutes:.0f} 分钟，平均每轮十几秒。'
              f'训练过程中的损失和指标曲线如图 3-1 所示。')
    add_figure(doc, FIG / 'train_results.png', '图3-1 训练过程的损失与验证指标曲线', 16.0)
    body(doc, '图 3-1 一共有 10 张小图：第一行前 3 张是训练损失（box_loss、cls_loss、'
              'dfl_loss），后 2 张是验证集的 Precision 和 Recall；第二行前 3 张是验证损失，'
              '后 2 张是 mAP50 和 mAP50-95。前 10 轮损失下降很快，mAP50 从 0 涨到 0.97 左右；'
              '之后曲线变平，只有小幅波动。第 50 轮关闭 Mosaic 时，训练损失有一次明显的跳变，'
              '这是因为数据分布突然从“拼图”变回“整图”，属于正常现象，不是训练失败。')
    body(doc, f'验证集上 mAP50 最高出现在第 {BEST_EPOCH} 轮，为 {BEST_MAP50:.4f}；'
              f'之后没有再明显提升，说明模型已经收敛。验证损失没有出现持续上升，'
              f'说明没有明显过拟合。')
    body(doc, '整个训练过程没有出现显存不足或崩溃。中间有一次失败是我们在写快速验证'
              '脚本时忘了加 if __name__ == "__main__" 保护，Windows 上 DataLoader 的'
              '多进程会把脚本反复重新导入，看起来像卡死；加上保护、把 workers 设为 0 '
              '之后就正常了。正式训练脚本一开始就写了保护，所以没有这个问题。')

    h2(doc, '3.5 评估指标与结果')
    body(doc, '训练结束后，用验证集挑出的 best.pt 在测试集上做最终评估。测试集有 '
              f'{STATS["test"]["images"]} 张图片、{STATS["test"]["boxes"]} 个缺陷框，'
              '模型之前没有见过这些图片。总体指标见表 3-4。')
    add_table(doc, ['指标', '数值', '说明'],
              [['Precision', f'{M["precision"]:.4f}', '查准率：检出的缺陷里有多少是真的'],
               ['Recall', f'{M["recall"]:.4f}', '查全率：真实缺陷里有多少被检出'],
               ['mAP50', f'{M["map50"]:.4f}', 'IoU=0.5 时的平均精度，主要参考指标'],
               ['mAP50-95', f'{M["map50_95"]:.4f}', '更严格的指标，对框的贴合程度要求更高'],
               ['推理速度', f'{METRICS["speed_ms"].get("inference", 0):.1f} ms/张', 'GPU 上单张图片的模型前向时间']],
              widths=[3.6, 4.0, 7.8], center_cols=(0, 1), caption='表3-4 测试集总体指标')
    add_table(doc, ['类别', '测试框数', 'Precision', 'Recall', 'mAP50', 'mAP50-95'],
              [[CLASS_CN[name],
                STATS['test']['classes'][name],
                f'{PC[name]["precision"]:.4f}' if PC[name]['precision'] is not None else '—',
                f'{PC[name]["recall"]:.4f}' if PC[name]['recall'] is not None else '—',
                f'{PC[name]["map50"]:.4f}' if PC[name]['map50'] is not None else '—',
                f'{PC[name]["map50_95"]:.4f}' if PC[name]['map50_95'] is not None else '—']
               for name in ['scratch', 'crack', 'bright_spot', 'dark_spot', 'stain', 'edge_chip']],
              widths=[3.4, 2.8, 2.8, 2.8, 2.8, 3.0], center_cols=(0, 1, 2, 3, 4, 5),
              caption='表3-5 分类别指标')
    add_figure(doc, FIG / 'test_confusion_matrix.png', '图3-2 测试集归一化混淆矩阵', 12.0)
    add_figure(doc, FIG / 'test_pr_curve.png', '图3-3 测试集各类别的 PR 曲线', 13.0)
    map_values = {n: PC[n]['map50'] for n in PC if PC[n]['map50'] is not None}
    worst = min(map_values, key=map_values.get)
    best = max(map_values, key=map_values.get)
    body(doc, f'从表 3-5 和图 3-2、3-3 看，六类的 mAP50 在 {map_values[worst]:.4f} 到 '
              f'{map_values[best]:.4f} 之间，最低的是{CLASS_CN[worst]}，最高的是{CLASS_CN[best]}，'
              f'整体比较均衡。混淆矩阵里六类之间的非对角线元素基本是 0，说明类别本身没有'
              f'明显互混；相对多的误差落在 background 一列，主要是漏检和把背景误当成目标，'
              f'其中划痕对应的数值最高，和它线条细、对比度低有关。亮点和暗点的特征相反，'
              f'几乎没有互混。边缘崩缺和污渍的框比较大，定位容易，指标也高。')
    body(doc, '这里要再强调一次：这些数字是在合成测试集上得到的，图片风格和训练集一致，'
              '所以偏高是正常的。它的意义是证明“模型能从这些图片里学到六类缺陷的特征、'
              '训练流程是通的”，而不是证明“模型在真实产线上有 0.98 的 mAP”。真实场景的'
              '评估要等补拍数据之后再做。')
    add_figure(doc, FIG / 'train_val_pred.jpg', '图3-4 验证集批次的预测结果（框上方为预测类别与置信度）', 15.0)
    body(doc, '图 3-4 是验证集一个批次的预测示例，可以看到大部分缺陷都被框出来了，'
              '框的位置和类别标签基本正确。个别非常淡的划痕会漏检，这也是后面补真实'
              '数据时要重点解决的。')

    h2(doc, '3.6 调参与问题记录')
    body(doc, '实现过程中遇到的问题和我们的处理办法见表 3-6。这些问题有的是环境问题，'
              '有的是数据问题，记下来是为了以后换电脑或换数据时少走弯路。')
    add_table(doc, ['问题', '现象', '原因', '处理'],
              [['训练卡住', '第一次跑快速验证时，命令一直不结束，GPU 占用很低', '脚本没有 if __name__ 保护，Windows 多进程反复导入', '加保护，快速验证用 workers=0'],
               ['手机被裁切', '样本图里手机上下超出画布', '机身尺寸上限算错，高度超过画布', '把宽度上限从 0.66 降到 0.43'],
               ['壁纸不真实', '亮屏像几个大色块，和真机差别大', '模糊半径和色块透明度不合适', '改成渐变 + 波浪 + 低透明度色块'],
               ['训练初期 mAP=0', '只训 1 轮时所有指标都是 0', '模型还没学到东西，属正常', '至少训 30 轮再判断'],
               ['暗点样本偏少', '暗点只有 179 个训练框', '息屏时暗点不可见，生成概率被调低', '保留现状，避免学到错误先验'],
               ['Mosaic 关闭后损失跳变', '第 51 轮损失突然变大', '数据分布从拼图回到整图', '正常现象，不用处理'],
               ['显存占用', 'batch 24 时约 3.6 GB', '640 输入 + 24 张图', '8 GB 显存够用，不需要减小 batch']],
              widths=[3.2, 5.2, 4.6, 4.6], caption='表3-6 训练中的问题与处理')

    h2(doc, '3.7 模型部署方式')
    body(doc, '训练完的 best.pt 大约 6 MB，复制到项目的 models/ 目录，程序启动时'
              '用 YOLO("models/best.pt") 加载。检测器是进程内单例，第一次请求时加载，'
              '之后复用；加载时会先跑一张空白图预热，避免用户的第一张图特别慢。'
              '程序会自动判断有没有 CUDA，有就用 GPU，没有就退回 CPU，代码不用改。')
    body(doc, f'在本机 GPU 上，单张图片的模型前向时间约 {METRICS["speed_ms"].get("inference", 0):.1f} ms，'
              f'加上预处理和后处理约 {sum(v for k, v in METRICS["speed_ms"].items() if k in ("preprocess", "inference", "postprocess")):.1f} ms。'
              f'检测接口一次完整的请求（含上传、画框、写库）实测平均约 {PERF.get("api_ms", AVG_COST):.0f} ms，'
              f'具体见 5.5 节的性能测试。')
    body(doc, '模型文件不存在时，检测接口返回 503，页面会提示“模型未加载”，不会让整个'
              '系统崩溃。想换模型，只要把新的 best.pt 覆盖到 models/ 目录、重启程序即可，'
              '不需要改代码。')
    h2(doc, '3.8 小结')
    body(doc, '这一章完成了模型训练：用程序化合成的 1320 张图片，基于 COCO 预训练的'
              'yolov8n 做迁移学习，训了 60 轮，在合成测试集上 mAP50 达到 '
              f'{M["map50"]:.4f}、mAP50-95 达到 {M["map50_95"]:.4f}，单张推理约 '
              f'{METRICS["speed_ms"].get("inference", 0):.1f} ms。模型已经能稳定识别六类缺陷，'
              '满足课程演示的要求；真实场景的泛化能力还需要补数据验证。')

    # ------------------------------------------------------------ 4 模块详细设计
    h1(doc, '4 模块详细设计')
    h2(doc, '4.1 代码组织结构')
    body(doc, '代码分后端、前端、数据集与训练、测试四部分，目录结构如图 4-1 所示。'
              '后端用 Flask 的应用工厂模式，把页面路由、REST 接口、认证、检测、数据库'
              '拆成独立模块，互相之间只通过函数调用和数据库交互，不import对方内部的变量。')
    add_figure(doc, FIG / 'package_structure.png', '图4-1 代码包结构与依赖关系', 16.0)
    add_table(doc, ['文件', '行数', '主要职责'],
              [['run.py', '48', '启动入口：解析端口、初始化应用、预加载模型'],
               ['config.py', '41', '路径、类别、阈值、演示账号等配置'],
               ['app/__init__.py', '58', '应用工厂、蓝图注册、错误处理'],
               ['app/views.py', '110', '8 个页面的路由与登录/管理员保护'],
               ['app/api.py', '302', '18 个 REST 接口：注册、登录、资料、用户、上传、检测、记录、统计、参数'],
               ['app/auth.py', '133', 'PBKDF2 密码哈希、签名 token、登录装饰器'],
               ['app/detection.py', '186', 'YOLOv8 加载、推理、坐标换算、画框'],
               ['app/db.py', '253', '建表、记录增删改查、统计查询、参数读写'],
               ['app/utils.py', '92', '图片校验、保存、删除、路径安全'],
               ['datasets/gen_dataset.py', '599', '程序化生成数据集和 YOLO 标签'],
               ['train/train.py', '171', '训练、测试集评估、模型与指标归档']],
              widths=[5.4, 1.8, 8.2], center_cols=(1,), caption='表4-1 主要代码文件')
    body(doc, '后端 Python 代码约 2400 行，前端 HTML/CSS/JS 约 1800 行。前端没有用'
              'Vue 或 React，也没有打包步骤，就是 Flask 渲染模板 + 原生 fetch，'
              '这样演示时不需要装 Node，改一行刷新就能看到。')
    add_table(doc, ['配置项', '默认值', '说明'],
              [['DB_PATH', 'week11-14/data.db', 'SQLite 数据库文件'],
               ['UPLOAD_DIR', 'static/uploads', '原图目录'],
               ['RESULT_DIR', 'static/results', '画框结果图目录'],
               ['MODEL_PATH', 'models/best.pt', '训练好的模型'],
               ['MAX_CONTENT_LENGTH', '20 MB', '单张图片大小上限'],
               ['DEFAULT_CONF', '0.25', '默认置信度阈值'],
               ['DEFAULT_IOU', '0.45', 'NMS 的 IoU 阈值'],
               ['IMG_SIZE', '640', '模型输入尺寸'],
               ['TOKEN_MAX_AGE', '12 小时', '登录 token 有效期'],
               ['CLASSES', '6 类', '编号、英文名、中文名、画框颜色']],
              widths=[4.0, 5.0, 6.4], center_cols=(0, 1), caption='表4-2 主要配置项')

    h2(doc, '4.2 认证模块')
    body(doc, '认证模块负责三件事：密码怎么存、登录后怎么证明“我是我”、哪些接口需要登录。')
    body(doc, '注册通过 /register 页面完成：用户名限 2–20 位中文、字母、数字或下划线，'
              '密码至少 6 位，两次输入要一致，用户名不能重复；注册出来的账号角色固定为'
              ' user，不能自己选管理员。管理员账号仍然由初始化脚本创建，避免任何人注册'
              '成管理员。')
    body(doc, '密码不存明文，用 PBKDF2-SHA256 加盐哈希，迭代 120000 次，存成'
              '“算法$迭代次数$盐$摘要”的格式。校验的时候用 secrets.compare_digest 做'
              '恒定时间比较，避免通过响应时间猜密码。')
    code_block(doc, '''
def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'),
                                 salt.encode('utf-8'), 120000)
    return f'pbkdf2_sha256$120000${salt}${digest.hex()}'

def verify_password(password, stored):
    algo, iterations, salt, expected = stored.split('$')
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'),
                                 salt.encode('utf-8'), int(iterations))
    return secrets.compare_digest(digest.hex(), expected)
''', caption='代码4-1 密码哈希与校验（app/auth.py）')
    body(doc, '登录成功后，服务器用 itsdangerous 签发一个带签名的 token，里面放用户 id、'
              '用户名和角色，有效期 12 小时。token 写进 HttpOnly 的 Cookie，浏览器'
              '自动携带，JavaScript 读不到，能降低 XSS 偷 token 的风险。接口同时也接受'
              '请求头里的 X-Token，方便用脚本或 Postman 调试。')
    code_block(doc, '''
def issue_token(user):
    return _serializer().dumps({'uid': user['id'], 'username': user['username'],
                                'role': user['role']})

def get_current_user():
    token = (request.headers.get('X-Token')
             or request.cookies.get(current_app.config['COOKIE_NAME'], ''))
    payload = read_token(token)          # 校验签名和过期时间
    if not payload:
        return None
    user = db.get_user_by_id(int(payload['uid']))
    if not user or user['username'] != payload['username']:
        return None
    return user
''', caption='代码4-2 token 的签发与校验（app/auth.py 节选）')
    add_figure(doc, FIG / 'sequence_login.png', '图4-2 登录认证时序图', 15.0)
    body(doc, '页面和接口用了两个装饰器：page_login_required 在没登录时 302 跳到登录页，'
              'api_login_required 返回 401 JSON；api_admin_required 还会检查 role，'
              '不是管理员就返回 403。这样参数修改这类敏感操作只有管理员能做。')
    note(doc, '和概要设计的一处调整：概要设计里写的是“返回 token，前端存起来，之后放请求头”。'
              '详细设计改成“签名 token 写进 HttpOnly Cookie，接口同时兼容 X-Token”。'
              '原因是 localStorage 里的 token 能被 XSS 读走，而 HttpOnly Cookie 读不到；'
              '同时保留 X-Token 是为了方便接口测试。功能和安全目标都没有变。')

    h2(doc, '4.3 检测模块')
    body(doc, '检测模块是整个系统的核心，输入一张图片的路径，输出缺陷列表（类别、置信度、'
              '归一化坐标）、画好框的 PIL 图片和推理耗时。对外只暴露 DefectDetector 类，'
              '主要方法见表 4-3。')
    add_table(doc, ['方法', '输入', '输出', '说明'],
              [['__init__', 'model_path, imgsz, device', '实例', '保存配置，不加载模型'],
               ['_ensure_model', '无', '无', '第一次调用时加载 best.pt 并预热，失败抛异常'],
               ['detect', 'image_path, conf, iou', 'dict', '读图、推理、后处理、画框'],
               ['annotate', 'PIL 图片, defects', 'PIL 图片', '按类别颜色画框和标签'],
               ['loaded', '无', 'bool', '模型是否已加载，供健康检查使用']],
              widths=[3.4, 5.4, 2.8, 5.8], center_cols=(0, 2), caption='表4-3 DefectDetector 的方法')
    add_figure(doc, FIG / 'detect_flow.png', '图4-3 单张图片的检测流程', 13.5)
    body(doc, '检测流程可以分为四段：')
    body(doc, '（1）预处理。用 PIL 打开图片，先按 EXIF 信息把手机拍的横竖方向转正，'
              '再转成 RGB。缩放和补边交给 ultralytics 内部做：它会把长边缩到 640，'
              '短边补灰边，保持长宽比不变。这样图片不会变形，框换算回去也简单。')
    body(doc, '（2）推理。调用 model.predict(source=img, imgsz=640, conf=conf, iou=iou)，'
              '返回的 boxes 里已经是原图坐标系下的 xyxy，不需要我们再乘缩放比例。'
              '置信度过滤和 NMS 都在 predict 里完成，我们只做一次坐标裁剪，防止框越界。')
    body(doc, '（3）后处理。把 xyxy 转成“中心点 + 宽高”再除以图片宽高，得到 0–1 的'
              '归一化坐标。数据库里存的就是归一化坐标，好处是换分辨率、换前端显示尺寸'
              '都不用改数据。缺陷按置信度从高到低排序。')
    body(doc, '（4）画框。按类别取颜色，画一个带圆角的框，框上方画类别中文名和置信度，'
              '左上角再叠一行“检出 N 处缺陷”。中文需要字体文件，优先用微软雅黑，'
              '找不到就退回黑体，再找不到就用 PIL 默认字体（这时中文会显示成方块，'
              '但不会报错）。')
    code_block(doc, '''
def detect(self, image_path, conf=None, iou=None):
    self._ensure_model()
    img = ImageOps.exif_transpose(Image.open(image_path)).convert('RGB')
    width, height = img.size
    with self.lock:                         # ultralytics 推理不是线程安全的
        t0 = time.perf_counter()
        result = self.model.predict(source=img, imgsz=self.imgsz, conf=conf,
                                    iou=iou, device=self.device, verbose=False)[0]
        cost_ms = int((time.perf_counter() - t0) * 1000)

    defects = []
    for (x0, y0, x1, y1), cf, cid in zip(result.boxes.xyxy.cpu().numpy(),
                                         result.boxes.conf.cpu().numpy(),
                                         result.boxes.cls.cpu().numpy().astype(int)):
        defects.append({
            'class_id': int(cid),
            'conf': round(float(cf), 4),
            'x': round((x0 + x1) / 2 / width, 6),
            'y': round((y0 + y1) / 2 / height, 6),
            'w': round((x1 - x0) / width, 6),
            'h': round((y1 - y0) / height, 6),
        })
    defects.sort(key=lambda d: d['conf'], reverse=True)
    return {'defects': defects, 'annotated': self.annotate(img, defects),
            'width': width, 'height': height, 'cost_ms': cost_ms}
''', caption='代码4-3 检测主流程（app/detection.py 节选）')
    body(doc, '检测器用线程锁保护推理。Flask 开发服务器是多线程的，如果两个请求同时'
              '调用同一个模型实例，PyTorch 的 CUDA 上下文可能报错，加锁之后请求会排队，'
              '单机演示场景下影响不大。模型只在第一次请求时加载，之后的请求直接复用，'
              '所以第一张图会慢几秒，后面就稳定了。')

    h2(doc, '4.4 数据库模块')
    body(doc, '数据库用 SQLite，整个库就是一个 data.db 文件，不用装数据库软件。'
              '按照概要设计建了 4 张表：用户表、检测记录表、缺陷明细表、系统参数表，'
              '表结构和关系如图 4-4 所示。')
    add_figure(doc, FIG / 'db_schema.png', '图4-4 数据库表结构与关系', 16.0)
    body(doc, '和概要设计相比，记录表多了一个 cost_ms 字段，用来存这次推理的耗时；'
              '用户表多了 nickname 和 avatar，用来存自定义昵称和头像。统计页要显示'
              '“平均耗时”，个人资料页要显示昵称头像，没有这两个字段就只能用用户名和'
              '字母头像代替。其他字段和概要设计一致。')
    add_table(doc, ['字段', '类型', '约束', '说明'],
              [['id', 'INTEGER', 'PK, AUTOINCREMENT', '用户编号'],
               ['username', 'TEXT', 'NOT NULL, UNIQUE', '用户名（登录用，不可改）'],
               ['password', 'TEXT', 'NOT NULL', 'PBKDF2 哈希值'],
               ['role', 'TEXT', 'NOT NULL', 'admin / user'],
               ['nickname', 'TEXT', '', '昵称，2–16 位，可为空时回退用户名'],
               ['avatar', 'TEXT', '', '头像相对路径 avatars/xxx.jpg'],
               ['created_at', 'TEXT', 'NOT NULL', '注册时间']],
              widths=[3.2, 2.8, 4.8, 5.0], center_cols=(0, 1), caption='表4-4 用户表 t_user')
    add_table(doc, ['字段', '类型', '约束', '说明'],
              [['id', 'INTEGER', 'PK', '记录编号'],
               ['user_id', 'INTEGER', 'FK → t_user.id', '检测人'],
               ['image_path', 'TEXT', 'NOT NULL', '原图相对路径'],
               ['result_path', 'TEXT', '', '结果图相对路径'],
               ['total', 'INTEGER', 'NOT NULL', '缺陷数'],
               ['status', 'TEXT', 'NOT NULL', 'done / failed'],
               ['conf', 'REAL', 'NOT NULL', '使用的置信度阈值'],
               ['cost_ms', 'INTEGER', 'NOT NULL', '推理耗时（毫秒）'],
               ['created_at', 'TEXT', 'INDEX', '检测时间']],
              widths=[3.2, 2.8, 5.0, 4.8], center_cols=(0, 1), caption='表4-5 检测记录表 t_record')
    add_table(doc, ['字段', '类型', '约束', '说明'],
              [['id', 'INTEGER', 'PK', '明细编号'],
               ['record_id', 'INTEGER', 'FK → t_record.id', '所属记录'],
               ['class_id', 'INTEGER', 'NOT NULL', '类别 0–5'],
               ['class_name', 'TEXT', 'NOT NULL', '英文类别名'],
               ['conf', 'REAL', 'NOT NULL', '置信度'],
               ['x / y', 'REAL', 'NOT NULL', '框中心归一化坐标'],
               ['w / h', 'REAL', 'NOT NULL', '框归一化宽高']],
              widths=[3.2, 2.8, 5.0, 4.8], center_cols=(0, 1), caption='表4-6 缺陷明细表 t_defect')
    add_table(doc, ['字段', '类型', '约束', '说明'],
              [['id', 'INTEGER', 'PK', '参数编号'],
               ['name', 'TEXT', 'UNIQUE', '参数名'],
               ['value', 'TEXT', 'NOT NULL', '参数值（统一存字符串）']],
              widths=[3.2, 2.8, 5.0, 4.8], center_cols=(0, 1), caption='表4-7 系统参数表 t_config')
    body(doc, '索引和约束有这几个考虑：t_record.created_at 建了普通索引，历史页按时间'
              '倒序查比较快；t_record.user_id 和 t_defect.record_id 也建了索引，'
              '按用户筛记录、按记录查明细都不慢；username 加了唯一约束，避免注册重复。')
    body(doc, 'SQLite 默认不启用外键约束，所以删除记录时不能只删 t_record，要先删'
              't_defect 再删 t_record，否则会留下孤儿明细。这个逻辑写在 delete_record() '
              '里，同时把原图和结果图也删掉，避免磁盘越用越满。')
    code_block(doc, '''
def create_record(user_id, image_path, result_path, total, status,
                  conf, cost_ms, defects):
    db = get_db()
    cur = db.execute(
        'INSERT INTO t_record (user_id, image_path, result_path, total, status, '
        'conf, cost_ms, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (user_id, image_path, result_path, total, status, conf, cost_ms, now_str()))
    rid = cur.lastrowid
    for d in defects:
        db.execute(
            'INSERT INTO t_defect (record_id, class_id, class_name, conf, x, y, w, h) '
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (rid, d['class_id'], d['class_name'], d['conf'],
             d['x'], d['y'], d['w'], d['h']))
    db.commit()
    return rid
''', caption='代码4-4 一次检测的入库（app/db.py 节选）')
    body(doc, '记录和明细在同一个事务里插入，要么都成功，要么都回滚，不会出现“记录有了'
              '但没有缺陷”的半截数据。统计查询用 GROUP BY 按类别汇总，再在 Python 里'
              '补齐没有出现的类别，保证前端拿到的永远是 6 类，柱状图和饼图不会缺项。')

    h2(doc, '4.5 接口模块')
    add_figure(doc, FIG / 'sequence_detect.png', '图4-5 检测接口的时序图', 16.0)
    add_table(doc, ['方法', '地址', '登录', '参数', '作用'],
              [['POST', '/api/login', '否', 'username, password', '登录，返回 token'],
               ['POST', '/api/register', '否', 'username, password, confirm', '注册普通用户'],
               ['POST', '/api/logout', '是', '无', '退出登录'],
               ['GET', '/api/me', '是', '无', '当前登录用户'],
               ['GET/PUT', '/api/profile', '是', 'nickname', '查看/修改昵称'],
               ['POST/DELETE', '/api/profile/avatar', '是', 'file（POST）', '上传/恢复默认头像'],
               ['GET', '/api/users', '是（管理员）', '无', '所有用户的列表和检测统计'],
               ['POST', '/api/upload', '是', 'file', '上传图片，返回相对路径'],
               ['POST', '/api/detect', '是', 'file 或 image_path, conf', '检测并写记录'],
               ['GET', '/api/records', '是', 'page, size, start, end, has_defect, user_id（管理员）', '分页查记录'],
               ['GET', '/api/records/<id>', '是', '无', '记录详情含缺陷'],
               ['DELETE', '/api/records/<id>', '是', '无', '删除记录和文件'],
               ['GET', '/api/records/<id>/csv', '是', '无', '导出缺陷明细 CSV'],
               ['GET', '/api/stats', '是', 'start, end', '分类、总量、趋势统计'],
               ['GET/PUT', '/api/settings', '是（PUT 管理员）', 'conf_threshold, iou_threshold', '查看/修改参数'],
               ['GET', '/api/health', '否', '无', '模型与数据库健康检查']],
              widths=[2.0, 5.4, 3.0, 5.0, 5.0], center_cols=(0, 1, 2), font_size=9.5,
              caption='表4-8 接口列表')
    body(doc, '所有接口返回统一的 JSON：code 是业务状态码，message 是给人看的提示，'
              'data 是实际数据。成功时 code=200，出错时 HTTP 状态码和 code 一致，'
              '前端只要判断 code 是不是 200 就行。')
    code_block(doc, '''
// 成功
{"code": 200, "message": "检测完成", "data": {
    "record_id": 24, "total": 2,
    "result_image": "results/res_img_20261120_101500_ab12.jpg",
    "defects": [
        {"class_id": 0, "class_name": "scratch", "conf": 0.91,
         "x": 0.31, "y": 0.45, "w": 0.12, "h": 0.08}
    ]
}}
// 失败（HTTP 400）
{"code": 400, "message": "置信度阈值必须在 0.01 到 0.99 之间", "data": null}
''', caption='代码4-5 接口返回格式示例')
    body(doc, '参数校验放在接口层：conf 限定 0.01–0.99，iou 限定 0.05–0.95，'
              '日期必须是 YYYY-MM-DD，page 和 size 有上下限（size 最大 100）。'
              '图片路径只接受 uploads/ 开头、并且确实存在于 static 目录下的文件，'
              '防止通过 image_path 读到系统里的其他文件。')
    add_table(doc, ['情况', 'HTTP / code', '返回提示'],
              [['未登录或 token 过期', '401', '请先登录'],
               ['普通用户改参数', '403', '只有管理员可以修改参数'],
               ['参数不合法', '400', '参数错误 / 阈值超出范围'],
               ['记录不存在或不属于当前用户', '404', '记录不存在'],
               ['图片格式不对或超过 20MB', '400 / 413', '图片格式不支持 / 图片超过 20MB'],
               ['模型文件缺失', '503', '模型文件不存在，请先训练模型'],
               ['检测过程异常', '500', '检测失败（记录 #id）：原因']],
              widths=[6.0, 3.2, 6.2], center_cols=(1,), caption='表4-9 错误码约定')

    h2(doc, '4.6 前端模块')
    body(doc, '前端一共 5 个页面，都用同一个 base.html 套侧边栏和顶栏，只有内容区不同。'
              '样式用 Bootstrap 5 的基础栅格和按钮，再叠一层自己的 style.css；图表用'
              'ECharts，直接放在 static/vendor 里，不联网也能显示。')
    add_table(doc, ['页面', '路由', '主要内容', '对应脚本'],
              [['登录页', '/login', '用户名密码、错误提示、演示账号', '内联脚本'],
               ['检测页', '/detect', '拖拽上传、多图预览、阈值滑块、最近检测', 'detect.js'],
               ['结果页', '/result/<id>', '结果图、缺陷列表、下载、导出 CSV', '无'],
               ['历史记录', '/history', '日期/有无缺陷筛选、表格、分页、删除', 'history.js'],
               ['数据统计', '/stats', '4 个数字卡片、柱状图、饼图、趋势图', 'stats.js'],
               ['个人资料', '/profile', '头像、昵称、我的检测统计', 'profile.js'],
               ['用户管理（管理员）', '/admin/users', '所有用户、检测次数、缺陷数、查看记录', 'admin_users.js']],
              widths=[3.0, 3.4, 7.4, 3.0], center_cols=(0, 1, 3), caption='表4-10 页面说明')
    add_figure(doc, SHOT / '01_login.png', '图4-6 登录页', 14.0)
    add_figure(doc, SHOT / '03_detect.png', '图4-7 检测页', 14.0)
    add_figure(doc, SHOT / '04_result.png', '图4-8 检测结果页', 14.0)
    add_figure(doc, SHOT / '05_history.png', '图4-9 历史记录页', 14.0)
    add_figure(doc, SHOT / '06_stats.png', '图4-10 数据统计页', 14.0)
    body(doc, '检测页支持拖拽和点选，多张图会按顺序逐张上传、逐张检测，进度条显示'
              '“第 i / N 张”。全部完成后跳到第一张的结果页，其余的已经存进历史记录。'
              '这样做的好处是不用等所有图都传完才看到结果，也不会一次发太多请求把'
              '后台堵住。')
    body(doc, '结果页的图片是后台画好框的静态图，右边按置信度从高到低列缺陷，'
              '每条显示类别、英文名、置信度、中心坐标和宽高，下面有“下载结果图”'
              '和“导出 CSV”两个按钮。没有缺陷时显示绿色的“未发现缺陷”，'
              '并提示可以降低阈值再试。')
    body(doc, '历史页的筛选条件会拼到查询参数里，翻页时保持筛选；删除前弹'
              'confirm 确认，删掉后当前页没有数据会自动退回上一页。统计页的 4 个'
              '卡片有数字滚动效果，柱状图、饼图和趋势图都跟着时间筛选联动，'
              '窗口大小变化时自动 resize。')
    code_block(doc, '''
async function api(path, options = {}) {
  const opts = Object.assign({ credentials: 'same-origin' }, options);
  opts.headers = Object.assign({}, options.headers || {});
  if (opts.body && !(opts.body instanceof FormData)) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(opts.body);
  }
  const res = await fetch(path, opts);
  const payload = await res.json();
  if (res.status === 401) {                 // 登录过期，回登录页
    location.href = '/login?next=' + encodeURIComponent(location.pathname);
    throw new Error('请先登录');
  }
  if (!res.ok || payload.code !== 200) throw new Error(payload.message);
  return payload.data;
}
''', caption='代码4-6 前端请求封装（static/js/common.js）')
    body(doc, '前端所有插入到页面的文本都过一遍 escapeHtml，防止记录里的文件名带'
              '尖括号把页面结构破坏；日期、数字也做了格式化，避免出现 undefined。'
              '这些细节不影响主流程，但演示时看起来会舒服很多。')

    h2(doc, '4.7 一次完整检测的流程')
    body(doc, '把上面几个模块串起来，一次完整检测是这样的：')
    body(doc, '1）用户在检测页选择图片，浏览器用 URL.createObjectURL 显示缩略图；')
    body(doc, '2）点“开始检测”，前端用 FormData 把图片和阈值 POST 到 /api/detect；')
    body(doc, '3）后台先校验格式和大小，把图片统一转成 JPEG 存到 static/uploads；')
    body(doc, '4）从 t_config 里读阈值（用户没传的话用默认值），调用 DefectDetector；')
    body(doc, '5）检测器加载 best.pt（第一次）或复用已加载的模型，推理得到框；')
    body(doc, '6）把框坐标归一化、画到图上，结果图存到 static/results；')
    body(doc, '7）把记录和缺陷写进 t_record、t_defect，返回记录号和结果图地址；')
    body(doc, '8）前端跳到 /result/<id>，页面从数据库读记录，显示结果图和缺陷列表。')
    body(doc, '整条链路里，原图、结果图和数据库记录是一一对应的：记录里存的是相对'
              '路径，删除记录时一起删文件，不会出现“数据库删了、图片还在”的情况。')

    h2(doc, '4.8 异常处理与安全')
    body(doc, '这一节把开发时考虑到的异常和安全问题列一下。系统是课程设计，'
              '不追求企业级安全，但常见的坑要避开。')
    add_table(doc, ['风险 / 异常', '处理方式'],
              [['SQL 注入', '所有 SQL 都用 ? 占位符传参，不拼字符串'],
               ['XSS', '前端插入文本前 escapeHtml；模板默认转义'],
               ['越权查看记录', '查询时带 user_id，非管理员只能看自己的；别人的记录返回 404'],
               ['越权修改参数', 'PUT /api/settings 加 api_admin_required'],
               ['路径穿越', 'image_path 必须以 uploads/ 开头且真实存在；删除文件时校验在 static 目录内'],
               ['恶意文件上传', '扩展名白名单 + PIL 真实解码 + 20MB 上限 + 尺寸检查'],
               ['密码泄露', 'PBKDF2 加盐哈希，不存明文；比较用 compare_digest'],
               ['token 被脚本读取', 'token 放 HttpOnly Cookie，JS 读不到；12 小时过期'],
               ['模型缺失 / 推理异常', '返回 503 / 500，写 failed 记录，页面给提示，进程不崩'],
               ['超大图片', '超过 3000 像素先缩小，减少内存和推理时间']],
              widths=[5.2, 9.6], caption='表4-11 异常与安全处理')
    body(doc, '还有几个已知的不足：没有做 CSRF token（依赖 SameSite=Lax 和同源策略）；'
              '登录没有失败次数限制；SQLite 在多人同时写的时候会锁库；Flask 自带的'
              '开发服务器不适合正式部署。这些问题在课程演示的规模下不会暴露，'
              '如果以后要上线，需要换成 gunicorn/waitress、加 CSRF、换 PostgreSQL 或'
              'MySQL。')

    h2(doc, '4.9 用户资料与用户管理')
    body(doc, '注册用户可以在“个人资料”页修改昵称、上传头像，查看自己的检测次数和'
              '最近检测时间。昵称限制 2–16 位中文、字母、数字、下划线或空格；头像限制'
              ' JPG/PNG/BMP/WEBP、不超过 2MB，服务端会居中裁成 200×200 的 JPEG，'
              '并删除旧头像文件。用户名不允许修改，避免登录凭证和历史记录对不上。')
    add_figure(doc, SHOT / '10_profile.png', '图4-11 个人资料页', 14.0)
    body(doc, '管理员在侧边栏多一个“用户管理”入口，对应 /admin/users。页面调用'
              ' GET /api/users，返回所有用户的用户名、昵称、角色、注册时间、检测次数、'
              '缺陷数和最近检测时间；普通用户访问这个页面会返回 403。管理员点某个用户的'
              '“查看记录”，会跳到 /history?user_id=xxx，历史页只显示该用户的记录；'
              '接口层也支持 GET /api/records?user_id=xxx，但只有管理员能用这个参数，'
              '普通用户传了也会被忽略，仍然只看自己的记录。')
    add_figure(doc, SHOT / '11_admin_users.png', '图4-12 用户管理页', 14.0)
    body(doc, '头像和昵称都只影响展示，不参与检测；检测记录仍然按 user_id 归属，'
              '管理员看全部、普通用户看自己。这样既满足“管理员能看到其他人信息”，'
              '又不会让普通用户越权看到别人的记录。')

    h2(doc, '4.10 与概要设计的差异')
    body(doc, '实现过程中对概要设计做了几处小调整，都是为了让系统更完整或更安全，'
              '功能和接口的整体结构没有变。')
    add_table(doc, ['项目', '概要设计', '详细设计 / 实现', '原因'],
              [['登录凭证', '返回 token，前端存起来放请求头', '签名 token 写 HttpOnly Cookie，同时兼容 X-Token', '降低 XSS 窃取风险，也方便脚本调试'],
               ['记录表字段', '7 个字段', '增加 cost_ms', '统计页需要平均耗时'],
               ['额外接口', '无', '增加注册、/api/me、/api/logout、/api/health、资料/头像、用户列表、CSV 导出', '页面需要、健康检查、结果页导出'],
               ['参数设置', '独立设置接口', '接口保留，界面上放在检测页（仅管理员）', '原有页面结构不变，参数放在检测页'],
               ['置信度默认值', '0.25', '0.25，可在页面调整并保存', '和概要设计一致']],
              widths=[3.2, 5.4, 5.4, 4.6], font_size=9.8, caption='表4-12 与概要设计的差异')

    # ------------------------------------------------------------ 5 测试
    h1(doc, '5 测试设计')
    h2(doc, '5.1 测试环境与方法')
    body(doc, '测试分三层：单元/接口测试用 Python 的 unittest 和 Flask 自带的 test_client，'
              '不启动服务器，直接在进程里发请求；数据集测试检查图片和标签的一致性；'
              '模型测试加载真实的 best.pt 跑测试图。界面和完整流程用 Edge 浏览器手动测，'
              '并用 Playwright 截图留证。')
    body(doc, '接口测试用了一个 FakeDetector 代替真实模型：它固定返回两个缺陷，'
              '这样测试不依赖 GPU 和 best.pt，跑得快，也能稳定复现。数据集和模型的'
              '测试则用真实文件，检查的是数据和模型本身。')
    body(doc, '测试环境：Windows 11、Python 3.11.16、Flask 3.1.3、SQLite 3、Edge 浏览器；'
              '接口测试用临时数据库，不会污染 data.db；上传的测试图片在用例结束后删除。')

    h2(doc, '5.2 测试用例设计')
    add_table(doc, ['编号', '模块', '测试内容', '输入 / 操作', '预期结果'],
              [['T01', '认证', '登录成功', 'admin / 123456', '200，返回 token 和 role'],
               ['T02', '认证', '密码错误', 'admin / bad', '400，提示用户名或密码错误'],
               ['T03', '认证', '未登录访问接口', 'GET /api/records', '401'],
               ['T04', '认证', '未登录访问页面', 'GET /detect', '302 跳转 /login'],
               ['T05', '上传', '上传合法图片', '200×160 PNG', '200，返回 uploads/ 路径'],
               ['T06', '上传', '上传非图片', 'a.txt', '400，格式不支持'],
               ['T07', '检测', '检测并写记录', 'PNG + conf=0.3', '总缺陷 2，结果图存在'],
               ['T08', '检测', '置信度越界', 'conf=1.5', '400'],
               ['T09', '记录', 'CSV 导出', 'GET /api/records/1/csv', '含“缺陷总数”和“划痕”'],
               ['T10', '权限', '普通用户看管理员记录', 'user 访问 admin 的记录', '404'],
               ['T11', '记录', '删除记录', 'DELETE /api/records/1', '数据库和文件都删除'],
               ['T12', '参数', '普通用户改参数', 'PUT /api/settings', '403'],
               ['T13', '参数', '管理员改参数 / 越界', '0.4 / 1.5', '200 / 400'],
               ['T14', '记录', '分页', '3 条记录，size=2', 'total=3，pages=2，每页 2 条'],
               ['T15', '数据集', '划分数量', 'train/val/test', '1000/160/160'],
               ['T16', '数据集', '标签合法性', '全部 txt', '5 列，类别 0–5，坐标 0–1'],
               ['T17', '数据集', '图片标签对应', '全部图片', '每张图都有同名 txt'],
               ['T18', '数据集', '类别覆盖', '每一类', '每个划分至少 20 个样本'],
               ['T19', '模型', '真实推理', 'test 图片，conf=0.25', '返回框和画框图，耗时 >0'],
               ['T20', '模型', '阈值生效', 'conf=0.05 vs 0.9', '低阈值的框不少于高阈值'],
               ['T21', '认证', '注册成功并登录', '新用户名 + abc12345', '200，role=user，能登录'],
               ['T22', '认证', '注册校验', '重复名/短密码/两次不一致', '都返回 400'],
               ['T23', '认证', '注册页面', 'GET /register', '200，页面正常显示'],
               ['T24', '资料', '修改昵称', 'PUT /api/profile', '200，昵称更新；非法昵称 400'],
               ['T25', '资料', '上传/恢复头像', '200×160 PNG，再 DELETE', '200，文件生成/删除'],
               ['T26', '权限', '用户列表', '管理员 / 普通用户 GET /api/users', '200 / 403']],
              widths=[1.4, 2.2, 4.6, 4.6, 4.4], center_cols=(0, 1), font_size=9.3,
              caption='表5-1 自动化测试用例')
    body(doc, '这 26 个用例覆盖了注册、登录、权限、上传、检测、记录、统计、参数、数据集和模型，'
              '基本对应需求分析里的功能点。界面上的交互（拖拽、翻页、图表、响应式）'
              '没法用 unittest 覆盖，放在 5.4 节手动测。')

    h2(doc, '5.3 自动化测试结果')
    body(doc, '三个测试文件分别运行，结果全部通过：')
    code_block(doc, TEST_OUT.strip(), caption='代码5-1 测试执行输出（节选）')
    body(doc, f'26 个用例全部通过，0 失败、0 错误。接口测试不到 1 秒，数据集测试'
              f'不到 1 秒，模型测试约十几秒（含加载模型和 ROI 预处理）。测试命令：')
    code_block(doc, '''
python -m unittest tests.test_api -v
python -m unittest tests.test_dataset -v
python -m unittest tests.test_detection -v
''', caption='代码5-2 运行测试')

    h2(doc, '5.4 系统功能测试')
    body(doc, '界面和完整流程用手动测试，浏览器用 Edge，分辨率 1440×950，'
              '另外用开发者工具切到手机宽度检查了响应式。测试结果见表 5-2。')
    body(doc, '除了手动点，我们还写了一个 Playwright 脚本 tests/ui_smoke.py，'
              '用真实浏览器自动走了一遍“登录 → 选 2 张图 → 检测 → 结果页 → 历史 → 统计 → 删除”'
              '的流程，并检查了阈值保存和恢复，运行结果正常。这样界面上的主流程每次改完'
              '都可以快速回归一遍。')
    add_table(doc, ['编号', '测试项', '操作步骤', '实际结果'],
              [['M01', '登录页展示', '打开 /login', '左右分栏正常，演示账号可见，密码可切换显示'],
               ['M02', '登录失败提示', '输入错误密码', '表单上方出现红色提示，不跳转'],
               ['M03', '拖拽上传', '把 3 张图拖进上传区', '缩略图出现，可单张移除，按钮变为可用'],
               ['M04', '单张检测', '选 1 张点开始检测', '进度条走完，跳到结果页，框和列表一致'],
               ['M05', '多张检测', '选 3 张点开始检测', '逐张显示进度，完成后跳第一张，历史里有 3 条'],
               ['M06', '结果下载', '点下载结果图', '浏览器保存 result_<id>.jpg'],
               ['M07', 'CSV 导出', '点导出 CSV', '下载文件带 BOM，中文正常，列齐全'],
               ['M08', '历史筛选', '选日期 + 有缺陷', '列表和总数同步变化，翻页保留条件'],
               ['M09', '删除记录', '点删除并确认', '记录消失，原图和结果图被删除'],
               ['M10', '统计图表', '打开 /stats', '4 个卡片、柱状图、饼图、趋势图都有数据'],
               ['M11', '管理员参数', '拖动阈值并保存', '提示保存成功，刷新后仍是新值'],
               ['M12', '响应式', '宽度调到 390px', '侧边栏收起，卡片单列，表格可横向滚动']],
              widths=[1.4, 3.2, 5.4, 7.2], center_cols=(0, 1), font_size=9.5,
              caption='表5-2 界面与流程测试')
    body(doc, '界面上还调整了几个细节：一是历史页没有记录时加了一个空状态提示，'
              '避免表格高度塌陷；二是统计页在数据全为 0 时饼图显示“暂无缺陷数据”，'
              '而不是一片空白；三是登录页在手机宽度下隐藏左侧插画、只留表单。')

    h2(doc, '5.5 性能测试')
    body(doc, '性能只测了单机演示最关心的几个数：模型加载、单张推理、接口端到端、'
              '页面响应。结果见表 5-3。')
    add_table(doc, ['测试项', '方法', '结果'],
              [['模型加载（首次）', '启动时 preload，计时到加载完成', f'{PERF.get("model_load_s", "—")} 秒'],
               ['单张推理（GPU）', 'ultralytics 统计，640 输入', f'{METRICS["speed_ms"].get("inference", 0):.1f} ms'],
               ['预处理 / 后处理', 'ultralytics 统计', f'{METRICS["speed_ms"].get("preprocess", 0):.1f} / {METRICS["speed_ms"].get("postprocess", 0):.1f} ms'],
               ['检测接口端到端', '上传 + 推理 + 画框 + 写库，取 10 次平均', f'{PERF.get("api_ms", AVG_COST):.0f} ms'],
               ['页面响应', 'GET /detect、/history、/stats 各 5 次平均', f'{PERF.get("page_ms", "—")} ms'],
               ['连续检测 10 张', '检测页多选 10 张', f'{PERF.get("batch10_s", "—")} 秒'],
               ['数据库查询', '当前记录量下分页查询', f'{PERF.get("query_ms", "—")} ms']],
              widths=[4.6, 7.4, 3.4], center_cols=(2,), caption='表5-3 性能测试结果')
    body(doc, f'本机 GPU 上单张推理约 {METRICS["speed_ms"].get("inference", 0):.1f} ms，'
              f'加上上传、画框、写库，接口一次约 {PERF.get("api_ms", AVG_COST):.0f} ms，'
              f'连续检测 10 张也在几秒内完成，用于课程演示完全够用。如果没有显卡，'
              f'推理会慢一些，但仍然可用，只是第一次加载模型的时间会变长。')

    h2(doc, '5.6 异常与兼容性测试')
    add_table(doc, ['场景', '操作', '结果'],
              [['模型缺失', '把 models/best.pt 改名后检测', '返回 503，页面提示，进程正常'],
               ['超大文件', '上传 25MB 图片', '413，提示超过 20MB'],
               ['错误格式', '上传 .gif / .txt', '400，提示格式不支持'],
               ['未登录直接访问', '清 Cookie 后打开 /history', '跳转登录页，登录后回到原页面'],
               ['越权访问', 'user 访问 admin 的记录', '404，不暴露记录存在'],
               ['记录已删除', '打开已删除记录的 /result/<id>', '404 页面，有返回按钮'],
               ['浏览器兼容', 'Edge（Chromium 内核）', '布局和图表正常'],
               ['小屏适配', '390×844', '侧边栏可展开，单列布局，无横向溢出']],
              widths=[4.2, 6.8, 4.4], caption='表5-4 异常与兼容性测试')
    body(doc, '没有发现会导致系统崩溃的问题。唯一需要注意的是，模型文件缺失时虽然'
              '接口返回 503，但页面顶部的状态会显示“模型未加载”，演示前要先确认'
              'models/best.pt 存在。')

    h2(doc, '5.7 测试结论')
    body(doc, f'自动化测试 26/26 通过，手动功能测试 12 项全部通过，异常场景都能给出'
              f'明确的提示。模型在合成测试集上 mAP50={M["map50"]:.4f}，'
              f'单张推理 {METRICS["speed_ms"].get("inference", 0):.1f} ms，'
              f'满足课程设计“能演示、能解释、指标可查”的要求。')
    body(doc, '已知的不足：合成数据的域差异、没有真实照片验证、CSRF 和登录限流没做、'
              'SQLite 并发能力有限。这些不影响课程演示，但要在报告和答辩里说清楚，'
              '不能把合成测试集的指标当成真实产线指标。')

    # ------------------------------------------------------------ 6 部署
    h1(doc, '6 系统部署与运行')
    h2(doc, '6.1 环境准备')
    body(doc, '需要 Python 3.10 以上，建议直接用本机的 conda 环境 diffusion-course，'
              '里面已经有 CUDA 版 PyTorch。如果换电脑，先装依赖：')
    code_block(doc, '''
pip install -r requirements.txt
''', caption='代码6-1 安装依赖')
    body(doc, 'requirements.txt 里的主要包是 ultralytics、torch、torchvision、flask、'
              'opencv-python、numpy、pillow、pandas、PyYAML。装完可以用 '
              'python -c "import torch; print(torch.cuda.is_available())" 检查显卡是否可用。')
    h2(doc, '6.2 启动与账号')
    body(doc, '在 week11-14 目录下运行：')
    code_block(doc, '''
python run.py                 # 默认 http://127.0.0.1:5000
python run.py --port 5001     # 端口被占用时换一个
python run.py --no-warmup     # 不预加载模型，启动更快
''', caption='代码6-2 启动命令')
    body(doc, '也可以双击“启动系统.bat”，它会自动切换到项目目录并调用 conda 环境里的'
              'Python。启动后浏览器打开 http://127.0.0.1:5000，用 admin / 123456 或 '
              'user / 123456 登录。admin 能看所有记录、改参数；user 只能看自己的记录。')
    h2(doc, '6.3 目录与数据备份')
    body(doc, '系统运行需要的文件有：data.db（数据库）、models/best.pt（模型）、'
              'static/uploads（原图）、static/results（结果图）。换电脑时把这四项'
              '一起拷走，代码和依赖重新装一遍就能继续用。备份也很简单，停掉程序，'
              '把 data.db 复制一份即可；图片目录如果很大，可以只备份数据库，'
              '图片按需保留。')
    h2(doc, '6.4 常见问题')
    add_table(doc, ['问题', '原因', '处理'],
              [['检测返回 503', 'models/best.pt 不存在', '先运行 train/train.py，或把训练好的模型放进去'],
               ['第一张图很慢', '模型第一次加载 + 预热', '等几秒；启动时加 --warmup 可提前加载'],
               ['端口被占用', '5000 被其他程序占用', 'python run.py --port 5001'],
               ['上传失败', '格式不支持或超过 20MB', '转成 JPG/PNG，压缩到 20MB 以内'],
               ['提示“这是结果图”', '把带检测框的结果图又上传了一次', '上传原始照片；系统会拦截，避免框被当成新缺陷'],
               ['登录后又跳回登录页', 'Cookie 被浏览器拦截或 token 过期', '检查浏览器 Cookie 设置，重新登录'],
               ['统计页没有数据', '当前账号没有检测记录', '先检测几张，或换 admin 账号看全部']],
              widths=[4.4, 5.2, 5.8], caption='表6-1 常见问题')
    h2(doc, '6.5 演示流程')
    body(doc, '答辩演示按下面的顺序走，大约 3 分钟：')
    body(doc, '1）打开登录页，介绍两种角色，用 admin 登录；')
    body(doc, '2）进入检测页，拖入一张测试图，调整阈值，点开始检测；')
    body(doc, '3）结果页展示框、类别、置信度，下载结果图、导出 CSV；')
    body(doc, '4）回到检测页，一次选 3 张图，演示批量检测；')
    body(doc, '5）打开历史记录，按日期筛选、翻页、删除一条；')
    body(doc, '6）打开统计页，展示 4 个卡片和三个图表；')
    body(doc, '7）最后用 user 登录，说明普通用户只能看自己的记录。')

    # ------------------------------------------------------------ 7 低对比度改进
    h1(doc, '7 低对比度小目标改进')
    body(doc, '上面的第 2–3 章和 5 章写的是第一版模型（v1）。把系统拿到真实碎屏照片上'
              '试用时，效果很差：阈值 0.25 时一张 720×552 的图检出 26 个框，几乎全是水花'
              '和反光；把阈值抬到 0.9，框数直接变成 0，真正的裂纹网一个都没框住。这一章'
              '记录我们针对这个问题做的第二次迭代，以及目前还解决不了的地方。')

    h2(doc, '7.1 问题现象')
    body(doc, '问题可以概括成“漏检”和“误检”同时存在：')
    bullet(doc, '漏检：真实碎屏图上的蜘蛛网裂纹，模型只在高阈值下勉强给出 1–2 个很低的'
                '分数（0.3 左右），主裂纹区域没有框住；')
    bullet(doc, '误检：水面反光、背景散景、屏幕上的水珠被大量识别成“亮点”和“污渍”，'
                '一张图 26 个框里 20 多个是这类背景；')
    bullet(doc, '阈值救不了：降低阈值误检更多，抬高阈值漏检更多，说明模型没有学到'
                '“低对比度细线/小点”的特征，只是在套合成数据里的高对比度亮斑。')
    body(doc, '需要说明的是，这跟 CPU 训练没有关系。CPU 和 GPU 只是计算速度不同，'
              '同样的数据、参数和轮数，模型学到的内容是一样的；CPU 训练真正的影响是'
              '慢，容易让人为了省时间把输入尺寸、轮数、数据量都调小，间接拉低效果。'
              '这一版的根因是训练数据和真实缺陷的分布不一致。')

    h2(doc, '7.2 原因分析')
    body(doc, '把失败样本和训练数据摆在一起看，原因有四个：')
    body(doc, '（1）对比度和形态不一致。合成缺陷是亮白线、亮圆点，背景很暗；真实裂纹'
              '是灰色细线，屏幕本身也是灰的，局部对比度只有十几个灰度级。合成裂纹是'
              '3–6 条稀疏分支，真实碎屏是从撞击点发散的密集蜘蛛网，两者形状差别很大。')
    body(doc, '（2）没有“难负样本”。原数据里的背景只有桌面纹理，模型没见过水珠、'
              '散景光斑、玻璃反光这些和目标非常像的干扰物，于是在真实图上把它们当成了'
              '亮点。')
    body(doc, '（3）目标太小。缺陷只有几个像素，640 输入再一缩放，细线只剩 1 个像素，'
              '卷积网络很难把它和噪声分开。')
    body(doc, '（4）类别规则不一致。真实水珠有亮心、暗边和阴影，尺寸 20–40 像素；'
              '而“亮点/暗点”在定义上是坏点，只有几个像素。模型没有尺寸先验，就会把'
              '大水珠当成大亮点。')

    h2(doc, '7.3 改进方案')
    body(doc, '针对上面的原因，我们做了四件事。')
    body(doc, '第一，重做困难版数据（datasets_hard）。裂纹改成从撞击点发散的 10–16 条'
              '主分支，加 3 层同心连接线和子裂纹，形成蜘蛛网；划痕、亮点、暗点、污渍、'
              '崩缺的尺寸都缩小到 2–10 像素，颜色贴近背景；每张图随机加 20–50 个水珠、'
              '反光带和散景光斑，这些干扰物故意不标注，作为难负样本；另外留 15% 的图'
              '完全没有缺陷，只保留水珠和反光。共生成 600 张训练、100 张验证、100 张测试。')
    body(doc, '第二，混合训练。只用困难数据会把原来合成测试集的效果拉下来（v2 在原'
              '测试集只有 0.542），所以把原数据 1000 张和困难数据 600 张合在一起，'
              '以困难数据训出的模型为初始化，再训 30 轮；增强上把 Mosaic 降到 0.4、'
              '缩放降到 0.35，避免把本来就只有几像素的缺陷再缩小。')
    body(doc, '第三，推理时先找屏幕区域再检测（ROI）。用 Canny 边缘和轮廓找手机外接'
              '矩形，裁掉背景再送进模型，背景里的水花和散景不参与推理，缺陷相对变大；'
              '找不到手机时自动退回整图。')
    body(doc, '第四，加尺寸规则。亮点/暗点在定义上是“坏点”，尺寸很小；如果检出的框'
              '最长边超过图片的 2.5%，就认为是水珠或反光，直接丢掉。这条规则只作用于'
              '亮点和暗点，不影响裂纹、划痕、污渍。检测页也加了“屏幕区域聚焦”开关，'
              '用户可以按需关掉。')

    h2(doc, '7.4 对比结果')
    body(doc, '三个版本在“原测试集”“困难测试集”和那张真实碎屏图上的表现见表 7-1。'
              '原测试集是第 2 章的数据，困难测试集是这一章新生成的数据；真实图只有一张，'
              '只能作为案例分析，不能当统计指标。')
    add_table(doc, ['模型版本', '原测试集 mAP50', '困难测试集 mAP50', '真实图框数', '真实图裂纹'],
              [['v1（第一版）', f'{ABL["v1"]["v1_map50"]:.4f}', f'{ABL["v1"]["hard_map50"]:.4f}',
                ABL['v1']['real_boxes'], '2 个低分框，未框住主裂纹'],
               ['v2（只用困难数据）', f'{ABL["v2"]["v1_map50"]:.4f}', f'{ABL["v2"]["hard_map50"]:.4f}',
                ABL['v2']['real_boxes'], '3 个框，覆盖主裂纹'],
               ['mix（混合训练，最终部署）', f'{ABL["mix"]["v1_map50"]:.4f}',
                f'{ABL["mix"]["hard_map50"]:.4f}', ABL['mix']['real_boxes'],
                '1 个框，覆盖右侧裂纹区']],
              widths=[4.6, 3.0, 3.2, 2.4, 4.4], center_cols=(1, 2, 3), font_size=9.8,
              caption='表7-1 三个版本的效果对比')
    note(doc, '说明：真实图框数是默认流程在同一张 720×552 碎屏图上的检出数量；v1 是'
              '26 个（未做 ROI 和尺寸过滤），mix 是开启 ROI 和尺寸过滤后的 3 个。'
              '数量少不代表精度一定高，但背景误检确实明显减少，而且主裂纹被框住了。')
    add_figure(doc, FIG / 'real_compare.png', '图7-1 真实碎屏图改进前后的检测结果对比', 16.0)
    body(doc, '从图 7-1 可以看到，改进前满屏都是绿色/黄色的小框，真正裂纹反而没有框；'
              '改进后只剩 3 个框，其中红色框覆盖了右侧裂纹最密集的区域，另外两个是'
              '摄像头和反光造成的污渍误检。这个结果离“完美”还有距离，但已经从'
              '“完全不可用”变成了“能定位主要缺陷、误检可控”。')

    h2(doc, '7.5 CPU 训练参数')
    body(doc, '如果只能用 CPU 训练，建议用下面的配置。它不是“CPU 专用模型”，只是把'
              '批大小、线程数和 AMP 调成适合 CPU 的值，训练质量和 GPU 一致。')
    code_block(doc, '''
python train/train_hard.py --profile cpu ^
    --data datasets_mix/data_mix.yaml ^
    --epochs 30 --imgsz 640 --batch 8
''', caption='代码7-1 CPU 混合训练命令（Windows 用 ^ 续行，Linux 用 \\）')
    body(doc, 'profile=cpu 会自动设置 workers=0（Windows 上 CPU 多进程 DataLoader 容易'
              '卡住）、关闭 AMP；1600 张图、30 轮在本机 GPU 上约 10 分钟，CPU 上预计'
              '1.5–3 小时，具体看机器。时间不够可以只训 15–20 轮，或把数据裁到 800 张；'
              '不要为了快把 imgsz 降到 416，那会把本来就很小的缺陷直接抹掉。')

    h2(doc, '7.6 还没解决的问题')
    body(doc, '这一版只是把最明显的域差异补上了一部分，离真实产线还有距离：')
    bullet(doc, '只用了一张真实图做验证，不能代表所有手机、光照和缺陷类型；真实场景的'
                'mAP 仍然没有统计意义；')
    bullet(doc, '裂纹只框住了右半区域，左半没有框全；如果要框住整片裂纹，需要真实'
                '裂纹标注做微调，或者把多个裂纹框合并成一个区域；')
    bullet(doc, '摄像头孔和反光仍会被误判成污渍（图 7-1 里的两个黄框）；尺寸过滤只能'
                '处理亮点/暗点，处理不了这类圆形结构；')
    bullet(doc, '亮点/暗点的 2.5% 尺寸阈值是经验值，真实坏点如果特别大就会被漏掉。')
    body(doc, '下一步最有效的办法不是继续调参，而是补真实标注数据：收集 100–200 张'
              '真实屏幕图，其中 30% 是正常屏幕、反光、水渍等负样本；按第 2.3 节的规范'
              '用 LabelImg 标注；用当前 mix 模型初始化，学习率 0.001，训练 20–30 轮。'
              '数据到位后，这一节的结论需要重新用真实测试集评估，不能沿用合成指标的'
              '说法。')

    # ------------------------------------------------------------ 8 总结
    h1(doc, '8 总结')
    body(doc, '第 11–14 周我们完成了从数据到系统的整条链路：写了程序化数据生成器，'
              f'造了 1320 张带标注的屏幕图片；用 YOLOv8n 迁移学习训了 60 轮，'
              f'在测试集上 mAP50 达到 {M["map50"]:.4f}；用 Flask + SQLite 做了'
              f'登录、上传、检测、结果、历史、统计 8 个页面和 18 个接口；'
              f'写了 26 个自动化测试，全部通过；最后把《详细设计说明书》写完。')
    body(doc, '和最初的想法比，最大的变化是数据集。原计划是“网上找图 + 自己拍 + '
              'LabelImg 标注”，真正做的时候发现根本凑不齐六类缺陷，标注也很费时间，'
              '所以改成了程序化合成。这个选择让我们在两周内就把数据、训练、评估跑通了，'
              '代价是合成数据和真实照片有差距。我们把这一点明确写进了文档，'
              '并在 2.7 节留了真实数据的接入方案，没有把合成测试集的指标当成真实精度。')
    body(doc, '另一个体会是“先把流程跑通，再抠细节”。一开始我们想在界面上做很多'
              '效果，后来发现模型跑不通、接口对不上，界面再好看也没用。于是先把'
              '上传 → 检测 → 存库 → 展示这条主链路做通，再补统计、筛选、导出、'
              '响应式这些功能。这样即使时间不够，核心功能也是完整的。')
    body(doc, '第 15–18 周的计划是：补拍 200–300 张真实照片，按同样的规范标注，'
              '用现在这个模型做初始化再微调，重新评估真实场景的 mAP；根据实测结果'
              '调整阈值和类别；修一修已知的小问题（CSRF、登录限流、SQLite 并发）；'
              '然后写测试报告、用户手册和课程设计报告，准备答辩 PPT。')
    body(doc, '总的来说，这个阶段把概要设计里的图变成了能跑的代码，也让我们真正'
              '体会到了目标检测项目里“数据比模型更难搞”。系统还有很多不足，'
              '但作为一个课程设计，它已经能完整演示“上传一张屏幕照片，自动找出'
              '缺陷并留下记录”这件事了。')

    doc.save(OUT)
    print('OK:', OUT)


if __name__ == '__main__':
    build()









