# 基于 YOLOv8 的手机屏幕外观缺陷智能检测系统

课程设计第 11–14 周（实现阶段）成果：一个可以本地运行的网页检测系统 + 训练好的
YOLOv8 模型 + 数据集构建与训练脚本 + 自动化测试 + 《详细设计说明书》。

## 0. 本阶段结果

- 基线模型 v1：YOLOv8n，60 轮，合成测试集 mAP50 **0.9932**、mAP50-95 0.8167
- 部署模型 mix：原数据 + 困难数据混合训练，原测试集 mAP50 **0.9875**、
  困难测试集 mAP50 **0.8883**
- 真实碎屏图：误检从 **26 个框降到 3 个**，主裂纹可以被框出（详见文档第 7 章）
- 推理：GPU 单张约 **4 ms**，检测接口端到端约 **90 ms**
- 测试：**26/26** 自动化用例通过
- 文档：`详细设计说明书.docx`（52 页，新增“低对比度小目标改进”一章）
- 演示数据：数据库里有 24 条合成图检测记录，打开统计页就有数据

> 指标是在**合成测试集**上得到的，不代表真实产线精度。真实图目前只有一张，
> 只能做案例分析；要得到真实 mAP，需要补真实标注数据（见文档 7.6 节）。

## 0.1 针对真实低对比度缺陷的改进

第一版在真实碎屏图上漏检、误检都很严重（阈值 0.25 出 26 个框，抬到 0.9 变 0）。
第 11–14 周后半段做了三件事：

1. `datasets/gen_hard.py`：生成困难版数据（蜘蛛网裂纹、2–10 像素微小缺陷、
   水珠/反光/散景负样本、15% 纯负样本）；
2. `train/train_hard.py`：在困难数据或混合数据上训练，弱 Mosaic、弱缩放，
   支持 CPU 配置；
3. 检测端：自动找手机屏幕区域（ROI）再检测，亮点/暗点加 2.5% 尺寸过滤，
   检测页有“屏幕区域聚焦”开关。

复现命令：

```powershell
python datasets/gen_hard.py --train 600 --val 100 --test 100
python train/train_hard.py --profile cpu --data datasets_mix/data_mix.yaml --epochs 30
```

## 0.2 在线展示站（GitHub Pages）

仓库根目录的 `site/` 是一个纯静态展示站，可以部署到 GitHub Pages：

- 首页：`../site/index.html`（功能、界面截图、真实案例、技术方案、快速开始）
- 交互演示：`../site/demo.html`（选择样张，回放真实系统预生成的检测结果）

本地预览（在仓库根目录执行）：

```powershell
python -m http.server 8090 --directory site
# 打开 http://127.0.0.1:8090/
```

发布到 GitHub Pages 的步骤见仓库根目录的 `PUBLISH.md`。GitHub Pages 只能托管静态页面，
跑不了 Flask + YOLOv8；在线演示里的结果图是预先跑出来的，不是浏览器实时推理。

## 1. 功能

- 注册 / 登录 / 退出（注册账号固定为普通用户，管理员由初始化脚本创建）
- 上传或拖拽手机屏幕照片（支持多张，单张 ≤ 20MB）
- YOLOv8 自动检测 6 类外观缺陷：划痕、裂纹、亮点、暗点、污渍、边缘崩缺
- 结果图自动画框并标注类别与置信度，可下载结果图、导出 CSV
- 检测记录入库，支持按时间、有无缺陷筛选，分页查看、删除
- 统计页：检测总数、缺陷总数、今日检测、平均耗时、类别柱状图/饼图、最近趋势
- 个人资料：自定义昵称、上传头像（2MB 内，自动裁成 200×200）
- 管理员可查看所有用户列表、检测次数/缺陷数和每个用户的记录
- 管理员可修改默认置信度阈值

## 2. 快速开始

环境要求：Python 3.10+，依赖见 `requirements.txt`。本项目在本机使用
`C:\Users\wzy06\.conda\envs\diffusion-course` 这个 conda 环境（已带 CUDA 版 PyTorch）。

```powershell
# 1）安装依赖（如果环境里还没有）
pip install -r requirements.txt

# 2）启动系统
python run.py
# 浏览器打开 http://127.0.0.1:5000
```

