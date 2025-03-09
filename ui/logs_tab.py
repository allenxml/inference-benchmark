# -*- coding: utf-8 -*-
"""
日志标签页模块，实现日志显示界面。
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Dict, List, Any
import datetime


class LogsTab(ttk.Frame):
    """日志标签页类"""
    
    def __init__(self, parent, app):
        """
        初始化日志标签页
        
        Args:
            parent: 父窗口
            app: 应用实例
        """
        super().__init__(parent)
        self.app = app
        
        # 创建日志文本框
        self.log_text = scrolledtext.ScrolledText(self, wrap=tk.WORD, width=80, height=30)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 设置只读
        self.log_text.config(state=tk.DISABLED)
        
        # 按钮框架
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 清空按钮
        ttk.Button(button_frame, text="清空日志", command=self.clear_log, width=15).pack(side=tk.LEFT, padx=5)
        
        # 保存按钮
        ttk.Button(button_frame, text="保存日志", command=self.save_log, width=15).pack(side=tk.LEFT, padx=5)
        
        # 自动滚动选项
        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(button_frame, text="自动滚动", variable=self.auto_scroll_var).pack(side=tk.RIGHT, padx=5)
    
    def add_log(self, message: str):
        """
        添加日志消息
        
        Args:
            message: 日志消息
        """
        # 获取当前时间
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 启用编辑
        self.log_text.config(state=tk.NORMAL)
        
        # 添加时间戳和消息
        self.log_text.insert(tk.END, f"[{now}] {message}\n")
        
        # 如果启用了自动滚动，则滚动到底部
        if self.auto_scroll_var.get():
            self.log_text.see(tk.END)
        
        # 禁用编辑
        self.log_text.config(state=tk.DISABLED)
    
    def clear_log(self):
        """清空日志"""
        # 启用编辑
        self.log_text.config(state=tk.NORMAL)
        
        # 清空文本
        self.log_text.delete(1.0, tk.END)
        
        # 禁用编辑
        self.log_text.config(state=tk.DISABLED)
        
        # 更新状态栏
        self.app.update_status("日志已清空")
    
    def save_log(self):
        """保存日志到文件"""
        from tkinter import filedialog
        import os
        
        # 获取保存路径
        file_path = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("日志文件", "*.log"), ("文本文件", "*.txt"), ("所有文件", "*.*")],
            initialdir=os.getcwd(),
            title="保存日志"
        )
        
        if file_path:
            try:
                # 获取日志内容
                log_content = self.log_text.get(1.0, tk.END)
                
                # 保存到文件
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(log_content)
                
                # 更新状态栏
                self.app.update_status(f"日志已保存到: {file_path}")
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("错误", f"保存日志失败: {str(e)}")
    
    def get_log_content(self) -> str:
        """
        获取日志内容
        
        Returns:
            日志内容
        """
        return self.log_text.get(1.0, tk.END) 