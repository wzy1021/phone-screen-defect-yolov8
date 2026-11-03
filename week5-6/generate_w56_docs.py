# -*- coding: utf-8 -*-
"""生成《需求分析说明书》与《可行性分析报告》两门Word文档（课程设计第5-6周交付物）。"""
import datetime
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

BODY_EAST = '宋体'
HEAD_EAST = '黑体'
ASCII_FONT = 'Times New Roman'

# ---------------------------------------------------------------- 基础工具
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
    # 页面设置 A4
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.top_margin = sec.bottom_margin = Cm(2.54)
    sec.left_margin, sec.right_margin = Cm(3.0), Cm(2.6)
    # 正文样式
    normal = doc.styles['Normal']
    normal.font.name = ASCII_FONT
    normal.font.size = Pt(12)
    set_style_east(normal, BODY_EAST)
    pf = normal.paragraph_format
    pf.line_spacing = 1.5
    pf.space_after = Pt(3)
    # 标题样式（黑色、黑体）
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
    # 页脚页码
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
            '成    员：王周毅　林城于', '学    号：＿＿＿＿＿＿＿＿',
            '指导教师：无', '日    期：20＿＿ 年 ＿＿ 月 ＿＿ 日']
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
    t = OxmlElement('w:t'); t.text = '（请在 Word 中右键此处，选择“更新域”以自动生成目录）'
    f3 = OxmlElement('w:fldChar'); f3.set(qn('w:fldCharType'), 'end')
    run._r.append(f1); run._r.append(it); run._r.append(f2); run._r.append(t); run._r.append(f3)
    doc.add_page_break()

def h1(doc, text):
    doc.add_paragraph(text, style='Heading 1')

def h2(doc, text):
    doc.add_paragraph(text, style='Heading 2')

def h3(doc, text):
    doc.add_paragraph(text, style='Heading 3')

def body(doc, text, indent=True, bold=False):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.bold = bold
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
            for row in t.rows:
                row.cells[i].width = Cm(w)
    doc.add_paragraph()
    return t

