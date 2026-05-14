<#
.SYNOPSIS
cms-docdb PowerShell 兼容包装脚本

.DESCRIPTION
统一处理 Python 脚本调用的兼容性问题：
1. 自动查找 Python 可执行文件
2. 处理 PowerShell 版本兼容性（避免使用 || 操作符）
3. 确保 UTF-8 编码输出

.PARAMETER ScriptPath
要执行的 Python 脚本路径（相对于 scripts/ 目录）

.PARAMETER Arguments
传递给脚本的参数

.EXAMPLE
.\run-script.ps1 "browse/browse.py" "1792835212949254145"

.EXAMPLE
.\run-script.ps1 "query/search.py" "搜索关键词" --project-id 123
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ScriptPath,
    
    [string[]]$Arguments
)

# OpenClaw / exec：Windows 控制台默认代码页易导致中文与 PowerShell 报错乱码
try {
    chcp 65001 | Out-Null
} catch {}
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    [Console]::InputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch {}

# 定义可能的 Python 路径列表（含 OpenClaw / EasyClaw 捆绑路径；其余环境依赖 PATH 中的 python/python3）
$pythonPaths = @(
    "$env:USERPROFILE/.openclaw/python-3.12/python.exe",
    "$env:USERPROFILE/.easyclaw/python-3.12/python.exe",
    "$env:USERPROFILE/AppData/Local/Programs/Python/Python312/python.exe",
    "$env:ProgramFiles/Python312/python.exe",
    "python",
    "python3"
)

# 查找可用的 Python
function Find-Python {
    foreach ($path in $pythonPaths) {
        try {
            if (Get-Command $path -ErrorAction SilentlyContinue) {
                # 验证 Python 版本
                $versionOutput = & $path --version 2>&1
                if ($versionOutput -match "Python 3\.") {
                    return $path
                }
            }
        } catch {
            # 忽略错误，继续尝试下一个路径
        }
    }
    return $null
}

# 查找脚本完整路径
function Find-ScriptPath {
    param([string]$relativePath)
    
    # 尝试从当前目录查找
    $localPath = Join-Path (Get-Location) $relativePath
    if (Test-Path $localPath) {
        return $localPath
    }
    
    # 尝试从脚本所在目录查找
    $scriptDir = Split-Path $MyInvocation.MyCommand.Definition -Parent
    $scriptPath = Join-Path $scriptDir $relativePath
    if (Test-Path $scriptPath) {
        return $scriptPath
    }
    
    # 尝试从上级目录的 scripts 文件夹查找
    $parentDir = Split-Path $scriptDir -Parent
    $scriptsPath = Join-Path $parentDir "scripts" | Join-Path -ChildPath $relativePath
    if (Test-Path $scriptsPath) {
        return $scriptsPath
    }
    
    return $null
}

# 主执行逻辑
try {
    # 查找 Python
    $python = Find-Python
    if (-not $python) {
        Write-Error "未找到 Python 解释器，请确保已安装 Python 3.x"
        exit 1
    }
    
    # 查找脚本路径
    $fullScriptPath = Find-ScriptPath $ScriptPath
    if (-not $fullScriptPath) {
        Write-Error "未找到脚本文件: $ScriptPath"
        exit 1
    }
    
    # 设置环境变量确保 UTF-8 输出
    $env:PYTHONIOENCODING = "utf-8"
    $env:PYTHONUTF8 = "1"
    
    # 执行脚本（使用 & 操作符确保兼容性）
    $commandArgs = @($fullScriptPath) + $Arguments
    
    # PowerShell 5.x 兼容的执行方式
    & $python @commandArgs
    
    # 传递退出码
    exit $LASTEXITCODE
} catch {
    Write-Error "执行脚本时发生错误: $_"
    exit 1
}