@echo off
chcp 65001 >nul
echo ============================================================
echo  Recomind 智能推荐系统 - 数据库初始化
echo ============================================================
echo.
echo  本脚本将执行 scripts\init_database.sql 创建数据库与数据表。
echo  请确保 MySQL 服务已启动，并按提示输入 root 密码。
echo.
mysql -u root -p < "%~dp0init_database.sql"
echo.
if %errorlevel% equ 0 (
    echo 数据库初始化完成！
) else (
    echo 初始化失败，请检查 MySQL 是否启动以及密码是否正确。
)
pause
