@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PY=C:\Users\wzy06\.conda\envs\diffusion-course\python.exe"
if not exist "%PY%" (
  echo [警告] 没有找到 conda 环境 diffusion-course，尝试使用 PATH 里的 python。
  set "PY=python"
)
"%PY%" -c "import ultralytics, torch" >nul 2>&1
if errorlevel 1 (
  echo.
  echo [错误] 当前 Python 环境没有安装 ultralytics/torch，无法启动检测系统。
  echo 当前解释器：
  "%PY%" -c "import sys; print(sys.executable)"
  echo.
  echo 请确认 conda 环境 diffusion-course 完整，或执行：
  echo   pip install -r requirements.txt
  echo.
  pause
  exit /b 1
)
echo 正在启动手机屏幕缺陷检测系统...
echo 浏览器访问：http://127.0.0.1:5000
"%PY%" run.py
pause