也可以双击 `启动系统.bat`。

演示账号：

| 账号 | 密码 | 角色 |
|------|------|------|
| admin | 123456 | 管理员（可看所有记录、改参数） |
| user | 123456 | 普通用户（只看自己的记录） |

> 第一次启动会自动创建 `data.db` 并写入演示账号；换电脑时把 `data.db`、
> `models/best.pt`、`static/uploads`、`static/results` 一起拷走即可。
>
> 登录页有“立即注册”入口，新注册的账号角色固定为普通用户（只能看自己的记录）；
> 管理员账号不开放注册。

## 3. 目录结构

```
week11-14/
├── run.py                  启动入口
├── config.py               配置（路径、类别、阈值、演示账号）
├── requirements.txt
├── app/                    Flask 应用
│   ├── __init__.py         应用工厂、错误处理
│   ├── db.py               SQLite 建表与增删改查
│   ├── auth.py             密码哈希、签名 token、登录装饰器
│   ├── detection.py        YOLOv8 加载、推理、画框
│   ├── api.py              REST 接口
│   ├── views.py            页面路由
│   └── utils.py            图片校验与文件管理
├── templates/              5 个页面模板
├── static/                 CSS / JS / Bootstrap / ECharts / 上传与结果图
├── datasets/
│   ├── gen_dataset.py      原版合成数据（高对比度）
│   ├── gen_hard.py         困难版数据（微小低对比度 + 水珠/反光负样本）
│   ├── data.yaml           原数据训练配置
│   ├── images|labels/      train / val / test
│   └── dataset_stats.json  类别统计
├── datasets_hard/          困难版数据（600/100/100）
├── datasets_mix/           原数据 + 困难数据的混合数据（1600/260/260）
├── train/train.py          原版训练 + 测试集评估 + 指标导出
├── train/train_hard.py     困难版/混合版训练，支持 --profile cpu
├── models/best.pt          当前部署的混合训练模型
├── models/best_v1.pt       第一版模型备份
├── models/metrics.json     v1 测试集指标
├── models/metrics_mix.json 混合模型在混合测试集上的指标
├── tests/                  接口、数据集、模型测试、UI 冒烟与截图脚本
├── screenshots/            系统页面截图（用于文档）
└── docs/                   详细设计说明书及配图
```

## 4. 数据集

由于课程设计期间很难收集上千张带标注的真实屏幕缺陷照片，本项目使用
`datasets/gen_dataset.py` **程序化合成**数据：随机生成桌面、手机外壳、玻璃反光和
亮/息屏壁纸，再按真实外观绘制六类缺陷。标注框由绘制位置直接换算，坐标天然准确。

```powershell
python datasets/gen_dataset.py --train 1000 --val 160 --test 160
```

- 图片 640×640，YOLO 格式标签（`class cx cy w h`，归一化）
- 按 8:1:1 划分 train / val / test
- 输出 `dataset_stats.json` 记录每个类别的框数量

> 说明：合成数据与真实照片存在域差异，模型的 mAP 只代表在本数据集上的效果。
> 真实照片的接入方式：用 LabelImg 标注后，把图片和 txt 放进同样的
> `images/train`、`labels/train` 目录即可混合训练，不需要改代码。

### 4.1 困难版数据（针对真实低对比度缺陷）

原版数据的缺陷太亮、太大，拿到真实碎屏图上会漏检裂纹、把水花当成亮点。为此增加
`datasets/gen_hard.py`：裂纹画成蜘蛛网，缺陷缩小到 2–10 像素、颜色贴近背景，并
随机加不标注的水珠/反光/散景作为难负样本，另有 15% 纯负样本。

```powershell
python datasets/gen_hard.py --train 600 --val 100 --test 100
```

输出到 `datasets_hard/`；`datasets_mix/` 是把原数据（1000 张）和困难数据（600 张）
合并后的训练集，给 `train/train_hard.py` 用。

## 5. 训练

```powershell
python train/train.py --epochs 80 --batch 16 --device 0
```

