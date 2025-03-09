# -*- coding: utf-8 -*-
"""
测试场景标签页模块，实现测试场景管理界面。
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Any
import traceback


def show_error_dialog(error_msg):
    """显示错误对话框"""
    import tkinter as tk
    from tkinter import messagebox
    
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    messagebox.showerror("错误", error_msg)
    root.destroy()


class ScenariosTab(ttk.Frame):
    """测试场景标签页类"""
    
    def __init__(self, parent, app):
        """
        初始化测试场景标签页
        
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
        
        # 左侧 - 场景列表
        ttk.Label(left_frame, text="测试场景列表", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5, columnspan=2)
        
        # 场景列表
        self.scenario_tree = ttk.Treeview(left_frame, columns=("input", "output", "concurrency", "requests"), show="headings")
        self.scenario_tree.grid(row=1, column=0, columnspan=2, sticky=tk.NSEW, pady=2)
        
        # 设置列标题
        self.scenario_tree.heading("input", text="输入长度")
        self.scenario_tree.heading("output", text="输出长度")
        self.scenario_tree.heading("concurrency", text="并发数")
        self.scenario_tree.heading("requests", text="请求数")
        
        # 设置列宽
        self.scenario_tree.column("input", width=80, anchor=tk.CENTER)
        self.scenario_tree.column("output", width=80, anchor=tk.CENTER)
        self.scenario_tree.column("concurrency", width=80, anchor=tk.CENTER)
        self.scenario_tree.column("requests", width=80, anchor=tk.CENTER)
        
        # 绑定选择事件
        self.scenario_tree.bind("<<TreeviewSelect>>", self.on_scenario_select)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.scenario_tree.yview)
        scrollbar.grid(row=1, column=2, sticky=tk.NS)
        self.scenario_tree.configure(yscrollcommand=scrollbar.set)
        
        # 按钮
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Button(button_frame, text="添加", command=self.add_scenario, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="更新", command=self.update_scenario, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="删除", command=self.delete_scenario, width=10).pack(side=tk.LEFT, padx=5)
        
        # 右侧 - 场景编辑
        ttk.Label(right_frame, text="场景编辑", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5, columnspan=2)
        
        # 场景名称
        ttk.Label(right_frame, text="场景名称:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.name_var = tk.StringVar()
        ttk.Entry(right_frame, textvariable=self.name_var, width=30).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # 输入长度
        ttk.Label(right_frame, text="输入长度:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.input_len_var = tk.IntVar(value=50)
        ttk.Entry(right_frame, textvariable=self.input_len_var, width=10).grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # 输出长度
        ttk.Label(right_frame, text="输出长度:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.output_len_var = tk.IntVar(value=1024)
        ttk.Entry(right_frame, textvariable=self.output_len_var, width=10).grid(row=3, column=1, sticky=tk.W, pady=2)
        
        # 并发数
        ttk.Label(right_frame, text="并发数:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.concurrency_var = tk.IntVar(value=4)
        ttk.Entry(right_frame, textvariable=self.concurrency_var, width=10).grid(row=4, column=1, sticky=tk.W, pady=2)
        
        # 请求数
        ttk.Label(right_frame, text="请求数:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.num_prompts_var = tk.IntVar(value=20)
        ttk.Entry(right_frame, textvariable=self.num_prompts_var, width=10).grid(row=5, column=1, sticky=tk.W, pady=2)
        
        # 范围比率
        ttk.Label(right_frame, text="范围比率:").grid(row=6, column=0, sticky=tk.W, pady=2)
        self.range_ratio_var = tk.DoubleVar(value=1.0)
        ttk.Entry(right_frame, textvariable=self.range_ratio_var, width=10).grid(row=6, column=1, sticky=tk.W, pady=2)
        
        # 前缀长度
        ttk.Label(right_frame, text="前缀长度:").grid(row=7, column=0, sticky=tk.W, pady=2)
        self.prefix_len_var = tk.IntVar(value=0)
        ttk.Entry(right_frame, textvariable=self.prefix_len_var, width=10).grid(row=7, column=1, sticky=tk.W, pady=2)
        
        # 说明
        ttk.Label(right_frame, text="说明:", font=("Arial", 10, "bold")).grid(row=8, column=0, sticky=tk.W, pady=5)
        ttk.Label(right_frame, text="1. 输入长度: 每个请求的输入词元数").grid(row=9, column=0, columnspan=2, sticky=tk.W)
        ttk.Label(right_frame, text="2. 输出长度: 每个请求的输出词元数").grid(row=10, column=0, columnspan=2, sticky=tk.W)
        ttk.Label(right_frame, text="3. 并发数: 最大并发请求数").grid(row=11, column=0, columnspan=2, sticky=tk.W)
        ttk.Label(right_frame, text="4. 请求数: 要处理的提示数量").grid(row=12, column=0, columnspan=2, sticky=tk.W)
        ttk.Label(right_frame, text="5. 范围比率: 输入/输出长度的采样比例范围").grid(row=13, column=0, columnspan=2, sticky=tk.W)
        ttk.Label(right_frame, text="6. 前缀长度: 随机上下文前的固定前缀词元数").grid(row=14, column=0, columnspan=2, sticky=tk.W)
        
        # 配置grid权重
        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)
        
        # 当前选中的场景索引
        self.selected_index = None
    
    def load_config(self, scenarios: List[Dict[str, Any]]):
        """
        加载测试场景配置
        
        Args:
            scenarios: 测试场景列表
        """
        # 清空树视图
        for item in self.scenario_tree.get_children():
            self.scenario_tree.delete(item)
        
        # 添加场景到树视图
        for i, scenario in enumerate(scenarios):
            name = scenario.get("name", f"场景{i+1}")
            input_len = scenario.get("input_len", 0)
            output_len = scenario.get("output_len", 0)
            concurrency = scenario.get("concurrency", 0)
            num_prompts = scenario.get("num_prompts", 0)
            
            self.scenario_tree.insert("", tk.END, text=name, values=(input_len, output_len, concurrency, num_prompts))
    
    def on_scenario_select(self, event):
        """
        场景选择事件处理
        
        Args:
            event: 事件对象
        """
        selected_items = self.scenario_tree.selection()
        if not selected_items:
            return
        
        # 获取选中项的索引
        self.selected_index = self.scenario_tree.index(selected_items[0])
        
        # 获取场景数据
        scenarios = self.app.config_manager.scenarios.get_scenarios()
        if self.selected_index < len(scenarios):
            scenario = scenarios[self.selected_index]
            
            # 更新表单
            self.name_var.set(scenario.get("name", f"场景{self.selected_index+1}"))
            self.input_len_var.set(scenario.get("input_len", 50))
            self.output_len_var.set(scenario.get("output_len", 1024))
            self.concurrency_var.set(scenario.get("concurrency", 4))
            self.num_prompts_var.set(scenario.get("num_prompts", 20))
            self.range_ratio_var.set(scenario.get("range_ratio", 1.0))
            self.prefix_len_var.set(scenario.get("prefix_len", 0))
    
    def get_form_data(self) -> Dict[str, Any]:
        """
        获取表单数据
        
        Returns:
            表单数据字典
        """
        try:
            return {
                "name": self.name_var.get() or f"场景{len(self.app.config_manager.scenarios.get_scenarios())+1}",
                "input_len": self.input_len_var.get(),
                "output_len": self.output_len_var.get(),
                "concurrency": self.concurrency_var.get(),
                "num_prompts": self.num_prompts_var.get(),
                "range_ratio": self.range_ratio_var.get(),
                "prefix_len": self.prefix_len_var.get()
            }
        except tk.TclError:
            messagebox.showerror("错误", "请输入有效的数值")
            return None
    
    def add_scenario(self):
        """添加测试场景"""
        # 获取表单数据
        scenario = self.get_form_data()
        if not scenario:
            return
        
        # 添加场景
        self.app.config_manager.scenarios.add_scenario(scenario)
        
        # 更新列表
        self.load_config(self.app.config_manager.scenarios.get_scenarios())
        
        # 更新主标签页的场景列表
        self.app.main_tab.load_scenarios()
        
        # 更新状态栏
        self.app.update_status(f"已添加测试场景: {scenario['name']}")
    
    def update_scenario(self):
        """更新测试场景"""
        if self.selected_index is None:
            messagebox.showerror("错误", "请选择要更新的测试场景")
            return
        
        # 获取表单数据
        scenario = self.get_form_data()
        if not scenario:
            return
        
        # 更新场景
        if self.app.config_manager.scenarios.update_scenario(self.selected_index, scenario):
            # 更新列表
            self.load_config(self.app.config_manager.scenarios.get_scenarios())
            
            # 更新主标签页的场景列表
            self.app.main_tab.load_scenarios()
            
            # 更新状态栏
            self.app.update_status(f"已更新测试场景: {scenario['name']}")
        else:
            messagebox.showerror("错误", "更新测试场景失败")
    
    def delete_scenario(self):
        """删除测试场景"""
        if self.selected_index is None:
            messagebox.showerror("错误", "请选择要删除的测试场景")
            return
        
        # 获取场景名称
        scenarios = self.app.config_manager.scenarios.get_scenarios()
        if self.selected_index < len(scenarios):
            scenario = scenarios[self.selected_index]
            name = scenario.get("name", f"场景{self.selected_index+1}")
            
            # 确认删除
            if messagebox.askyesno("确认", f"确定要删除测试场景 '{name}' 吗？"):
                # 删除场景
                if self.app.config_manager.scenarios.delete_scenario(self.selected_index):
                    # 更新列表
                    self.load_config(self.app.config_manager.scenarios.get_scenarios())
                    
                    # 更新主标签页的场景列表
                    self.app.main_tab.load_scenarios()
                    
                    # 清空选中索引
                    self.selected_index = None
                    
                    # 更新状态栏
                    self.app.update_status(f"已删除测试场景: {name}")
                else:
                    messagebox.showerror("错误", "删除测试场景失败") 