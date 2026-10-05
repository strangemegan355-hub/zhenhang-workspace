@echo off
chcp 65001 >nul
echo ========================================
echo   振航 ERP 一键启动
echo ========================================

echo.
echo [1/3] 检查 Docker...
docker ps >nul 2>&1
if errorlevel 1 (
    echo   正在启动 Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo   等待 Docker 就绪（最多 60 秒）...
    set /a count=0
    :wait_docker
    timeout /t 2 >nul
    set /a count+=2
    docker ps >nul 2>&1
    if errorlevel 1 (
        if !count! lss 60 goto wait_docker
        echo   [错误] Docker 启动超时，请手动启动
        goto :end
    )
)
echo   [√] Docker 已就绪

echo.
echo [2/3] 启动后端 (FastAPI :8000)...
cd /d D:\cursorxiangmu\shengtaixitong\backend
set PYTHONPATH=D:\cursorxiangmu\shengtaixitong\backend
start "Zhenhang Backend" cmd /c "python run.py"
echo   [√] 后端启动中... http://localhost:8000/docs

echo.
echo [3/3] 启动前端 (Next.js :3000)...
cd /d D:\cursorxiangmu\shengtaixitong\apps\web-admin
start "Zhenhang Frontend" cmd /c "npm run dev"
echo   [√] 前端启动中... http://localhost:3000

echo.
echo ========================================
echo   启动完成！
echo   后端: http://localhost:8000/docs
echo   前端: http://localhost:3000
echo   默认账号: admin / Admin@123456
echo ========================================
echo.
pause

:end
