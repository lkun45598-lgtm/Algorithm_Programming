@echo off
REM 启动 PyQt6 GUI (需要先在 pytorch conda 环境中)
call D:\Anaconda\Scripts\activate.bat pytorch
python src\gui\main.py
