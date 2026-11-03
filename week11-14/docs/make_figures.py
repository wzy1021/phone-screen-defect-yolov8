# -*- coding: utf-8 -*-
"""生成《详细设计说明书》的示意图。

输出到 docs/figures/：
    package_structure.png   代码包结构
    detect_flow.png         单张图片检测流程
    sequence_detect.png     检测接口时序图
    sequence_login.png      登录认证时序图
    db_schema.png           数据库表结构与关系
    class_diagram.png       主要类/模块关系
    dataset_samples.png     数据集中带标注的样例
    dataset_distribution.png 各类别数量分布
    dataset_boxsize.png     标注框尺寸分布

用法：python docs/make_figures.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

BASE = Path(__file__).resolve().parent.parent
FIG = BASE / 'docs' / 'figures'
DATA = BASE / 'datasets'

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

INK = '#1f2d45'
MUTED = '#6b7c96'
BLUE = '#2f6bff'
BLUE_L = '#eef4ff'
GREEN = '#1f9d55'
GREEN_L = '#eefaf2'
ORANGE = '#e87722'
ORANGE_L = '#fff4e8'
RED = '#d4380d'
RED_L = '#fff1ef'
GRAY_L = '#f5f7fb'


def new_canvas(w=12, h=7):
    fig, ax = plt.subplots(figsize=(w, h), dpi=200)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    fig.patch.set_facecolor('white')
    return fig, ax


def box(ax, x, y, w, h, text, fc=BLUE_L, ec=BLUE, fs=10, color=INK,
        bold=False, lw=1.3, align='center', pad=0.012):
    p = FancyBboxPatch((x, y), w, h, boxstyle=f'round,pad=0.004,rounding_size=0.012',
                       facecolor=fc, edgecolor=ec, linewidth=lw, zorder=2)
    ax.add_patch(p)
    if align == 'center':
        ax.text(x + w / 2, y + h / 2, text, ha='center', va='center', fontsize=fs,
                color=color, fontweight='bold' if bold else 'normal', linespacing=1.6, zorder=3)
    else:
        ax.text(x + pad, y + h / 2, text, ha='left', va='center', fontsize=fs,
                color=color, fontweight='bold' if bold else 'normal', linespacing=1.6, zorder=3)


def arrow(ax, p1, p2, color=MUTED, lw=1.3, style='-|>', rad=0.0, ls='-'):
    a = FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=13, color=color,
                        lw=lw, connectionstyle=f'arc3,rad={rad}', linestyle=ls, zorder=1,
                        shrinkA=2, shrinkB=2)
    ax.add_patch(a)


def label(ax, x, y, text, fs=9, color=MUTED, ha='center', va='center', bold=False):
    ax.text(x, y, text, fontsize=fs, color=color, ha=ha, va=va,
            fontweight='bold' if bold else 'normal', zorder=4)


# ================================================================ 1 包结构
def fig_package():
    fig, ax = new_canvas(13, 8)
    # 外层
    ax.add_patch(FancyBboxPatch((0.03, 0.02), 0.94, 0.96,
                                boxstyle='round,pad=0.004,rounding_size=0.012',
                                fc='none', ec='#c8d4e6', lw=1.4, ls='--'))
    label(ax, 0.055, 0.955, '工程 week11-14', fs=10, color=MUTED, ha='left')

    # 展示层
    box(ax, 0.06, 0.80, 0.88, 0.12,
        '展示层  templates/ 5 个页面  +  static/  css · js · 图片',
        fc=BLUE_L, ec=BLUE, fs=11, bold=True)

    # 业务层容器
    ax.add_patch(FancyBboxPatch((0.06, 0.28), 0.88, 0.46,
                                boxstyle='round,pad=0.004,rounding_size=0.012',
                                fc='#fbfcff', ec='#aac0e8', lw=1.3))
    label(ax, 0.08, 0.715, '业务层  app/  Flask 应用包', fs=10.5, color=BLUE, ha='left', bold=True)

    rows = [
        ('views.py\n页面路由', 'api.py\nREST 接口', 'auth.py\n登录与 token', 'utils.py\n图片与文件'),
        ('detection.py\n模型加载/推理/画框', 'db.py\nSQLite 访问', 'config.py\n路径与类别配置', 'run.py\n启动入口'),
    ]
    for r, row in enumerate(rows):
        for c, text in enumerate(row):
            x = 0.085 + c * 0.215
            y = 0.49 - r * 0.15
            box(ax, x, y, 0.19, 0.115, text, fc='white', ec='#9db7e4', fs=9.5)

    # 依赖指向
    arrow(ax, (0.50, 0.80), (0.50, 0.745), color=BLUE)
    label(ax, 0.565, 0.775, 'HTTP / JSON', fs=9)

    # 数据与模型
    box(ax, 0.06, 0.10, 0.20, 0.12, 'SQLite\ndata.db', fc=GREEN_L, ec=GREEN, fs=10.5, bold=True)
    box(ax, 0.32, 0.10, 0.20, 0.12, '模型\nmodels/best.pt', fc=ORANGE_L, ec=ORANGE, fs=10.5, bold=True)
    box(ax, 0.58, 0.10, 0.17, 0.12, '原图\nstatic/uploads', fc=GRAY_L, ec='#9aa8bd', fs=10, bold=True)
    box(ax, 0.79, 0.10, 0.15, 0.12, '结果图\nstatic/results', fc=GRAY_L, ec='#9aa8bd', fs=9.5, bold=True)

    arrow(ax, (0.29, 0.28), (0.19, 0.22), color=GREEN)
    arrow(ax, (0.45, 0.28), (0.42, 0.22), color=ORANGE)
    arrow(ax, (0.22, 0.28), (0.64, 0.22), color='#9aa8bd', rad=-0.15)
    arrow(ax, (0.30, 0.28), (0.84, 0.22), color='#9aa8bd', rad=-0.1)

    label(ax, 0.5, 0.045, '依赖方向：页面 → 接口 → 检测 / 数据库 → 模型与文件', fs=9, color=MUTED)
    fig.savefig(FIG / 'package_structure.png', bbox_inches='tight', facecolor='white')
    plt.close(fig)


# ================================================================ 2 检测流程
def fig_detect_flow():
    fig, ax = new_canvas(12, 11)
    steps = [
        ('接收请求\nfile + conf', BLUE_L, BLUE),
        ('校验格式 / 大小 / 图片有效性', BLUE_L, BLUE),
        ('保存原图（统一转 JPEG）', BLUE_L, BLUE),
        ('读取阈值（数据库，缺省 0.25）', BLUE_L, BLUE),
        ('检测器已加载？\n（否则加载 best.pt）', '#fffbe6', '#d4a017'),
        ('PIL 读图，记录原图宽高', BLUE_L, BLUE),
        ('缩放 / 补边到 640×640', BLUE_L, BLUE),
        ('YOLOv8 前向推理', ORANGE_L, ORANGE),
        ('置信度过滤 + NMS', BLUE_L, BLUE),
        ('坐标映射回原图并归一化', BLUE_L, BLUE),
        ('画框，保存结果图', BLUE_L, BLUE),
        ('写 t_record / t_defect', GREEN_L, GREEN),
        ('返回 JSON：记录号、缺陷列表、结果图', GREEN_L, GREEN),
    ]
    top, bottom = 0.955, 0.035
    gap = (top - bottom) / len(steps)
    h = gap * 0.64
    for i, (text, fc, ec) in enumerate(steps):
        y = top - (i + 1) * gap + (gap - h) / 2
        box(ax, 0.16, y, 0.52, h, text, fc=fc, ec=ec, fs=10.5)
        if i < len(steps) - 1:
            arrow(ax, (0.42, y), (0.42, y - (gap - h) / 2 - 0.001), color='#8194b3')

    # 错误分支
    errs = [
        (1, '格式 / 大小不对\n→ 400', RED_L, RED),
        (4, '模型文件不存在\n→ 503', RED_L, RED),
        (7, '推理异常\n→ 500 + failed 记录', RED_L, RED),
    ]
    for idx, text, fc, ec in errs:
        y = top - (idx + 1) * gap + (gap - h) / 2
        box(ax, 0.75, y - 0.012, 0.20, h * 0.62, text, fc=fc, ec=ec, fs=8.8)
        arrow(ax, (0.68, y + h / 2), (0.75, y + h * 0.30), color=RED, ls='--')

    fig.savefig(FIG / 'detect_flow.png', bbox_inches='tight', facecolor='white')
    plt.close(fig)


# ================================================================ 3 时序图
def fig_sequence_detect():
    fig, ax = new_canvas(13, 7.5)
    actors = [
        ('浏览器', 0.08, '#eef4ff', BLUE),
        ('Flask 接口', 0.28, '#eef4ff', BLUE),
        ('检测模块', 0.48, '#fff4e8', ORANGE),
        ('YOLOv8', 0.66, '#fff4e8', ORANGE),
        ('文件存储', 0.82, '#f5f7fb', '#8b9bb4'),
        ('SQLite', 0.94, '#eefaf2', GREEN),
    ]
    for name, x, fc, ec in actors:
        box(ax, x - 0.055, 0.88, 0.11, 0.075, name, fc=fc, ec=ec, fs=9.5, bold=True)
        ax.plot([x, x], [0.06, 0.88], color='#b9c6da', lw=1, ls=(0, (4, 4)), zorder=0)

    msgs = [
        (0.08, 0.28, 0.82, '1. POST /api/detect（file, conf）'),
        (0.28, 0.82, 0.76, '2. 保存原图'),
        (0.28, 0.48, 0.70, '3. detect(path, conf)'),
        (0.48, 0.66, 0.64, '4. predict（模型已缓存）'),
        (0.66, 0.48, 0.58, '5. 返回 boxes / conf / cls'),
        (0.48, 0.82, 0.52, '6. 保存画框结果图'),
        (0.48, 0.28, 0.46, '7. defects + result_path'),
        (0.28, 0.94, 0.40, '8. INSERT t_record / t_defect'),
        (0.94, 0.28, 0.34, '9. record_id'),
        (0.28, 0.08, 0.28, '10. JSON（result_url, defects）'),
    ]
    for x1, x2, y, text in msgs:
        color = '#2f6bff' if x2 > x1 else '#7b8aa3'
        arrow(ax, (x1, y), (x2, y), color=color, lw=1.4)
        label(ax, (x1 + x2) / 2, y + 0.022, text, fs=8.8, color=INK)

    # 激活条
    for x, y1, y2 in [(0.28, 0.28, 0.82), (0.48, 0.46, 0.70), (0.66, 0.58, 0.64)]:
        ax.add_patch(Rectangle((x - 0.004, y1), 0.008, y2 - y1, fc='#c9d6ea', ec='none', zorder=0))

    fig.savefig(FIG / 'sequence_detect.png', bbox_inches='tight', facecolor='white')
    plt.close(fig)


def fig_sequence_login():
    fig, ax = new_canvas(12.5, 6.5)
    actors = [
        ('浏览器', 0.10, '#eef4ff', BLUE),
        ('Flask 页面/接口', 0.36, '#eef4ff', BLUE),
        ('auth 模块', 0.60, '#fff4e8', ORANGE),
        ('SQLite', 0.86, '#eefaf2', GREEN),
    ]
    for name, x, fc, ec in actors:
        box(ax, x - 0.07, 0.86, 0.14, 0.08, name, fc=fc, ec=ec, fs=9.5, bold=True)
        ax.plot([x, x], [0.08, 0.86], color='#b9c6da', lw=1, ls=(0, (4, 4)), zorder=0)

    msgs = [
        (0.10, 0.36, 0.78, '1. POST /login（username, password）'),
        (0.36, 0.60, 0.70, '2. login_user(name, pwd)'),
        (0.60, 0.86, 0.62, '3. SELECT * FROM t_user'),
        (0.86, 0.60, 0.55, '4. 用户记录 / 空'),
        (0.60, 0.60, 0.46, '5. PBKDF2 校验密码（compare_digest）'),
        (0.60, 0.36, 0.38, '6. 签发 token（itsdangerous 签名）'),
        (0.36, 0.10, 0.30, '7. 302 /detect + Set-Cookie: ps_token'),
        (0.10, 0.36, 0.22, '8. GET /detect（Cookie 自动携带）'),
        (0.36, 0.60, 0.16, '9. read_token → 查用户 → 放行'),
        (0.36, 0.10, 0.10, '10. 200 页面 HTML'),
    ]
    for x1, x2, y, text in msgs:
        color = '#2f6bff' if x2 > x1 else '#7b8aa3'
        arrow(ax, (x1, y), (x2, y), color=color, lw=1.4)
        label(ax, (x1 + x2) / 2, y + 0.025, text, fs=8.8, color=INK)
    for x, y1, y2 in [(0.36, 0.10, 0.78), (0.60, 0.16, 0.70)]:
        ax.add_patch(Rectangle((x - 0.004, y1), 0.008, y2 - y1, fc='#c9d6ea', ec='none', zorder=0))

    fig.savefig(FIG / 'sequence_login.png', bbox_inches='tight', facecolor='white')
    plt.close(fig)


# ================================================================ 4 数据库表
def table_card(ax, x, y, w, title, cols, color=BLUE, fc='white'):
    row_h = 0.037
    head_h = 0.055
    h = head_h + row_h * len(cols) + 0.012
    ax.add_patch(FancyBboxPatch((x, y - h + head_h + 0.012), w, h,
                                boxstyle='round,pad=0.003,rounding_size=0.008',
                                fc=fc, ec=color, lw=1.4, zorder=2))
    ax.add_patch(Rectangle((x + 0.004, y - head_h + 0.008), w - 0.008, head_h,
                           fc=color, ec='none', zorder=3))
    ax.text(x + w / 2, y - head_h / 2 + 0.012, title, ha='center', va='center',
            fontsize=10, color='white', fontweight='bold', zorder=4)
    for i, (name, typ, mark) in enumerate(cols):
        ty = y - head_h - i * row_h - 0.002
        ax.text(x + 0.014, ty, name, ha='left', va='center', fontsize=8.2,
                color=INK, fontweight='bold' if mark in ('PK', 'FK') else 'normal', zorder=4)
        ax.text(x + w * 0.44, ty, typ, ha='left', va='center', fontsize=7.8, color=MUTED, zorder=4)
        if mark:
            ax.text(x + w - 0.012, ty, mark, ha='right', va='center', fontsize=7.2,
                    color=ORANGE if mark == 'FK' else BLUE, fontweight='bold', zorder=4)
    return h


def fig_db_schema():
    fig, ax = new_canvas(13, 8)
    user = [
        ('id', 'INTEGER', 'PK'), ('username', 'TEXT', 'UQ'), ('password', 'TEXT', ''),
        ('role', 'TEXT', ''), ('created_at', 'TEXT', ''),
    ]
    record = [
        ('id', 'INTEGER', 'PK'), ('user_id', 'INTEGER', 'FK'), ('image_path', 'TEXT', ''),
        ('result_path', 'TEXT', ''), ('total', 'INTEGER', ''), ('status', 'TEXT', ''),
        ('conf', 'REAL', ''), ('cost_ms', 'INTEGER', ''), ('created_at', 'TEXT', 'IDX'),
    ]
    defect = [
        ('id', 'INTEGER', 'PK'), ('record_id', 'INTEGER', 'FK'), ('class_id', 'INTEGER', ''),
        ('class_name', 'TEXT', ''), ('conf', 'REAL', ''), ('x / y', 'REAL', ''),
        ('w / h', 'REAL', ''),
    ]
    config = [('id', 'INTEGER', 'PK'), ('name', 'TEXT', 'UQ'), ('value', 'TEXT', '')]

    table_card(ax, 0.05, 0.93, 0.26, 't_user  用户表', user, BLUE)
    table_card(ax, 0.39, 0.93, 0.30, 't_record  检测记录表', record, ORANGE, '#fffdf8')
    table_card(ax, 0.39, 0.43, 0.30, 't_defect  缺陷明细表', defect, GREEN, '#f8fdfa')
    table_card(ax, 0.73, 0.93, 0.23, 't_config  参数表', config, '#8b5cf6', '#fbf8ff')

    # 关系线：1 对多
    arrow(ax, (0.31, 0.855), (0.39, 0.855), color='#7b8aa3', style='-')
    label(ax, 0.335, 0.875, '1', fs=9, color=INK)
    label(ax, 0.395, 0.875, 'N', fs=9, color=INK)
    label(ax, 0.345, 0.825, 'user_id', fs=8, color=MUTED)

    arrow(ax, (0.54, 0.46), (0.54, 0.40), color='#7b8aa3', style='-')
    label(ax, 0.525, 0.43, '1', fs=9, color=INK)
    label(ax, 0.525, 0.465, 'N', fs=9, color=INK)
    label(ax, 0.60, 0.43, 'record_id', fs=8, color=MUTED)

    label(ax, 0.05, 0.10,
          '说明：删除记录时先删 t_defect 再删 t_record（SQLite 默认不启用外键级联）；\n'
          't_record.created_at 建普通索引，历史页按 id 倒序分页。',
          fs=9, color=MUTED, ha='left')
    fig.savefig(FIG / 'db_schema.png', bbox_inches='tight', facecolor='white')
    plt.close(fig)


# ================================================================ 5 类图
def class_box(ax, x, y, w, title, attrs, methods, color=BLUE, fc=BLUE_L):
    line_h = 0.030
    h = 0.050 + line_h * (len(attrs) + len(methods)) + 0.02
    ax.add_patch(FancyBboxPatch((x, y - h + 0.02), w, h,
                                boxstyle='round,pad=0.003,rounding_size=0.008',
                                fc=fc, ec=color, lw=1.4, zorder=2))
    ax.add_patch(Rectangle((x + 0.004, y - 0.048 + 0.02), w - 0.008, 0.048,
                           fc=color, ec='none', zorder=3))
    ax.text(x + w / 2, y - 0.024 + 0.02, title, ha='center', va='center',
            fontsize=9.5, color='white', fontweight='bold', zorder=4)
    yy = y - 0.055 + 0.02
    for a in attrs:
        ax.text(x + 0.012, yy, a, fontsize=7.8, color=INK, ha='left', va='center', zorder=4)
        yy -= line_h
    ax.plot([x + 0.008, x + w - 0.008], [yy + line_h * 0.6, yy + line_h * 0.6],
            color=color, lw=0.8, zorder=4)
    for m in methods:
        ax.text(x + 0.012, yy, m, fontsize=7.8, color=MUTED, ha='left', va='center', zorder=4)
        yy -= line_h
    return h


def fig_class_diagram():
    fig, ax = new_canvas(13, 8)
    class_box(ax, 0.04, 0.93, 0.27, 'ApiBlueprint  (api.py)',
              ['+ blueprint: Blueprint'],
              ['+ login() / upload()', '+ detect(file, conf)', '+ records() / stats()',
               '+ settings() / health()'], BLUE)
    class_box(ax, 0.04, 0.58, 0.27, 'AuthService  (auth.py)',
              ['- serializer', '- TOKEN_MAX_AGE'],
              ['+ hash_password()', '+ verify_password()', '+ issue_token()',
               '+ get_current_user()', '+ login_required()'], '#8b5cf6', '#fbf8ff')
    class_box(ax, 0.37, 0.93, 0.28, 'DefectDetector  (detection.py)',
              ['- model: YOLO | None', '- imgsz: int = 640', '- lock: Lock'],
              ['+ detect(path, conf, iou)', '+ annotate(img, defects)', '- _ensure_model()',
               '+ loaded: bool'], ORANGE, ORANGE_L)
    class_box(ax, 0.70, 0.93, 0.26, 'Database  (db.py)',
              ['+ get_db() -> Connection'],
              ['+ create_record()', '+ get_record()', '+ list_records()',
               '+ delete_record()', '+ get_stats()'], GREEN, GREEN_L)
    class_box(ax, 0.37, 0.55, 0.28, 'FileStore  (utils.py)',
              ['- UPLOAD_DIR', '- RESULT_DIR'],
              ['+ save_upload(FileStorage)', '+ static_abs(rel)', '+ delete_static_file()'],
              '#64748b', '#f5f7fb')
    class_box(ax, 0.70, 0.55, 0.26, 'YOLO  (ultralytics)',
              ['- weights: best.pt'],
              ['+ predict(source, imgsz)', '→ boxes / conf / cls'], '#b45309', '#fff7ed')

    arrow(ax, (0.31, 0.895), (0.37, 0.895), color='#7b8aa3')
    label(ax, 0.34, 0.912, '调用', fs=8)
    arrow(ax, (0.65, 0.895), (0.70, 0.895), color='#7b8aa3')
    label(ax, 0.675, 0.912, '写记录', fs=8)

    arrow(ax, (0.17, 0.71), (0.17, 0.58), color='#7b8aa3')
    label(ax, 0.215, 0.645, '校验密码 / 签发 token', fs=8, ha='left')
    arrow(ax, (0.60, 0.65), (0.83, 0.55), color='#b45309')
    label(ax, 0.70, 0.625, '推理', fs=8, color='#b45309', ha='left')

    label(ax, 0.04, 0.06, '+ 公有方法   - 私有属性；调用关系用实线，依赖用虚线。',
          fs=9, color=MUTED, ha='left')
    fig.savefig(FIG / 'class_diagram.png', bbox_inches='tight', facecolor='white')
    plt.close(fig)


# ================================================================ 6 数据集图
def _class_info():
    stats = json.loads((DATA / 'dataset_stats.json').read_text(encoding='utf-8'))
    names = stats['classes']
    return stats, names


def fig_dataset_distribution():
    stats, classes = _class_info()
    cn = [c[1] for c in classes]
    keys = [c[0] for c in classes]
    splits = ['train', 'val', 'test']
    colors = ['#2f6bff', '#52c41a', '#faad14']

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2), dpi=200,
                             gridspec_kw={'width_ratios': [1.55, 1]})
    ax = axes[0]
    width = 0.26
    x = range(len(keys))
    for i, (split, color) in enumerate(zip(splits, colors)):
        vals = [stats[split]['classes'][k] for k in keys]
        bars = ax.bar([v + (i - 1) * width for v in x], vals, width=width,
                      label={'train': '训练集', 'val': '验证集', 'test': '测试集'}[split],
                      color=color, edgecolor='white', linewidth=0.5)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 8, str(v), ha='center',
                    va='bottom', fontsize=7.5, color=MUTED)
    ax.set_xticks(list(x))
    ax.set_xticklabels(cn, fontsize=10)
    ax.set_ylabel('缺陷框数量', fontsize=10)
    ax.set_title('各划分的类别数量', fontsize=12, pad=10)
    ax.legend(frameon=False, fontsize=9)
    ax.grid(axis='y', alpha=0.25, linestyle='--')
    ax.set_axisbelow(True)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)

    ax2 = axes[1]
    totals = [stats['train']['classes'][k] + stats['val']['classes'][k] + stats['test']['classes'][k]
              for k in keys]
    palette = ['#ff7a45', '#ff4d4f', '#52c41a', '#722ed1', '#faad14', '#13c2c2']
    wedges, _, autotexts = ax2.pie(totals, colors=palette, autopct='%1.1f%%',
                                   startangle=120, pctdistance=0.75,
                                   wedgeprops=dict(width=0.42, edgecolor='white'))
    for t in autotexts:
        t.set_fontsize(8.5)
        t.set_color('white')
        t.set_fontweight('bold')
    ax2.set_title('全部缺陷的类别占比', fontsize=12, pad=10)
    ax2.legend(wedges, cn, loc='center left', bbox_to_anchor=(0.96, 0.5),
               frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG / 'dataset_distribution.png', bbox_inches='tight', facecolor='white')
    plt.close(fig)


def fig_boxsize():
    import random
    _, classes = _class_info()
    colors = ['#ff7a45', '#ff4d4f', '#52c41a', '#722ed1', '#faad14', '#13c2c2']
    points = {c[0]: ([], []) for c in classes}
    rng = random.Random(0)
    for split in ('train', 'val', 'test'):
        for lbl in (DATA / 'labels' / split).glob('*.txt'):
            for line in lbl.read_text(encoding='utf-8').splitlines():
                if not line.strip():
                    continue
                cid, cx, cy, w, h = line.split()
                cid = int(cid)
                name = classes[cid][0]
                if len(points[name][0]) < 900:
                    points[name][0].append(float(w) * 100)
                    points[name][1].append(float(h) * 100)

    fig, ax = plt.subplots(figsize=(8.6, 5.6), dpi=200)
    for (name, (xs, ys)), color, (ename, cn) in zip(points.items(), colors, classes):
        ax.scatter(xs, ys, s=8, alpha=0.55, color=color, label=cn, edgecolors='none')
    ax.set_xlabel('标注框宽度 / 图片宽度（%）', fontsize=10)
    ax.set_ylabel('标注框高度 / 图片高度（%）', fontsize=10)
    ax.set_title('六类缺陷标注框的尺寸分布', fontsize=12, pad=10)
    ax.grid(alpha=0.25, linestyle='--')
    ax.legend(frameon=False, fontsize=9, markerscale=2)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG / 'dataset_boxsize.png', bbox_inches='tight', facecolor='white')
    plt.close(fig)


def fig_dataset_samples(count=8, cols=4):
    """从 test 集选图，画上真实标注框，拼成样例图。"""
    from PIL import Image, ImageDraw, ImageFont

    classes = json.loads((DATA / 'dataset_stats.json').read_text(encoding='utf-8'))['classes']
    colors = ['#ff7a45', '#ff4d4f', '#52c41a', '#722ed1', '#faad14', '#13c2c2']
    font_path = r'C:\Windows\Fonts\msyh.ttc'
    font = ImageFont.truetype(font_path, 17) if os.path.exists(font_path) else ImageFont.load_default()

    # 每类尽量挑一张，补足 count
    chosen, used = [], set()
    for cid in range(len(classes)):
        for lbl in sorted((DATA / 'labels' / 'test').glob('*.txt')):
            lines = [l for l in lbl.read_text(encoding='utf-8').splitlines() if l.strip()]
            if not lines:
                continue
            ids = {int(l.split()[0]) for l in lines}
            img = DATA / 'images' / 'test' / (lbl.stem + '.jpg')
            if cid in ids and img not in used:
                chosen.append(img)
                used.add(img)
                break
    for img in sorted((DATA / 'images' / 'test').glob('*.jpg')):
        if len(chosen) >= count:
            break
        if img not in used:
            chosen.append(img)
            used.add(img)
    chosen = chosen[:count]

    cell_w, cell_h = 420, 500
    rows = (count + cols - 1) // cols
    canvas = Image.new('RGB', (cols * cell_w, rows * cell_h + 70), 'white')
    d = ImageDraw.Draw(canvas)
    for i, img_path in enumerate(chosen):
        im = Image.open(img_path).convert('RGB').resize((400, 400), Image.LANCZOS)
        dd = ImageDraw.Draw(im)
        lbl = DATA / 'labels' / 'test' / (img_path.stem + '.txt')
        for line in lbl.read_text(encoding='utf-8').splitlines():
            if not line.strip():
                continue
            cid, cx, cy, w, h = line.split()
            cid = int(cid)
            cx, cy, w, h = float(cx), float(cy), float(w), float(h)
            x0, y0 = (cx - w / 2) * 400, (cy - h / 2) * 400
            x1, y1 = (cx + w / 2) * 400, (cy + h / 2) * 400
            color = colors[cid]
            dd.rectangle([x0, y0, x1, y1], outline=color, width=3)
            name = classes[cid][1]
            bbox = dd.textbbox((0, 0), name, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            ty = y0 - th - 6 if y0 - th - 6 > 0 else y0 + 3
            dd.rectangle([x0, ty, x0 + tw + 10, ty + th + 6], fill=color)
            dd.text((x0 + 5, ty + 2), name, font=font, fill='white')
        x = (i % cols) * cell_w + 10
        y = (i // cols) * cell_h + 10
        canvas.paste(im, (x, y))
        cap = ImageFont.truetype(font_path, 15) if os.path.exists(font_path) else font
        d.text((x + 4, y + 408), f'{img_path.stem}（640×640）', font=cap, fill='#6b7c96')

    # 图例
    lx = 20
    ly = rows * cell_h + 20
    legend_font = ImageFont.truetype(font_path, 16) if os.path.exists(font_path) else font
    for cid, (ename, cn) in enumerate(classes):
        d.rectangle([lx, ly, lx + 16, ly + 16], fill=colors[cid])
        d.text((lx + 22, ly - 2), cn, font=legend_font, fill='#1f2d45')
        lx += 22 + d.textlength(cn, font=legend_font) + 28
    canvas.save(FIG / 'dataset_samples.png', quality=95)
    print('saved dataset_samples.png', len(chosen), 'images')


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    fig_package()
    print('saved package_structure.png')
    fig_detect_flow()
    print('saved detect_flow.png')
    fig_sequence_detect()
    print('saved sequence_detect.png')
    fig_sequence_login()
    print('saved sequence_login.png')
    fig_db_schema()
    print('saved db_schema.png')
    fig_class_diagram()
    print('saved class_diagram.png')
    fig_dataset_distribution()
    print('saved dataset_distribution.png')
    fig_boxsize()
    print('saved dataset_boxsize.png')
    fig_dataset_samples()
    print('done')


if __name__ == '__main__':
    main()
