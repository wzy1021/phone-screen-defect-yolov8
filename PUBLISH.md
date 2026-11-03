# 发布到 GitHub / GitHub Pages

这个仓库包含两部分：

1. **完整系统**：Flask + SQLite + YOLOv8，只能在本机或有 Python 的服务器上运行；
2. **静态展示站**：`site/` 目录，纯 HTML/CSS/JS，可以部署到 GitHub Pages，在线看界面和交互演示。

> GitHub Pages 只能托管静态文件，跑不了 Flask 和 YOLOv8 推理。在线演示里的检测结果是真实系统预生成的，不是浏览器实时推理。

## 一、把仓库推到 GitHub

在项目根目录（`基于YOLOv8的手机屏幕外观缺陷智能检测系统/`）执行：

```powershell
git init
git add .
git commit -m "手机屏幕外观缺陷智能检测系统：系统、模型、文档与展示站"
git branch -M main

# 先在 GitHub 上新建一个空仓库，然后替换下面地址
git remote add origin https://github.com/<你的用户名>/<仓库名>.git
git push -u origin main
```

`.gitignore` 已经排除了 `data.db`、上传/结果图片、`datasets*/`、`train/runs*/` 这些大文件或含用户数据的文件。仓库里保留：

- 代码、`models/best.pt`、`models/metrics*.json`
- 各阶段 docx、`screenshots/`、`docs/figures/`
- `site/` 静态展示站
- 数据生成脚本（`datasets/gen_dataset.py`、`gen_hard.py`）和训练脚本

## 二、开启 GitHub Pages

1. 打开 GitHub 仓库 → **Settings** → **Pages**
2. **Build and deployment** → **Source** 选择 **GitHub Actions**
3. 推送到 `main` 后，Actions 里的 `Deploy static site to GitHub Pages` 会自动运行
4. 运行完在 Actions 或 Pages 页面拿到地址，形如：

```
https://<你的用户名>.github.io/<仓库名>/
```

站点入口是 `site/index.html`，在线演示是 `site/demo.html`。

## 三、仓库链接自动适配

`site/assets/app.js` 会自动根据当前 Pages 地址推导仓库地址：

```js
if (location.hostname.endsWith('github.io')) {
  const user = location.hostname.split('.')[0];
  const repo = location.pathname.split('/')[1];
  REPO_URL = `https://github.com/${user}/${repo}`;
}
```

所以正常情况下不需要手工改链接。如果部署在自定义域名，把 `app.js` 里的 `REPO_URL` 改成你的仓库地址即可。

## 四、README 预览

GitHub 仓库首页会直接渲染 `README.md`。README 里已经有功能、指标、目录结构和运行方式，配合 `screenshots/` 可以在 GitHub 上直接看界面。

## 五、如果想在线跑完整系统

GitHub Pages 不行，需要能跑 Python 的托管平台，例如：

- Render / Railway / Fly.io（部署 Flask + Gunicorn）
- 一台有 Python 的云服务器（Nginx + Gunicorn + Waitress）
- 继续本机演示（`python run.py`）

注意：完整系统需要 `models/best.pt` 和 `torch/ultralytics`，免费平台的内存和启动时间可能不够；课程演示用本机最稳。
