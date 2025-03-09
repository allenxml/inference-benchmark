# -*- coding: utf-8 -*-
"""
错误处理包装器，用于捕获和显示错误。
"""
import sys
import traceback

def main():
    try:
        # 导入真正的主模块
        from ui.app import BenchmarkApp
        
        # 创建必要的目录
        import os
        os.makedirs("config", exist_ok=True)
        
        # 启动应用
        app = BenchmarkApp()
        app.mainloop()
    except Exception as e:
        # 捕获并显示错误
        error_msg = f"发生错误: {str(e)}\n\n"
        error_msg += traceback.format_exc()
        print(error_msg)
        
        # 在Windows上，保持窗口打开
        if sys.platform.startswith('win'):
            print("\n按回车键退出...")
            input()

if __name__ == "__main__":
    main() 