- 预训练权重 `yolov8n.pt`（首次运行自动下载）
- 输入 640×640，AdamW，学习率 0.005，Mosaic / 翻转 / 亮度等增强
- 结果在 `train/runs/phonescreen_yolov8n/`
- 训练完自动在 test 划分上评估，`best.pt` 复制到 `models/`，
  指标写入 `models/metrics.json`

只想快速验证流程：

```powershell
python train/train.py --epochs 2 --batch 8 --device 0 --name smoke
```

困难版/混合版训练（推荐用于真实低对比度照片）：

```powershell
# 只用困难数据
python train/train_hard.py --data datasets_hard/data_hard.yaml --epochs 45 --device 0

# 原数据 + 困难数据混合，从困难版模型初始化
python train/train_hard.py --data datasets_mix/data_mix.yaml ^
    --model train/runs_hard/hard_yolov8n/weights/best.pt ^
    --epochs 30 --name mix_yolov8n --project train/runs_mix ^
    --metrics models/metrics_mix.json --mosaic 0.4 --scale 0.35 --lr0 0.001

# 只有 CPU
python train/train_hard.py --profile cpu --data datasets_mix/data_mix.yaml --epochs 30
```

`--profile cpu` 会自动设 `workers=0`、关 AMP、batch 不超过 8。CPU 和 GPU 训练
质量一致，只是慢；CPU 上 1600 张、30 轮大约 1.5–3 小时。

## 6. 测试

```powershell
python tests/run_all.py                     # 一次跑完 26 个用例，输出写到 docs/test_output.txt
python -m unittest tests.test_api -v        # 接口测试（假检测器，不需要模型）
python -m unittest tests.test_dataset -v    # 数据集完整性
python -m unittest tests.test_detection -v  # 真实模型推理（需要 best.pt）
python tests/ui_smoke.py                    # 真实浏览器走一遍主流程（需先启动系统）
```

页面截图（需要本机 Edge + playwright）：

```powershell
python tests/screenshot.py                  # 输出到 screenshots/
```

## 7. 文档

《详细设计说明书》在 `详细设计说明书.docx`，目录和页码需要在 Word 里
右键“更新域”生成。重新生成文档：

```powershell
python docs/make_figures.py   # 画包结构、流程、时序、数据库等示意图
python docs/make_doc.py       # 读取实际指标、测试输出，生成 docx
```

文档里的数据、指标、测试结果都从 `datasets/dataset_stats.json`、
`models/metrics.json`、`docs/test_output.txt`、`docs/perf.json` 读取，
不是手写死的。

## 8. 主要接口

| 方法 | 地址 | 作用 |
|------|------|------|
| POST | `/api/login` | 登录，返回 token 并写入 HttpOnly Cookie |
| POST | `/api/upload` | 上传图片 |
| POST | `/api/detect` | 检测（file 或 image_path + conf） |
| GET | `/api/records` | 分页查询记录（page/size/start/end/has_defect） |
| GET | `/api/records/<id>` | 记录详情 |
| DELETE | `/api/records/<id>` | 删除记录及文件 |
| GET | `/api/records/<id>/csv` | 导出缺陷明细 CSV |
| GET | `/api/stats` | 分类、总量、耗时、趋势统计 |
| GET/PUT | `/api/settings` | 查看/修改阈值（PUT 仅管理员） |
| GET | `/api/health` | 健康检查（模型是否存在/已加载） |

返回格式统一为 `{"code": 200, "message": "ok", "data": ...}`。

## 9. 常见问题

- **检测返回 503 / 页面提示“模型未加载”**：还没有 `models/best.pt`，先运行训练脚本。
- **检测报 `No module named 'ultralytics'`**：启动时用错了 Python 环境。双击
  `启动系统.bat`，或明确用 `C:\Users\wzy06\.conda\envs\diffusion-course\python.exe run.py`；
  不要用系统 python / base 环境。
- **端口被占用**：`python run.py --port 5001`。
- **首次检测很慢**：模型第一次加载需要几秒，之后单张约几十毫秒（GPU）。
- **上传失败**：确认格式是 jpg/png/bmp/webp 且不超过 20MB。
- **提示“这是系统生成的结果图”**：不要上传带检测框的结果图，上传原始照片；
  结果图里的框和文字会被模型当成新的缺陷（详见“结果图回流”问题）。



