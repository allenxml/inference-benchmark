# -*- coding: utf-8 -*-
import argparse
import asyncio
import datetime
import json
import os
import platform
import random
import smtplib
import subprocess
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import requests
from tqdm.asyncio import tqdm

# 导入原始benchmark_serving_random.py中的核心功能
# 这里我们会直接整合原始脚本的代码，而不是导入

# 定义API密钥存储和管理功能
class ApiKeyManager:
    def __init__(self, config_file="api_keys.json"):
        self.config_file = config_file
        self.api_keys = {}
        self.load_keys()
    
    def load_keys(self):
        """从配置文件加载API密钥"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.api_keys = json.load(f)
            except json.JSONDecodeError:
                print(f"警告: API密钥配置文件格式错误，将创建新文件")
                self.api_keys = {}
        else:
            self.api_keys = {}
    
    def save_keys(self):
        """保存API密钥到配置文件"""
        with open(self.config_file, 'w') as f:
            json.dump(self.api_keys, f, indent=2)
    
    def add_key(self, service_name, api_key):
        """添加或更新API密钥"""
        self.api_keys[service_name] = api_key
        self.save_keys()
    
    def get_key(self, service_name):
        """获取指定服务的API密钥"""
        return self.api_keys.get(service_name)
    
    def list_services(self):
        """列出所有已配置的服务名称"""
        return list(self.api_keys.keys())
    
    def delete_key(self, service_name):
        """删除指定服务的API密钥"""
        if service_name in self.api_keys:
            del self.api_keys[service_name]
            self.save_keys()
            return True
        return False

# 邮件配置管理
class EmailConfigManager:
    def __init__(self, config_file="email_config.json"):
        self.config_file = config_file
        self.config = {
            "email_from": "",
            "email_to": "",
            "email_password": "",
            "smtp_server": "smtp.qq.com",
            "smtp_port": 465,
            "send_each": True,
            "send_final": True
        }
        self.load_config()
    
    def load_config(self):
        """从配置文件加载邮件配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # 更新配置，保留默认值
                    for key, value in loaded_config.items():
                        if key in self.config:
                            self.config[key] = value
            except json.JSONDecodeError:
                print(f"警告: 邮件配置文件格式错误，将使用默认配置")
    
    def save_config(self):
        """保存邮件配置到配置文件"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def update_config(self, **kwargs):
        """更新邮件配置"""
        for key, value in kwargs.items():
            if key in self.config:
                self.config[key] = value
        self.save_config()
    
    def get_config(self):
        """获取邮件配置"""
        return self.config

# 测试场景配置管理
class TestScenarioManager:
    def __init__(self, config_file="test_scenarios.json"):
        self.config_file = config_file
        self.scenarios = []
        self.load_scenarios()
    
    def load_scenarios(self):
        """从配置文件加载测试场景"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.scenarios = json.load(f)
            except json.JSONDecodeError:
                print(f"警告: 测试场景配置文件格式错误，将使用空列表")
                self.scenarios = []
        else:
            # 默认测试场景
            self.scenarios = [
                {
                    "name": "默认场景",
                    "input_len": 50,
                    "output_len": 1024,
                    "concurrency": 4,
                    "num_prompts": 20,
                    "range_ratio": 1.0,
                    "prefix_len": 0
                }
            ]
            self.save_scenarios()
    
    def save_scenarios(self):
        """保存测试场景到配置文件"""
        with open(self.config_file, 'w') as f:
            json.dump(self.scenarios, f, indent=2)
    
    def add_scenario(self, scenario):
        """添加测试场景"""
        self.scenarios.append(scenario)
        self.save_scenarios()
    
    def update_scenario(self, index, scenario):
        """更新测试场景"""
        if 0 <= index < len(self.scenarios):
            self.scenarios[index] = scenario
            self.save_scenarios()
            return True
        return False
    
    def delete_scenario(self, index):
        """删除测试场景"""
        if 0 <= index < len(self.scenarios):
            del self.scenarios[index]
            self.save_scenarios()
            return True
        return False
    
    def get_scenarios(self):
        """获取所有测试场景"""
        return self.scenarios

