# -*- coding: utf-8 -*-
"""生成《概要设计说明书.docx》（课程设计第 7-10 周交付物）。

配图由 generate_w710_figures.py 生成于 figures/ 目录。
本脚本使用 python-docx 排版，输出《概要设计说明书.docx》。
"""
import os

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIG = lambda name: os.path.join(BASE_DIR, 'figures', name)

BODY_EAST = '宋体'
HEAD_EAST = '黑体'
ASCII_FONT = 'Times New Roman'


# ---------------------------------------------------------------- 排版工具
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
    # 打开文档时让 Word 自动更新目录域
    uf = OxmlElement('w:updateFields')
    uf.set(qn('w:val'), 'true')
    doc.settings.element.append(uf)
    return doc


def add_cover(doc, doc_name):
    for _ in range(5):
        doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('基于YOLOv8的手机屏幕外观缺陷\n智能检测系统'); r.font.size = Pt(22); r.font.bold = True; set_run_font(r)
    for _ in range(2):
        doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(doc_name); r.font.size = Pt(26); r.font.bold = True; set_run_font(r)
    for _ in range(4):
        doc.add_paragraph()
    info = ['院    系：人工智能学院', '专    业：信息工程', '班    级：2025219106',
            '成    员：王周毅　林城于', '日    期：2026 年 11 月 4 日']
    for line in info:
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(line); r.font.size = Pt(14); set_run_font(r)
        p.paragraph_format.space_after = Pt(10)
    doc.add_page_break()


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
    doc.add_page_break()


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
    return p


