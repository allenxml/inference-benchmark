# -*- coding: utf-8 -*-
"""
主页标签页模块，实现主要配置界面。
"""
import tkinter as tk
from tkinter import ttk, filedialog
from typing import Dict, List, Any


class MainTab(ttk.Frame):
    """主页标签页类"""
    
    def __init__(self, parent, app):
        """
        初始化主页标签页
        
        Args:
            parent: 父窗口
            app: 应用实例
        """
        super().__init__(parent)
        self.app = app
        
        # 创建左右分栏
        left_frame = ttk.Frame(self)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        right_frame = ttk.Frame(self)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧 - 基本配置
        ttk.Label(left_frame, text="基本配置", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5, columnspan=2)
        
        # 服务器URL
        ttk.Label(left_frame, text="服务器URL:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.url_var = tk.StringVar(value="http://127.0.0.1:8000")
        ttk.Entry(left_frame, textvariable=self.url_var, width=40).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # 模型名称
        ttk.Label(left_frame, text="模型名称:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.model_var = tk.StringVar(value="test")
        ttk.Entry(left_frame, textvariable=self.model_var, width=40).grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # 分词器路径
        ttk.Label(left_frame, text="分词器路径:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.tokenizer_var = tk.StringVar()
        tokenizer_frame = ttk.Frame(left_frame)
        tokenizer_frame.grid(row=3, column=1, sticky=tk.W, pady=2)
        ttk.Entry(tokenizer_frame, textvariable=self.tokenizer_var, width=30).pack(side=tk.LEFT)
        ttk.Button(tokenizer_frame, text="浏览...", command=self.browse_tokenizer).pack(side=tk.LEFT, padx=5)
        
        # 后端类型
        ttk.Label(left_frame, text="后端类型:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.backend_var = tk.StringVar(value="openai")
        backend_values = ["openai", "vllm"]
        backend_combo = ttk.Combobox(left_frame, textvariable=self.backend_var, values=backend_values, state="readonly", width=38)
        backend_combo.grid(row=4, column=1, sticky=tk.W, pady=2)
        
        # 端点
        ttk.Label(left_frame, text="API端点:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.endpoint_var = tk.StringVar(value="/v1/completions")
        ttk.Entry(left_frame, textvariable=self.endpoint_var, width=40).grid(row=5, column=1, sticky=tk.W, pady=2)
        
        # 右侧 - 测试场景选择
        ttk.Label(right_frame, text="测试场景", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5, columnspan=2)
        
        # 场景列表
        ttk.Label(right_frame, text="选择测试场景:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.scenario_listbox = tk.Listbox(right_frame, height=8, width=40, selectmode=tk.MULTIPLE)
        self.scenario_listbox.grid(row=2, column=0, columnspan=2, sticky=tk.W+tk.E, pady=2)
        
        # 场景列表滚动条
        scenario_scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.scenario_listbox.yview)
        scenario_scrollbar.grid(row=2, column=2, sticky=tk.N+tk.S)
        self.scenario_listbox.config(yscrollcommand=scenario_scrollbar.set)
        
        # 选择全部/取消全部按钮
        button_frame = ttk.Frame(right_frame)
        button_frame.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        ttk.Button(button_frame, text="全选", command=self.select_all_scenarios).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消全选", command=self.deselect_all_scenarios).pack(side=tk.LEFT, padx=5)
        
        # 邮件选项
        ttk.Label(right_frame, text="邮件选项:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky=tk.W, pady=5, columnspan=2)
        
        # 发送每轮邮件
        self.send_each_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(right_frame, text="每轮测试后发送邮件", variable=self.send_each_var).grid(row=5, column=0, sticky=tk.W, pady=2)
        
        # 发送最终汇总邮件
        self.send_final_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(right_frame, text="发送最终汇总邮件", variable=self.send_final_var).grid(row=6, column=0, sticky=tk.W, pady=2)
        
        # 底部 - 开始测试按钮
        button_frame = ttk.Frame(self)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="开始测试", command=self.start_benchmark, width=20).pack(side=tk.RIGHT, padx=10)
        ttk.Button(button_frame, text="保存配置", command=self.save_config, width=20).pack(side=tk.RIGHT, padx=10)
    
    def browse_tokenizer(self):
        """浏览选择分词器路径"""
        tokenizer_path = filedialog.askdirectory(title="选择分词器路径")
        if tokenizer_path:
            self.tokenizer_var.set(tokenizer_path)
    
    def load_config(self, config: Dict[str, Any]):
        """
        加载配置
        
        Args:
            config: 配置字典
        """
        if "base_url" in config:
            self.url_var.set(config["base_url"])
        if "model" in config:
            self.model_var.set(config["model"])
        if "tokenizer" in config:
            self.tokenizer_var.set(config["tokenizer"])
        if "backend" in config:
            self.backend_var.set(config["backend"])
        if "endpoint" in config:
            self.endpoint_var.set(config["endpoint"])
        
        # 加载测试场景
        self.load_scenarios()
    
    def load_scenarios(self):
        """加载测试场景到列表框"""
        self.scenario_listbox.delete(0, tk.END)
        scenarios = self.app.config_manager.scenarios.get_scenarios()
        for scenario in scenarios:
            name = scenario.get("name", "未命名场景")
            input_len = scenario.get("input_len", 0)
            output_len = scenario.get("output_len", 0)
            concurrency = scenario.get("concurrency", 0)
            self.scenario_listbox.insert(tk.END, f"{name} (输入={input_len}, 输出={output_len}, 并发={concurrency})")
    
    def get_config(self) -> Dict[str, Any]:
        """
        获取配置
        
        Returns:
            配置字典
        """
        return {
            "base_url": self.url_var.get(),
            "model": self.model_var.get(),
            "tokenizer": self.tokenizer_var.get(),
            "backend": self.backend_var.get(),
            "endpoint": self.endpoint_var.get()
        }
    
    def get_selected_scenarios(self) -> List[int]:
        """
        获取选中的测试场景索引
        
        Returns:
            选中的测试场景索引列表
        """
        return list(self.scenario_listbox.curselection())
    
    def select_all_scenarios(self):
        """选择所有测试场景"""
        self.scenario_listbox.selection_set(0, tk.END)
    
    def deselect_all_scenarios(self):
        """取消选择所有测试场景"""
        self.scenario_listbox.selection_clear(0, tk.END)
    
    def save_config(self):
        """保存配置"""
        self.app.save_configs()
    
    def start_benchmark(self):
        """启动基准测试"""
        self.app.start_benchmark() 