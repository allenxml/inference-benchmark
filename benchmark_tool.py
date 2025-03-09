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

# 邮件发送功能
def send_email(subject, body_file, attachment=None, email_from=None, email_to=None, password=None):
    """发送邮件功能"""
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
        server = smtplib.SMTP_SSL('smtp.qq.com', 465)
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
    start_time = time.time()
    success = False
    generated_text = ""
    output_tokens = 0
    ttft = 0
    itl = []
    error = None
    
    try:
        headers = {
            "Content-Type": "application/json",
        }
        
        # 如果提供了API密钥，则添加到请求头
        if request_func_input.api_key:
            headers["Authorization"] = f"Bearer {request_func_input.api_key}"
        
        data = {
            "model": request_func_input.model,
            "prompt": request_func_input.prompt,
            "max_tokens": request_func_input.output_len,
            "stream": True,
        }
        
        if request_func_input.logprobs is not None:
            data["logprobs"] = request_func_input.logprobs
        
        if request_func_input.best_of > 1:
            data["best_of"] = request_func_input.best_of
        
        if request_func_input.ignore_eos:
            data["stop"] = []
        
        async with aiohttp.ClientSession() as session:
            async with session.post(request_func_input.api_url, 
                                   headers=headers, 
                                   json=data) as response:
                if response.status != 200:
                    error = f"HTTP错误: {response.status}, {await response.text()}"
                    return RequestFuncOutput(success=False, error=error, prompt_len=request_func_input.prompt_len)
                
                # 处理流式响应
                first_token_received = False
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: ') and not line.endswith('[DONE]'):
                        json_str = line[6:]  # 去掉 'data: ' 前缀
                        try:
                            chunk = json.loads(json_str)
                            if 'choices' in chunk and len(chunk['choices']) > 0:
                                token = chunk['choices'][0].get('text', '')
                                if token:
                                    generated_text += token
                                    output_tokens += 1
                                    
                                    current_time = time.time()
                                    if not first_token_received:
                                        ttft = current_time - start_time
                                        first_token_received = True
                                    else:
                                        itl.append(current_time - prev_token_time)
                                    
                                    prev_token_time = current_time
                        except json.JSONDecodeError:
                            pass
                
                success = True
                latency = time.time() - start_time
                
                if pbar:
                    pbar.update(1)
                
                return RequestFuncOutput(
                    success=success,
                    generated_text=generated_text,
                    prompt_len=request_func_input.prompt_len,
                    output_tokens=output_tokens,
                    latency=latency,
                    ttft=ttft,
                    itl=itl
                )
    
    except Exception as e:
        error = str(e)
        return RequestFuncOutput(success=False, error=error, prompt_len=request_func_input.prompt_len)

# 定义异步请求函数字典
ASYNC_REQUEST_FUNCS = {
    "openai": openai_request,
    "vllm": openai_request,  # vLLM使用与OpenAI兼容的API
}

# 主要的基准测试函数
async def run_benchmark(args):
    """运行基准测试"""
    # 这里需要整合原始脚本中的benchmark函数
    # 为了简洁，我们只展示框架，完整代码需要整合原始脚本
    
    # 初始化API密钥管理器
    key_manager = ApiKeyManager()
    api_key = key_manager.get_key(args.backend)
    
    # 设置基本参数
    backend = args.backend
    model_id = args.model
    model_name = args.served_model_name or model_id
    
    if args.base_url:
        api_url = f"{args.base_url}{args.endpoint}"
        base_url = args.base_url
    else:
        api_url = f"http://{args.host}:{args.port}{args.endpoint}"
        base_url = f"http://{args.host}:{args.port}"
    
    # 生成随机请求
    input_requests = sample_random_requests(
        prefix_len=args.random_prefix_len,
        input_len=args.random_input_len,
        output_len=args.random_output_len,
        num_prompts=args.num_prompts,
        range_ratio=args.random_range_ratio,
        tokenizer=None  # 需要实现获取tokenizer的逻辑
    )
    
    # 执行基准测试
    # 这里需要整合原始脚本中的benchmark函数的核心逻辑
    
    # 返回结果
    return {}

