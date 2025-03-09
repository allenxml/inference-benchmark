# -*- coding: utf-8 -*-
"""
API密钥管理标签页模块，实现API密钥管理界面。
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Any

from config.config_manager import ApiKeyConfig
from utils.security import mask_sensitive_data


class ApiKeyTab(ttk.Frame):
    """API密钥管理标签页类"""
    
    def __init__(self, parent, app):
        """
        初始化API密钥管理标签页
        
        Args:
            parent: 父窗口
            app: 应用实例
        """
        super().__init__(parent)
        self.app = app
        
        # 标题
        ttk.Label(self, text="API密钥管理", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5, columnspan=3)
        
        # 服务名称
        ttk.Label(self, text="服务名称:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.service_var = tk.StringVar()
        service_values = ["openai", "vllm"]
        service_combo = ttk.Combobox(self, textvariable=self.service_var, values=service_values, width=30)
        service_combo.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # API密钥
        ttk.Label(self, text="API密钥:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.api_key_var = tk.StringVar()
        self.api_key_entry = ttk.Entry(self, textvariable=self.api_key_var, width=50, show="*")
        self.api_key_entry.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # 显示/隐藏密钥
        self.show_key_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self, text="显示密钥", variable=self.show_key_var, command=self.toggle_key_visibility).grid(row=2, column=2, sticky=tk.W, pady=2)
        
        # 按钮
        button_frame = ttk.Frame(self)
        button_frame.grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=10)
        
        ttk.Button(button_frame, text="添加/更新", command=self.add_api_key, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="删除", command=self.delete_api_key, width=15).pack(side=tk.LEFT, padx=5)
        
        # 已配置的API密钥列表
        ttk.Label(self, text="已配置的API密钥:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky=tk.W, pady=5, columnspan=3)
        
        self.api_keys_listbox = tk.Listbox(self, height=10, width=70)
        self.api_keys_listbox.grid(row=5, column=0, columnspan=3, sticky=tk.W+tk.E, pady=2)
        self.api_keys_listbox.bind('<<ListboxSelect>>', self.on_api_key_select)
        
        # 滚动条
        api_keys_scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.api_keys_listbox.yview)
        api_keys_scrollbar.grid(row=5, column=3, sticky=tk.N+tk.S)
        self.api_keys_listbox.config(yscrollcommand=api_keys_scrollbar.set)
    
    def load_config(self, api_key_config: ApiKeyConfig):
        """
        加载API密钥配置
        
        Args:
            api_key_config: API密钥配置对象
        """
        self.api_keys_listbox.delete(0, tk.END)
        services = api_key_config.list_services()
        for service in services:
            key = api_key_config.get_key(service)
            masked_key = mask_sensitive_data(key)
            self.api_keys_listbox.insert(tk.END, f"{service}: {masked_key}")
    
    def toggle_key_visibility(self):
        """切换API密钥的可见性"""
        if self.show_key_var.get():
            self.api_key_entry.config(show="")
        else:
            self.api_key_entry.config(show="*")
    
    def add_api_key(self):
        """添加或更新API密钥"""
        service = self.service_var.get()
        api_key = self.api_key_var.get()
        
        if not service:
            messagebox.showerror("错误", "请输入服务名称")
            return
        
        if not api_key:
            messagebox.showerror("错误", "请输入API密钥")
            return
        
        # 添加或更新API密钥
        self.app.config_manager.api_keys.add_key(service, api_key)
        
        # 更新列表
        self.load_config(self.app.config_manager.api_keys)
        
        # 清空输入框
        self.service_var.set("")
        self.api_key_var.set("")
        
        # 更新状态栏
        self.app.update_status(f"已添加/更新服务 '{service}' 的API密钥")
    
    def delete_api_key(self):
        """删除API密钥"""
        selected = self.api_keys_listbox.curselection()
        if not selected:
            messagebox.showerror("错误", "请选择要删除的API密钥")
            return
        
        index = selected[0]
        item = self.api_keys_listbox.get(index)
        service = item.split(":")[0].strip()
        
        # 确认删除
        if messagebox.askyesno("确认", f"确定要删除服务 '{service}' 的API密钥吗？"):
            # 删除API密钥
            self.app.config_manager.api_keys.delete_key(service)
            
            # 更新列表
            self.load_config(self.app.config_manager.api_keys)
            
            # 更新状态栏
            self.app.update_status(f"已删除服务 '{service}' 的API密钥")
    
    def on_api_key_select(self, event):
        """
        API密钥选择事件处理
        
        Args:
            event: 事件对象
        """
        selected = self.api_keys_listbox.curselection()
        if not selected:
            return
        
        index = selected[0]
        item = self.api_keys_listbox.get(index)
        service = item.split(":")[0].strip()
        
        # 设置服务名称
        self.service_var.set(service)
        
        # 设置API密钥（从配置中获取，而不是从列表项中获取）
        api_key = self.app.config_manager.api_keys.get_key(service)
        if api_key:
            self.api_key_var.set(api_key) 