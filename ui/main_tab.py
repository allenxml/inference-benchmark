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
        
        # 创建布局
        self.create_widgets()
        
        # 绑定快捷键
        self.bind_shortcuts()
    
    def bind_shortcuts(self):
        """绑定快捷键"""
        # 为按钮添加提示文本
        if hasattr(self, 'start_button'):
            self.start_button.config(text="开始测试 (Ctrl+R)")
        if hasattr(self, 'select_all_button'):
            self.select_all_button.config(text="全选 (Ctrl+A)")
    
    def create_widgets(self):
        """创建界面元素"""
        # 设置列权重
        self.grid_columnconfigure(0, weight=1)  # 左侧区域
        self.grid_columnconfigure(1, weight=1)  # 右侧区域
        
        # 左侧 - 基本配置
        left_frame = ttk.LabelFrame(self, text="基本配置")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # URL配置
        ttk.Label(left_frame, text="服务器URL:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.url_var = tk.StringVar(value="http://127.0.0.1:8000")
        ttk.Entry(left_frame, textvariable=self.url_var, width=40).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        # 模型名称
        ttk.Label(left_frame, text="模型名称:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.model_var = tk.StringVar(value="test")
        ttk.Entry(left_frame, textvariable=self.model_var, width=40).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # 分词器路径
        ttk.Label(left_frame, text="分词器路径:").grid(row=2, column=0, sticky=tk.W, pady=2)
        tokenizer_frame = ttk.Frame(left_frame)
        tokenizer_frame.grid(row=2, column=1, sticky=tk.W, pady=2)
        self.tokenizer_var = tk.StringVar()
        tokenizer_entry = ttk.Entry(tokenizer_frame, textvariable=self.tokenizer_var, width=35)
        tokenizer_entry.grid(row=0, column=0, sticky=tk.W)
        browse_button = ttk.Button(tokenizer_frame, text="浏览...", command=self.browse_tokenizer)
        browse_button.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # 后端类型
        ttk.Label(left_frame, text="后端类型:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.backend_var = tk.StringVar(value="openai")
        backend_values = ["openai", "vllm"]
        backend_combo = ttk.Combobox(left_frame, textvariable=self.backend_var, values=backend_values, state="readonly", width=38)
        backend_combo.grid(row=3, column=1, sticky=tk.W, pady=2)
        
        # 端点
        ttk.Label(left_frame, text="API端点:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.endpoint_var = tk.StringVar(value="/v1/completions")
        ttk.Entry(left_frame, textvariable=self.endpoint_var, width=40).grid(row=4, column=1, sticky=tk.W, pady=2)
        
        # 保存配置按钮
        self.save_button = ttk.Button(left_frame, text="保存配置", command=self.save_config)
        self.save_button.grid(row=5, column=0, columnspan=2, pady=10)
        
        # 右侧 - 测试场景选择
        right_frame = ttk.LabelFrame(self, text="测试场景")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # 场景列表
        ttk.Label(right_frame, text="选择测试场景:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(right_frame, text="(名称-输入/输出/并发/请求数)").grid(row=0, column=1, sticky=tk.W, pady=2)
        self.scenario_listbox = tk.Listbox(right_frame, height=8, width=38, selectmode=tk.MULTIPLE)
        self.scenario_listbox.grid(row=1, column=0, columnspan=2, sticky=tk.W+tk.E, pady=2)
        
        # 场景列表滚动条
        scenario_scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.scenario_listbox.yview)
        scenario_scrollbar.grid(row=1, column=2, sticky=tk.N+tk.S)
        self.scenario_listbox.config(yscrollcommand=scenario_scrollbar.set)
        
        # 选择全部/取消全部按钮
        button_frame = ttk.Frame(right_frame)
        button_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        self.select_all_button = ttk.Button(button_frame, text="全选", command=self.select_all_scenarios)
        self.select_all_button.grid(row=0, column=0, padx=5)
        
        self.deselect_all_button = ttk.Button(button_frame, text="取消全选", command=self.deselect_all_scenarios)
        self.deselect_all_button.grid(row=0, column=1, padx=5)
        
        # 邮件选项
        email_frame = ttk.LabelFrame(right_frame, text="邮件选项")
        email_frame.grid(row=3, column=0, columnspan=2, sticky=tk.W+tk.E, pady=5)
        
        self.send_each_var = tk.BooleanVar(value=True)
        each_checkbox = ttk.Checkbutton(email_frame, text="每轮测试后发送邮件", variable=self.send_each_var)
        each_checkbox.grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.send_final_var = tk.BooleanVar(value=True)
        final_checkbox = ttk.Checkbutton(email_frame, text="最终汇总发送邮件", variable=self.send_final_var)
        final_checkbox.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        # 开始测试按钮
        self.start_button = ttk.Button(right_frame, text="开始测试", command=self.start_benchmark, width=20)
        self.start_button.grid(row=4, column=0, columnspan=2, pady=10)
    
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
            num_prompts = scenario.get("num_prompts", 0)
            range_ratio = scenario.get("range_ratio", 1.0)
            prefix_len = scenario.get("prefix_len", 0)
            self.scenario_listbox.insert(tk.END, f"{name} - {input_len}/{output_len}/{concurrency}/{num_prompts}")
    
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