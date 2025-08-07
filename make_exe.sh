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

# 2. PyInstaller 실행
echo "2. Running PyInstaller..."
echo "   Command: pyinstaller --onefile --console --collect-all=fastapi --collect-all=uvicorn --add-data=\"frontend/views;frontend/views\" --add-data=\"frontend/public;frontend/public\" --name=batmon backend/main.py"
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
    --name=batmon \
    backend/main.py

# 3. 결과 확인
echo ""
if [ -f "dist/batmon.exe" ]; then
    file_size=$(du -h "dist/batmon.exe" | cut -f1)
    echo "✓ SUCCESS: Build completed!"
    echo "   Output: dist/batmon.exe ($file_size)"
    echo ""
    echo "Next steps:"
    echo "   - Test: ./dist/batmon.exe"
    echo "   - Access: http://localhost:8000"
else
    echo "✗ FAILED: Build failed!"
    echo "   Check the error messages above"
    exit 1
fi