# ================================================================ 需求分析说明书
def build_requirements():
    doc = init_document()
    cp = doc.core_properties
    cp.title = '基于YOLOv8的手机屏幕外观缺陷智能检测系统——需求分析说明书'
    cp.author = '王周毅、林城于'
    add_cover(doc, '需求分析说明书')
    h1(doc, '目录')
    add_toc(doc)

    h1(doc, '1 引言')
    h2(doc, '1.1 编写目的')
    body(doc, '本说明书是《基于YOLOv8的手机屏幕外观缺陷智能检测系统》课程设计的阶段性交付文档，'
              '在第 5–6 周“分析阶段”编写。其目的是以用户和系统的视角全面、准确地描述本系统应具备的功能、'
              '性能与约束，明确“系统做什么”，作为后续概要设计、详细设计、编码实现、测试与验收的共同依据。'
              '本文档的预期读者包括：课程设计指导教师、项目组成员、系统设计人员、开发人员与测试人员。')
    h2(doc, '1.2 项目背景')
    body(doc, '手机屏幕是手机中表面质量要求最高、最易出现外观缺陷的部件。当前手机生产及检测环节中，'
              '屏幕外观缺陷（划痕、裂纹、亮点、污渍等）的检测主要依赖人工目检，存在效率低、漏检率高、'
              '判定标准因人而异、长时间工作易疲劳等突出问题。')
    body(doc, '随着深度学习与目标检测技术的发展，YOLO 系列算法已能在保证实时性的同时取得较高的检测精度。'
              '本项目拟采用 YOLOv8 目标检测算法，训练可识别屏幕缺陷类别的检测模型，并构建 B/S 架构的 Web 应用，'
              '实现“上传图像—自动检测—结果可视化—记录管理”的完整业务流程，为手机屏幕外观质量检验提供智能化辅助手段。')
    h2(doc, '1.3 术语定义')
    add_table(doc,
              ['术语/缩写', '含义'],
              [['YOLOv8', 'Ultralytics 公司发布的最新一代 YOLO 目标检测算法，支持检测、分割、分类等任务'],
               ['目标检测', '在图像中定位目标位置（矩形框）并识别其类别的计算机视觉任务'],
               ['缺陷', '本系统特指手机屏幕表面的划痕、裂纹、亮点、暗点、污渍、边缘崩缺等外观瑕疵'],
               ['标注', '人工为图像中的缺陷添加类别标签与位置框的过程，采用 YOLO txt / Pascal VOC 格式'],
               ['推理/预测', '将待检图像输入训练好的模型，输出缺陷类别、位置与置信度的过程'],
               ['mAP50', 'IoU 阈值为 0.5 时的平均精度（mean Average Precision），衡量检测精度的核心指标'],
               ['mAP50-95', 'IoU 阈值从 0.5 到 0.95 的平均 mAP，衡量定位与分类的综合精度'],
               ['置信度', '模型对检测结果可靠程度的估计，介于 0–1 之间'],
               ['B/S 架构', '浏览器/服务器架构，用户通过浏览器访问系统，无需安装客户端'],
               ['API', '应用编程接口，本系统中指前后端之间约定的 HTTP 接口'],
               ['ONNX', '开放神经网络交换格式，用于模型部署与推理加速'],
               ['NMS', '非极大值抑制，用于去除重叠的检测框'],
               ['数据增强', '对训练数据施加旋转、翻转、噪声等变换以扩充样本、提升泛化能力']],
              widths=[4.0, 8.6], center_cols=(0,))
    h2(doc, '1.4 参考资料')
    bullet(doc, '《课程设计任务书》及课程进度安排（第 5–6 周分析阶段）')
    bullet(doc, 'Ultralytics YOLOv8 官方文档：https://docs.ultralytics.com')
    bullet(doc, 'PyTorch 官方文档：https://pytorch.org/docs')
    bullet(doc, '《软件工程》教材中需求分析、用例建模相关章节')
    bullet(doc, 'GB/T 8567-2006《计算机软件文档编制规范》（文档结构参考）')

    h1(doc, '2 项目概述')
    h2(doc, '2.1 项目目标')
    bullet(doc, '训练并评估一个可用的 YOLOv8 手机屏幕缺陷检测模型，支持多类别缺陷的同时检出与定位；')
    bullet(doc, '构建一个 B/S 架构的 Web 系统，实现图像上传、自动检测、结果可视化、历史记录管理与统计；')
    bullet(doc, '系统界面友好、操作简洁，便于课堂演示与课程验收；')
    bullet(doc, '完成需求分析、概要设计、详细设计、测试等全套课程文档，满足课程各阶段进度要求。')
    h2(doc, '2.2 项目范围')
    body(doc, '本项目包含以下内容：用户登录管理、图像上传（单张/批量）、缺陷自动检测、检测结果可视化'
              '（类别、位置框、置信度）、检测记录管理（查询/删除/导出）、检测参数设置（置信度阈值等），'
              '以及可选的缺陷统计数据展示。')
    body(doc, '本项目不包含以下内容：生产线硬件（工业相机、传送带、光源）的采购与集成、与 PLC/MES 等'
              '生产系统的对接、移动端原生 App 开发、多模型自动训练平台。上述内容属于后续工程化扩展方向，'
              '不属于本次课程设计范围。')
    h2(doc, '2.3 用户群体')
    add_table(doc,
              ['用户角色', '说明', '主要操作'],
              [['普通用户（质检员）', '使用系统完成日常屏幕缺陷检测', '上传图像、发起检测、查看结果、下载结果'],
               ['管理员', '系统维护与数据管理', '用户管理、参数配置、记录维护、数据统计']],
              widths=[3.6, 4.6, 4.4], center_cols=(0,))
    h2(doc, '2.4 运行环境')
    add_table(doc,
              ['类别', '环境要求'],
              [['服务端操作系统', 'Windows 10/11 或 Linux（Ubuntu 18.04+）'],
               ['服务端软件', 'Python 3.8+、PyTorch ≥ 2.0、ultralytics、Flask/FastAPI、OpenCV'],
               ['计算资源', 'GPU 可选（训练建议 CUDA 显卡或云算力）；CPU 可完成推理演示'],
               ['客户端', 'Chrome/Edge/Firefox 等现代浏览器，无需安装额外插件'],
               ['数据库', 'SQLite（默认，零配置）或 MySQL 5.7+（可选）']],
              widths=[3.6, 9.0], center_cols=(0,))
    h2(doc, '2.5 假设与约束')
    bullet(doc, '输入图像为手机屏幕的清晰外观照片，分辨率建议不低于 640×640，单张图片大小不超过 20MB；')
    bullet(doc, '同一时间在线用户数按课程演示规模（不大于 10 个并发用户）设计；')
    bullet(doc, '模型权重与系统源码以开源协议使用，仅用于课程学习与科研演示，不涉及商业应用；')
    bullet(doc, '课程周期约束：需在第 11–14 周完成开发，设计上遵循“先做精核心链路、再扩展功能”的原则。')

    h1(doc, '3 功能需求')
    h2(doc, '3.1 功能总览')
    add_table(doc,
              ['编号', '功能模块', '功能点', '优先级'],
              [['FR-01', '用户管理', '登录、登出、密码修改、用户列表（管理员）', '高'],
               ['FR-02', '图像上传', '单张上传、批量上传、图片预览与删除', '高'],
               ['FR-03', '缺陷检测', '模型推理、多缺陷同时检出、置信度输出', '高'],
               ['FR-04', '结果可视化', '原图标注框、类别与置信度显示、结果图下载', '高'],
               ['FR-05', '记录管理', '检测历史查询、详情查看、删除、结果导出', '中'],
               ['FR-06', '参数设置', '置信度阈值、模型文件选择（管理员）', '中'],
               ['FR-07', '数据统计', '按类别缺陷数量统计与图表展示', '低（可选）']],
              widths=[1.6, 2.8, 5.4, 2.8], center_cols=(0, 3))
    h2(doc, '3.2 用例图与用例描述')
    body(doc, '系统参与者包括“普通用户”和“管理员”。主要用例：登录、上传图像、执行检测、查看结果、'
              '查看历史记录、导出结果、设置检测参数、查看统计。')
    add_table(doc,
              ['用例名称', '参与者', '前置条件', '主流程（简化）', '异常流程'],
              [['执行检测', '普通用户', '已登录', '上传图像→点击检测→系统返回标注结果图与缺陷列表',
                '检测失败时提示错误并允许重试'],
               ['查看历史', '普通用户', '已登录且存在记录', '进入历史页→按时间/关键词查询→查看详情',
                '无记录时给出空状态提示'],
               ['设置参数', '管理员', '已登录且为管理员', '进入设置页→修改阈值/模型→保存并即时生效',
                '参数非法时拒绝保存并提示'],
               ['数据统计', '普通用户', '已登录', '进入统计页→选择时间范围→查看各缺陷类别分布',
                '数据不足时显示空图表']],
              widths=[2.2, 1.8, 2.6, 3.6, 2.4], font_size=10)
    h2(doc, '3.3 功能需求详述')
    h3(doc, '3.3.1 用户登录与角色管理（FR-01）')
    body(doc, '输入：用户名、密码。处理：系统校验用户信息，密码以哈希形式存储，登录成功后签发会话；'
              '不同角色拥有不同权限（普通用户可检测与查看记录；管理员额外可管理用户与参数）。'
              '输出：登录成功/失败提示、当前用户角色。异常处理：连续失败 5 次提示稍后再试；'
              '未登录用户访问业务功能时跳转登录页。')
    h3(doc, '3.3.2 图像上传（FR-02）')
    body(doc, '输入：一张或多张屏幕外观图像（支持 jpg/png/bmp/webp）。处理：前端本地预览，'
              '后端校验文件格式与大小，保存至临时目录并生成任务记录。输出：上传成功回执与图片缩略图。'
              '异常处理：格式不支持或超过大小限制时给出明确提示。')
    h3(doc, '3.3.3 缺陷检测（FR-03）')
    body(doc, '处理：服务端加载 YOLOv8 模型，对输入图像执行推理，应用置信度阈值与非极大值抑制（NMS）后处理，'
              '得到缺陷集合（类别、框坐标、置信度）。输出：JSON 检测结果（缺陷数量、各类别明细）。'
              '异常处理：模型文件缺失时提示管理员；推理超时或图像损坏时返回可读错误信息。')
    h3(doc, '3.3.4 结果可视化（FR-04）')
    body(doc, '处理：在原始图像上绘制检测框，不同缺陷类别使用不同颜色区分，标注类别名与置信度数值。'
              '输出：标注结果图（页面展示 + 可下载 PNG）。异常处理：无检测结果时提示“未检出缺陷”。')
    h3(doc, '3.3.5 检测记录管理（FR-05）')
    body(doc, '处理：每次检测自动写入数据库（原图、结果图、缺陷明细、检测时间、检测者）；'
              '支持按时间范围与缺陷是否存在进行查询、单条删除、结果导出（CSV）。输出：记录列表与导出文件。')
    h3(doc, '3.3.6 检测参数设置（FR-06）')
    body(doc, '处理：管理员可调整置信度阈值（默认 0.25）、选择要加载的模型权重版本，修改即时生效并持久化。'
              '输出：参数保存成功提示。')
    h3(doc, '3.3.7 数据统计（FR-07，可选）')
    body(doc, '处理：按检测记录统计各缺陷类别的检出数量与占比，以柱状图/饼图呈现。输出：统计图表。')

    h1(doc, '4 非功能需求')
    h2(doc, '4.1 性能需求')
    add_table(doc,
              ['性能指标', '要求', '说明'],
              [['检测精度', 'mAP50 ≥ 0.85（目标值）', '在自建验证集上评估'],
               ['单张检测耗时', 'GPU ≤ 0.5s；CPU ≤ 3s', '640×640 输入，不含上传时间'],
               ['并发能力', '支持 ≥ 10 个并发用户', '课程演示规模'],
               ['上传大小', '单张 ≤ 20MB', '超过时前端先行拦截'],
               ['平均检索响应', '历史查询 ≤ 2s', '万级记录规模下']],
              widths=[3.2, 4.2, 5.2], center_cols=())
    h2(doc, '4.2 易用性')
    bullet(doc, '界面采用简洁明快的布局，核心操作“上传—检测—查看结果”不超过三步；')
    bullet(doc, '关键操作均有友好提示与错误反馈；结果图清晰标注缺陷位置，便于非技术用户理解。')
    h2(doc, '4.3 可靠性')
    bullet(doc, '检测任务失败不导致系统崩溃，可自动清理临时文件；')
    bullet(doc, '数据库定期备份，重要记录不因异常中断而丢失。')
    h2(doc, '4.4 安全性')
    bullet(doc, '密码不以明文存储（哈希处理）；')
    bullet(doc, '数据库访问使用参数化查询，防止 SQL 注入；')
    bullet(doc, '上传文件做类型白名单校验，防止恶意文件上传。')
    h2(doc, '4.5 可维护性与可扩展性')
    bullet(doc, '前后端分离、模块化开发，代码遵循统一命名规范并附必要注释；')
    bullet(doc, '缺陷类别通过配置扩展，模型文件可热替换，便于后续新增缺陷类型；')
    bullet(doc, '接口设计预留版本号，便于功能演进。')

    h1(doc, '5 数据需求')
    h2(doc, '5.1 缺陷类别定义')
    body(doc, '结合手机屏幕常见外观缺陷与公开数据集情况，定义如下缺陷类别（初始按 6 类实施，可视数据量调整）：')
    add_table(doc,
              ['代号', '类别', '中文名', '形态描述'],
              [['0', 'scratch', '划痕', '屏幕表面细长线状划伤，方向不定'],
               ['1', 'crack', '裂纹/碎屏', '玻璃面辐射状或网络状裂纹'],
               ['2', 'bright_dot', '亮点/坏点', '局部异常发亮的点状区域'],
               ['3', 'dark_spot', '暗点', '局部亮度偏低或发黑的不规则区域'],
               ['4', 'stain', '污渍/异物', '灰尘、指纹、油渍等附着物'],
               ['5', 'chip', '边缘崩缺', '屏幕边缘的崩边、缺口或破损']],
              widths=[1.6, 2.8, 3.0, 5.2], center_cols=(0, 4))
    h2(doc, '5.2 数据集规模与划分')
    add_table(doc,
              ['项目', '要求'],
              [['单类样本量', '每类有效标注样本 ≥ 300 张，总量建议 ≥ 2000 张'],
               ['划分比例', '训练集:验证集:测试集 = 8:1:1'],
               ['标注格式', 'YOLO txt（归一化中心坐标+宽高）或 Pascal VOC XML'],
               ['标注工具', 'LabelImg / x-anylabeling']],
              widths=[3.4, 8.6], center_cols=(0,))
    h2(doc, '5.3 数据增强')
    body(doc, '为缓解样本不足、提升泛化能力，训练时启用数据增强：随机翻转、90°旋转、亮度/对比度扰动、'
              '高斯噪声、随机缩放与裁剪，以及 YOLOv8 内置的 Mosaic 拼接增强。')
    h2(doc, '5.4 数据来源')
    bullet(doc, '公开数据集：收集工业外观缺陷公开数据（如 TILDA、NEU 等思路借鉴）及开源屏幕缺陷图像；')
    bullet(doc, '自采/合成：利用手机和平板设备拍摄真实屏幕缺陷，或通过图像处理手段合成缺陷样本；')
    bullet(doc, '所有数据仅用于课程学习与科研演示，注明来源与许可协议。')

    h1(doc, '6 接口需求')
    h2(doc, '6.1 系统内部接口（前后端 API）')
    add_table(doc,
              ['方法', '路径', '功能', '请求/响应要点'],
              [['POST', '/api/login', '用户登录', '返回 token 与角色信息'],
               ['POST', '/api/upload', '上传图像', '返回文件 ID 与预检信息'],
               ['POST', '/api/detect', '执行缺陷检测', '返回缺陷列表与结果图 URL'],
               ['GET', '/api/records', '查询检测历史', '支持分页与时间筛选'],
               ['GET', '/api/records/{id}', '查看记录详情', '返回原图、结果图与标注明细'],
               ['DELETE', '/api/records/{id}', '删除记录', '同时删除关联文件'],
               ['GET', '/api/stats', '缺陷统计', '返回各类别数量与占比'],
               ['PUT', '/api/settings', '更新检测参数', '管理员权限']],
              widths=[1.8, 3.6, 3.0, 4.2], center_cols=(0, 1))
    h2(doc, '6.2 外部接口')
    bullet(doc, '模型权重文件：.pt（torchscript）训练/验证格式，.onnx 部署格式；')
    bullet(doc, '数据集接口：与开源标注格式（YOLO txt / VOC XML）兼容，便于导入开源数据。')

    h1(doc, '7 验收标准')
    add_table(doc,
              ['类别', '验收项', '通过标准'],
              [['功能', '全部用例执行', '3.2 节用例主流程全部通过，异常流程有合理提示'],
               ['性能', '检测精度与速度', 'mAP50 ≥ 0.85；GPU 单张 ≤ 0.5s，CPU ≤ 3s'],
               ['数据', '数据集与模型', '完成标注与训练，交付权重文件与评估指标记录'],
               ['文档', '课程文档', '需求分析、概要设计、详细设计、测试报告齐全并符合规范'],
               ['演示', '课堂演示', '可在现场完成“上传—检测—结果展示”全流程演示']],
              widths=[1.8, 4.0, 6.8], center_cols=(0,))
    h1(doc, '8 后续工作安排')
    add_table(doc,
              ['阶段', '周次', '主要工作', '对应文档'],
              [['设计阶段', '7–10', '总体架构、数据库、接口、UI 设计', '《概要设计说明书》'],
               ['实现阶段', '11–14', '数据准备、模型训练、前后端开发、联调测试', '《详细设计说明书》'],
               ['验收阶段', '15–18', '系统演示、项目完善、文档整合', '测试报告、用户手册、课程设计报告']],
              widths=[2.4, 2.0, 5.0, 3.2], center_cols=(0, 1))
    doc.save(r'需求分析说明书.docx')
    print('OK: 需求分析说明书.docx')