# 邮件发送功能
def send_email(subject, body_file, attachment=None, email_config=None):
    """发送邮件功能"""
    if not email_config:
        print("错误: 邮箱配置不完整，无法发送邮件")
        return False
    
    email_from = email_config.get("email_from")
    email_to = email_config.get("email_to")
    password = email_config.get("email_password")
    smtp_server = email_config.get("smtp_server", "smtp.qq.com")
    smtp_port = email_config.get("smtp_port", 465)
    
    if not email_from or not email_to or not password:
        print("错误: 邮箱配置不完整，无法发送邮件")
        return False
    
    try:
        # 创建邮件
        msg = MIMEMultipart()
        msg['From'] = email_from
        msg['To'] = email_to
        msg['Subject'] = subject
        
        # 读取邮件内容
        with open(body_file, 'r', encoding='utf-8') as f:
            body = f.read()
        
        # 添加邮件正文
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # 添加附件（如果存在）
        if attachment and os.path.exists(attachment):
            try:
                with open(attachment, "rb") as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    filename = os.path.basename(attachment)
                    part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                    msg.attach(part)
                    print(f"已添加附件: {filename}")
            except Exception as e:
                print(f"添加附件时出错: {e}")
        
        # 连接邮件服务器并发送
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(email_from, password)
        server.sendmail(email_from, email_to.split(','), msg.as_string())
        server.quit()
        print(f"邮件已成功发送到 {email_to}")
        return True
    except Exception as e:
        print(f"邮件发送失败: {e}")
        return False

