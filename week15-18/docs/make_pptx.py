# -*- coding: utf-8 -*-
"""生成《答辩PPT.pptx》（课程设计第 15-18 周验收交付物）。

用法：python week15-18/docs/make_pptx.py
"""
from __future__ import annotations

import json
import csv
import sys
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = BASE.parent
W1114 = ROOT / 'week11-14'
SHOT = W1114 / 'screenshots'
FIG11 = W1114 / 'docs' / 'figures'
FIG15 = HERE / 'figures'
OUT = BASE / '答辩PPT.pptx'


def _best_epoch():
    path = W1114 / 'train' / 'runs' / 'phonescreen_yolov8n' / 'results.csv'
    rows = list(csv.DictReader(path.open(encoding='utf-8')))
    key = 'metrics/mAP50(B)'
    best = max(rows, key=lambda r: float(r[key]))
    return int(best['epoch']), float(best[key])


BEST_EPOCH, BEST_MAP50 = _best_epoch()

INK = RGBColor(0x10, 0x1A, 0x2E)
INK2 = RGBColor(0x2B, 0x3A, 0x55)
MUTED = RGBColor(0x6F, 0x7F, 0x99)
BLUE = RGBColor(0x2F, 0x6B, 0xFF)
BLUE2 = RGBColor(0x1B, 0x4E, 0xD8)
LIGHT = RGBColor(0xEE, 0xF4, 0xFF)
BG = RGBColor(0xF6, 0xF8, 0xFC)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BORDER = RGBColor(0xE4, 0xEB, 0xF6)
GREEN = RGBColor(0x1F, 0x9D, 0x55)
ORANGE = RGBColor(0xF5, 0xA6, 0x23)
RED = RGBColor(0xE5, 0x48, 0x4D)
DARK = RGBColor(0x0B, 0x14, 0x25)
SOFT = RGBColor(0x8F, 0xA6, 0xC9)

FONT = 'Microsoft YaHei'


def _font(run, size, color, bold=False):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn('a:ea'))
    if ea is None:
        ea = rPr.makeelement(qn('a:ea'), {})
        rPr.append(ea)
    ea.set('typeface', FONT)


def _set_alpha(color, alpha):
    c = RGBColor(*color)
    return c


def tx(slide, l, t, w, h, text, size=14, color=INK, bold=False,
       align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=1.15, margins=(0, 0, 0, 0)):
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left, tf.margin_right, tf.margin_top, tf.margin_bottom = [Inches(m) for m in margins]
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = spacing
    r = p.add_run()
    r.text = text
    _font(r, size, color, bold)
    return tb


def tx_lines(slide, l, t, w, h, lines, spacing=1.12, margins=(0, 0, 0, 0)):
    """lines: [(text, size, color, bold, space_before)]"""
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left, tf.margin_right, tf.margin_top, tf.margin_bottom = [Inches(m) for m in margins]
    first = True
    for text, size, color, bold, before in lines:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.line_spacing = spacing
        p.space_before = Pt(before)
        r = p.add_run()
        r.text = text
        _font(r, size, color, bold)
    return tb


def rect(slide, l, t, w, h, fill=WHITE, line=None, radius=None, shape=MSO_SHAPE.RECTANGLE):
    if radius is not None:
        shape = MSO_SHAPE.ROUNDED_RECTANGLE
    shp = slide.shapes.add_shape(shape, Inches(l), Inches(t), Inches(w), Inches(h))
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid()
        shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(1)
    shp.shadow.inherit = False
    if radius is not None:
        shp.adjustments[0] = radius
    return shp


def card(slide, l, t, w, h, fill=WHITE, line=BORDER, radius=0.07):
    return rect(slide, l, t, w, h, fill=fill, line=line, radius=radius)


def picture_fit(slide, path, l, t, w, h, border=True):
    """在 (l,t,w,h) 盒子里按比例放图并居中。"""
    path = Path(path)
    if not path.exists():
        return None
    iw, ih = Image.open(path).size
    scale = min(w / iw, h / ih)
    pw, ph = iw * scale, ih * scale
    px, py = l + (w - pw) / 2, t + (h - ph) / 2
    if border:
        rect(slide, px - 0.03, py - 0.03, pw + 0.06, ph + 0.06,
             fill=WHITE, line=BORDER, radius=0.02)
    return slide.shapes.add_picture(str(path), Inches(px), Inches(py),
                                    Inches(pw), Inches(ph))


def bg(slide, color=WHITE):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def add_slide(prs, color=WHITE):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg(s, color)
    return s


def header(slide, kicker, title, num=None):
    tx(slide, 0.7, 0.38, 7.0, 0.3, kicker, 10, MUTED, True)
    tx(slide, 0.7, 0.68, 10.8, 0.65, title, 27, INK, True)
    rect(slide, 0.7, 1.38, 0.55, 0.06, fill=BLUE)
    if num:
        tx(slide, 11.6, 0.32, 1.1, 0.9, num, 46, RGBColor(0xE8, 0xEF, 0xFC), True,
           align=PP_ALIGN.RIGHT)


def footer(slide, idx, total):
    rect(slide, 0.7, 7.02, 11.93, 0.01, fill=BORDER)
    tx(slide, 0.7, 7.1, 8.0, 0.25, '基于 YOLOv8 的手机屏幕外观缺陷智能检测系统', 8.5, MUTED)
    tx(slide, 10.6, 7.1, 2.0, 0.25, f'{idx:02d} / {total:02d}', 8.5, MUTED, align=PP_ALIGN.RIGHT)


def pill(slide, l, t, w, h, text, color=BLUE, fill=LIGHT, size=10.5):
    shp = card(slide, l, t, w, h, fill=fill, line=None, radius=0.5)
    tf = shp.text_frame
    tf.word_wrap = False
    tf.margin_left = tf.margin_right = Inches(0.05)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = text
    _font(r, size, color, True)
    return shp


def metric(slide, l, t, w, value, label, color=BLUE, sub=None, vsize=34):
    tx(slide, l, t, w, 0.8, value, vsize, color, True)
    tx(slide, l, t + 0.76, w, 0.3, label, 10.5, MUTED)
    if sub:
        tx(slide, l, t + 1.06, w, 0.3, sub, 9.5, MUTED)


