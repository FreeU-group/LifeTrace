@echo off
chcp 65001 >nul
echo LifeTrace Recorder 构建脚本
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
pip install -r requirements_recorder.txt
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
pyinstaller build_recorder.spec
if %errorlevel% neq 0 (
    echo 错误: 构建失败
    pause
    exit /b 1
)

echo.
echo 5. 构建完成！
echo 可执行文件位置: dist\LifeTrace_Recorder.exe
echo.

echo 6. 测试运行...
echo 按任意键测试运行可执行文件，或按Ctrl+C跳过测试
pause >nul

echo 启动测试...
cd dist
LifeTrace_Recorder.exe --help
cd ..

echo.
echo 构建和测试完成！
echo 可执行文件: dist\LifeTrace_Recorder.exe
pause
