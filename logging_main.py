# -*- coding: utf-8 -*-
"""
带日志记录的主文件，用于记录错误信息。
"""
import os
import sys
import logging
import traceback
from datetime import datetime

# 配置日志
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def show_error_message(message):
    """显示错误消息对话框"""
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        messagebox.showerror("错误", message)
        root.destroy()
    except Exception as e:
        logging.error(f"无法显示错误对话框: {str(e)}")

def main():
    try:
        # 记录启动信息
        logging.info("应用程序启动")
        
        # 导入真正的主模块
        from ui.app import BenchmarkApp
        
        # 创建必要的目录
        import os
        os.makedirs("config", exist_ok=True)
        
        # 启动应用
        app = BenchmarkApp()
        app.mainloop()
        
        logging.info("应用程序正常退出")
    except Exception as e:
        # 记录错误
        error_msg = f"发生错误: {str(e)}\n\n"
        error_msg += traceback.format_exc()
        logging.error(error_msg)
        
        # 显示错误对话框
        show_error_message(f"应用程序发生错误:\n{str(e)}\n\n详细信息已记录到日志文件:\n{log_file}")

if __name__ == "__main__":
    main() 