# 主函数
def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="LLM服务基准测试工具")
    
    # 基本选项
    parser.add_argument("-u", "--url", dest="base_url", type=str, default="http://127.0.0.1:8000",
                        help="设置基础URL (默认: http://127.0.0.1:8000)")
    parser.add_argument("-m", "--model", type=str, default="test",
                        help="设置模型名称 (默认: test)")
    parser.add_argument("-t", "--tokenizer", type=str, default=None,
                        help="设置分词器路径")
    parser.add_argument("-b", "--backend", type=str, default="openai",
                        choices=list(ASYNC_REQUEST_FUNCS.keys()),
                        help="设置后端类型 (默认: openai)")
    
    # API密钥管理选项
    key_group = parser.add_argument_group("API密钥管理")
    key_group.add_argument("--add-key", nargs=2, metavar=("SERVICE", "KEY"),
                          help="添加或更新API密钥")
    key_group.add_argument("--list-keys", action="store_true",
                          help="列出所有已配置的API密钥")
    key_group.add_argument("--delete-key", metavar="SERVICE",
                          help="删除指定服务的API密钥")
    
    # 邮件选项
    email_group = parser.add_argument_group("邮件选项")
    email_group.add_argument("-f", "--email-from", type=str, default=None,
                            help="设置发件人邮箱地址")
    email_group.add_argument("-e", "--email-to", type=str, default=None,
                            help="设置收件人邮箱地址，多个地址用逗号分隔")
    email_group.add_argument("--email-password", type=str, default=None,
                            help="设置邮箱密码")
    email_group.add_argument("--send-each", action="store_true", default=True,
                            help="启用每轮测试后发送邮件 (默认: 启用)")
    email_group.add_argument("--no-send-each", action="store_false", dest="send_each",
                            help="禁用每轮测试后发送邮件")
    email_group.add_argument("--send-final", action="store_true", default=True,
                            help="启用最终汇总邮件发送 (默认: 启用)")
    email_group.add_argument("--no-send-final", action="store_false", dest="send_final",
                            help="禁用最终汇总邮件发送")
    
    # 测试场景选项
    scenario_group = parser.add_argument_group("测试场景选项")
    scenario_group.add_argument("--random-input-len", type=int, default=1024,
                               help="每个请求的输入词元数 (默认: 1024)")
    scenario_group.add_argument("--random-output-len", type=int, default=128,
                               help="每个请求的输出词元数 (默认: 128)")
    scenario_group.add_argument("--random-range-ratio", type=float, default=1.0,
                               help="输入/输出长度的采样比例范围 (默认: 1.0)")
    scenario_group.add_argument("--random-prefix-len", type=int, default=0,
                               help="随机上下文前的固定前缀词元数 (默认: 0)")
    scenario_group.add_argument("--num-prompts", type=int, default=20,
                               help="要处理的提示数量 (默认: 20)")
    scenario_group.add_argument("--max-concurrency", type=int, default=4,
                               help="最大并发请求数 (默认: 4)")
    
    # 解析参数
    args = parser.parse_args()
    
    # 初始化API密钥管理器
    key_manager = ApiKeyManager()
    
    # 处理API密钥管理命令
    if args.add_key:
        service, key = args.add_key
        key_manager.add_key(service, key)
        print(f"已添加/更新服务 '{service}' 的API密钥")
        return
    
    if args.list_keys:
        services = key_manager.list_services()
        if services:
            print("已配置的API密钥:")
            for service in services:
                key = key_manager.get_key(service)
                masked_key = key[:4] + "*" * (len(key) - 8) + key[-4:] if len(key) > 8 else "****"
                print(f"  {service}: {masked_key}")
        else:
            print("尚未配置任何API密钥")
        return
    
    if args.delete_key:
        if key_manager.delete_key(args.delete_key):
            print(f"已删除服务 '{args.delete_key}' 的API密钥")
        else:
            print(f"未找到服务 '{args.delete_key}' 的API密钥")
        return
    
    # 创建日志目录
    log_dir = f"benchmark_logs_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(log_dir, exist_ok=True)
    
    # 收集系统信息
    sys_info = collect_system_info()
    
    # 将系统信息写入文件
    with open(os.path.join(log_dir, "system_info.txt"), "w", encoding="utf-8") as f:
        f.write("测试系统信息:\n")
        for key, value in sys_info.items():
            if key != "GPU信息":
                f.write(f"{key}: {value}\n")
        
        # 写入GPU信息
        f.write("GPU信息:\n")
        if isinstance(sys_info["GPU信息"], list):
            for gpu in sys_info["GPU信息"]:
                for k, v in gpu.items():
                    f.write(f"  {k}: {v}\n")
                f.write("\n")
        else:
            f.write(f"  {sys_info['GPU信息']}\n")
    
    # 创建测试场景
    scenarios = [
        (args.random_input_len, args.random_output_len, args.max_concurrency, args.num_prompts, args.random_range_ratio, args.random_prefix_len)
    ]
    
    # 创建汇总Markdown文件
    summary_md = os.path.join(log_dir, "benchmark_summary.md")
    with open(summary_md, "w", encoding="utf-8") as f:
        f.write("# vLLM基准测试结果汇总报告\n\n")
        f.write(f"生成时间: {datetime.datetime.now()}\n\n")
        
        # 记录配置信息
        f.write("## 测试配置\n\n")
        f.write(f"- 基础URL: {args.base_url}\n")
        f.write(f"- 模型: {args.model}\n")
        f.write(f"- 分词器: {args.tokenizer}\n")
        f.write(f"- 后端: {args.backend}\n\n")
        
        # 记录系统信息
        f.write("## 系统信息\n\n")
        for key, value in sys_info.items():
            if key != "GPU信息":
                f.write(f"- **{key}:** {value}\n")
        
        # 记录GPU信息
        f.write("\n### GPU信息\n\n")
        if isinstance(sys_info["GPU信息"], list):
            for gpu in sys_info["GPU信息"]:
                f.write(f"**GPU {gpu['索引']}: {gpu['名称']}**\n")
                for k, v in gpu.items():
                    if k != "索引" and k != "名称":
                        f.write(f"- {k}: {v}\n")
                f.write("\n")
        else:
            f.write(f"{sys_info['GPU信息']}\n\n")
    
    # 执行测试场景
    # 这里需要实现测试场景的执行逻辑
    
    print("测试完成！")
    print(f"结果保存在: {log_dir}")

if __name__ == "__main__":
    main() 