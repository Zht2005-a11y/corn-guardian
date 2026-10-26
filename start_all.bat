@echo off
title 启动玉米病害智能诊断全栈系统

echo =========================================================
echo   玉米病害多尺度感知与大屏诊断系统 全栈一键启动
echo   [1] 后端服务: http://localhost:8010
echo   [2] 前端大屏: http://localhost:5173
echo   [3] 接口文档: http://localhost:8010/docs
echo =========================================================

echo 正在启动后端推理引擎服务...
start "玉米病害-后端服务(8010)" cmd /k "%~dp0run_backend.bat"

echo 等待后端初始化完成 (3秒)...
ping 127.0.0.1 -n 4 >nul

echo 正在启动前端可视化大屏...
start "玉米病害-前端大屏(5173)" cmd /k "%~dp0run_frontend.bat"

echo 等待前端服务就绪 (2秒)...
ping 127.0.0.1 -n 3 >nul

echo 正在为您打开大屏界面...
start http://localhost:5173

echo 全栈系统已启动完成！