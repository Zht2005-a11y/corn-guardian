@echo off
title 玉米病害智能识别后端服务 (Port: 8010)

echo =======================================================
echo   玉米病害智能识别系统 - 后端推理服务
echo   设备: RTX 4050 Laptop GPU (CUDA 加速)
echo   默认模型: ResNet50-CBAM
echo =======================================================

cd /d "%~dp0model\corn_disease_system_20261021"
"D:\anaconda\envs\torch_gpu\python.exe" app\api.py
pause