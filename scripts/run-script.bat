@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 定义可能的 Python 路径列表
set "pythonPaths="%USERPROFILE%\.easyclaw\python-3.12\python.exe";"%USERPROFILE%\AppData\Local\Programs\Python\Python312\python.exe";"%ProgramFiles%\Python312\python.exe";python;python3"

:: 查找可用的 Python
set "python="
for %%p in (%pythonPaths%) do (
    where "%%p" >nul 2>&1
    if !errorlevel! equ 0 (
        set "python=%%p"
        goto :python_found
    )
)

:python_found
if not defined python (
    echo 错误: 未找到 Python 解释器，请确保已安装 Python 3.x
    exit /b 1
)

:: 设置 UTF-8 环境变量
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

:: 检查脚本参数
if "%~1"=="" (
    echo 错误: 请指定要执行的脚本路径
    exit /b 1
)

:: 查找脚本完整路径
set "scriptPath=%~1"
if not exist "%scriptPath%" (
    :: 尝试从脚本所在目录查找
    set "scriptDir=%~dp0"
    set "fullPath=!scriptDir!%~1"
    if exist "!fullPath!" (
        set "scriptPath=!fullPath!"
    ) else (
        :: 尝试从上级目录的 scripts 文件夹查找
        for %%d in ("!scriptDir!..") do (
            set "parentDir=%%~fd"
        )
        set "fullPath=!parentDir!\scripts\%~1"
        if exist "!fullPath!" (
            set "scriptPath=!fullPath!"
        ) else (
            echo 错误: 未找到脚本文件: %~1
            exit /b 1
        )
    )
)

:: 执行脚本
shift
"%python%" "%scriptPath%" %*

:: 传递退出码
exit /b %errorlevel%