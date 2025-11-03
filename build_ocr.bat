@echo off
echo Building LifeTrace OCR Module...

REM 激活虚拟环境（如果存在）
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM 清理之前的构建文件
if exist "build_ocr" (
    echo Cleaning previous build files...
    rmdir /s /q build_ocr
)

if exist "dist\LifeTrace_OCR.exe" (
    echo Removing previous executable...
    del "dist\LifeTrace_OCR.exe"
)

REM 使用PyInstaller构建
echo Running PyInstaller...
pyinstaller build_ocr.spec

REM 检查构建结果
if exist "dist\LifeTrace_OCR.exe" (
    echo.
    echo ✅ Build successful!
    echo Executable location: dist\LifeTrace_OCR.exe
    echo.
    echo To test the OCR module:
    echo   cd dist
    echo   .\LifeTrace_OCR.exe
) else (
    echo.
    echo ❌ Build failed!
    echo Please check the error messages above.
)

pause
