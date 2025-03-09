# -*- coding: utf-8 -*-
"""
主入口文件，用于启动应用。
"""
import os
import sys

# 确保当前目录在路径中
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入应用
from ui.app import BenchmarkApp


def main():
    """主函数"""
    # 创建必要的目录
    os.makedirs("config", exist_ok=True)
    
    # 启动应用
    app = BenchmarkApp()
    app.mainloop()


if __name__ == "__main__":
    main() 