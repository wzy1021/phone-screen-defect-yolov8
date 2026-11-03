# 第 15–18 周：验收阶段材料

课程设计最后四周（验收阶段）的交付物：测试报告、用户使用手册、课程设计报告、答辩 PPT，
以及生成脚本和自检脚本。

## 1. 文件清单

```
week15-18/
├── 测试报告.docx            测试范围、用例、性能、模型、缺陷跟踪
├── 用户使用手册.docx        安装、操作、FAQ、演示清单
├── 课程设计报告.docx        背景、需求、设计、实现、测试、评价
├── 答辩PPT.pptx             22 页，16:9，含讲稿备注
├── 答辩讲稿.md              逐页口播稿（约 10 分钟）
├── 验收演示脚本.md          现场演示顺序、预期结果、翻车预案、问答
├── 交付说明.md              本阶段做了什么、怎么打开、指标口径
└── docs/
    ├── docx_kit.py          Word 公共排版
    ├── make_figures.py      统计图
    ├── make_test_report.py
    ├── make_user_manual.py
    ├── make_course_report.py
    ├── make_pptx.py
    ├── qa_check.py          结构自检
    ├── render_preview.py    PPT 粗略预览（自检用，非精确渲染）
    └── figures/             生成的统计图
```

## 2. 三份文档看什么

- **测试报告**：先看第 2 章通过准则和第 11 章结论；要核对细节看第 5 章 26 个用例、
  第 7 章性能和 第 8 章模型指标。
- **用户使用手册**：第一次用按第 3–5 章走；遇到报错直接翻第 11 章；答辩前看第 12 章。
- **课程设计报告**：老师通常看摘要、第 3 章设计、第 5 章结果、第 6 章局限；
  参考文献和附录在最后。

Word 打开后，目录处右键“更新域”生成页码。

## 3. 指标口径（重要）

| 数字 | 含义 |
|------|------|
| 0.9932 | v1 模型，原测试集 160 张，mAP50 |
| 0.9593 | mix 模型，混合测试集 260 张，mAP50 |
| 0.9875 | mix 模型，回到原测试集，mAP50 |
| 0.8883 | mix 模型，困难测试集 100 张，mAP50 |
| 26 → 3 | 同一张真实碎屏图，改进前/后的检出框数 |

三组测试集不同，不能横向比较。所有 mAP 都是合成数据上的结果，真实图只有一张，
只能做案例分析。

## 4. 重新生成

```powershell
python week15-18/docs/make_figures.py
python week15-18/docs/make_test_report.py
python week15-18/docs/make_user_manual.py
python week15-18/docs/make_course_report.py
python week15-18/docs/make_pptx.py
python week15-18/docs/qa_check.py
```

指标、测试输出、记录数从 `week11-14/` 的实际文件读取；数据或模型更新后重跑即可。

## 5. 自检

`qa_check.py` 会检查：Word 标题层级、表格列数与宽度、图片是否缺失；PPT 形状是否越界、
文本是否可能溢出、每页是否有备注。当前结果：三份 Word 0 问题，PPT 0 问题。

> 说明：本机没有可用的 LibreOffice/Office 自动化渲染，PPT 的视觉效果用
> `render_preview.py` 做粗略版式检查，最终效果以 PowerPoint 打开为准。
