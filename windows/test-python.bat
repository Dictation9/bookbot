@echo off
echo Python Detection Test
echo ====================
echo.

echo Current directory: %CD%
echo.

echo Testing Python commands:
echo.

echo 1. Testing 'python --version':
python --version 2>&1
if errorlevel 1 (
    echo    ❌ 'python' command failed
) else (
    echo    ✅ 'python' command works
)
echo.

echo 2. Testing 'python3 --version':
python3 --version 2>&1
if errorlevel 1 (
    echo    ❌ 'python3' command failed
) else (
    echo    ✅ 'python3' command works
)
echo.

echo 3. Testing 'py --version':
py --version 2>&1
if errorlevel 1 (
    echo    ❌ 'py' command failed
) else (
    echo    ✅ 'py' command works
)
echo.

echo 4. Testing 'where python':
where python 2>&1
echo.

echo 5. Testing 'where python3':
where python3 2>&1
echo.

echo 6. Testing 'where py':
where py 2>&1
echo.

echo 7. PATH environment variable:
echo %PATH%
echo.

pause