# ================================================================ 可行性分析报告
def build_feasibility():
    doc = init_document()
    cp = doc.core_properties
    cp.title = '基于YOLOv8的手机屏幕外观缺陷智能检测系统——可行性分析报告'
    cp.author = '王周毅、林城于'
    add_cover(doc, '可行性分析报告')
    h1(doc, '目录')
    add_toc(doc)

    h1(doc, '1 引言')
    h2(doc, '1.1 编写目的')
    body(doc, '本报告在第 5–6 周“分析阶段”编写，从技术、经济、操作、进度、数据、法律安全等方面，'
              '对《基于YOLOv8的手机屏幕外观缺陷智能检测系统》项目的可行性进行分析与论证，'
              '判断项目是否具备实施条件，为项目立项与后续设计开发提供决策依据。')
    h2(doc, '1.2 项目背景')
    body(doc, '手机屏幕外观缺陷检测长期依赖人工目检，存在效率低、漏检率高、标准不统一等问题。'
              '近年来，以 YOLO 系列为代表的深度学习目标检测算法在工业质检中得到广泛应用，'
              '配合 Web 可视化系统可低成本构建智能检测工具，具有显著的教学价值与应用前景。')
    h2(doc, '1.3 项目目标')
    body(doc, '训练 YOLOv8 缺陷检测模型并构建 Web 检测系统，实现手机屏幕缺陷的自动识别、定位与结果管理，'
              '满足课程设计的完整流程要求并产出可演示成果。')

    h1(doc, '2 技术可行性')
    h2(doc, '2.1 算法选型成熟度高')
    body(doc, 'YOLOv8 由 Ultralytics 公司于 2023 年发布，是当前最主流的目标检测算法之一。'
              '其提供了 YOLOv8n/s/m/l/x 等不同规模模型，兼顾速度与精度；官方开源了训练、评估、导出、'
              '部署的完整工具链，预训练权重公开可用，社区活跃、教程丰富，学习曲线平滑，完全适合学生课程项目掌握与二次开发。')
    h2(doc, '2.2 开发工具链完善')
    add_table(doc,
              ['层次', '技术选型', '可行性说明'],
              [['算法', 'Ultralytics YOLOv8 + PyTorch', 'pip 一键安装，训练/评估 API 成熟，支持 GPU/CPU'],
               ['后端', 'Flask 或 FastAPI', '轻量 Python Web 框架，与算法生态天然对接'],
               ['前端', 'HTML/CSS/JavaScript（Vue 可选）', '浏览器即可访问，无需安装客户端'],
               ['数据库', 'SQLite / MySQL', 'SQLite 零配置，足以支撑课程演示规模'],
               ['标注', 'LabelImg / x-anylabeling', '图形化标注工具，导出 YOLO 格式'],
               ['部署', 'ONNX Runtime', '模型可导出 ONNX 获得推理加速']],
              widths=[2.0, 5.2, 5.4], center_cols=(0,))
    h2(doc, '2.3 技术先例充分')
    body(doc, '工业外观缺陷检测（钢材表面、PCB、织物等）已有大量基于 YOLO 系列的成功案例与公开论文，'
              '手机屏幕缺陷检测亦属于同一类“小目标、低对比度、细长形状”检测问题，技术路线上有充分先例可循。')
    h2(doc, '2.4 技术难点与应对')
    add_table(doc,
              ['难点', '说明', '应对措施'],
              [['缺陷目标小、对比度低', '划痕等目标细长，易与纹理噪声混淆', '提高输入分辨率（如 1280）；合理设置 NMS 与阈值；在数据集整理时保证缺陷清晰可见'],
               ['样本不足', '公开屏幕缺陷数据有限', '数据增强 + COCO 预训练迁移学习 + 合成数据 + 必要时缩减类别'],
               ['精度指标压力', '期望 mAP50 ≥ 0.85', '模型由 n/s 起步逐级尝试，调优学习率、epochs，记录消融对比'],
               ['机器性能有限', '无 GPU 时训练慢', '优先 YOLOv8n/s；使用 Google Colab 免费 GPU；CPU 仅做推理演示']],
              widths=[3.4, 3.2, 6.0], font_size=10)
    body(doc, '结论：技术路线成熟、工具齐全、有先例与兜底方案，项目在技术上是可行的。', bold=True)

    h1(doc, '3 经济可行性')
    h2(doc, '3.1 开发成本')
    add_table(doc,
              ['成本项', '金额/方式', '说明'],
              [['软件', '0 元', 'Python、PyTorch、ultralytics、Flask 等均为开源免费软件'],
               ['数据集', '约 0–100 元', '公开数据免费；自采与合成数据成本极低'],
               ['硬件', '0–100 元', '本机 CPU 可开发调试；云 GPU（如 Colab/租用显卡）按需付费，训练小时数有限'],
               ['合计', '≲ 200 元', '远低于同类型商业质检系统成本']],
              widths=[2.6, 3.4, 6.6], center_cols=(0, 1))
    h2(doc, '3.2 运行成本')
    body(doc, '课程演示阶段在本地或校园网服务器运行即可，无持续性云服务费用；如需对外演示，'
              '可选取低配置云服务器（约数十元/月）承载 Web 服务。')
    h2(doc, '3.3 效益分析')
    bullet(doc, '教学效益：完整覆盖“数据—算法—系统”全链路，锻炼工程与科研能力；')
    bullet(doc, '应用效益：验证了 YOLOv8 用于手机屏幕质检的技术可行性，为后续产业落地积累经验；')
    body(doc, '结论：项目以开源技术为主，投入成本低、收益明确，在经济上是可行的。', bold=True)

    h1(doc, '4 操作可行性')
    body(doc, '系统采用 B/S 架构，用户通过浏览器访问，无需安装任何客户端软件，只需“上传图片—点击检测—查看结果”'
              '三步即可完成操作，界面提供明确提示与状态反馈，普通质检人员经简单培训即可上手；管理员功能操作集中在'
              '设置与记录管理页面，逻辑清晰。系统对使用方信息化水平要求低，在操作上是可行的。')

    h1(doc, '5 进度可行性')
    add_table(doc,
              ['阶段', '周次', '工作量（人·周）', '关键产出'],
              [['需求分析', '5–6', '2', '需求分析说明书、可行性分析报告'],
               ['概要设计', '7–10', '4', '概要设计说明书'],
               ['详细设计与实现', '11–14', '4', '详细设计说明书、可运行系统'],
               ['测试与验收', '15–18', '4', '测试报告、演示、课程设计报告']],
              widths=[3.6, 2.0, 2.6, 4.4], center_cols=(1, 2))
    body(doc, '项目已确定技术路线，团队对 Python、深度学习有基础，开发属单人主导的小型系统，'
              '核心链路（数据—训练—检测—展示）可与课程周次一一对应，时间安排留有缓冲（每周预留约 1/4 时间应对返工），'
              '在进度上是可行的。', bold=True)

    h1(doc, '6 数据可行性')
    h2(doc, '6.1 数据来源')
    bullet(doc, '公开数据集：开源社区存在工业缺陷检测数据集与手机表面缺陷图片，可合法用于学习科研；')
    bullet(doc, '自采数据：使用闲置手机/平板拍摄真实屏幕缺陷，成本低、可控度高；')
    bullet(doc, '合成数据：通过图像处理合成缺陷（划痕、污渍模拟），扩充长尾类别。')
    h2(doc, '6.2 标注工作量估算')
    add_table(doc,
              ['项目', '估算'],
              [['总样本数', '2000–3000 张'],
               ['每张平均标注耗时', '约 1–3 分钟'],
               ['总人工标注耗时', '约 40–100 小时'],
               ['缓解措施', '多人协作标注 + 数据增强扩充 + 先用小数据集验证流程']],
              widths=[4.2, 8.4], center_cols=(0,))
    body(doc, '结论：数据可获得、标注工作量在可控范围内，并有数据增强作为兜底，在数据上是可行的。', bold=True)

    h1(doc, '7 法律与安全可行性')
    bullet(doc, '所用开源软件与数据集将核对其许可证（如 ultralytics 采用 AGPL-3.0），仅用于课程学习与科研演示，不进行商业化使用；')
    bullet(doc, '系统不含任何个人隐私数据，不涉及敏感信息收集；')
    bullet(doc, '项目符合学校学术诚信要求，数据集来源予以注明。')

    h1(doc, '8 风险分析与对策')
    add_table(doc,
              ['风险项', '概率', '影响', '应对措施'],
              [['缺陷数据不足', '高', '高', '数据增强、迁移学习、合成数据、缩减类别数'],
               ['检测精度不达标', '中', '高', '调优训练参数、提高分辨率、尝试更大模型、扩充样本'],
               ['算力受限', '中', '中', '使用 Colab 云 GPU、采用 n/s 小模型、模型量化'],
               ['开发进度延误', '中', '中', '按里程碑检查、先做核心链路、预留缓冲周'],
               ['环境依赖配置困难', '高', '低', '固定依赖版本、提供 requirements.txt 与安装文档'],
               ['标注质量参差', '中', '中', '统一标注规范、抽样复核、二次纠正']],
              widths=[3.2, 1.6, 1.6, 6.2], font_size=10, center_cols=(1, 2))
    h1(doc, '9 结论')
    body(doc, '综上，本系统在技术、经济、操作、进度、数据、法律安全六个维度均具备可行性。'
              '项目成本低、技术路线成熟、成果可演示、风险可控且有明确应对措施，'
              '建议立项，并按照课程周次安排进入第 7–10 周“概要设计”阶段。')
    doc.save(r'可行性分析报告.docx')
    print('OK: 可行性分析报告.docx')

if __name__ == '__main__':
    build_feasibility()
    build_requirements()
    print('全部完成：', datetime.datetime.now())
