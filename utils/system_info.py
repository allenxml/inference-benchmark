# -*- coding: utf-8 -*-
"""
系统信息收集模块，用于获取系统和硬件信息。
"""
import platform
import subprocess
import datetime
from typing import Dict, Any, List

# 尝试导入psutil，如果不可用则忽略
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


def collect_system_info() -> Dict[str, Any]:
    """
    收集系统信息
    
    Returns:
        包含系统信息的字典
    """
    info = {}
    info["日期"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info["主机名"] = platform.node()
    info["操作系统"] = platform.platform()
    info["Python版本"] = platform.python_version()
    
    # 收集CPU信息
    info.update(collect_cpu_info())
    
    # 收集内存信息
    info.update(collect_memory_info())
    
    # 收集GPU信息
    info["GPU信息"] = collect_gpu_info()
    
    return info


def collect_cpu_info() -> Dict[str, str]:
    """
    收集CPU信息
    
    Returns:
        包含CPU信息的字典
    """
    info = {}
    
    if platform.system() == "Windows":
        if HAS_PSUTIL:
            info["CPU信息"] = platform.processor()
            info["核心数"] = str(psutil.cpu_count(logical=True))
            info["物理核心数"] = str(psutil.cpu_count(logical=False))
            info["CPU使用率"] = f"{psutil.cpu_percent()}%"
        else:
            info["CPU信息"] = platform.processor()
            info["核心数"] = "未知（需要安装psutil）"
    else:
        try:
            # Linux系统
            cpu_info = subprocess.check_output("cat /proc/cpuinfo | grep 'model name' | head -1", shell=True).decode()
            cpu_info = cpu_info.split(':')[1].strip() if ':' in cpu_info else "未知"
            info["CPU信息"] = cpu_info
            
            cores = subprocess.check_output("nproc", shell=True).decode().strip()
            info["核心数"] = cores
            
            # 尝试获取物理核心数
            try:
                physical_cores = subprocess.check_output("lscpu | grep 'Core(s) per socket' | awk '{print $4}'", shell=True).decode().strip()
                info["物理核心数"] = physical_cores
            except:
                info["物理核心数"] = "未知"
            
            # 尝试获取CPU使用率
            if HAS_PSUTIL:
                info["CPU使用率"] = f"{psutil.cpu_percent()}%"
        except:
            info["CPU信息"] = "无法获取"
            info["核心数"] = "无法获取"
    
    return info


def collect_memory_info() -> Dict[str, str]:
    """
    收集内存信息
    
    Returns:
        包含内存信息的字典
    """
    info = {}
    
    if HAS_PSUTIL:
        vm = psutil.virtual_memory()
        info["内存总量"] = f"{round(vm.total / (1024**3), 2)} GB"
        info["可用内存"] = f"{round(vm.available / (1024**3), 2)} GB"
        info["内存使用率"] = f"{vm.percent}%"
    else:
        if platform.system() == "Windows":
            info["内存总量"] = "未知（需要安装psutil）"
        else:
            try:
                # Linux系统
                mem_info = subprocess.check_output("free -h | grep Mem", shell=True).decode().strip()
                parts = mem_info.split()
                if len(parts) >= 2:
                    info["内存总量"] = parts[1]
                if len(parts) >= 4:
                    info["可用内存"] = parts[6]  # 'available' column
            except:
                info["内存总量"] = "无法获取"
    
    return info


def collect_gpu_info() -> List[Dict[str, str]]:
    """
    收集GPU信息
    
    Returns:
        包含GPU信息的列表，每个元素是一个字典
    """
    gpu_info = []
    
    try:
        # 尝试使用nvidia-smi获取GPU信息
        if platform.system() == "Windows":
            nvidia_smi = subprocess.check_output("nvidia-smi --query-gpu=index,name,driver_version,memory.total,utilization.gpu,temperature.gpu --format=csv,noheader", shell=True).decode()
        else:
            nvidia_smi = subprocess.check_output("nvidia-smi --query-gpu=index,name,driver_version,memory.total,utilization.gpu,temperature.gpu --format=csv,noheader", shell=True).decode()
        
        for line in nvidia_smi.strip().split('\n'):
            parts = [part.strip() for part in line.split(',')]
            if len(parts) >= 6:
                gpu_dict = {
                    "索引": parts[0],
                    "名称": parts[1],
                    "驱动版本": parts[2],
                    "显存总量": parts[3],
                    "GPU利用率": parts[4],
                    "温度": parts[5]
                }
                gpu_info.append(gpu_dict)
    except:
        # 如果无法获取GPU信息，返回一个包含错误信息的列表
        return "未检测到NVIDIA GPU或无法访问nvidia-smi"
    
    return gpu_info


def format_system_info_markdown(info: Dict[str, Any]) -> str:
    """
    将系统信息格式化为Markdown文本
    
    Args:
        info: 系统信息字典
        
    Returns:
        格式化后的Markdown文本
    """
    markdown = "## 系统信息\n\n"
    
    # 添加基本系统信息
    for key, value in info.items():
        if key != "GPU信息":
            markdown += f"- **{key}:** {value}\n"
    
    # 添加GPU信息
    markdown += "\n### GPU信息\n\n"
    if isinstance(info["GPU信息"], list):
        for gpu in info["GPU信息"]:
            markdown += f"**GPU {gpu['索引']}: {gpu['名称']}**\n"
            for k, v in gpu.items():
                if k != "索引" and k != "名称":
                    markdown += f"- {k}: {v}\n"
            markdown += "\n"
    else:
        markdown += f"{info['GPU信息']}\n\n"
    
    return markdown


def format_system_info_text(info: Dict[str, Any]) -> str:
    """
    将系统信息格式化为纯文本
    
    Args:
        info: 系统信息字典
        
    Returns:
        格式化后的纯文本
    """
    text = "测试系统信息:\n"
    
    # 添加基本系统信息
    for key, value in info.items():
        if key != "GPU信息":
            text += f"{key}: {value}\n"
    
    # 添加GPU信息
    text += "\nGPU信息:\n"
    if isinstance(info["GPU信息"], list):
        for gpu in info["GPU信息"]:
            text += f"GPU {gpu['索引']}: {gpu['名称']}\n"
            for k, v in gpu.items():
                if k != "索引" and k != "名称":
                    text += f"  {k}: {v}\n"
            text += "\n"
    else:
        text += f"{info['GPU信息']}\n"
    
    return text 