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
        self.selected_index = None
        
        # 创建布局
        self.create_widgets()
        
        # 绑定快捷键
        self.bind_shortcuts()
        
        # 加载配置
        self.load_config(self.app.config_manager.scenarios.get_scenarios())
    
    def create_widgets(self):
        """创建界面元素"""
        # 设置列权重
        self.grid_columnconfigure(0, weight=1)  # 左侧列表区域
        self.grid_columnconfigure(1, weight=2)  # 右侧表单区域
        
        # 左侧的场景列表框架
        list_frame = ttk.LabelFrame(self, text="测试场景列表")
        list_frame.grid(row=0, column=0, rowspan=20, sticky="nsew", padx=5, pady=5)
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        
        # 使用Treeview创建表格
        columns = ("name", "input_len", "output_len", "concurrency", "num_prompts", "range_ratio", "prefix_len")
        self.scenario_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=20)
        
        # 定义列头
        self.scenario_tree.heading("name", text="场景名称")
        self.scenario_tree.heading("input_len", text="输入长度")
        self.scenario_tree.heading("output_len", text="输出长度")
        self.scenario_tree.heading("concurrency", text="并发数")
        self.scenario_tree.heading("num_prompts", text="请求数")
        self.scenario_tree.heading("range_ratio", text="范围比率")
        self.scenario_tree.heading("prefix_len", text="前缀长度")
        
        # 设置列宽
        self.scenario_tree.column("name", width=100, anchor="w")
        self.scenario_tree.column("input_len", width=60, anchor="center")
        self.scenario_tree.column("output_len", width=60, anchor="center")
        self.scenario_tree.column("concurrency", width=50, anchor="center")
        self.scenario_tree.column("num_prompts", width=50, anchor="center")
        self.scenario_tree.column("range_ratio", width=60, anchor="center")
        self.scenario_tree.column("prefix_len", width=60, anchor="center")
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.scenario_tree.yview)
        self.scenario_tree.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        self.scenario_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # 绑定选择事件
        self.scenario_tree.bind("<<TreeviewSelect>>", self.on_scenario_select)
        
        # 按钮框架
        button_frame = ttk.Frame(list_frame)
        button_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # 添加按钮
        self.add_button = ttk.Button(button_frame, text="添加场景", command=self.add_scenario, width=15)
        self.add_button.grid(row=0, column=0, padx=2)
        
        # 编辑按钮
        self.edit_button = ttk.Button(button_frame, text="编辑场景", command=self.edit_scenario, width=15)
        self.edit_button.grid(row=0, column=1, padx=2)
        self.edit_button.config(state=tk.DISABLED)
        
        # 删除按钮
        self.delete_button = ttk.Button(button_frame, text="删除场景", command=self.delete_scenario, width=15)
        self.delete_button.grid(row=0, column=2, padx=2)
        self.delete_button.config(state=tk.DISABLED)
        
        # 全选/全不选按钮
        additional_buttons_frame = ttk.Frame(list_frame)
        additional_buttons_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        self.select_all_button = ttk.Button(additional_buttons_frame, text="全选", 
                                           command=self.select_all_scenarios, width=15)
        self.select_all_button.grid(row=0, column=0, padx=2)
        
        self.deselect_all_button = ttk.Button(additional_buttons_frame, text="全不选",
                                             command=self.deselect_all_scenarios, width=15)
        self.deselect_all_button.grid(row=0, column=1, padx=2)
        
        # 保存按钮
        self.save_button = ttk.Button(additional_buttons_frame, text="保存配置", 
                                     command=self.save_config, width=15)
        self.save_button.grid(row=0, column=2, padx=2)
        
        # 右侧 - 场景编辑
        ttk.Label(self, text="场景编辑", font=("Arial", 12, "bold")).grid(row=0, column=1, sticky=tk.W, pady=5, columnspan=2)
        
        # 场景名称
        ttk.Label(self, text="场景名称:").grid(row=1, column=1, sticky=tk.W, pady=2)
        self.name_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.name_var, width=30).grid(row=1, column=2, sticky=tk.W, pady=2)
        
        # 输入长度
        ttk.Label(self, text="输入长度:").grid(row=2, column=1, sticky=tk.W, pady=2)
        self.input_len_var = tk.IntVar(value=50)
        ttk.Entry(self, textvariable=self.input_len_var, width=10).grid(row=2, column=2, sticky=tk.W, pady=2)
        
        # 输出长度
        ttk.Label(self, text="输出长度:").grid(row=3, column=1, sticky=tk.W, pady=2)
        self.output_len_var = tk.IntVar(value=1024)
        ttk.Entry(self, textvariable=self.output_len_var, width=10).grid(row=3, column=2, sticky=tk.W, pady=2)
        
        # 并发数
        ttk.Label(self, text="并发数:").grid(row=4, column=1, sticky=tk.W, pady=2)
        self.concurrency_var = tk.IntVar(value=4)
        ttk.Entry(self, textvariable=self.concurrency_var, width=10).grid(row=4, column=2, sticky=tk.W, pady=2)
        
        # 请求数
        ttk.Label(self, text="请求数:").grid(row=5, column=1, sticky=tk.W, pady=2)
        self.num_prompts_var = tk.IntVar(value=20)
        ttk.Entry(self, textvariable=self.num_prompts_var, width=10).grid(row=5, column=2, sticky=tk.W, pady=2)
        
        # 范围比率
        ttk.Label(self, text="范围比率:").grid(row=6, column=1, sticky=tk.W, pady=2)
        self.range_ratio_var = tk.DoubleVar(value=1.0)
        ttk.Entry(self, textvariable=self.range_ratio_var, width=10).grid(row=6, column=2, sticky=tk.W, pady=2)
        
        # 前缀长度
        ttk.Label(self, text="前缀长度:").grid(row=7, column=1, sticky=tk.W, pady=2)
        self.prefix_len_var = tk.IntVar(value=0)
        ttk.Entry(self, textvariable=self.prefix_len_var, width=10).grid(row=7, column=2, sticky=tk.W, pady=2)
        
        # 说明
        ttk.Label(self, text="说明:", font=("Arial", 10, "bold")).grid(row=8, column=1, sticky=tk.W, pady=5)
        ttk.Label(self, text="1. 输入长度: 每个请求的输入词元数").grid(row=9, column=1, columnspan=2, sticky=tk.W)
        ttk.Label(self, text="2. 输出长度: 每个请求的输出词元数").grid(row=10, column=1, columnspan=2, sticky=tk.W)
        ttk.Label(self, text="3. 并发数: 最大并发请求数").grid(row=11, column=1, columnspan=2, sticky=tk.W)
        ttk.Label(self, text="4. 请求数: 要处理的提示数量").grid(row=12, column=1, columnspan=2, sticky=tk.W)
        ttk.Label(self, text="5. 范围比率: 输入/输出长度的采样比例范围").grid(row=13, column=1, columnspan=2, sticky=tk.W)
        ttk.Label(self, text="6. 前缀长度: 随机上下文前的固定前缀词元数").grid(row=14, column=1, columnspan=2, sticky=tk.W)
    
    def bind_shortcuts(self):
        """绑定快捷键"""
        # 在顶层窗口中绑定快捷键，确保在场景标签页激活时有效
        self.app.bind('<Control-n>', lambda e: self.add_scenario())
        self.app.bind('<Control-e>', lambda e: self.edit_scenario())
        self.app.bind('<Control-d>', lambda e: self.delete_scenario())
        self.app.bind('<Control-s>', lambda e: self.save_config())
        self.app.bind('<Control-a>', lambda e: self.select_all_scenarios())
        
        # 为每个按钮添加快捷键提示
        self.add_button.config(text="添加场景 (Ctrl+N)")
        self.edit_button.config(text="编辑场景 (Ctrl+E)")
        self.delete_button.config(text="删除场景 (Ctrl+D)")
        self.save_button.config(text="保存配置 (Ctrl+S)")
        self.select_all_button.config(text="全选 (Ctrl+A)")
    
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
            input_len = scenario.get("input_len", 50)
            output_len = scenario.get("output_len", 1024)
            concurrency = scenario.get("concurrency", 4)
            num_prompts = scenario.get("num_prompts", 20)
            range_ratio = scenario.get("range_ratio", 1.0)
            prefix_len = scenario.get("prefix_len", 0)
            
            self.scenario_tree.insert("", "end", values=(name, input_len, output_len, concurrency, num_prompts, range_ratio, prefix_len))
    
    def on_scenario_select(self, event):
        """
        场景选择事件处理
        
        Args:
            event: 事件对象
        """
        selected_items = self.scenario_tree.selection()
        if not selected_items:
            # 如果没有选中项，禁用编辑和删除按钮
            self.edit_button.config(state=tk.DISABLED)
            self.delete_button.config(state=tk.DISABLED)
            return
        
        # 启用编辑和删除按钮
        self.edit_button.config(state=tk.NORMAL)
        self.delete_button.config(state=tk.NORMAL)
        
        # 获取选中项在列表中的索引
        selected_item = selected_items[0]
        all_items = self.scenario_tree.get_children()
        self.selected_index = all_items.index(selected_item)
        
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
    
    def edit_scenario(self):
        """编辑测试场景"""
        if self.selected_index is None:
            messagebox.showerror("错误", "请选择要编辑的测试场景")
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
    
    def save_config(self):
        """保存测试场景配置"""
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
            self.app.update_status(f"已保存测试场景: {scenario['name']}")
        else:
            messagebox.showerror("错误", "保存测试场景失败")
    
    def select_all_scenarios(self):
        """全选所有场景"""
        for item in self.scenario_tree.get_children():
            self.scenario_tree.selection_add(item)
    
    def deselect_all_scenarios(self):
        """全不选所有场景"""
        self.scenario_tree.selection_remove(self.scenario_tree.selection()) 