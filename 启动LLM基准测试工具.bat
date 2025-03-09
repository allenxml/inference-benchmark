@echo off
echo 正在启动LLM基准测试工具...
"LLM基准测试工具.exe"
echo.
if %ERRORLEVEL% NEQ 0 (
    echo 程序异常退出，错误代码: %ERRORLEVEL%
    pause
) else (
    echo 程序正常退出
) 