def build():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    total = 22

    # ------------------------------------------------------------ 1 封面
    s = add_slide(prs, DARK)
    # 背景装饰
    rect(s, 8.55, 0, 4.783, 7.5, fill=RGBColor(0x0F, 0x1D, 0x35))
    rect(s, 0.0, 0.0, 0.09, 7.5, fill=BLUE)
    tx(s, 0.9, 0.72, 7.0, 0.3, '北京邮电大学 · 人工智能学院 · 课程设计', 10.5, SOFT, True)
    tx_lines(s, 0.9, 1.35, 7.3, 2.6, [
        ('基于 YOLOv8 的', 38, WHITE, True, 0),
        ('手机屏幕外观缺陷', 38, WHITE, True, 2),
        ('智能检测系统', 38, RGBColor(0x7F, 0xA6, 0xFF), True, 2),
    ], spacing=1.12)
    rect(s, 0.9, 3.92, 0.9, 0.06, fill=BLUE)
    tx(s, 0.9, 4.15, 6.8, 0.5, '从程序化数据合成，到可解释的质检原型', 15, RGBColor(0xC9, 0xD5, 0xE8))
    tx(s, 0.9, 4.75, 6.8, 0.35, '王周毅　林城于　·　2025219106　·　2026 年 12 月', 11.5, SOFT)
    for i, (v, label) in enumerate([('6 类', '缺陷'), ('8', '页面'), ('18', '接口'), ('26/26', '测试')]):
        x = 0.9 + i * 1.45
        tx(s, x, 5.55, 1.3, 0.4, v, 17, WHITE, True)
        tx(s, x, 5.98, 1.3, 0.25, label, 9, SOFT)
    # 右侧检测结果图
    card(s, 8.95, 1.02, 3.95, 5.46, fill=RGBColor(0x14, 0x24, 0x40),
         line=RGBColor(0x2B, 0x42, 0x66), radius=0.03)
    picture_fit(s, SHOT / '04_result.png', 9.1, 1.2, 3.65, 4.75, border=False)
    tx(s, 9.1, 6.02, 3.65, 0.3, '真实检测结果 · YOLOv8n', 9, SOFT, align=PP_ALIGN.CENTER)
    notes(s, '各位老师好，我们做的是基于 YOLOv8 的手机屏幕外观缺陷智能检测系统。'
             '一句话概括：上传一张屏幕照片，系统自动框出六类缺陷、给出类别和置信度，'
             '并把记录存下来，支持历史查询和统计。右边是系统的真实结果页。')

    # ------------------------------------------------------------ 2 一页看懂
    s = add_slide(prs)
    header(s, 'EXECUTIVE SUMMARY', '一页看懂这个项目')
    kpis = [('6 类', '外观缺陷', '划痕 / 裂纹 / 亮点 / 暗点 / 污渍 / 崩缺', BLUE),
            ('26/26', '自动化测试', '另有 12 项界面流程测试全部通过', GREEN),
            ('0.9875', '原测试集 mAP50', '困难测试集 0.8883', ORANGE),
            ('3 个', '真实图误检框', '改进前是 26 个', RED)]
    for i, (v, label, sub, color) in enumerate(kpis):
        x = 0.7 + i * 3.03
        card(s, x, 1.75, 2.78, 1.72, fill=BG, line=BORDER)
        tx(s, x + 0.25, 1.90, 2.3, 0.75, v, 32, color, True)
        tx(s, x + 0.25, 2.68, 2.3, 0.28, label, 11, INK, True)
        tx(s, x + 0.25, 2.97, 2.35, 0.45, sub, 8.8, MUTED)
    # 三列
    cols = [('问题', '人工目检慢、标准不一致、结果不可追溯', '真实场景还有反光、水珠、微小裂纹'),
            ('做法', 'YOLOv8n + Flask 全链路；合成数据先跑通，再用困难数据补真实场景', '数据、模型、系统、测试四块都留了脚本'),
            ('结果', '能演示、指标可查、缺陷可追溯', '边界写得清楚：合成指标 ≠ 真实产线精度')]
    for i, (t1, t2, t3) in enumerate(cols):
        x = 0.7 + i * 4.0
        tx(s, x, 3.85, 0.9, 0.3, f'0{i+1}', 10, BLUE, True)
        tx(s, x, 4.12, 3.7, 0.4, t1, 18, INK, True)
        tx(s, x, 4.55, 3.65, 0.9, t2, 11, INK2, spacing=1.35)
        tx(s, x, 5.45, 3.65, 0.6, t3, 9.5, MUTED, spacing=1.25)
    rect(s, 0.7, 6.28, 11.9, 0.5, fill=BG, line=None)
    tx(s, 0.92, 6.36, 11.5, 0.3, '结论：主链路能演示、指标可查、缺陷可追溯；真实产线精度仍需补数据验证。',
       10, INK2, True)
    footer(s, 2, total)
    notes(s, '先用一页把结论讲完：六类缺陷、26 个测试全过、原测试集 mAP50 0.9875、'
             '真实图误检从 26 个降到 3 个。下面按“问题—做法—结果—反思”四部分展开。')

    # ------------------------------------------------------------ 3 目录
    s = add_slide(prs)
    header(s, 'AGENDA', '今天讲四件事')
    items = [('01', '问题与目标', '为什么做、做到什么程度', '人工质检的三个痛点；系统边界'),
             ('02', '设计与实现', '架构、数据、模型、系统', '三层架构；合成数据；YOLOv8n；Flask 闭环'),
             ('03', '测试与结果', '功能、性能、模型、真实案例', '26/26；88 ms；26 → 3 个框'),
             ('04', '反思与改进', '局限、下一步', '域差异；真实数据；工程化')]
    for i, (num, title, sub, detail) in enumerate(items):
        y = 1.7 + i * 1.25
        card(s, 0.7, y, 11.9, 1.05, fill=BG if i % 2 == 0 else WHITE, line=BORDER)
        tx(s, 0.95, y + 0.27, 0.8, 0.45, num, 20, BLUE, True)
        tx(s, 1.75, y + 0.18, 3.0, 0.35, title, 16, INK, True)
        tx(s, 1.75, y + 0.58, 3.2, 0.3, sub, 9.5, MUTED)
        tx(s, 5.1, y + 0.36, 7.2, 0.35, detail, 10.5, INK2)
    footer(s, 3, total)
    notes(s, '汇报分四块：先讲问题和目标，再讲设计与实现，然后看测试结果，'
             '最后讲局限和改进。重点会放在数据、真实场景的翻车和改进过程上。')

    # ------------------------------------------------------------ 4 背景
    s = add_slide(prs)
    header(s, '01 · 问题', '人工目检的三个现实问题', '01')
    items = [('慢', '一块屏幕要看亮屏、息屏、多个角度', '单块几十秒到几分钟，批量时更明显'),
             ('不一致', '不同人、不同光线、不同疲劳度', '同一块屏幕，两个人可能给出不同结论'),
             ('不可追溯', '只记一个 OK / NG', '出了争议，拿不出当时的图和缺陷位置')]
    for i, (t1, t2, t3) in enumerate(items):
        x = 0.7 + i * 4.02
        card(s, x, 1.75, 3.78, 2.55, fill=BG, line=BORDER)
        tx(s, x + 0.3, 1.95, 0.8, 0.7, f'0{i+1}', 30, RGBColor(0xC9, 0xD9, 0xFF), True)
        tx(s, x + 0.3, 2.55, 3.1, 0.45, t1, 20, INK, True)
        tx(s, x + 0.3, 3.05, 3.15, 0.55, t2, 11, INK2, spacing=1.3)
        tx(s, x + 0.3, 3.68, 3.15, 0.45, t3, 9.2, MUTED, spacing=1.25)
    tx(s, 0.7, 4.75, 11.9, 0.5, '我们想把“看图、判断、记录”合成一件事：', 14, INK, True)
    tx(s, 0.7, 5.22, 11.9, 0.5, '上传一张照片 → 自动框出缺陷 → 结果入库 → 历史可查、统计可看',
       14, BLUE, True)
    card(s, 0.7, 5.95, 11.9, 0.72, fill=LIGHT, line=None)
    tx(s, 0.95, 6.12, 11.4, 0.4, '定位：质检工位的辅助检测原型，不替代人工做最终判定。', 11, BLUE2, True)
    footer(s, 4, total)
    notes(s, '先讲为什么做。人工目检不是不行，而是慢、标准不稳定、结果留不下来。'
             '所以我们想做的是把看图、判断、记录合成一条链路，定位是辅助，不是替代人。')

    # ------------------------------------------------------------ 5 目标与边界
    s = add_slide(prs)
    header(s, '01 · 目标', '做什么，不做什么', '01')
    card(s, 0.7, 1.7, 5.85, 4.95, fill=RGBColor(0xF3, 0xF9, 0xF5), line=RGBColor(0xD6, 0xEC, 0xDD))
    tx(s, 1.0, 1.92, 4.8, 0.4, '本期要做', 17, GREEN, True)
    doit = ['登录 / 注册 / 角色权限', '上传、拖拽、批量检测',
            '六类缺陷检测 + 画框 + 置信度', '结果图下载、CSV 导出',
            '历史筛选、分页、删除', '数据统计：卡片、柱状、饼图、趋势',
            '个人资料、头像、管理员用户列表']
    for i, item in enumerate(doit):
        y = 2.45 + i * 0.52
        tx(s, 1.0, y, 0.3, 0.3, '✓', 12, GREEN, True)
        tx(s, 1.35, y - 0.02, 4.9, 0.4, item, 11, INK2)
    card(s, 6.75, 1.7, 5.85, 4.95, fill=RGBColor(0xFB, 0xF4, 0xF4), line=RGBColor(0xF0, 0xDA, 0xDA))
    tx(s, 7.05, 1.92, 4.8, 0.4, '本期不做', 17, RED, True)
    dont = ['多人协同、细粒度权限', '在线训练、模型管理平台',
            '移动端 App、产线设备对接', '高并发、工业级部署',
            '真实产线精度认证']
    for i, item in enumerate(dont):
        y = 2.45 + i * 0.55
        tx(s, 7.05, y, 0.3, 0.3, '×', 12, RED, True)
        tx(s, 7.4, y - 0.02, 4.8, 0.4, item, 11, INK2)
    tx(s, 7.05, 5.4, 5.2, 0.85, '先把主链路做通，再补锦上添花的功能；\n'
        '边界写进文档，不把原型说成产品。', 10, MUTED, spacing=1.35)
    footer(s, 5, total)
    notes(s, '目标很明确：主链路完整、能演示、记录可查。不做多人协同、在线训练和产线对接。'
             '我们宁可把边界写清楚，也不把原型包装成工业系统。')

    # ------------------------------------------------------------ 6 系统总览
    s = add_slide(prs)
    header(s, '02 · 系统', '一套能跑起来的完整闭环', '02')
    picture_fit(s, SHOT / '04_result.png', 0.7, 1.7, 5.9, 4.95)
    tx(s, 0.7, 6.68, 5.9, 0.25, '检测结果页：框、指标卡、缺陷明细、下载与导出', 8.5, MUTED)
    tx(s, 6.95, 1.72, 5.5, 0.35, '8 个页面', 13, BLUE, True)
    tx(s, 6.95, 2.05, 5.4, 0.7, '登录 · 注册 · 检测 · 结果\n历史 · 统计 · 资料 · 用户管理', 10.5, INK2, spacing=1.35)
    tx(s, 6.95, 2.95, 5.5, 0.35, '18 个接口 + 4 张表', 13, BLUE, True)
    tx(s, 6.95, 3.28, 5.4, 0.7, '认证 / 上传 / 检测 / 记录 / 统计 / 参数\nSQLite：用户、记录、缺陷、参数', 10.5, INK2, spacing=1.35)
    tx(s, 6.95, 4.18, 5.5, 0.35, '两种角色', 13, BLUE, True)
    tx(s, 6.95, 4.51, 5.4, 0.7, '普通用户只看自己的记录\n管理员看全部、管用户、改默认阈值', 10.5, INK2, spacing=1.35)
    tx(s, 6.95, 5.42, 5.5, 0.35, '一条记录留下什么', 13, BLUE, True)
    tx_lines(s, 6.95, 5.78, 5.4, 1.0, [
        ('原图 + 结果图 + 检测时间 + 耗时 + 阈值', 10, INK2, False, 0),
        ('每处缺陷的类别、置信度、位置', 10, INK2, False, 3),
    ], spacing=1.3)
    footer(s, 6, total)
    notes(s, '系统整体是 8 个页面、18 个接口、4 张表、两种角色。右边这张结果页能代表整个闭环：'
             '上面是检测出来的框，下面是缺陷明细，右上角能下载结果图和 CSV。')

    # ------------------------------------------------------------ 7 架构
    s = add_slide(prs)
    header(s, '02 · 架构', '三层结构，模型与业务解耦', '02')
    # 展示层
    rect(s, 0.7, 1.62, 7.55, 1.15, fill=RGBColor(0xEE, 0xF4, 0xFF), line=RGBColor(0xCF, 0xDF, 0xFF), radius=0.05)
    tx(s, 0.95, 1.72, 2.0, 0.3, '展示层', 11, BLUE, True)
    tx(s, 0.95, 2.02, 7.1, 0.55, '浏览器 · HTML / CSS / JS · Bootstrap / ECharts', 12, INK, True)
    tx(s, 0.95, 2.38, 7.0, 0.28, '登录 · 检测 · 结果 · 历史 · 统计 · 资料 · 管理', 8.8, MUTED)
    # 业务层
    rect(s, 0.7, 3.02, 7.55, 1.55, fill=RGBColor(0xF2, 0xF8, 0xF4), line=RGBColor(0xD3, 0xE9, 0xDB), radius=0.05)
    tx(s, 0.95, 3.12, 2.0, 0.3, '业务层', 11, GREEN, True)
    tx(s, 0.95, 3.42, 7.1, 0.35, 'Flask：认证 · 校验 · 调度 · 记录 · 统计', 12, INK, True)
    tx(s, 0.95, 3.82, 7.0, 0.55, '统一返回 {code, message, data}；PBKDF2 + 签名 token；\n'
        '权限装饰器；图片与结果图文件管理', 8.8, MUTED, spacing=1.3)
    # 数据层
    rect(s, 0.7, 4.72, 7.55, 1.05, fill=RGBColor(0xF7, 0xF9, 0xFC), line=BORDER, radius=0.05)
    tx(s, 0.95, 4.82, 2.0, 0.3, '数据层', 11, INK2, True)
    tx(s, 0.95, 5.12, 7.1, 0.35, 'SQLite（4 表） · 原图/结果图 · best.pt', 12, INK, True)
    tx(s, 0.95, 5.45, 7.0, 0.25, 'data.db · static/uploads · static/results · models/', 8.8, MUTED)
    # 箭头
    for y in (2.86, 4.66):
        tx(s, 4.1, y - 0.08, 0.6, 0.25, '↓', 13, BLUE, True, align=PP_ALIGN.CENTER)
    # 右侧检测模块
    card(s, 8.6, 3.02, 4.0, 2.75, fill=RGBColor(0xFF, 0xF8, 0xEC), line=RGBColor(0xF6, 0xDF, 0xB8))
    tx(s, 8.85, 3.16, 3.5, 0.3, '独立检测模块', 11, ORANGE, True)
    tx(s, 8.85, 3.48, 3.45, 0.35, 'Ultralytics YOLOv8n', 13, INK, True)
    steps = ['加载一次，所有请求复用', 'ROI 找屏幕，裁掉背景', '640 推理 + NMS',
             '尺寸过滤 + 映射回原图', 'Pillow 画框、保存结果图']
    for i, step in enumerate(steps):
        y = 3.92 + i * 0.34
        tx(s, 8.85, y, 0.25, 0.25, '·', 11, ORANGE, True)
        tx(s, 9.05, y - 0.02, 3.3, 0.28, step, 9.2, INK2)
    tx(s, 8.85, 5.78, 3.5, 0.3, '换模型不影响页面', 9, MUTED)
    tx(s, 0.7, 6.05, 7.5, 0.35, '模型只负责“图片 → 框”，业务只负责“谁、什么时候、结果怎么存”',
       10.5, INK2)
    footer(s, 7, total)
    notes(s, '架构分三层，检测模块单独拎出来。好处是换模型不影响页面，页面也不关心'
             '模型怎么跑。检测模块启动时加载一次，后面所有请求复用。')

    # ------------------------------------------------------------ 8 技术栈
    s = add_slide(prs)
    header(s, '02 · 技术', '为什么选这套技术栈', '02')
    techs = [('Flask 3', '后端', '轻量、路由直观；test_client 方便写接口测试', BLUE),
             ('YOLOv8n', '检测', '约 6 MB，GPU 几毫秒；CPU 也能跑', GREEN),
             ('PyTorch 2', '训练', '生态成熟；本机 CUDA 12.6 直接加速', ORANGE),
             ('SQLite 3', '数据', '单文件、零配置，拷走目录就能换电脑', RGBColor(0x72, 0x2E, 0xD1)),
             ('Bootstrap 5', '前端', '本地引入、离线可用；表格表单开箱即用', RGBColor(0x13, 0xC2, 0xC2)),
             ('ECharts 5', '图表', '柱状/饼图/趋势，配置简单，中文友好', RED)]
    for i, (name, cat, why, color) in enumerate(techs):
        col, row = i % 3, i // 3
        x = 0.7 + col * 4.02
        y = 1.72 + row * 2.05
        card(s, x, y, 3.78, 1.82, fill=WHITE, line=BORDER)
        rect(s, x, y, 0.08, 1.82, fill=color)
        tx(s, x + 0.28, y + 0.22, 0.9, 0.25, cat, 8.5, color, True)
        tx(s, x + 0.28, y + 0.5, 3.2, 0.4, name, 17, INK, True)
        tx(s, x + 0.28, y + 1.02, 3.25, 0.65, why, 9.5, MUTED, spacing=1.3)
    tx(s, 0.7, 5.95, 11.9, 0.35, '原则：能用现成库就不自己造；能离线就不依赖网络；能讲清楚就不追新。',
       10.5, INK2)
    footer(s, 8, total)
    notes(s, '技术选型没有追新，都是成熟、能离线、能讲清楚的方案。'
             'YOLOv8n 是最小的版本，看重的是能带走、能演示。')

    # ------------------------------------------------------------ 9 数据集
    s = add_slide(prs)
    header(s, '02 · 数据', '数据从哪来：程序化合成', '02')
    steps = [('01', '画背景', '木纹 / 磨砂 / 布料\n渐变 + 暗角 + 噪声'),
             ('02', '放手机', '随机宽度、位置\n±7° 旋转、圆角边框'),
             ('03', '画屏幕', '亮屏壁纸 / 息屏玻璃\n保留反光'),
             ('04', '画缺陷', '六类规则\n0–4 个，查 IoU'),
             ('05', '合成退化', '1280→640、模糊\n亮度扰动、JPEG 噪声')]
    for i, (num, title, desc) in enumerate(steps):
        x = 0.7 + i * 2.42
        card(s, x, 1.7, 2.18, 1.55, fill=BG, line=BORDER)
        tx(s, x + 0.18, 1.8, 0.45, 0.3, num, 9, BLUE, True)
        tx(s, x + 0.18, 2.08, 1.8, 0.3, title, 12, INK, True)
        tx(s, x + 0.18, 2.42, 1.85, 0.65, desc, 8.2, MUTED, spacing=1.3)
        if i < 4:
            tx(s, x + 2.2, 2.18, 0.22, 0.45, '›', 18, RGBColor(0xB9, 0xC7, 0xDE), True)
    tx(s, 0.7, 3.45, 5.7, 0.3, '为什么合成', 11, BLUE, True)
    tx_lines(s, 0.7, 3.78, 5.65, 2.0, [
        ('真实缺陷图凑不齐六类，很多带水印；', 9.8, INK2, False, 0),
        ('自己拍不好制造划痕/裂纹，标注也慢；', 9.8, INK2, False, 4),
        ('合成：两天出 1320 张，类别均衡、标签准确、可复现；', 9.8, INK2, False, 4),
        ('代价：和真实照片有域差异，后面专门讲。', 9.8, RED, True, 4),
    ], spacing=1.3)
    for i, (v, label, color) in enumerate([('1320', '原数据', BLUE), ('800', '困难数据', ORANGE),
                                           ('2120', '混合数据', GREEN)]):
        x = 0.7 + i * 1.95
        tx(s, x, 5.62, 1.7, 0.45, v, 22, color, True)
        tx(s, x, 6.08, 1.7, 0.25, label, 8.5, MUTED)
    picture_fit(s, FIG11 / 'dataset_samples.png', 6.55, 3.35, 6.1, 3.1)
    tx(s, 6.55, 6.5, 6.1, 0.25, '合成样例：不同桌面、亮/息屏、不同尺度缺陷', 8.2, MUTED)
    footer(s, 9, total)
    notes(s, '数据是这个项目最花时间的部分。真实图凑不齐，我们写程序合成：'
             '画背景、放手机、画屏幕、画缺陷、加退化，最后算标签。'
             '两天做了 1320 张，标签天然准确。代价是域差异，后面会讲怎么补。')

    # ------------------------------------------------------------ 10 六类缺陷
    s = add_slide(prs)
    header(s, '02 · 数据', '六类外观缺陷', '02')
    classes = [('划痕', 'scratch', '细长亮线，可弯曲', RGBColor(0xFF, 0x7A, 0x45)),
               ('裂纹', 'crack', '分叉亮线，蜘蛛网', RGBColor(0xFF, 0x4D, 0x4F)),
               ('亮点', 'bright_spot', '发白/发绿小圆点', RGBColor(0x52, 0xC4, 0x1A)),
               ('暗点', 'dark_spot', '暗色小圆斑', RGBColor(0x72, 0x2E, 0xD1)),
               ('污渍', 'stain', '半透明模糊斑块', RGBColor(0xFA, 0xAD, 0x14)),
               ('边缘崩缺', 'edge_chip', '边缘锯齿缺口', RGBColor(0x13, 0xC2, 0xC2))]
    for i, (cn, en, desc, color) in enumerate(classes):
        col, row = i % 3, i // 3
        x = 0.7 + col * 4.02
        y = 1.72 + row * 2.15
        card(s, x, y, 3.78, 1.95, fill=WHITE, line=BORDER)
        rect(s, x + 0.28, y + 0.28, 0.12, 0.55, fill=color)
        tx(s, x + 0.55, y + 0.25, 2.7, 0.4, cn, 18, INK, True)
        tx(s, x + 0.55, y + 0.68, 2.7, 0.25, en, 8.5, MUTED)
        tx(s, x + 0.28, y + 1.12, 3.2, 0.35, desc, 10, INK2)
        rect(s, x + 0.28, y + 1.55, 3.2, 0.04, fill=color)
    tx(s, 0.7, 6.1, 11.9, 0.4, '标注规范：YOLO 格式（class cx cy w h，归一化）；每类颜色固定，结果图和统计图共用。',
       9.5, MUTED)
    footer(s, 10, total)
    notes(s, '六类缺陷，每类一个固定颜色，结果图和统计图都用同一套颜色。'
             '标注用 YOLO 格式，归一化坐标。裂缝和划痕的区别是裂纹有分叉、常从一点发散。')

    # ------------------------------------------------------------ 11 训练
    s = add_slide(prs)
    header(s, '02 · 模型', '训练：迁移学习 + 两轮迭代', '02')
    params = [('模型', 'YOLOv8n'), ('输入', '640 × 640'), ('轮数', '60 → 30'),
              ('batch', '24 → 16'), ('优化器', 'AdamW'), ('学习率', '0.005 → 0.001')]
    for i, (a, b) in enumerate(params):
        y = 1.78 + i * 0.62
        tx(s, 0.7, y, 1.1, 0.3, a, 9.5, MUTED)
        tx(s, 1.85, y - 0.02, 1.9, 0.32, b, 11, INK, True)
    tx(s, 0.7, 5.62, 3.2, 0.8, '第二轮把 Mosaic 降到 0.4、缩放降到 0.35，\n'
        '避免把几像素的缺陷再缩小。', 8.5, MUTED, spacing=1.3)
    picture_fit(s, FIG11 / 'train_results.png', 4.15, 1.7, 8.5, 4.35)
    tx(s, 4.15, 6.18, 8.5, 0.3, '训练损失与验证指标：前 10 轮上升最快，之后趋稳，没有明显过拟合',
       8.5, MUTED)
    card(s, 4.15, 6.55, 8.45, 0.38, fill=LIGHT, line=None)
    tx(s, 4.3, 6.61, 8.2, 0.28, f'验证集最佳：第 {BEST_EPOCH} 轮 mAP50 {BEST_MAP50:.4f}；测试集 0.9932',
       9.5, BLUE2, True)
    footer(s, 11, total)
    notes(s, '训练用迁移学习，加载 COCO 预训练的 YOLOv8n，换成 6 类再微调。'
             '第一版 60 轮，后来做混合训练 30 轮。增强上特意把 Mosaic 和缩放调小，'
             '因为缺陷本来就小，再缩就没了。')

    # ------------------------------------------------------------ 12 指标
    s = add_slide(prs)
    header(s, '03 · 结果', '指标：分类别都过 0.89', '03')
    metric(s, 0.7, 1.72, 2.3, '0.9875', 'mix · 原测试集 mAP50', BLUE, 'v1 基线为 0.9932')
    metric(s, 3.15, 1.72, 2.3, '0.9593', 'mix · 混合测试集 mAP50', GREEN, 'mAP50-95 0.7590')
    metric(s, 5.6, 1.72, 2.3, '0.8883', 'mix · 困难测试集 mAP50', ORANGE, '从 0.259 提升')
    # 图表
    order = ['scratch', 'crack', 'bright_spot', 'dark_spot', 'stain', 'edge_chip']
    cn = {'scratch': '划痕', 'crack': '裂纹', 'bright_spot': '亮点',
          'dark_spot': '暗点', 'stain': '污渍', 'edge_chip': '边缘崩缺'}
    pc = {c['class_name']: c for c in json.loads(
        (W1114 / 'models' / 'metrics_mix.json').read_text(encoding='utf-8'))['per_class']}
    data = CategoryChartData()
    data.categories = [cn[k] for k in order]
    data.add_series('mAP50', [round(pc[k]['map50'], 4) for k in order])
    chart = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(8.1), Inches(1.72),
                               Inches(4.55), Inches(4.0), data).chart
    chart.has_legend = False
    chart.font.name = FONT
    chart.font.size = Pt(9)
    chart.font.color.rgb = MUTED
    plot = chart.plots[0]
    plot.gap_width = 55
    plot.has_data_labels = True
    dl = plot.data_labels
    dl.number_format = '0.00'
    dl.number_format_is_linked = False
    dl.position = XL_LABEL_POSITION.OUTSIDE_END
    dl.font.size = Pt(9)
    dl.font.bold = True
    dl.font.color.rgb = INK
    ser = plot.series[0]
    ser.format.fill.solid()
    ser.format.fill.fore_color.rgb = BLUE
    va = chart.value_axis
    va.minimum_scale = 0.8
    va.maximum_scale = 1.02
    va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = BORDER
    va.tick_labels.font.size = Pt(8)
    va.tick_labels.font.color.rgb = MUTED
    ca = chart.category_axis
    ca.tick_labels.font.size = Pt(9)
    ca.tick_labels.font.color.rgb = INK2
    ca.format.line.color.rgb = BORDER
    tx(s, 8.1, 5.82, 4.55, 0.3, '混合模型在混合测试集上的分类别 mAP50', 8.5, MUTED,
       align=PP_ALIGN.CENTER)
    card(s, 0.7, 3.32, 7.0, 0.62, fill=BG, line=None)
    tx(s, 0.92, 3.46, 6.6, 0.3, '注意：三个数来自三个不同测试集，不能直接横向比较。', 9.5, BLUE2, True)
    tx_lines(s, 0.7, 4.3, 7.0, 1.9, [
        ('六类 mAP50 都 ≥ 0.89；裂纹、亮点、崩缺 ≥ 0.97。', 10.5, INK2, False, 0),
        ('划痕最低（0.899）：细长目标对框的贴合最敏感。', 10.5, INK2, False, 5),
        ('主要错误是漏检/误检，不是类别串认。', 10.5, INK2, False, 5),
    ], spacing=1.3)
    footer(s, 12, total)
    notes(s, '指标分三组口径，不能混着比：v1 在原测试集 0.9932，混合模型在混合测试集 0.9593，'
             '在困难测试集 0.8883。分类别看，六类都过 0.89，划痕最低，因为细长目标框最难贴。')

    # ------------------------------------------------------------ 13 真实场景
    s = add_slide(prs)
    header(s, '03 · 真实场景', '拿到真实碎屏图，第一版翻车了', '03')
    picture_fit(s, FIG11 / 'real_compare.png', 0.55, 1.65, 8.2, 4.7)
    tx(s, 0.55, 5.92, 8.2, 0.3, '左：v1（26 个框）　右：mix + ROI + 尺寸过滤（3 个框）', 8.5, MUTED)
    card(s, 8.95, 1.72, 3.65, 1.55, fill=RGBColor(0xFB, 0xF0, 0xF0), line=RGBColor(0xF0, 0xD5, 0xD5))
    tx(s, 9.2, 1.88, 3.2, 0.3, '翻车现场', 10, RED, True)
    tx_lines(s, 9.2, 2.22, 3.2, 0.9, [
        ('阈值 0.25：26 个框，全是水花/反光', 8.5, INK2, False, 0),
        ('阈值 0.9：0 个框，裂纹全漏', 8.5, INK2, False, 4),
    ], spacing=1.25)
    card(s, 8.95, 3.45, 3.65, 1.55, fill=RGBColor(0xF2, 0xF8, 0xF4), line=RGBColor(0xD5, 0xE9, 0xDC))
    tx(s, 9.2, 3.61, 3.2, 0.3, '问题不在阈值', 10, GREEN, True)
    tx(s, 9.2, 3.95, 3.2, 0.9, '模型没学过低对比度细线、\n也没见过水珠/反光这类负样本。', 8.5, INK2, spacing=1.25)
    tx(s, 8.95, 5.25, 3.65, 0.9, '真实图只有这一张，\n只能做案例分析，不能算 mAP。', 9, MUTED, spacing=1.3)
    footer(s, 13, total)
    notes(s, '这是整个项目最有价值的一页。第一版拿到真实碎屏图，阈值 0.25 出 26 个框，'
             '几乎全是水花和反光；阈值抬到 0.9 又变 0。问题不是阈值，是训练数据没见过'
             '低对比度细线，也没见过水珠这种难负样本。')

    # ------------------------------------------------------------ 14 改进
    s = add_slide(prs)
    header(s, '03 · 改进', '针对四个原因，做了三件事', '03')
    cards3 = [('01', '重做困难数据', '蜘蛛网裂纹、2–10 像素缺陷\n20–50 个水珠/反光负样本\n15% 纯负样本',
               '让模型见过真实的样子'),
              ('02', '混合训练', '原数据 1000 + 困难 600\n从困难模型初始化，30 轮\n弱 Mosaic、弱缩放',
               '兼顾简单样本和困难样本'),
              ('03', '推理加两道闸', 'ROI：先找屏幕，裁掉背景\n尺寸过滤：亮点/暗点 > 2.5% 丢掉\n检测页可开关',
               '不改模型也能压误检')]
    for i, (num, title, body, why) in enumerate(cards3):
        x = 0.7 + i * 4.02
        card(s, x, 1.7, 3.78, 3.45, fill=BG, line=BORDER)
        tx(s, x + 0.28, 1.88, 0.7, 0.5, num, 22, RGBColor(0xC9, 0xD9, 0xFF), True)
        tx(s, x + 0.28, 2.4, 3.2, 0.4, title, 15, INK, True)
        tx(s, x + 0.28, 2.92, 3.25, 1.2, body, 9.2, INK2, spacing=1.45)
        rect(s, x + 0.28, 4.25, 3.2, 0.03, fill=BORDER)
        tx(s, x + 0.28, 4.4, 3.2, 0.55, why, 8.8, BLUE2, True)
    # 底部对比条
    card(s, 0.7, 5.42, 11.9, 1.15, fill=BG, line=BORDER)
    tx(s, 1.0, 5.58, 1.6, 0.3, '困难测试集', 9.5, MUTED, True)
    tx(s, 2.4, 5.5, 1.4, 0.45, '0.259', 20, RED, True)
    tx(s, 3.5, 5.62, 0.5, 0.3, '→', 14, MUTED, True)
    tx(s, 4.0, 5.5, 1.4, 0.45, '0.8883', 20, GREEN, True)
    tx(s, 6.1, 5.58, 1.6, 0.3, '真实图框数', 9.5, MUTED, True)
    tx(s, 7.5, 5.5, 1.4, 0.45, '26', 20, RED, True)
    tx(s, 8.3, 5.62, 0.5, 0.3, '→', 14, MUTED, True)
    tx(s, 8.8, 5.5, 1.4, 0.45, '3', 20, GREEN, True)
    tx(s, 10.5, 5.58, 1.9, 0.55, '代价：原测试集\n0.9932 → 0.9875', 8.2, MUTED, spacing=1.2)
    footer(s, 14, total)
    notes(s, '针对四个原因做了三件事：重做困难数据、混合训练、推理时加 ROI 和尺寸过滤。'
             '结果是困难测试集从 0.259 到 0.8883，真实图从 26 个框到 3 个。'
             '代价是原测试集从 0.9932 掉到 0.9875，这个权衡我们认。')

    # ------------------------------------------------------------ 15 检测页
    s = add_slide(prs)
    header(s, '03 · 系统', '检测页：三步完成一次检测', '03')
    picture_fit(s, SHOT / '03_detect.png', 0.7, 1.65, 7.4, 4.95)
    tx(s, 0.7, 6.66, 7.4, 0.25, '检测页：上传区、预览、阈值、ROI、最近检测', 8.5, MUTED)
    steps = [('1', '选图', '点击或拖拽，可多选\nJPG/PNG/BMP/WEBP ≤ 20 MB'),
             ('2', '调参', '置信度 0.05–0.90\nROI 开关，管理员可存默认'),
             ('3', '检测', '逐张调用接口\n完成后跳结果页')]
    for i, (num, title, desc) in enumerate(steps):
        y = 1.75 + i * 1.55
        card(s, 8.5, y, 4.1, 1.32, fill=BG, line=BORDER)
        shp = rect(s, 8.7, y + 0.35, 0.55, 0.55, fill=BLUE, radius=0.5)
        tf = shp.text_frame
        tf.margin_left = tf.margin_right = 0
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = num
        _font(r, 12, WHITE, True)
        tx(s, 9.42, y + 0.18, 2.9, 0.3, title, 12, INK, True)
        tx(s, 9.42, y + 0.52, 2.95, 0.65, desc, 8.5, MUTED, spacing=1.3)
    tx(s, 8.5, 6.35, 4.1, 0.35, '单张约 90 ms（GPU）', 9, BLUE2, True)
    footer(s, 15, total)
    notes(s, '检测页操作只有三步：选图、调参、点检测。可以拖拽、多选，'
             '阈值和 ROI 都能调。单张在 GPU 上大约 90 毫秒。')

    # ------------------------------------------------------------ 16 历史统计
    s = add_slide(prs)
    header(s, '03 · 系统', '记录与统计：让结果可追溯', '03')
    picture_fit(s, SHOT / '05_history.png', 0.55, 1.65, 6.0, 4.55)
    tx(s, 0.55, 6.27, 6.0, 0.25, '历史记录：日期 / 缺陷 / 用户筛选，分页、详情、删除', 8, MUTED)
    picture_fit(s, SHOT / '06_stats.png', 6.75, 1.65, 6.0, 4.55)
    tx(s, 6.75, 6.27, 6.0, 0.25, '数据统计：4 个指标卡 + 柱状图 + 饼图 + 趋势', 8, MUTED)
    tx(s, 0.7, 6.62, 11.9, 0.3, '普通用户只看自己的；管理员看全部，并能按用户筛。删除记录时原图和结果图一起清理。',
       9, INK2)
    footer(s, 16, total)
    notes(s, '历史页按时间、有无缺陷、用户筛，支持分页和删除；统计页有四个卡片和三张图。'
             '所有记录都能追到原图、结果图和每个缺陷的位置。')

    # ------------------------------------------------------------ 17 工程难点
    s = add_slide(prs)
    header(s, '03 · 工程', '四个踩过的坑', '03')
    probs = [('结果图回流', '结果页下载的图再上传，框和文字被当成新缺陷',
              'dHash 比对最近 300 张结果图，再和原图比，确实画了框才拒绝'),
             ('中文 CSV 乱码', 'Excel 默认按本地编码解析 UTF-8',
              '文件开头加 BOM；下载文件名用英文'),
             ('越权与开放重定向', '普通用户想看别人记录；next 参数能跳外站',
              '接口层校验 user_id；safe_next 只允许站内单斜杠路径'),
             ('模型缺失的 500', 'best.pt 不在时抛异常，页面只显示服务器错误',
              '健康检查 + 503 + 明确提示；演示前先看引擎状态')]
    for i, (title, prob, fix) in enumerate(probs):
        col, row = i % 2, i // 2
        x = 0.7 + col * 6.0
        y = 1.7 + row * 2.45
        card(s, x, y, 5.85, 2.2, fill=WHITE, line=BORDER)
        tx(s, x + 0.28, y + 0.2, 0.5, 0.3, f'0{i+1}', 9, BLUE, True)
        tx(s, x + 0.65, y + 0.16, 4.9, 0.35, title, 14, INK, True)
        tx(s, x + 0.28, y + 0.68, 5.25, 0.55, prob, 9, MUTED, spacing=1.3)
        rect(s, x + 0.28, y + 1.32, 5.2, 0.02, fill=BORDER)
        tx(s, x + 0.28, y + 1.42, 5.25, 0.65, '解法：' + fix, 9, INK2, spacing=1.3)
    footer(s, 17, total)
    notes(s, '工程上踩过四个典型的坑：结果图回流、CSV 乱码、越权和开放重定向、模型缺失报 500。'
             '这些不是算法问题，但会直接影响演示和体验，修完都补了回归用例。')

    # ------------------------------------------------------------ 18 测试
    s = add_slide(prs)
    header(s, '03 · 测试', '测试：26/26，性能达标', '03')
    stats = [('26/26', '自动化用例', GREEN, '接口 18 + 数据集 6 + 模型 2'),
             ('12/12', '界面流程测试', BLUE, '登录、上传、结果、历史、统计、响应式'),
             ('88 ms', '检测接口平均', ORANGE, '最小 73.6 / 最大 178.4 ms'),
             ('7.04 s', '模型首次加载', RGBColor(0x72, 0x2E, 0xD1), '只发生一次，之后复用')]
    for i, (v, label, color, sub) in enumerate(stats):
        x = 0.7 + i * 3.03
        card(s, x, 1.7, 2.78, 1.5, fill=BG, line=BORDER)
        tx(s, x + 0.24, 1.85, 2.35, 0.55, v, 26, color, True)
        tx(s, x + 0.24, 2.43, 2.35, 0.28, label, 10, INK, True)
        tx(s, x + 0.24, 2.75, 2.4, 0.32, sub, 8, MUTED)
    # 左表
    tx(s, 0.7, 3.48, 6.0, 0.3, '测试覆盖', 11, BLUE, True)
    rows = [('认证 / 注册', '7 个用例'), ('上传 / 检测 / 参数', '4 个用例'),
            ('记录 / 导出 / 分页', '3 个用例'), ('资料 / 权限', '4 个用例'),
            ('数据集 / 模型', '8 个用例')]
    for i, (a, b) in enumerate(rows):
        y = 3.88 + i * 0.48
        rect(s, 0.7, y + 0.44, 5.8, 0.01, fill=BORDER)
        tx(s, 0.7, y, 4.2, 0.3, a, 9.5, INK2)
        tx(s, 5.0, y, 1.4, 0.3, b, 9.5, MUTED, align=PP_ALIGN.RIGHT)
    # 右表
    tx(s, 6.95, 3.48, 5.6, 0.3, '性能拆解', 11, BLUE, True)
    perf = [('单张推理', '3.95 ms'), ('接口端到端', '87.7 ms'),
            ('页面响应', '3.1 ms'), ('连续 10 张', '0.88 s'),
            ('数据库查询', '2.15 ms')]
    for i, (a, b) in enumerate(perf):
        y = 3.88 + i * 0.48
        rect(s, 6.95, y + 0.44, 5.6, 0.01, fill=BORDER)
        tx(s, 6.95, y, 4.0, 0.3, a, 9.5, INK2)
        tx(s, 10.9, y, 1.65, 0.3, b, 9.5, INK, True, align=PP_ALIGN.RIGHT)
    tx(s, 0.7, 6.48, 11.9, 0.35, '结论：瓶颈不在模型，在图片 IO 和画框；并发没做压测，是明确短板。',
       9.5, MUTED)
    footer(s, 18, total)
    notes(s, '测试 26 个自动化用例全过，12 项界面流程全过。性能上单张推理只有 4 毫秒，'
             '接口 88 毫秒，瓶颈在图片 IO 和画框，不在模型。并发没有压测，这是短板。')

    # ------------------------------------------------------------ 19 边界
    s = add_slide(prs)
    header(s, '04 · 反思', '必须说清楚的四个边界', '04')
    limits = [('01', '合成数据有域差异', '训练图是程序画的，真实照片的光照、噪声、材质不一样；mAP 只代表合成测试集。',
               RED),
              ('02', '真实图只有 1 张', '只能做案例分析，不能算真实 mAP，也不能代表所有手机和光照。',
               ORANGE),
              ('03', '裂纹可能框不全', '蜘蛛网分支多，模型可能只框住最密集的一块；相邻框没有合并。',
               BLUE),
              ('04', '工程化不足', '没有 CSRF、登录限流、并发优化；Flask 开发服务器 + SQLite 只适合单机演示。',
               RGBColor(0x72, 0x2E, 0xD1))]
    for i, (num, title, desc, color) in enumerate(limits):
        x = 0.7 + i * 3.03
        card(s, x, 1.75, 2.82, 3.45, fill=WHITE, line=BORDER)
        rect(s, x, 1.75, 2.82, 0.07, fill=color)
        tx(s, x + 0.24, 1.98, 0.6, 0.3, num, 9, color, True)
        tx(s, x + 0.24, 2.3, 2.35, 0.65, title, 13, INK, True)
        tx(s, x + 0.24, 3.05, 2.38, 1.9, desc, 8.8, MUTED, spacing=1.4)
    card(s, 0.7, 5.55, 11.9, 0.95, fill=RGBColor(0xFB, 0xF4, 0xF4), line=RGBColor(0xF0, 0xDA, 0xDA))
    tx(s, 0.95, 5.72, 11.4, 0.65, '不把“合成集 0.99”说成“真实产线精度”，也不把原型说成产品。'
        '这些边界已经写进详细设计、测试报告和本 PPT。', 11, INK2, spacing=1.3)
    footer(s, 19, total)
    notes(s, '这一页是主动讲边界。合成数据和真实照片有域差异，真实图只有一张，'
             '裂纹可能框不全，工程化也不足。我们不想把 0.99 说成真实产线精度，'
             '这是做研究和做产品都该有的诚实。')

    # ------------------------------------------------------------ 20 后续
    s = add_slide(prs)
    header(s, '04 · 下一步', '把“能演示”推到“能统计”', '04')
    roadmap = [('第一步', '补真实数据', '100–200 张真实屏幕图，30% 负样本；LabelImg 标注；用 mix 初始化微调 20–30 轮', GREEN),
               ('第二步', '重新评估', '独立真实测试集算 P/R/mAP；按结果调阈值和类别；替换所有“真实场景”结论', BLUE),
               ('第三步', '模型与后处理', '裂纹相邻框合并；亮点/暗点尺寸规则；困难样本回流', ORANGE),
               ('第四步', '工程化', 'CSRF、登录限流、SQLite WAL、waitress；用例接 GitHub Actions', RGBColor(0x72, 0x2E, 0xD1))]
    for i, (step, title, desc, color) in enumerate(roadmap):
        y = 1.72 + i * 1.18
        card(s, 0.7, y, 11.9, 1.02, fill=WHITE, line=BORDER)
        rect(s, 0.7, y, 0.08, 1.02, fill=color)
        tx(s, 1.0, y + 0.16, 1.0, 0.3, step, 8.8, color, True)
        tx(s, 1.95, y + 0.14, 2.2, 0.35, title, 13, INK, True)
        tx(s, 4.25, y + 0.24, 7.9, 0.6, desc, 9.5, INK2, spacing=1.2)
    tx(s, 0.7, 6.55, 11.9, 0.3, '最有效的改进不是调参，是补真实标注数据。', 10, RED, True)
    footer(s, 20, total)
    notes(s, '下一步四件事，第一步也是最有效的：补真实数据、重新评估。'
             '模型和后处理、工程化排在后面。我们的判断是，继续调参的收益已经不如补数据。')

    # ------------------------------------------------------------ 21 总结
    s = add_slide(prs, DARK)
    tx(s, 0.9, 0.72, 7.0, 0.3, 'SUMMARY', 10.5, SOFT, True)
    tx(s, 0.9, 1.15, 8.0, 0.7, '三句话总结', 32, WHITE, True)
    rect(s, 0.9, 2.0, 0.9, 0.06, fill=BLUE)
    lines = [('01', '把一条链路做通了', '登录 → 上传 → 检测 → 结果 → 历史 → 统计，能演示、能追溯。'),
             ('02', '把真实问题暴露出来了', '真实碎屏图上从 26 个框降到 3 个，也明确了域差异和样本不足。'),
             ('03', '把边界写清楚了', '合成指标不等于真实精度；不夸大、不回避，是这次最大的收获。')]
    for i, (num, title, desc) in enumerate(lines):
        y = 2.45 + i * 1.35
        tx(s, 0.9, y, 0.6, 0.35, num, 10, RGBColor(0x7F, 0xA6, 0xFF), True)
        tx(s, 1.5, y - 0.05, 6.5, 0.4, title, 18, WHITE, True)
        tx(s, 1.5, y + 0.42, 6.9, 0.55, desc, 10.5, RGBColor(0xC9, 0xD5, 0xE8), spacing=1.3)
    tx(s, 9.2, 2.55, 3.4, 0.3, '一句话', 9, SOFT, True)
    tx(s, 9.2, 2.92, 3.3, 1.3, '数据比模型\n更难搞。', 24, WHITE, True, spacing=1.2)
    tx(s, 9.2, 4.55, 3.3, 1.2, '下一步最该做的\n不是调参，是补\n真实标注数据。', 10, RGBColor(0xC9, 0xD5, 0xE8), spacing=1.35)
    tx(s, 0.9, 6.55, 7.5, 0.3, '王周毅　林城于　·　2025219106　·　2026.12', 9.5, SOFT)
    notes(s, '最后三句话：链路做通了，真实问题暴露出来了，边界写清楚了。'
             '最大的收获是理解了数据比模型更难搞。')

    # ------------------------------------------------------------ 22 谢谢
    s = add_slide(prs, DARK)
    rect(s, 0.0, 0.0, 0.09, 7.5, fill=BLUE)
    tx(s, 0.9, 1.75, 7.5, 0.4, 'THANKS FOR LISTENING', 10.5, SOFT, True)
    tx(s, 0.9, 2.2, 8.0, 1.0, '谢谢，请提问', 46, WHITE, True)
    rect(s, 0.9, 3.35, 0.9, 0.06, fill=BLUE)
    tx(s, 0.9, 3.65, 7.6, 0.4, '基于 YOLOv8 的手机屏幕外观缺陷智能检测系统', 13, RGBColor(0xC9, 0xD5, 0xE8))
    tx(s, 0.9, 4.2, 7.6, 0.35, '代码与文档：github.com/wzy1021/phone-screen-defect-yolov8', 9.5, SOFT)
    tx(s, 0.9, 4.58, 7.6, 0.35, '在线演示：wzy1021.github.io/phone-screen-defect-yolov8', 9.5, SOFT)
    tx(s, 0.9, 5.55, 7.6, 0.35, '王周毅　林城于　·　北京邮电大学 人工智能学院', 10, SOFT)
    # 右侧大数字
    tx(s, 9.4, 1.55, 3.2, 1.0, '26→3', 46, RGBColor(0x7F, 0xA6, 0xFF), True, align=PP_ALIGN.RIGHT)
    tx(s, 9.4, 2.55, 3.2, 0.3, '真实图误检框', 9, SOFT, align=PP_ALIGN.RIGHT)
    tx(s, 9.4, 3.3, 3.2, 1.0, '26/26', 40, WHITE, True, align=PP_ALIGN.RIGHT)
    tx(s, 9.4, 4.2, 3.2, 0.3, '自动化测试通过', 9, SOFT, align=PP_ALIGN.RIGHT)
    notes(s, '我的汇报到这里，谢谢各位老师，欢迎提问。')

    prs.core_properties.title = '基于YOLOv8的手机屏幕外观缺陷智能检测系统——答辩PPT'
    prs.core_properties.author = '王周毅、林城于'
    prs.core_properties.subject = '课程设计第 15-18 周验收答辩'
    prs.save(OUT)
    print('OK:', OUT, 'slides:', len(prs.slides))


if __name__ == '__main__':
    build()
