#!/bin/bash

# 간단한 BatMon PyInstaller 빌드 스크립트

echo "BatMon Build Script"
echo "==================="

# 1. dist 폴더 삭제
echo "1. Cleaning dist folder..."
rm -rf dist/
rm -rf build/
rm -f *.spec
echo "   ✓ Cleaned"

# 2. .env.local 파일 확인
echo "2. Checking for environment files..."
ENV_ARGS=()
if [ -f ".env.local" ]; then
    ENV_ARGS+=("--add-data=.env.local;.")
    echo "   ✓ Found .env.local - will be included in exe"
elif [ -f ".env" ]; then
    ENV_ARGS+=("--add-data=.env;.")
    echo "   ✓ Found .env - will be included in exe"
else
    echo "   ⚠ No .env.local or .env file found"
fi

# 3. PyInstaller 실행
echo "3. Building executable..."
echo "   Running PyInstaller..."
echo ""

uv run pyinstaller \
    --onefile \
    --console \
    --paths=. \
    --collect-all=fastapi \
    --collect-all=uvicorn \
    --collect-all=starlette \
    --add-data="frontend/views;frontend/views" \
    --add-data="frontend/public;frontend/public" \
    "${ENV_ARGS[@]}" \
    --name=batmon \
    backend/main.py

# 4. 결과 확인
echo ""
if [ -f "dist/batmon.exe" ]; then
    file_size=$(du -h "dist/batmon.exe" | cut -f1)
    echo "✓ SUCCESS: Build completed!"
    echo "   Output: dist/batmon.exe ($file_size)"
    if [ ${#ENV_ARGS[@]} -gt 0 ]; then
        echo "   Config: Environment file included in exe"
    fi
    echo ""
    echo "Next steps:"
    echo "   - Test: ./dist/batmon.exe"
    echo "   - Access: http://localhost:8002 (or port from .env.local)"
else
    echo "✗ FAILED: Build failed!"
    echo "   Check the error messages above"
    exit 1
fi