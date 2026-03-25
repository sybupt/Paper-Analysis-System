@echo off
echo ==============================================
echo  🚀 论文智能调研分析系统
echo  💡 双击启动，无需配置环境
echo ==============================================
echo.
echo 正在安装依赖库...
python -m pip install -r requirements.txt
echo.
echo 正在启动系统，请稍候...
echo 系统启动后会自动打开浏览器
echo.
streamlit run paper_system.py
pause