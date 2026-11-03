# -*- coding: utf-8 -*-
"""PIL 绘制《概要设计说明书》的全部配图（第 7-10 周交付物）。

包括：系统总体架构图、模块划分图、数据库 ER 图、检测流程示意图、
UI 原型图（登录/检测/结果/历史/统计）、进度甘特图。
输出到本目录 figures/ 下。
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(BASE_DIR, 'figures')
os.makedirs(FIG_DIR, exist_ok=True)

FONT_REG = 'C:/Windows/Fonts/msyh.ttc'
FONT_BOLD = 'C:/Windows/Fonts/msyhbd.ttc'

C_BLUE = '#2E75B6'
C_BLUE_F = '#DEEBF7'
C_GREEN = '#548235'
C_GREEN_F = '#E2EFDA'
C_ORANGE = '#ED7D31'
C_ORANGE_F = '#FBE5D6'
C_GRAY = '#595959'
C_GRAY_F = '#F2F2F2'
C_ITEM = '#F7F7F7'
C_BORDER = '#BFBFBF'
C_TEXT = '#262626'
C_WHITE = '#FFFFFF'


def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def wrap(draw, text, fnt, max_w):
    lines, cur = [], ''
    for ch in str(text):
        if ch == '\n':
            lines.append(cur)
            cur = ''
            continue
        if draw.textlength(cur + ch, font=fnt) <= max_w:
            cur += ch
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines or ['']


def center_text(draw, cx, cy, text, fnt, fill=C_TEXT, max_w=1e9):
    lines = wrap(draw, text, fnt, max_w)
    line_h = fnt.size + 8
    y = cy - (len(lines) - 1) * line_h / 2
    for ln in lines:
        w = draw.textlength(ln, font=fnt)
        draw.text((cx - w / 2, y), ln, font=fnt, fill=fill)
        y += line_h


def rbox(draw, box, fill=C_ITEM, outline=C_BORDER, width=2, radius=10):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def arrow(draw, p1, p2, color=C_BLUE, width=2, head=12):
    draw.line([p1, p2], fill=color, width=width)
    ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    for da in (150, -150):
        a = ang + math.radians(da)
        tip = (p2[0] + head * math.cos(a), p2[1] + head * math.sin(a))
        draw.line([p2, tip], fill=color, width=width)


def dashed_line(draw, p1, p2, color=C_GRAY, width=2, dash=14, gap=10):
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    length = math.hypot(dx, dy)
    if length == 0:
        return
    n = int(length // (dash + gap))
    ux, uy = dx / length, dy / length
    for i in range(n + 1):
        s = i * (dash + gap)
        x0, y0 = p1[0] + ux * s, p1[1] + uy * s
        x1, y1 = x0 + ux * dash, y0 + uy * dash
        draw.line([(x0, y0), (x1, y1)], fill=color, width=width)


def save_fig(img, name):
    path = os.path.join(FIG_DIR, name)
    img.save(path)
    return path


def new_canvas(w, h, bg=C_WHITE):
    img = Image.new('RGB', (w, h), bg)
    return img, ImageDraw.Draw(img)


# ============================================================ 图1 系统总体架构图
def draw_architecture():
    W, H = 1600, 1120
    img, d = new_canvas(W, H)
    center_text(d, 800, 48, '系统总体架构图', font(34, True), C_TEXT)
    center_text(d, 800, 90, '基于 B/S 架构的三层结构 + AI 检测推理模块', font(17), C_GRAY)

    # 展示层
    rbox(d, (120, 128, 1480, 316), C_BLUE_F, C_BLUE, 3)
    d.rounded_rectangle((120, 128, 1480, 176), radius=12, fill=C_BLUE)
    center_text(d, 800, 152, '展 示 层（浏览器 Web 前端）', font(23, True), C_WHITE)
    center_text(d, 800, 204, '技术栈：HTML + CSS + JavaScript · Bootstrap', font(15), C_GRAY)
    pages = ['登录页', '检测页', '结果页', '历史页', '统计页']
    x = 188
    for p in pages:
        rbox(d, (x, 236, x + 222, 300), C_WHITE, C_BLUE, 2)
        center_text(d, x + 111, 268, p, font(18, True), C_BLUE)
        x += 250
    arrow(d, (800, 318), (800, 390))
    center_text(d, 815, 356, 'HTTP 请求 / JSON 响应（图片上传、结果下载）', font(15), C_BLUE)

    # 业务层
    rbox(d, (120, 396, 1480, 792), '#EDF4EC', C_GREEN, 3)
    d.rounded_rectangle((120, 396, 1480, 444), radius=12, fill=C_GREEN)
    center_text(d, 800, 420, '业 务 / 接 口 层（后端服务 + AI 检测推理）', font(23, True), C_WHITE)

    rbox(d, (260, 460, 740, 774), C_WHITE, C_GREEN, 2)
    d.rounded_rectangle((260, 460, 740, 502), radius=10, fill=C_GREEN)
    center_text(d, 500, 481, '后端服务（Flask）', font(18, True), C_WHITE)
    items = ['用户认证', '图像上传', '缺陷检测', '记录管理', '参数设置', '数据统计']
    pos = [(350, 518), (510, 518), (350, 584), (510, 584), (350, 650), (510, 650)]
    for (ix, iy), it in zip(pos, items):
        rbox(d, (ix, iy, ix + 140, iy + 54), C_GREEN_F, C_GREEN, 2)
        center_text(d, ix + 70, iy + 27, it, font(15), C_TEXT)

    rbox(d, (780, 460, 1340, 774), C_WHITE, C_ORANGE, 2)
    d.rounded_rectangle((780, 460, 1340, 502), radius=10, fill=C_ORANGE)
    center_text(d, 1060, 481, '检测推理模块（Python + YOLOv8）', font(18, True), C_WHITE)
    acts = ['模型加载与切换', '图像预处理（640 归一化）', 'YOLOv8 模型推理',
            '后处理（阈值过滤 + NMS）', '结果解析与画框']
    yy = 514
    for a in acts:
        rbox(d, (805, yy, 1315, yy + 42), C_ORANGE_F, C_ORANGE, 2)
        center_text(d, 1060, yy + 21, a, font(14), C_TEXT)
        yy += 51
    center_text(d, 760, 560, '调\n用\n推\n理', font(13, True), C_GREEN)

    arrow(d, (800, 792), (800, 856))
    center_text(d, 815, 826, 'ORM / SQL · 文件读写 · 模型权重读写', font(15), C_BLUE)

    # 数据层
    rbox(d, (120, 860, 1480, 1090), C_GRAY_F, C_GRAY, 3)
    d.rounded_rectangle((120, 860, 1480, 908), radius=12, fill=C_GRAY)
    center_text(d, 800, 884, '数 据 层（SQLite 数据库 + 文件存储 + 模型仓库）', font(23, True), C_WHITE)

    rbox(d, (160, 934, 560, 1068), C_WHITE, C_GRAY, 2)
    center_text(d, 360, 957, 'SQLite 数据库', font(17, True), C_BLUE)
    for i, t in enumerate(['用户表 t_user', '检测记录表 t_record',
                           '缺陷结果表 t_defect', '系统参数表 t_config']):
        center_text(d, 360, 990 + i * 21, t, font(14), C_TEXT)

    rbox(d, (600, 934, 1000, 1068), C_WHITE, C_GRAY, 2)
    center_text(d, 800, 957, '文件存储', font(17, True), C_GREEN)
    for i, t in enumerate(['上传原图目录', '标注结果图目录', '导出文件目录']):
        center_text(d, 800, 996 + i * 21, t, font(14), C_TEXT)

    rbox(d, (1040, 934, 1440, 1068), C_WHITE, C_GRAY, 2)
    center_text(d, 1240, 957, '模型文件', font(17, True), C_ORANGE)
    for i, t in enumerate(['训练好的模型 best.pt', '类别名称文件']):
        center_text(d, 1240, 996 + i * 21, t, font(14), C_TEXT)

    return save_fig(img, 'fig_architecture.png')


# ============================================================ 图2 模块划分图
def draw_modules():
    W, H = 1600, 560
    img, d = new_canvas(W, H)
    center_text(d, 800, 45, '系统模块划分图', font(34, True), C_TEXT)

    rbox(d, (480, 82, 1120, 156), C_BLUE_F, C_BLUE, 3)
    center_text(d, 800, 119, '基于YOLOv8的手机屏幕外观缺陷智能检测系统', font(20, True), C_BLUE)

    mods = [
        ('网页模块', ['登录/检测/结果页', '历史/统计页', '图片上传与预览', '结果画框显示']),
        ('后台接口模块', ['登录与权限', '上传与检测接口', '记录管理接口', '统计与设置接口']),
        ('检测模块', ['加载模型', '图片预处理', 'YOLOv8 推理', '后处理与画框']),
        ('数据标注与数据集', ['收集图片', '标注与格式转换', '划分数据集', '数据增强']),
        ('数据库模块', ['建表与初始化', '增删改查', '图片路径管理', '备份']),
    ]
    x = 70
    for m, subs in mods:
        cx = x + 130
        arrow(d, (800, 158), (cx, 200), C_GRAY, 2, head=10)
        rbox(d, (x, 200, x + 260, 284), C_BLUE_F, C_BLUE, 2)
        center_text(d, cx, 242, m, font(19, True), C_BLUE)
        yy = 300
        for s in subs:
            rbox(d, (x + 10, yy, x + 250, yy + 40), C_ITEM, C_BORDER, 2)
            center_text(d, cx, yy + 20, s, font(15), C_TEXT)
            yy += 48
        x += 300
    return save_fig(img, 'fig_modules.png')


# ============================================================ 图3 数据库 ER 图
def draw_er():
    W, H = 1650, 700
    img, d = new_canvas(W, H)
    center_text(d, 825, 42, '数据库 ER 图（实体-联系，1:N）', font(34, True), C_TEXT)

    def entity(box, name, attrs, head_fill):
        x0, y0, x1, y1 = box
        rbox(d, box, C_WHITE, C_BLUE, 2)
        d.rounded_rectangle((x0, y0, x1, y0 + 50), radius=8, fill=head_fill)
        center_text(d, (x0 + x1) / 2, y0 + 25, name, font(21, True), C_WHITE)
        yy = y0 + 64
        for label in attrs:
            center_text(d, (x0 + x1) / 2, yy + 18, label, font(16), C_TEXT)
            yy += 40

    entity((110, 140, 500, 468), '用户 t_user',
           ['id（PK）', 'username（唯一）', 'password_hash', 'role（user/admin）', 'created_at'], C_BLUE)
    entity((560, 82, 1060, 570), '检测记录 t_record',
           ['id（PK）', 'user_id（FK）', 'image_path', 'result_path', 'total_defects',
            'status', 'conf_threshold', 'created_at'], C_GREEN)
    entity((1120, 110, 1540, 640), '缺陷结果 t_defect',
           ['id（PK）', 'record_id（FK）', 'class_id / class_name', 'conf（置信度）',
            'x / y（归一化中心）', 'w / h（归一化宽高）'], C_ORANGE)

    arrow(d, (500, 300), (560, 300), C_GRAY, 2, head=10)
    center_text(d, 530, 282, '1', font(17, True), C_TEXT)
    center_text(d, 530, 322, '拥有', font(13), C_GRAY)
    center_text(d, 600, 282, 'N', font(17, True), C_TEXT)

    arrow(d, (1060, 390), (1120, 390), C_GRAY, 2, head=10)
    center_text(d, 1088, 372, '1', font(17, True), C_TEXT)
    center_text(d, 1094, 410, '包含', font(13), C_GRAY)
    center_text(d, 1156, 372, 'N', font(17, True), C_TEXT)

    center_text(d, 825, 678,
                '说明：一条检测记录只属于一个用户；一条记录可包含多条缺陷结果；删除记录时级联删除其缺陷结果。',
                font(14), C_GRAY)
    return save_fig(img, 'fig_er.png')


# ============================================================ 图4 检测流程示意图
def draw_flow():
    W, H = 1650, 430
    img, d = new_canvas(W, H)
    center_text(d, 825, 42, '单张图像检测处理流程', font(30, True), C_TEXT)
    boxes = ['输入屏幕图像', '预处理\n缩放到 640×640\n归一化', 'YOLOv8 模型推理',
             '解析预测结果', '置信度阈值\n过滤', 'NMS 去重', '整理结果\n类别/坐标/置信度',
             '画框并保存结果图']
    w, gap = 172, 34
    x0 = (W - (8 * w + 7 * gap)) // 2
    y0 = 150
    for i, b in enumerate(boxes):
        rbox(d, (x0, y0, x0 + w, y0 + 118), C_BLUE_F, C_BLUE, 2)
        center_text(d, x0 + w / 2, y0 + 60, b, font(14), C_TEXT, max_w=w - 14)
        if i < len(boxes) - 1:
            arrow(d, (x0 + w, y0 + 59), (x0 + w + gap, y0 + 59), C_BLUE, 2, head=10)
        x0 += w + gap
    center_text(d, 825, 330, '模型：COCO 预训练权重 → 迁移微调（屏幕缺陷数据集）', font(15), C_GRAY)
    center_text(d, 825, 372, '输出：标注结果图（画框 + 类别 + 置信度）与 JSON 缺陷明细', font(15), C_GRAY)
    return save_fig(img, 'fig_flow.png')


# ============================================================ 图5-9 UI 原型图
def ui_frame(d, title):
    rbox(d, (20, 20, 1080, 765), '#E7E6E6', C_GRAY, 2, radius=12)
    d.rounded_rectangle((20, 20, 1080, 62), radius=10, fill=C_GRAY)
    for i in range(3):
        d.ellipse((36 + i * 22, 34, 46 + i * 22, 44), fill='#E7E6E6')
    d.rounded_rectangle((110, 30, 700, 52), radius=10, fill=C_WHITE)
    center_text(d, 405, 41, 'http://localhost:5000', font(13), C_GRAY)
    center_text(d, 800, 41, title, font(15, True), C_WHITE)


def ui_sidebar(d, active):
    rbox(d, (20, 70, 200, 765), '#2E5D88', '#1F4E79', 2, radius=8)
    items = [('检测中心', 'detect'), ('结果查看', 'result'), ('历史记录', 'history'),
             ('数据统计', 'stats'), ('参数设置', 'settings')]
    for i, (label, key) in enumerate(items):
        y = 92 + i * 58
        if key == active:
            rbox(d, (30, y, 190, y + 44), '#4A7FB5', '#4A7FB5', 2)
            center_text(d, 110, y + 22, label, font(15, True), C_WHITE)
        else:
            center_text(d, 110, y + 22, label, font(15), '#C7D6E4')
    center_text(d, 110, 726, '当前用户：admin', font(13), '#C7D6E4')


def ui_placeholder(d, box, text, fill='#EAF0F6', outline='#9DB9D2'):
    rbox(d, box, fill, outline, 2)
    center_text(d, (box[0] + box[2]) / 2, (box[1] + box[3]) / 2, text, font(15), C_GRAY,
                max_w=box[2] - box[0] - 24)


def draw_ui_login():
    W, H = 1120, 800
    img, d = new_canvas(W, H)
    ui_frame(d, '登录页')
    d.rounded_rectangle((330, 200, 790, 660), radius=14, fill=C_WHITE, outline=C_BLUE, width=3)
    center_text(d, 560, 250, '基于YOLOv8的手机屏幕外观缺陷智能检测系统', font(20, True), C_BLUE, max_w=430)
    center_text(d, 560, 306, '用户登录', font(26, True), C_TEXT)
    for i, ph in enumerate(['请输入用户名', '请输入密码']):
        yy = 372 + i * 80
        rbox(d, (405, yy, 715, yy + 54), '#F5F7FA', C_BORDER, 2)
        d.text((422, yy + 17), ph, font=font(15), fill='#9AA4AF')
    rbox(d, (405, 556, 715, 608), C_BLUE, C_BLUE, 2, radius=8)
    center_text(d, 560, 582, '登  录', font(18, True), C_WHITE)
    center_text(d, 560, 642, '默认账号：admin / 123456（管理员）', font(13), C_GRAY)
    return save_fig(img, 'fig_ui_login.png')


def draw_ui_detect():
    W, H = 1120, 800
    img, d = new_canvas(W, H)
    ui_frame(d, '检测页（上传与检测）')
    ui_sidebar(d, 'detect')
    d.rounded_rectangle((240, 100, 1060, 160), radius=8, fill='#DEEBF7')
    center_text(d, 650, 130, '上传屏幕图像 → 智能检测 → 查看结果', font(18, True), C_BLUE)
    ui_placeholder(d, (270, 190, 570, 400), '拖拽或点击上传图像\n（支持 jpg/png/bmp/webp）\n\n+')
    ui_placeholder(d, (600, 190, 1030, 400), '原图预览区\n（缩略图）')
    ui_placeholder(d, (270, 430, 750, 540), '待检测图片列表（批量）')
    rbox(d, (800, 445, 1000, 505), C_BLUE, C_BLUE, 2, radius=8)
    center_text(d, 900, 475, '开 始 检 测', font(17, True), C_WHITE)
    center_text(d, 900, 528, '置信度阈值：0.25（可调）', font(13), C_GRAY)
    ui_placeholder(d, (270, 570, 1030, 730), '检测结果区：标注结果图 + 缺陷列表（点击“开始检测”后显示）')
    return save_fig(img, 'fig_ui_detect.png')


def draw_ui_result():
    W, H = 1120, 800
    img, d = new_canvas(W, H)
    ui_frame(d, '结果页（可视化展示）')
    ui_sidebar(d, 'result')
    center_text(d, 650, 100, '检测结果：发现 3 处缺陷', font(20, True), C_TEXT)
    rbox(d, (270, 140, 730, 620), '#222831', '#111827', 2)
    for (bx, by, bw, bh, label) in [(330, 222, 150, 60, 'scratch 0.92'),
                                    (440, 380, 90, 90, 'bright_dot 0.87'),
                                    (570, 182, 110, 40, 'scratch 0.78')]:
        d.rectangle((bx, by, bx + bw, by + bh), outline='#FF4444', width=4)
        d.rounded_rectangle((bx, by - 24, bx + 116, by), radius=4, fill='#FF4444')
        center_text(d, bx + 58, by - 12, label, font(14, True), C_WHITE)
    center_text(d, 500, 660, '标注结果图（画框 + 类别 + 置信度）', font(14), C_GRAY)
    rbox(d, (760, 140, 1060, 620), C_WHITE, C_BLUE, 2)
    center_text(d, 910, 165, '缺陷明细', font(17, True), C_BLUE)
    rows = [('序号', '类别', '置信度'), ('1', 'scratch 划痕', '0.92'),
            ('2', 'bright_dot 亮点', '0.87'), ('3', 'scratch 划痕', '0.78')]
    for i, row in enumerate(rows):
        yy = 195 + i * 42
        if i == 0:
            rbox(d, (780, yy, 1040, yy + 36), C_BLUE_F, C_BLUE, 1)
            center_text(d, 910, yy + 19, '   '.join(row), font(13, True), C_BLUE)
        else:
            center_text(d, 910, yy + 19, '   '.join(row), font(13), C_TEXT)
    for i, (txt, box) in enumerate([('下载结果图', (780, 640, 880, 692)),
                                    ('导出 CSV', (890, 640, 1040, 692))]):
        rbox(d, box, C_BLUE if i == 0 else C_WHITE, C_BLUE, 2, radius=8)
        fill = C_WHITE if i == 0 else C_BLUE
        center_text(d, (box[0] + box[2]) / 2, (box[1] + box[3]) / 2, txt, font(15, True), fill)
    return save_fig(img, 'fig_ui_result.png')


def draw_ui_history():
    W, H = 1120, 800
    img, d = new_canvas(W, H)
    ui_frame(d, '历史记录页')
    ui_sidebar(d, 'history')
    center_text(d, 650, 98, '检测历史记录', font(20, True), C_TEXT)
    rbox(d, (270, 130, 1060, 190), '#F5F7FA', C_BORDER, 2)
    center_text(d, 310, 160, '时间范围：', font(14), C_TEXT)
    rbox(d, (400, 138, 540, 180), C_WHITE, C_BORDER, 2)
    center_text(d, 470, 159, '近 7 天 ▼', font(13), C_GRAY)
    center_text(d, 590, 160, '缺陷类型：', font(14), C_TEXT)
    rbox(d, (690, 138, 860, 180), C_WHITE, C_BORDER, 2)
    center_text(d, 775, 159, '全部 ▼', font(13), C_GRAY)
    rbox(d, (890, 138, 1040, 180), C_BLUE, C_BLUE, 2, radius=6)
    center_text(d, 965, 159, '查 询', font(14, True), C_WHITE)
    rbox(d, (270, 210, 1060, 680), C_WHITE, C_BLUE, 2)
    header = ['记录ID', '检测时间', '原图', '缺陷数', '状态', '操作']
    col_x = [280, 340, 470, 570, 640, 790]
    for i, htxt in enumerate(header):
        x2 = col_x[i + 1] if i < len(col_x) - 1 else 1050
        center_text(d, (col_x[i] + x2) / 2, 234, htxt, font(14, True), C_BLUE)
    d.line((270, 250, 1060, 250), fill=C_BLUE, width=2)
    data = [('R101', '2026-10-01 10:12', 'img_1021.jpg', '3', '正常', ''),
            ('R100', '2026-10-01 09:48', 'img_1019.jpg', '0', '正常', ''),
            ('R099', '2026-09-30 16:30', 'img_1013.jpg', '1', '正常', ''),
            ('R098', '2026-09-30 14:05', 'img_1002.jpg', '2', '正常', '')]
    for i, row in enumerate(data):
        yy = 278 + i * 66
        for j, val in enumerate(row):
            x1 = col_x[j]
            x2 = col_x[j + 1] if j < len(col_x) - 1 else 1050
            center_text(d, (x1 + x2) / 2, yy, val, font(13), C_TEXT)
        rbox(d, (830, yy - 24, 878, yy + 8), C_BLUE_F, C_BLUE, 1)
        center_text(d, 854, yy - 8, '查看', font(12, True), C_BLUE)
        rbox(d, (888, yy - 24, 936, yy + 8), '#FDECEC', '#E06C6C', 1)
        center_text(d, 912, yy - 8, '删除', font(12, True), '#D94F4F')
    for i in range(1, 4):
        d.line((270, 250 + i * 66, 1060, 250 + i * 66), fill='#E8EDF2', width=1)
    for i in range(1, 5):
        rbox(d, (480 + (i - 1) * 70, 652, 480 + i * 70, 682), '#4A7FB5' if i == 1 else C_WHITE, C_BORDER, 2)
        center_text(d, 515 + (i - 1) * 70, 667, str(i), font(14, True) if i == 1 else font(14),
                    C_WHITE if i == 1 else C_TEXT)
    center_text(d, 920, 667, '共 28 条记录', font(13), C_GRAY)
    return save_fig(img, 'fig_ui_history.png')


def draw_ui_stats():
    W, H = 1120, 800
    img, d = new_canvas(W, H)
    ui_frame(d, '数据统计页')
    ui_sidebar(d, 'stats')
    center_text(d, 650, 96, '缺陷数据统计', font(20, True), C_TEXT)
    cards = [('检测总数', '286 次'), ('检出缺陷', '412 处'), ('今日检测', '18 次'), ('平均耗时', '1.2 秒')]
    x = 270
    for t, v in cards:
        rbox(d, (x, 130, x + 175, 215), C_WHITE, C_BLUE, 2)
        center_text(d, x + 87, 162, t, font(14), C_GRAY)
        center_text(d, x + 87, 190, v, font(20, True), C_BLUE)
        x += 200
    rbox(d, (270, 245, 710, 650), C_WHITE, C_BORDER, 2)
    center_text(d, 490, 270, '各类缺陷检出数量（柱状图）', font(15, True), C_TEXT)
    cats = [('划痕', 168), ('亮点', 96), ('污渍', 74), ('暗点', 42), ('裂纹', 22), ('崩缺', 10)]
    for i, (lab, v) in enumerate(cats):
        bx = 302 + i * 66
        bw = 44
        bh = max(8, int(v * 1.55))
        d.rectangle((bx, 612 - bh, bx + bw, 612), fill=C_BLUE_F, outline=C_BLUE, width=2)
        center_text(d, bx + bw / 2, 600 - bh - 12, str(v), font(13, True), C_BLUE)
        center_text(d, bx + bw / 2, 628, lab, font(13), C_TEXT)
    center_text(d, 490, 650, '数据来源：检测历史记录（按类别汇总）', font(12), C_GRAY)
    rbox(d, (745, 245, 1060, 650), C_WHITE, C_BORDER, 2)
    center_text(d, 902, 270, '类别占比', font(15, True), C_TEXT)
    d.line((755, 285, 1050, 285), fill=C_BORDER, width=1)
    for i, (lab, v) in enumerate(cats[:5]):
        pct = round(v / sum(c[1] for c in cats) * 100)
        center_text(d, 820, 318 + i * 40, lab, font(13), C_TEXT)
        center_text(d, 980, 318 + i * 40, f'{pct}%', font(13, True), C_BLUE)
    center_text(d, 902, 628, '支持按时间范围切换', font(12), C_GRAY)
    return save_fig(img, 'fig_ui_stats.png')


# ============================================================ 图10 进度甘特图
def draw_gantt():
    W, H = 1600, 680
    img, d = new_canvas(W, H)
    center_text(d, 800, 45, '第 7–10 周设计阶段进度安排（甘特图）', font(32, True), C_TEXT)

    x0, x1 = 430, 1520
    week_w = (x1 - x0) / 4
    weeks = ['第 7 周', '第 8 周', '第 9 周', '第 10 周']
    for i, wk in enumerate(weeks):
        cx = x0 + week_w * (i + 0.5)
        center_text(d, cx, 105, wk, font(16, True), C_BLUE)
        d.line((x0 + week_w * i, 118, x0 + week_w * i, 560), fill='#E4E8EC', width=1)
    d.line((x0, 118, x1, 118), fill=C_BORDER, width=2)
    d.line((x1, 118, x1, 560), fill=C_BORDER, width=1)

    tasks = [
        ('总体架构设计与模块划分', 0, 0, C_BLUE),
        ('技术栈选型与方案确定', 0, 0, C_BLUE),
        ('数据库表结构设计', 1, 1, C_GREEN),
        ('REST API 接口设计', 1, 1, C_GREEN),
        ('UI 原型设计（五个主要页面）', 2, 2, C_ORANGE),
        ('算法方案细化与模型选型', 2, 2, C_ORANGE),
        ('撰写《概要设计说明书》', 3, 3, C_GRAY),
    ]
    yy = 150
    for name, s, e, color in tasks:
        center_text(d, 215, yy + 19, name, font(16), C_TEXT)
        bx = x0 + week_w * s + 16
        bw = week_w * (e - s + 1) - 32
        rbox(d, (bx, yy, bx + bw, yy + 38), color, color, 2, radius=6)
        label = weeks[s][2:] + ('–' + weeks[e][2:] if e != s else '')
        center_text(d, bx + bw / 2, yy + 19, label, font(14, True), C_WHITE)
        yy += 52
    for (mx, mtxt) in [(x0 + week_w * 0.5, '架构方案\n确定'),
                       (x0 + week_w * 2.5, '原型评审\n（内部）'),
                       (x0 + week_w * 3.5, '提交文档\n里程碑')]:
        d.polygon([(mx, 600), (mx + 12, 612), (mx, 624), (mx - 12, 612)], fill=C_ORANGE)
        center_text(d, mx, 565, mtxt, font(13, True), C_ORANGE)
    center_text(d, 800, 655, '第 10 周末提交《概要设计说明书》并通过设计评审', font(14), C_GRAY)
    return save_fig(img, 'fig_gantt.png')


def build_figures():
    paths = {
        'arch': draw_architecture(),
        'modules': draw_modules(),
        'er': draw_er(),
        'flow': draw_flow(),
        'ui_login': draw_ui_login(),
        'ui_detect': draw_ui_detect(),
        'ui_result': draw_ui_result(),
        'ui_history': draw_ui_history(),
        'ui_stats': draw_ui_stats(),
        'gantt': draw_gantt(),
    }
    return paths


if __name__ == '__main__':
    for k, v in build_figures().items():
        print('figure OK:', k, v)