def shade_cell(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear'); shd.set(qn('w:fill'), fill)
    tcPr.append(shd)


def _set_table_fixed_layout(table, widths_cm):
    """强制固定列宽：设置 tblW、tblLayout、tblGrid，避免各列被拉成等宽。"""
    tbl = table._tbl
    tblPr = tbl.tblPr

    # 表格总宽 = 各列之和（单位 twip，1cm = 567 twip）
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
        cols = grid.findall(qn('w:gridCol'))
        for col, w in zip(cols, widths_cm):
            col.set(qn('w:w'), str(int(w * 567)))


def _mark_row_flags(table):
    """表头跨页重复、行内容不跨页拆分。"""
    for i, row in enumerate(table.rows):
        trPr = row._tr.get_or_add_trPr()
        cant = OxmlElement('w:cantSplit')
        trPr.append(cant)
        if i == 0:
            th = OxmlElement('w:tblHeader')
            trPr.append(th)


def add_table(doc, headers, rows, widths=None, font_size=10.5, center_cols=()):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, htxt in enumerate(headers):
        c = t.rows[0].cells[i]
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = c.paragraphs[0].add_run(htxt)
        r.font.bold = True; r.font.size = Pt(font_size); set_run_font(r)
        shade_cell(c, 'D9D9D9')
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            p0 = cells[i].paragraphs[0]
            if i in center_cols:
                p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p0.add_run(str(val))
            r.font.size = Pt(font_size); set_run_font(r)
    if widths:
        t.autofit = False
        for i, w in enumerate(widths):
            t.columns[i].width = Cm(w)          # 同步 tblGrid
            for row in t.rows:
                row.cells[i].width = Cm(w)      # 同步每个单元格 tcW
        _set_table_fixed_layout(t, widths)
    _mark_row_flags(t)
    doc.add_paragraph()
    return t


def add_figure(doc, img_path, caption, width_cm=15.0):
    # 让图前的说明文字跟随图片，避免图被单独甩到下一页
    if doc.paragraphs:
        doc.paragraphs[-1].paragraph_format.keep_with_next = True
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True   # 图和图题不分页
    run = p.add_run()
    run.add_picture(img_path, width=Cm(width_cm))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = cap.add_run(caption)
    r.font.size = Pt(9); r.font.bold = True; set_run_font(r)
    cap.paragraph_format.space_after = Pt(8)
    return cap


# ================================================================ 正文
def build():
    doc = init_document()
    cp = doc.core_properties
    cp.title = '基于YOLOv8的手机屏幕外观缺陷智能检测系统——概要设计说明书'
    cp.author = '王周毅、林城于'
    add_cover(doc, '概要设计说明书')
    h1(doc, '目录')
    add_toc(doc)

    # ------------------------------------------------------------ 1 引言
    h1(doc, '1 引言')
    h2(doc, '1.1 编写目的')
    body(doc, '这份文档是课程设计第 7–10 周（设计阶段）的交付物。第 5–6 周我们已经写了'
              '需求分析和可行性分析，知道了系统要做什么；这次要把系统整体怎么搭、'
              '分成哪几块、数据怎么存、接口怎么定、模型怎么选、页面长什么样、'
              '后面几周怎么安排先想清楚，作为第 11–14 周写代码的依据。')
    body(doc, '文档的读者是指老师和小组的两位同学。')
    h2(doc, '1.2 项目背景与范围')
    body(doc, '手机屏幕上的划痕、裂纹、亮点、污渍这些外观缺陷，现在主要靠人眼看，'
              '速度慢、容易看漏，标准也不完全一致。我们想用 YOLOv8 目标检测模型做一个网页系统，'
              '实现“上传图片 → 自动检测 → 显示结果 → 查看记录”的功能。')
    body(doc, '本文档只写设计层面的内容，具体代码、类和方法放到第 11–14 周的《详细设计说明书》；'
              '系统需要实现哪些功能，见第 5–6 周的《需求分析说明书》。')
    h2(doc, '1.3 术语定义')
    add_table(doc,
              ['术语', '说明'],
              [['YOLOv8', '一种目标检测算法，能在一张图里找出目标的位置并判断类别'],
               ['目标检测', '在图片中把目标框出来，并识别它是什么'],
               ['标注', '人工在图片上画框、选类别，作为训练数据'],
               ['置信度', '模型对自己判断的把握程度，0 到 1 之间，越大越有把握'],
               ['mAP50', '衡量检测精度的指标，数值越大说明检测越准'],
               ['B/S 架构', '浏览器和服务器结构，用户用浏览器就能访问，不用装客户端'],
               ['接口（API）', '后台提供给网页调用的功能地址，比如登录、检测'],
               ['SQLite', '一种小型数据库，整个库就是一个文件，不用单独安装'],
               ['训练集/验证集/测试集', '训练用的图片、训练中检查效果的图片、最后考试用的图片'],
               ['token', '登录成功后服务器发的凭证，之后请求带上它表示已经登录']],
              widths=[3.6, 10.6], center_cols=(0,))
    h2(doc, '1.4 参考资料')
    bullet(doc, '《需求分析说明书》《可行性分析报告》（我们组第 5–6 周的文档）')
    bullet(doc, 'Ultralytics YOLOv8 官方文档：https://docs.ultralytics.com')
    bullet(doc, 'Flask 官方文档：https://flask.palletsprojects.com')
    bullet(doc, 'SQLite 官方文档：https://www.sqlite.org')

    # ------------------------------------------------------------ 2 总体设计
    h1(doc, '2 总体设计')
    h2(doc, '2.1 设计思路')
    body(doc, '整个系统可以用一句话概括：用户打开网页上传一张手机屏幕照片，'
              '网页把图片发给后台；后台调用训练好的 YOLOv8 模型检测缺陷，'
              '把缺陷用方框标出来；再把结果返回给网页显示，同时把这次检测记录存进数据库，'
              '之后可以在历史记录里查看，也可以在统计页看各缺陷的数量。')
    body(doc, '系统分成三部分：网页（前端）、后台程序（Flask）、模型和数据库。'
              '网页负责显示和操作，后台负责处理请求和调用模型，数据库负责存数据。'
              '这样分工的好处是每一块都能单独改、单独调，出了问题也好找。')
    h2(doc, '2.2 系统总体架构')
    body(doc, '系统总体结构如图 2-1 所示，从下往上分三层：展示层、业务层、数据层，'
              '检测模块放在业务层里，由后台程序调用。')
    add_figure(doc, FIG('fig_architecture.png'), '图2-1 系统总体架构图', 15.0)
    body(doc, '各层具体做什么：')
    add_table(doc,
              ['层次', '由什么组成', '主要做什么'],
              [['展示层', '浏览器里的网页（HTML/CSS/JavaScript）', '登录、上传图片、显示检测结果、查看历史和统计'],
               ['业务层', 'Flask 后台程序 + 检测模块', '接收网页请求，调用模型检测图片，读写数据库，把结果返回给网页'],
               ['数据层', 'SQLite 数据库、图片文件夹、模型文件', '保存用户、检测记录、缺陷明细和参数；保存原图、结果图和训练好的模型']],
              widths=[2.4, 5.4, 7.0], center_cols=(0,))
    h2(doc, '2.3 技术栈选择')
    body(doc, '技术选型的原则是：免费开源、容易上手、和 Python 能配合。具体选择见下表。')
    add_table(doc,
              ['类别', '选用的技术', '为什么选它'],
              [['网页', 'HTML + CSS + JavaScript，Bootstrap 做样式', '浏览器直接打开就能用，不用装环境；Bootstrap 有现成的上传、表格样式，省时间'],
               ['统计图', 'ECharts', '画柱状图、饼图很方便，几行代码就能显示'],
               ['后台', 'Python + Flask', '语法简单、教程多，和 YOLOv8 都是 Python，在同一个程序里就能调用模型'],
               ['算法', 'ultralytics 的 YOLOv8', '官方把训练和预测都封装好了，一条命令就能用'],
               ['数据库', 'SQLite', 'Python 自带，不用安装数据库软件，整个库就是一个文件'],
               ['标注', 'LabelImg', '点鼠标画框、选类别，可以导出 YOLO 格式的标注文件'],
               ['开发工具', 'VS Code 或 PyCharm', '写代码和调试都方便']],
              widths=[2.2, 5.2, 7.6], center_cols=(0,))
    h2(doc, '2.4 运行方式')
    body(doc, '开发和使用都在本机进行：装好 Python 和依赖后运行 python app.py，'
              '浏览器打开 http://127.0.0.1:5000 就能使用。演示时用同一台笔记本电脑，'
              '模型文件和图片都放在本地，不联网也能跑。数据库就是项目目录下的 data.db 文件，'
              '复制走就能换一台电脑继续用。')

    # ------------------------------------------------------------ 3 模块划分
    h1(doc, '3 模块划分与功能描述')
    h2(doc, '3.1 模块划分')
    body(doc, '按功能把系统分成 5 个模块，如图 3-1 所示。每个模块负责一块相对独立的事情，'
              '模块之间通过接口或者函数调用配合。')
    add_figure(doc, FIG('fig_modules.png'), '图3-1 系统模块划分图', 15.0)
    add_table(doc,
              ['模块', '负责的内容', '大概怎么做'],
              [['网页模块', '5 个页面和页面之间的跳转', 'HTML/CSS/JavaScript，用 Bootstrap 做样式'],
               ['后台接口模块', '接收网页请求，处理登录、上传、检测、查询', '用 Flask 写路由，返回 JSON'],
               ['检测模块', '加载模型、预处理图片、推理、画框', '用 ultralytics 和 OpenCV'],
               ['数据标注与数据集模块', '准备训练用的图片和标注', 'LabelImg 标注，写脚本划分和增强'],
               ['数据库模块', '建表、保存记录、查询记录', 'Python 自带的 sqlite3 操作数据库']],
              widths=[3.6, 5.6, 6.0], center_cols=(0,))
    h2(doc, '3.2 网页模块')
    body(doc, '网页模块一共 5 个页面：')
    bullet(doc, '登录页：输入用户名和密码登录，没登录不能进别的页面；')
    bullet(doc, '检测页：选图片或把图片拖进来，显示缩略图，点“开始检测”；')
    bullet(doc, '结果页：左边看画了框的结果图，右边是缺陷列表，可以下载结果图；')
    bullet(doc, '历史记录页：按时间查以前的检测记录，可以看详情、删除；')
    bullet(doc, '统计页：看一共检测了多少张、各类缺陷分别有多少，用柱状图显示。')
    body(doc, '页面之间用链接跳转，数据通过 fetch 向后台请求，拿到结果后用 JavaScript 显示在页面上。')
    h2(doc, '3.3 后台接口模块')
    body(doc, '用 Flask 写，每个功能对应一个接口地址，比如 /api/login、/api/detect、/api/records。'
              '网页发请求过来，后台处理完返回 JSON 数据。登录后会给网页一个 token，'
              '后面请求都带上它，后台根据 token 判断是谁在操作。')
    h2(doc, '3.4 检测模块')
    body(doc, '检测模块是整个系统的核心，输入一张图片，输出缺陷的位置、类别、置信度和画好框的结果图。'
              '它主要做四件事：')
    bullet(doc, '加载模型：程序启动时用 YOLO("models/best.pt") 把模型加载好，后面直接使用，不用每次都加载；')
    bullet(doc, '预处理：把图片按比例缩放到 640×640，不够的地方补灰边，再把像素值除以 255；')
    bullet(doc, '推理：把图片交给模型，得到所有预测框、类别和置信度；')
    bullet(doc, '后处理：把置信度太低的框去掉，把重叠的框合并（NMS），再把坐标换算回原图大小，'
                '用 OpenCV 把框和类别文字画到图上，保存成结果图。')
    body(doc, '如果图片打不开或者模型文件不存在，就返回错误提示，不能让整个程序崩溃。检测流程如图 3-2 所示。')
    add_figure(doc, FIG('fig_flow.png'), '图3-2 单张图片检测流程示意图', 15.5)
    h2(doc, '3.5 数据标注与数据集模块')
    body(doc, '这个模块在训练模型之前用，主要是准备数据：')
    bullet(doc, '收集图片：从网上找手机屏幕的照片，再自己用手机拍一些有缺陷的屏幕，尽量每类缺陷都有；')
    bullet(doc, '标注：用 LabelImg 打开图片，画框、选类别，导出 YOLO 格式的 txt 文件，'
                '每行是“类别编号 中心x 中心y 宽 高”，坐标都是 0 到 1 的比例；')
    bullet(doc, '划分：按 8:1:1 分成训练集、验证集、测试集，再写一个 data.yaml 说明类别和路径；')
    bullet(doc, '数据增强：训练时打开翻转、亮度变化、加噪声、Mosaic 拼接这些增强（ultralytics 自带参数），'
                '相当于把图片变多，防止过拟合。')
    h2(doc, '3.6 数据库模块')
    body(doc, '用 Python 自带的 sqlite3 模块操作数据库，不引入别的框架。写一个 db.py 统一负责建表、'
              '插入记录、查询记录和删除记录，其他代码需要存数据时调用它就行。'
              '图片只存相对路径（比如 images/20261104_001.jpg），这样换电脑也能找到。')
    h2(doc, '3.7 模块之间怎么配合')
    body(doc, '一次完整的检测过程如下：')
    body(doc, '1）用户在检测页选一张图片，网页把文件发到后台的检测接口；')
    body(doc, '2）后台先把原图保存到 images 文件夹，然后调用检测模块；')
    body(doc, '3）检测模块加载模型、推理、画框，把结果图存到 results 文件夹；')
    body(doc, '4）后台把缺陷类别、置信度、坐标和图片路径写进数据库，返回 JSON 给网页；')
    body(doc, '5）网页跳到结果页，显示出带框的图片和缺陷列表。')

    # ------------------------------------------------------------ 4 数据库设计
    h1(doc, '4 数据库设计')
    h2(doc, '4.1 设计说明')
    body(doc, '数据库用 SQLite，就是一个 data.db 文件，不用单独安装数据库软件。'
              '一共设计 4 张表：用户表、检测记录表、缺陷明细表、系统参数表。'
              '每张表的主键都是自动增加的 id，记录之间用 user_id、record_id 关联。')
    h2(doc, '4.2 ER 图')
    add_figure(doc, FIG('fig_er.png'), '图4-1 数据库 ER 图', 14.5)
    body(doc, '从图 4-1 可以看到：一个用户可以有多条检测记录，一条检测记录可以查出多个缺陷，'
              '所以是“用户 1 对多 检测记录”“检测记录 1 对多 缺陷明细”两个关系。')
    h2(doc, '4.3 表结构')
    h3(doc, '4.3.1 用户表 t_user')
    add_table(doc,
              ['字段名', '类型', '说明'],
              [['id', 'INTEGER', '主键，自动增加'],
               ['username', 'TEXT', '用户名，不能重复'],
               ['password', 'TEXT', '密码，存加密后的值，不存明文'],
               ['role', 'TEXT', '角色：user 是普通用户，admin 是管理员'],
               ['created_at', 'TEXT', '注册时间']],
              widths=[3.4, 2.6, 8.0], center_cols=(0,))
    h3(doc, '4.3.2 检测记录表 t_record')
    add_table(doc,
              ['字段名', '类型', '说明'],
              [['id', 'INTEGER', '主键，自动增加'],
               ['user_id', 'INTEGER', '是谁检测的，对应 t_user.id'],
               ['image_path', 'TEXT', '原图路径'],
               ['result_path', 'TEXT', '结果图路径'],
               ['total', 'INTEGER', '这次检出几个缺陷'],
               ['status', 'TEXT', '成功 done，失败 failed'],
               ['conf', 'REAL', '这次用的置信度阈值'],
               ['created_at', 'TEXT', '检测时间']],
              widths=[3.4, 2.6, 8.0], center_cols=(0,))
    h3(doc, '4.3.3 缺陷明细表 t_defect')
    add_table(doc,
              ['字段名', '类型', '说明'],
              [['id', 'INTEGER', '主键，自动增加'],
               ['record_id', 'INTEGER', '属于哪条检测记录，对应 t_record.id'],
               ['class_id', 'INTEGER', '缺陷类别编号，0 到 5'],
               ['class_name', 'TEXT', '缺陷类别名称，比如 scratch（划痕）'],
               ['conf', 'REAL', '置信度，0 到 1'],
               ['x, y', 'REAL', '框中心点的横纵坐标，0 到 1 的比例'],
               ['w, h', 'REAL', '框的宽和高，0 到 1 的比例']],
              widths=[3.4, 2.6, 8.0], center_cols=(0,))
    h3(doc, '4.3.4 系统参数表 t_config')
    add_table(doc,
              ['字段名', '类型', '说明'],
              [['id', 'INTEGER', '主键，自动增加'],
               ['name', 'TEXT', '参数名，比如 conf_threshold'],
               ['value', 'TEXT', '参数值，比如 0.25']],
              widths=[3.4, 2.6, 8.0], center_cols=(0,))
    h2(doc, '4.4 其他说明')
    bullet(doc, '用户名加唯一约束，避免注册重复；')
    bullet(doc, '检测记录经常按时间倒序查，给 created_at 建一个索引；')
    bullet(doc, 'SQLite 默认不检查外键，删除检测记录时要在代码里把对应的缺陷明细一起删掉，不能留下孤儿数据；')
    bullet(doc, '备份很简单，把 data.db 文件复制一份就行。')

    # ------------------------------------------------------------ 5 接口设计
    h1(doc, '5 接口设计')
    h2(doc, '5.1 接口约定')
    bullet(doc, '网页和后台之间用 HTTP 传数据，普通请求用 JSON 格式，上传图片用 multipart/form-data；')
    bullet(doc, '登录成功后后台返回一个 token，之后的请求放在请求头里带上，表示已经登录；')
    bullet(doc, '返回格式统一用 {"code": 200, "message": "ok", "data": {...}}，'
                'code 是状态码，message 是提示信息，data 是实际数据。')
    h2(doc, '5.2 接口列表')
    add_table(doc,
              ['请求方式', '地址', '作用', '谁能用'],
              [['POST', '/api/login', '登录', '所有人'],
               ['POST', '/api/upload', '上传图片（可选）', '登录用户'],
               ['POST', '/api/detect', '检测图片', '登录用户'],
               ['GET', '/api/records', '查询历史记录（分页）', '登录用户'],
               ['GET', '/api/records/<id>', '查看一次检测的详情', '登录用户'],
               ['DELETE', '/api/records/<id>', '删除一条记录', '登录用户'],
               ['GET', '/api/stats', '按类别统计缺陷数量', '登录用户'],
               ['GET/PUT', '/api/settings', '查看或修改置信度阈值', '管理员']],
              widths=[2.4, 5.0, 5.6, 2.4], center_cols=(0, 1, 3))
    h2(doc, '5.3 主要接口说明')
    h3(doc, '5.3.1 登录 POST /api/login')
    body(doc, '请求参数：username（用户名）、password（密码）。'
              '返回：token 和角色。例如请求 {"username": "admin", "password": "123456"}，'
              '返回 {"code": 200, "data": {"token": "abc123", "role": "admin"}}。'
              '密码不对返回 code 400，提示“用户名或密码错误”。')
    h3(doc, '5.3.2 上传图片 POST /api/upload')
    body(doc, '请求：用 form-data 传一张图片，字段名 file。'
              '后台检查扩展名是不是 jpg/png/bmp/webp、大小是不是不超过 20MB，'
              '通过后存到 images 文件夹。返回文件编号和相对路径。')
    h3(doc, '5.3.3 检测 POST /api/detect')
    body(doc, '请求参数：图片文件，或者已经上传的图片路径，加上可选的置信度阈值 conf（默认 0.25）。'
              '后台调用检测模块，返回这次检出的缺陷列表和结果图地址。例如：')
    body(doc, '{"code": 200, "data": {"record_id": 1, "total": 3, '
              '"result_image": "results/20261104_001.jpg", '
              '"defects": [{"class_id": 0, "class_name": "scratch", "conf": 0.92, '
              '"x": 0.31, "y": 0.45, "w": 0.12, "h": 0.08}]}}')
    h3(doc, '5.3.4 查询历史 GET /api/records')
    body(doc, '参数：page（第几页）、size（每页几条）、start 和 end（时间范围，可选）。'
              '返回总条数和当前页的记录列表，按检测时间从新到旧排序。')
    h3(doc, '5.3.5 查看详情 GET /api/records/<id>')
    body(doc, '返回这条记录的原图、结果图、参数和缺陷明细列表。记录不存在时返回 404。')
    h3(doc, '5.3.6 删除记录 DELETE /api/records/<id>')
    body(doc, '把这个记录的数据库数据和对应的缺陷明细一起删掉，同时删掉原图和结果图文件。'
              '记录不存在时返回 404。')
    h3(doc, '5.3.7 统计 GET /api/stats')
    body(doc, '参数：start 和 end（时间范围，可选）。返回每类缺陷的数量，'
              '比如 [{"class_name": "scratch", "count": 168}, …]，网页用 ECharts 画柱状图。')
    h3(doc, '5.3.8 参数设置 GET/PUT /api/settings')
    body(doc, 'GET 返回当前的置信度阈值和模型名称；PUT（仅管理员）修改并保存到数据库。'
              '阈值不在 0 到 1 之间时返回 400。')
    h2(doc, '5.4 出错时返回什么')
    add_table(doc,
              ['情况', 'code', '提示信息'],
              [['没登录或 token 过期', '401', '请先登录'],
               ['参数不对（比如阈值超范围）', '400', '参数错误'],
               ['记录不存在', '404', '记录不存在'],
               ['图片太大或格式不支持', '413', '图片格式不对或超过 20MB'],
               ['服务器或模型出错', '500', '服务器出错，请稍后再试']],
              widths=[6.0, 2.4, 7.0], center_cols=(1,))

    # ------------------------------------------------------------ 6 算法方案
    h1(doc, '6 算法方案设计')
    h2(doc, '6.1 为什么选 YOLOv8')
    body(doc, 'YOLOv8 是 Ultralytics 公司开源的算法，能一次找出图里所有目标的位置和类别，'
              '速度快、精度也不错。官方把训练、预测、导出都封装好了，'
              '用起来只要几行代码，适合我们在课程设计里用。'
              '我们的任务就是“在一张屏幕照片里找出缺陷并画框”，正好是目标检测要做的事。')
    h2(doc, '6.2 模型大小怎么选')
    body(doc, 'YOLOv8 有 n、s、m、l、x 几种大小，模型越大精度越高，但训练和推理越慢。'
              '我们主要考虑自己的电脑有没有显卡，对比如下：')
    add_table(doc,
              ['模型', '大小（参数量）', '速度', '适合的情况'],
              [['yolov8n', '约 3M', '最快', '没有显卡，先用它把整个流程跑通'],
               ['yolov8s', '约 11M', '快', '有显卡时用，精度比 n 好一些'],
               ['yolov8m', '约 26M', '中等', '数据比较多、显卡也够用时可以试']],
              widths=[2.6, 3.4, 2.6, 6.8], center_cols=(0, 1, 2))
    body(doc, '我们的做法是：先在普通电脑上用 yolov8n 把“标注 → 训练 → 检测”整条流程跑通，'
              '如果效果不够好、又有显卡，再换成 yolov8s 训练。')
    h2(doc, '6.3 输入尺寸与预处理')
    body(doc, '输入图片统一缩放到 640×640。缩放时保持长宽比，短边补成灰色，这样图片不会变形；'
              '再把像素值除以 255，变成 0 到 1 之间的小数，模型处理起来更稳定。'
              '检测出来的框坐标是按 640 算的，要按缩放比例换回原图的大小，不然画框会偏。')
    h2(doc, '6.4 用预训练权重再训练')
    body(doc, '我们自己的图片只有几百到上千张，如果从头训练，模型学不到什么规律，效果会很差。'
              '所以先用官方在 COCO 数据集上训练好的权重（yolov8n.pt），'
              '把最后一层改成我们的 6 类缺陷，再用自己的图片继续训练，这叫迁移学习或者微调。'
              '这样需要的图片少很多，训练也更快。')
    h2(doc, '6.5 训练参数')
    add_table(doc,
              ['参数', '取值', '说明'],
              [['epochs', '100', '训练 100 轮，验证集不提升就提前停止'],
               ['batch', '8 或 16', '每次喂几张图，显卡小用 8，显卡大用 16'],
               ['imgsz', '640', '图片输入大小'],
               ['学习率', '0.01', '每轮更新模型的幅度'],
               ['优化器', 'AdamW', '训练时更新参数的方法'],
               ['数据增强', '翻转、亮度、噪声、Mosaic', '练习用参数，相当于把图片变多']],
              widths=[2.6, 5.2, 7.2], center_cols=(0,))
    h2(doc, '6.6 怎么判断训练得好不好')
    body(doc, '训练完在验证集上看 Precision（查准率）、Recall（查全率）和 mAP50 三个指标。'
              '我们给自己定的目标是 mAP50 达到 0.85 左右。'
              '如果达不到，先检查图片和标注有没有问题，再加图片、调数据增强、把输入尺寸调大，'
              '还不行就换大一点的模型或者改学习率。')
    h2(doc, '6.7 训练好的模型怎么用')
    body(doc, '训练完会得到一个 best.pt 文件，把它放到项目的 models 文件夹。'
              '程序里用 YOLO("models/best.pt") 加载，然后就能预测了。'
              '以后想换模型，只要把文件替换掉就行，不用改代码。')

    # ------------------------------------------------------------ 7 UI 设计
    h1(doc, '7 UI 界面设计')
    h2(doc, '7.1 整体风格')
    body(doc, '界面用 Bootstrap 做成常见的后台管理风格：左边一列菜单，右边是内容区，'
              '主色调是蓝色，看起来干净清楚。操作尽量简单，用户按“上传 → 检测 → 看结果”三步就能完成。'
              '按钮和提示都用中文，做错了要给出明确的提示。')
    h2(doc, '7.2 登录页')
    add_figure(doc, FIG('fig_ui_login.png'), '图7-1 登录页原型图', 12.5)
    body(doc, '页面中间一个登录框，输入用户名和密码，点“登录”。密码错了提示“用户名或密码错误”；'
              '没登录直接打开别的页面会自动回到登录页。')
    h2(doc, '7.3 检测页')
    add_figure(doc, FIG('fig_ui_detect.png'), '图7-2 检测页原型图', 12.5)
    body(doc, '上面是上传区，可以点“选择图片”或直接拖进来，选好后显示缩略图。'
              '下面可以调整置信度阈值（默认 0.25）。点“开始检测”后显示“检测中…”，'
              '检测完自动跳到结果页。一次可以传多张图片，排队处理。')
    h2(doc, '7.4 结果页')
    add_figure(doc, FIG('fig_ui_result.png'), '图7-3 结果页原型图', 12.5)
    body(doc, '左边显示画了框的结果图，右边是缺陷列表，列出序号、类别、置信度和坐标。'
              '下面有“下载结果图”和“导出 CSV”两个按钮。如果没查出缺陷，就显示“未发现缺陷”。')
    h2(doc, '7.5 历史记录页')
    add_figure(doc, FIG('fig_ui_history.png'), '图7-4 历史记录页原型图', 12.5)
    body(doc, '上面是筛选条件（时间范围、有没有缺陷），下面是记录表格，显示时间、图片、缺陷数和操作。'
              '可以点“查看”看详情，点“删除”删掉记录。记录多了分页显示。')
    h2(doc, '7.6 数据统计页')
    add_figure(doc, FIG('fig_ui_stats.png'), '图7-5 数据统计页原型图', 12.5)
    body(doc, '上面是 4 个数字卡片（检测总数、缺陷总数、今日检测、平均耗时），'
              '下面左边是柱状图，显示每类缺陷有多少，右边是各类占比。可以按时间范围筛选。')
    h2(doc, '7.7 页面跳转关系')
    body(doc, '登录页 → 检测页 → 结果页；检测页和结果页可以回到历史记录页；'
              '检测页、历史页都能进入统计页。')

    # ------------------------------------------------------------ 8 进度安排
    h1(doc, '8 进度安排')
    h2(doc, '8.1 分周任务')
    add_table(doc,
              ['周次', '要完成的事', '本周产出'],
              [['第 7 周', '确定总体架构、划分模块、选好技术栈', '架构图、模块划分表'],
               ['第 8 周', '设计数据库表、设计接口', 'ER 图、表结构、接口表'],
               ['第 9 周', '画页面原型图、细化算法方案', '5 张页面原型图、模型选型'],
               ['第 10 周', '写概要设计文档、修改完善、提交', '这份概要设计说明书']],
              widths=[1.8, 7.0, 5.4], center_cols=(0,))
    h2(doc, '8.2 甘特图')
    add_figure(doc, FIG('fig_gantt.png'), '图8-1 设计阶段进度甘特图', 15.0)
    h2(doc, '8.3 里程碑')
    add_table(doc,
              ['时间', '事情', '完成标志'],
              [['第 7 周末', '架构和模块定下来', '小组讨论通过'],
               ['第 9 周末', '页面原型和算法方案定稿', '小组内部确认一遍'],
               ['第 10 周末', '概要设计说明书提交', '交给老师'],
               ['第 11 周开始', '进入实现阶段', '按这份文档写详细设计、开始写代码']],
              widths=[2.6, 6.8, 5.0], center_cols=(0,))
    h2(doc, '8.4 可能遇到的问题和打算')
    add_table(doc,
              ['可能遇到的问题', '我们打算这么办'],
              [['图片不够，某些缺陷类别太少', '先用现有的图片把流程跑通，再慢慢补图片，训练时开数据增强'],
               ['没有显卡，训练很慢', '先用 yolov8n 小模型在 CPU 上训练，或者用 Colab 的免费显卡'],
               ['训练出来效果不好', '先看是漏检还是误检，再按 6.6 节的顺序调：查标注、加图片、调参数、换模型'],
               ['进度紧，来不及做完', '先做核心功能（上传、检测、结果展示），统计、参数设置这些放到后面']],
              widths=[5.6, 9.0])

    # ------------------------------------------------------------ 9 环境说明
    h1(doc, '9 软硬件环境说明')
    h2(doc, '9.1 开发环境')
    add_table(doc,
              ['项目', '要求'],
              [['操作系统', 'Windows 10/11（或者 Ubuntu）'],
               ['Python', '3.9 及以上'],
               ['主要 Python 库', 'torch、ultralytics、flask、opencv-python、numpy'],
               ['编辑器', 'VS Code 或 PyCharm'],
               ['浏览器', 'Chrome 或 Edge']],
              widths=[4.0, 10.2], center_cols=(0,))
    h2(doc, '9.2 运行环境')
    add_table(doc,
              ['项目', '要求'],
              [['电脑', '普通笔记本就可以，内存 8GB 以上'],
               ['显卡', '没有显卡也能用，CPU 推理一张图大概几秒；有显卡会快很多'],
               ['浏览器', 'Chrome 或 Edge，不用装插件'],
               ['网络', '不用联网，模型和图片都在本地']],
              widths=[3.4, 10.8], center_cols=(0,))
    h2(doc, '9.3 其他说明')
    bullet(doc, '训练好的模型文件 best.pt 大概几十 MB，放在项目的 models 文件夹；')
    bullet(doc, '数据集和模型比较大，不放进代码仓库，本地保存就行；')
    bullet(doc, '演示的时候按顺序讲：登录 → 上传图片 → 检测 → 看结果 → 查历史 → 看统计。')

    # ------------------------------------------------------------ 结语
    h1(doc, '10 结束语')
    body(doc, '这份概要设计说明书完成了第 7–10 周的任务：确定了系统的总体架构和技术栈，'
              '把系统分成 5 个模块，设计了 4 张数据库表和主要接口，'
              '选定了 YOLOv8 算法方案，画了 5 个页面的原型图，也排好了后面几周的进度。'
              '第 11–14 周我们会按照这份设计写《详细设计说明书》，并开始写代码、训练模型。')

    out = os.path.join(BASE_DIR, '概要设计说明书.docx')
    doc.save(out)
    print('OK:', out)


if __name__ == '__main__':
    build()
