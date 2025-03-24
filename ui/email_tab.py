# -*- coding: utf-8 -*-
"""
邮件配置标签页模块，实现邮件配置界面。
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any

from utils.email import EmailSender


class EmailTab(ttk.Frame):
    """邮件配置标签页类"""
    
    def __init__(self, parent, app):
        """
        初始化邮件配置标签页
        
        Args:
            parent: 父窗口
            app: 应用实例
        """
        super().__init__(parent)
        self.app = app
        
        # 标题
        ttk.Label(self, text="邮件配置", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5, columnspan=3)
        
        # 发件人邮箱
        ttk.Label(self, text="发件人邮箱:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.email_from_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.email_from_var, width=40).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # 收件人邮箱
        ttk.Label(self, text="收件人邮箱:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.email_to_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.email_to_var, width=40).grid(row=2, column=1, sticky=tk.W, pady=2)
        ttk.Label(self, text="(多个收件人用逗号分隔)").grid(row=2, column=2, sticky=tk.W, pady=2)
        
        # 邮箱密码
        ttk.Label(self, text="邮箱密码:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.email_password_var = tk.StringVar()
        self.password_entry = ttk.Entry(self, textvariable=self.email_password_var, width=40, show="*")
        self.password_entry.grid(row=3, column=1, sticky=tk.W, pady=2)
        
        # 显示/隐藏密码
        self.show_password_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self, text="显示密码", variable=self.show_password_var, command=self.toggle_password_visibility).grid(row=3, column=2, sticky=tk.W, pady=2)
        
        # SMTP服务器
        ttk.Label(self, text="SMTP服务器:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.smtp_server_var = tk.StringVar(value="smtp.qq.com")
        ttk.Entry(self, textvariable=self.smtp_server_var, width=40).grid(row=4, column=1, sticky=tk.W, pady=2)
        
        # SMTP端口
        ttk.Label(self, text="SMTP端口:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.smtp_port_var = tk.IntVar(value=465)
        ttk.Entry(self, textvariable=self.smtp_port_var, width=10).grid(row=5, column=1, sticky=tk.W, pady=2)
        
        # 添加自定义邮件内容
        ttk.Label(self, text="自定义邮件内容:", font=("Arial", 10, "bold")).grid(row=6, column=0, sticky=tk.W, pady=5)
        ttk.Label(self, text="(将会添加到测试结果邮件的开头)").grid(row=6, column=1, sticky=tk.W, pady=5)
        
        # 自定义邮件内容文本框
        self.custom_content_frame = ttk.Frame(self)
        self.custom_content_frame.grid(row=7, column=0, columnspan=3, sticky=tk.W+tk.E, pady=5)
        
        # 使用Text控件而不是Entry，以支持多行文本
        self.custom_content_text = tk.Text(self.custom_content_frame, height=10, width=80, wrap=tk.WORD)
        self.custom_content_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 添加滚动条
        custom_content_scrollbar = ttk.Scrollbar(self.custom_content_frame, orient=tk.VERTICAL, command=self.custom_content_text.yview)
        custom_content_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.custom_content_text.config(yscrollcommand=custom_content_scrollbar.set)
        
        # 测试邮件按钮
        button_frame = ttk.Frame(self)
        button_frame.grid(row=8, column=0, columnspan=3, sticky=tk.W, pady=10)
        
        ttk.Button(button_frame, text="测试邮件", command=self.test_email, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="保存配置", command=self.save_config, width=15).pack(side=tk.LEFT, padx=5)
        
        # 说明
        ttk.Label(self, text="说明:", font=("Arial", 10, "bold")).grid(row=9, column=0, sticky=tk.W, pady=5)
        ttk.Label(self, text="1. 对于QQ邮箱，请使用授权码而不是登录密码").grid(row=10, column=0, columnspan=3, sticky=tk.W)
        ttk.Label(self, text="2. 授权码可在QQ邮箱设置 -> 账户 -> POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务中获取").grid(row=11, column=0, columnspan=3, sticky=tk.W)
        ttk.Label(self, text="3. 如果使用其他邮箱服务，请修改SMTP服务器和端口").grid(row=12, column=0, columnspan=3, sticky=tk.W)
        ttk.Label(self, text="4. 自定义邮件内容将添加到测试结果邮件的开头").grid(row=13, column=0, columnspan=3, sticky=tk.W)
    
    def load_config(self, config: Dict[str, Any]):
        """
        加载邮件配置
        
        Args:
            config: 配置字典
        """
        if "email_from" in config:
            self.email_from_var.set(config["email_from"])
        if "email_to" in config:
            self.email_to_var.set(config["email_to"])
        if "email_password" in config:
            self.email_password_var.set(config["email_password"])
        if "smtp_server" in config:
            self.smtp_server_var.set(config["smtp_server"])
        if "smtp_port" in config:
            self.smtp_port_var.set(config["smtp_port"])
        if "custom_email_content" in config:
            self.custom_content_text.delete(1.0, tk.END)
            self.custom_content_text.insert(tk.END, config["custom_email_content"])
    
    def get_config(self) -> Dict[str, Any]:
        """
        获取邮件配置
        
        Returns:
            配置字典
        """
        return {
            "email_from": self.email_from_var.get(),
            "email_to": self.email_to_var.get(),
            "email_password": self.email_password_var.get(),
            "smtp_server": self.smtp_server_var.get(),
            "smtp_port": self.smtp_port_var.get(),
            "custom_email_content": self.custom_content_text.get(1.0, tk.END).strip()
        }
    
    def toggle_password_visibility(self):
        """切换密码的可见性"""
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")
    
    def save_config(self):
        """保存配置"""
        self.app.config_manager.email.update(self.get_config())
        self.app.update_status("邮件配置已保存")
    
    def test_email(self):
        """测试邮件发送"""
        config = self.get_config()
        
        if not config["email_from"]:
            messagebox.showerror("错误", "请输入发件人邮箱")
            return
        
        if not config["email_to"]:
            messagebox.showerror("错误", "请输入收件人邮箱")
            return
        
        if not config["email_password"]:
            messagebox.showerror("错误", "请输入邮箱密码")
            return
        
        # 创建邮件发送器
        email_sender = EmailSender(config)
        
        # 发送测试邮件
        subject = "LLM基准测试工具 - 测试邮件"
        body = "这是一封测试邮件，用于验证邮件配置是否正确。\n\n如果您收到这封邮件，说明邮件配置正确。"
        
        # 显示发送中对话框
        self.app.update_status("正在发送测试邮件...")
        
        # 在新线程中发送邮件
        import threading
        
        def send_email_thread():
            success = email_sender.send_email(subject, body)
            
            # 在主线程中更新UI
            self.after(0, lambda: self._handle_email_result(success))
        
        threading.Thread(target=send_email_thread, daemon=True).start()
    
    def _handle_email_result(self, success: bool):
        """
        处理邮件发送结果
        
        Args:
            success: 是否发送成功
        """
        if success:
            messagebox.showinfo("成功", "测试邮件发送成功！")
            self.app.update_status("测试邮件发送成功")
        else:
            messagebox.showerror("错误", "测试邮件发送失败，请检查邮件配置")
            self.app.update_status("测试邮件发送失败") 