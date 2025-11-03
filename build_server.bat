@echo off
chcp 65001 >nul
echo LifeTrace Server 构建脚本
echo ================================

echo 1. 检查Python环境...
python --version
if %errorlevel% neq 0 (
    echo 错误: 未找到Python环境
    pause
    exit /b 1
)

echo.
echo 2. 安装依赖包...
pip install -r requirements\requirements.txt
if %errorlevel% neq 0 (
    echo 错误: 依赖包安装失败
    pause
    exit /b 1
)

echo.
echo 3. 清理之前的构建文件...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

echo.
echo 4. 开始构建可执行文件...
pyinstaller build_server.spec
if %errorlevel% neq 0 (
    echo 错误: 构建失败
    pause
    exit /b 1
)

echo.
echo 5. 构建完成！
echo 可执行文件位置: dist\LifeTrace_Server.exe
echo.

echo 6. 使用说明:
echo    启动服务器: LifeTrace_Server.exe
echo    默认端口: 8000
echo    Web界面: http://localhost:8000
echo.

echo 7. 测试运行...
echo 按任意键测试运行可执行文件，或按Ctrl+C跳过测试
pause >nul

echo 启动测试...
cd dist
echo 测试服务器启动（5秒后自动停止）...
timeout /t 5 /nobreak >nul
echo 测试完成
cd ..

echo.
echo 构建和测试完成！
pause
chcp 65001 >nul
echo LifeTrace Server 构建脚本
echo ================================

echo 1. 检查Python环境...
python --version
if %errorlevel% neq 0 (
    echo 错误: 未找到Python环境
    pause
    exit /b 1
)

echo.
echo 2. 安装依赖包...
pip install -r requirements_server.txt
if %errorlevel% neq 0 (
    echo 错误: 依赖包安装失败
    pause
    exit /b 1
)

echo.
echo 3. 清理之前的构建文件...
if exist "dist_server" rmdir /s /q "dist_server"
if exist "build_server" rmdir /s /q "build_server"

echo.
echo 4. 开始构建可执行文件...
pyinstaller build_server.spec --distpath dist_server --workpath build_server
if %errorlevel% neq 0 (
    echo 错误: 构建失败
    pause
    exit /b 1
)

echo.
echo 5. 构建完成！
echo 可执行文件位置: dist_server\LifeTrace_Server.exe
echo.

echo 6. 使用说明:
echo    启动服务器: LifeTrace_Server.exe
echo    默认端口: 8000
echo    Web界面: http://localhost:8000
echo    API文档: http://localhost:8000/docs
echo.

echo 7. 测试运行...
echo 按任意键测试运行可执行文件，或按Ctrl+C跳过测试
pause >nul

echo 启动测试...
cd dist_server
echo 正在启动服务器，请稍等...
echo 服务器将在 http://localhost:8000 启动
echo 按 Ctrl+C 停止服务器
LifeTrace_Server.exe
cd ..

echo.
echo 构建和测试完成！
pause
