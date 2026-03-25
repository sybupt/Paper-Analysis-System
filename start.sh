#!/bin/bash
echo "=============================================="
echo " 🚀 论文智能调研分析系统"
echo " 💡 一键启动，无需配置环境"
echo "=============================================="
echo ""
echo "正在安装依赖库..."
pip install -r requirements.txt
echo ""
echo "正在启动系统..."
streamlit run paper_system.py