# 系统信息收集功能
def collect_system_info():
    """收集系统信息"""
    info = {}
    info["日期"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info["主机名"] = platform.node()
    info["操作系统"] = platform.platform()
    
    # CPU信息
    if platform.system() == "Windows":
        import psutil
        info["CPU信息"] = platform.processor()
        info["核心数"] = str(psutil.cpu_count(logical=True))
        info["内存总量"] = f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB"
    else:
        try:
            # Linux系统
            cpu_info = subprocess.check_output("cat /proc/cpuinfo | grep 'model name' | head -1", shell=True).decode()
            cpu_info = cpu_info.split(':')[1].strip() if ':' in cpu_info else "未知"
            info["CPU信息"] = cpu_info
            
            cores = subprocess.check_output("nproc", shell=True).decode().strip()
            info["核心数"] = cores
            
            mem_info = subprocess.check_output("free -h | grep Mem | awk '{print $2}'", shell=True).decode().strip()
            info["内存总量"] = mem_info
        except:
            info["CPU信息"] = "无法获取"
            info["核心数"] = "无法获取"
            info["内存总量"] = "无法获取"
    
    # GPU信息
    info["GPU信息"] = []
    try:
        if platform.system() == "Windows":
            # 在Windows上尝试使用nvidia-smi
            nvidia_smi = subprocess.check_output("nvidia-smi --query-gpu=name,driver_version,memory.total,utilization.gpu,temperature.gpu --format=csv,noheader", shell=True).decode()
            for i, line in enumerate(nvidia_smi.strip().split('\n')):
                parts = line.split(', ')
                if len(parts) >= 5:
                    gpu_info = {
                        "索引": i,
                        "名称": parts[0],
                        "驱动版本": parts[1],
                        "显存总量": parts[2],
                        "GPU利用率": parts[3],
                        "温度": parts[4]
                    }
                    info["GPU信息"].append(gpu_info)
        else:
            # Linux系统
            nvidia_smi = subprocess.check_output("nvidia-smi --query-gpu=index,name,driver_version,memory.total,utilization.gpu,temperature.gpu --format=csv,noheader", shell=True).decode()
            for line in nvidia_smi.strip().split('\n'):
                parts = line.split(', ')
                if len(parts) >= 6:
                    gpu_info = {
                        "索引": parts[0],
                        "名称": parts[1],
                        "驱动版本": parts[2],
                        "显存总量": parts[3],
                        "GPU利用率": parts[4],
                        "温度": parts[5]
                    }
                    info["GPU信息"].append(gpu_info)
    except:
        info["GPU信息"] = "未检测到NVIDIA GPU或无法访问nvidia-smi"
    
    return info

# 这里整合原始benchmark_serving_random.py的代码
# 为了简洁，我们只展示关键部分，完整代码需要整合原始脚本

# 定义RequestFuncInput和RequestFuncOutput类
class RequestFuncInput:
    def __init__(self, model, prompt, api_url, prompt_len, output_len, 
                 logprobs=None, best_of=1, multi_modal_content=None, 
                 ignore_eos=False, model_name=None, api_key=None):
        self.model = model
        self.model_name = model_name if model_name else model
        self.prompt = prompt
        self.api_url = api_url
        self.prompt_len = prompt_len
        self.output_len = output_len
        self.logprobs = logprobs
        self.best_of = best_of
        self.multi_modal_content = multi_modal_content
        self.ignore_eos = ignore_eos
        self.api_key = api_key  # 添加API密钥字段

class RequestFuncOutput:
    def __init__(self, success, generated_text="", prompt_len=0, output_tokens=0, 
                 latency=0, ttft=0, itl=None, error=None):
        self.success = success
        self.generated_text = generated_text
        self.prompt_len = prompt_len
        self.output_tokens = output_tokens
        self.latency = latency
        self.ttft = ttft
        self.itl = itl if itl is not None else []
        self.error = error

# 定义异步请求函数
async def openai_request(request_func_input, pbar=None):
    """OpenAI API请求函数"""
    # 这里需要整合原始脚本中的请求函数
    # 为了简洁，我们只展示框架
    return RequestFuncOutput(success=True)

# 定义异步请求函数字典
ASYNC_REQUEST_FUNCS = {
    "openai": openai_request,
    "vllm": openai_request,  # vLLM使用与OpenAI兼容的API
}

# 主要的基准测试函数
async def run_benchmark(config, log_callback=None):
    """运行基准测试"""
    # 这里需要整合原始脚本中的benchmark函数
    # 为了简洁，我们只展示框架
    
    if log_callback:
        log_callback("开始基准测试...")
    
    # 返回结果
    return {"success": True, "message": "测试完成"}

# GUI应用类
class BenchmarkApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("LLM服务基准测试工具")
        self.geometry("900x700")
        self.minsize(800, 600)
        
        # 初始化管理器
        self.api_key_manager = ApiKeyManager()
        self.email_config_manager = EmailConfigManager()
        self.test_scenario_manager = TestScenarioManager()
        
        # 创建主框架
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建各个标签页
        self.create_main_tab()
        self.create_api_key_tab()
        self.create_email_tab()
        self.create_scenarios_tab()
        self.create_logs_tab()
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        self.status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 加载配置
        self.load_configs()
    
    def create_main_tab(self):
        """创建主标签页"""
        main_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_frame, text="主页")
        
        # 创建左右分栏
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧 - 基本配置
        ttk.Label(left_frame, text="基本配置", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        
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
        backend_combo = ttk.Combobox(left_frame, textvariable=self.backend_var, values=list(ASYNC_REQUEST_FUNCS.keys()), state="readonly", width=38)
        backend_combo.grid(row=4, column=1, sticky=tk.W, pady=2)
        
        # 端点
        ttk.Label(left_frame, text="API端点:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.endpoint_var = tk.StringVar(value="/v1/completions")
        ttk.Entry(left_frame, textvariable=self.endpoint_var, width=40).grid(row=5, column=1, sticky=tk.W, pady=2)
        
        # 右侧 - 测试场景选择
        ttk.Label(right_frame, text="测试场景", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5, columnspan=2)
        
        # 场景列表
        ttk.Label(right_frame, text="选择测试场景:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.scenario_listbox = tk.Listbox(right_frame, height=8, width=40)
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
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="开始测试", command=self.start_benchmark, width=20).pack(side=tk.RIGHT, padx=10)
        ttk.Button(button_frame, text="保存配置", command=self.save_configs, width=20).pack(side=tk.RIGHT, padx=10)
    
    def create_api_key_tab(self):
        """创建API密钥标签页"""
        api_key_frame = ttk.Frame(self.notebook)
        self.notebook.add(api_key_frame, text="API密钥管理")
        
        # 标题
        ttk.Label(api_key_frame, text="API密钥管理", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5, columnspan=3)
        
        # 服务名称
        ttk.Label(api_key_frame, text="服务名称:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.service_var = tk.StringVar()
        service_combo = ttk.Combobox(api_key_frame, textvariable=self.service_var, values=list(ASYNC_REQUEST_FUNCS.keys()), width=30)
        service_combo.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # API密钥
        ttk.Label(api_key_frame, text="API密钥:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.api_key_var = tk.StringVar()
        ttk.Entry(api_key_frame, textvariable=self.api_key_var, width=50, show="*").grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # 显示/隐藏密钥
        self.show_key_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(api_key_frame, text="显示密钥", variable=self.show_key_var, command=self.toggle_key_visibility).grid(row=2, column=2, sticky=tk.W, pady=2)
        
        # 按钮
        button_frame = ttk.Frame(api_key_frame)
        button_frame.grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=10)
        
        ttk.Button(button_frame, text="添加/更新", command=self.add_api_key, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="删除", command=self.delete_api_key, width=15).pack(side=tk.LEFT, padx=5)
        
        # 已配置的API密钥列表
        ttk.Label(api_key_frame, text="已配置的API密钥:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky=tk.W, pady=5, columnspan=3)
        
        self.api_keys_listbox = tk.Listbox(api_key_frame, height=10, width=70)
        self.api_keys_listbox.grid(row=5, column=0, columnspan=3, sticky=tk.W+tk.E, pady=2)
        self.api_keys_listbox.bind('<<ListboxSelect>>', self.on_api_key_select)
        
        # 滚动条
        api_keys_scrollbar = ttk.Scrollbar(api_key_frame, orient=tk.VERTICAL, command=self.api_keys_listbox.yview)
        api_keys_scrollbar.grid(row=5, column=3, sticky=tk.N+tk.S)
        self.api_keys_listbox.config(yscrollcommand=api_keys_scrollbar.set)
    
    def create_email_tab(self):
        """创建邮件配置标签页"""
        email_frame = ttk.Frame(self.notebook)
        self.notebook.add(email_frame, text="邮件配置")
        
        # 标题
        ttk.Label(email_frame, text="邮件配置", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5, columnspan=2)
        
        # 发件人邮箱
        ttk.Label(email_frame, text="发件人邮箱:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.email_from_var = tk.StringVar()
        ttk.Entry(email_frame, textvariable=self.email_from_var, width=40).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # 收件人邮箱
        ttk.Label(email_frame, text="收件人邮箱:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.email_to_var = tk.StringVar()
        ttk.Entry(email_frame, textvariable=self.email_to_var, width=40).grid(row=2, column=1, sticky=tk.W, pady=2)
        ttk.Label(email_frame, text="(多个收件人用逗号分隔)").grid(row=2, column=2, sticky=tk.W, pady=2)
        
        # 邮箱密码
        ttk.Label(email_frame, text="邮箱密码:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.email_password_var = tk.StringVar()
        ttk.Entry(email_frame, textvariable=self.email_password_var, width=40, show="*").grid(row=3, column=1, sticky=tk.W, pady=2)
        
        # 显示/隐藏密码
        self.show_password_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(email_frame, text="显示密码", variable=self.show_password_var, command=self.toggle_password_visibility).grid(row=3, column=2, sticky=tk.W, pady=2)
        
        # SMTP服务器
        ttk.Label(email_frame, text="SMTP服务器:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.smtp_server_var = tk.StringVar(value="smtp.qq.com")
        ttk.Entry(email_frame, textvariable=self.smtp_server_var, width=40).grid(row=4, column=1, sticky=tk.W, pady=2)
        
        # SMTP端口
        ttk.Label(email_frame, text="SMTP端口:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.smtp_port_var = tk.IntVar(value=465)
        ttk.Entry(email_frame, textvariable=self.smtp_port_var, width=10).grid(row=5, column=1, sticky=tk.W, pady=2)
    
    def load_configs(self):
        # 实现加载配置的逻辑
        pass
    
    def save_configs(self):
        # 实现保存配置的逻辑
        pass
    
    def browse_tokenizer(self):
        # 实现浏览分词器路径的逻辑
        pass
    
    def toggle_key_visibility(self):
        # 实现显示/隐藏API密钥的逻辑
        pass
    
    def add_api_key(self):
        # 实现添加API密钥的逻辑
        pass
    
    def delete_api_key(self):
        # 实现删除API密钥的逻辑
        pass
    
    def on_api_key_select(self):
        # 实现API密钥选择时的逻辑
        pass
    
    def toggle_password_visibility(self):
        # 实现显示/隐藏邮箱密码的逻辑
        pass
    
    def start_benchmark(self):
        # 实现开始基准测试的逻辑
        pass
    
    def select_all_scenarios(self):
        # 实现选择所有测试场景的逻辑
        pass
    
    def deselect_all_scenarios(self):
        # 实现取消选择所有测试场景的逻辑
        pass

# 创建BenchmarkApp实例并运行
if __name__ == "__main__":
    app = BenchmarkApp()
    app.mainloop() 