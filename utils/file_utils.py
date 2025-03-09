# -*- coding: utf-8 -*-
"""
文件操作工具模块，用于处理文件和路径。
"""
import os
import sys
import json
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional


def get_resource_path(relative_path: str) -> str:
    """
    获取资源文件的绝对路径，兼容开发环境和PyInstaller打包后的环境
    
    Args:
        relative_path: 相对路径
        
    Returns:
        资源文件的绝对路径
    """
    try:
        # PyInstaller创建临时文件夹，将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


def create_log_directory() -> str:
    """
    创建日志目录
    
    Returns:
        日志目录路径
    """
    log_dir = f"benchmark_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def write_json_file(file_path: str, data: Any) -> bool:
    """
    将数据写入JSON文件
    
    Args:
        file_path: 文件路径
        data: 要写入的数据
        
    Returns:
        是否写入成功
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"写入JSON文件失败: {e}")
        return False


def read_json_file(file_path: str, default: Any = None) -> Any:
    """
    从JSON文件读取数据
    
    Args:
        file_path: 文件路径
        default: 默认值，如果文件不存在或读取失败则返回此值
        
    Returns:
        读取的数据，如果读取失败则返回默认值
    """
    if not os.path.exists(file_path):
        return default
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"读取JSON文件失败: {e}")
        return default


def write_text_file(file_path: str, text: str) -> bool:
    """
    将文本写入文件
    
    Args:
        file_path: 文件路径
        text: 要写入的文本
        
    Returns:
        是否写入成功
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
        return True
    except Exception as e:
        print(f"写入文本文件失败: {e}")
        return False


def read_text_file(file_path: str, default: str = "") -> str:
    """
    从文件读取文本
    
    Args:
        file_path: 文件路径
        default: 默认值，如果文件不存在或读取失败则返回此值
        
    Returns:
        读取的文本，如果读取失败则返回默认值
    """
    if not os.path.exists(file_path):
        return default
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"读取文本文件失败: {e}")
        return default


def create_markdown_summary(log_dir: str, title: str, config: Dict[str, Any], system_info: Dict[str, Any]) -> str:
    """
    创建Markdown格式的摘要文件
    
    Args:
        log_dir: 日志目录
        title: 标题
        config: 配置信息
        system_info: 系统信息
        
    Returns:
        Markdown文件路径
    """
    summary_md = os.path.join(log_dir, "benchmark_summary.md")
    
    with open(summary_md, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(f"生成时间: {datetime.now()}\n\n")
        
        # 记录配置信息
        f.write("## 测试配置\n\n")
        f.write(f"- 基础URL: {config.get('base_url', '')}\n")
        f.write(f"- 模型: {config.get('model', '')}\n")
        f.write(f"- 分词器: {config.get('tokenizer', '')}\n")
        f.write(f"- 后端: {config.get('backend', '')}\n\n")
        
        # 记录系统信息
        f.write("## 系统信息\n\n")
        for key, value in system_info.items():
            if key != "GPU信息":
                f.write(f"- **{key}:** {value}\n")
        
        # 记录GPU信息
        f.write("\n### GPU信息\n\n")
        if isinstance(system_info.get("GPU信息"), list):
            for gpu in system_info["GPU信息"]:
                f.write(f"**GPU {gpu['索引']}: {gpu['名称']}**\n")
                for k, v in gpu.items():
                    if k != "索引" and k != "名称":
                        f.write(f"- {k}: {v}\n")
                f.write("\n")
        else:
            f.write(f"{system_info.get('GPU信息', '未知')}\n\n")
    
    return summary_md


def append_to_markdown(file_path: str, content: str) -> bool:
    """
    向Markdown文件追加内容
    
    Args:
        file_path: 文件路径
        content: 要追加的内容
        
    Returns:
        是否追加成功
    """
    try:
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"向Markdown文件追加内容失败: {e}")
        return False


def create_round_markdown(log_dir: str, round_index: int, scenario: Dict[str, Any], results: Dict[str, Any], duration: int) -> str:
    """
    创建单轮测试的Markdown文件
    
    Args:
        log_dir: 日志目录
        round_index: 轮次索引
        scenario: 测试场景
        results: 测试结果
        duration: 测试持续时间（秒）
        
    Returns:
        Markdown文件路径
    """
    round_md = os.path.join(log_dir, f"round_{round_index}.md")
    
    with open(round_md, "w", encoding="utf-8") as f:
        f.write(f"# 场景 {round_index} 测试结果\n\n")
        
        # 场景信息
        f.write(f"**场景**: 输入={scenario.get('input_len')}, 输出={scenario.get('output_len')}, 并发={scenario.get('concurrency')}, 请求={scenario.get('num_prompts')}, 范围={scenario.get('range_ratio')}, 前缀={scenario.get('prefix_len')}\n\n")
        
        # 执行时间
        f.write(f"**执行时间**: {duration} 秒\n\n")
        
        # 请求统计
        f.write("### 请求统计\n\n")
        f.write(f"成功请求数: {results.get('completed', 0)} ({results.get('success_rate', 0)}%)\n")
        f.write(f"失败请求数: {results.get('failed', 0)} ({results.get('failure_rate', 0)}%)\n")
        f.write(f"总请求数: {results.get('total_requests', 0)}\n\n")
        
        # 吞吐量指标
        f.write("### 吞吐量指标\n\n")
        f.write(f"请求吞吐量: {results.get('request_throughput', 0)} req/s\n")
        f.write(f"输出词元吞吐量: {results.get('output_throughput', 0)} tok/s\n")
        f.write(f"每并发输出词元吞吐量: {results.get('per_concurrency_output_throughput', 0)} tok/s/并发\n")
        f.write(f"总词元吞吐量: {results.get('total_token_throughput', 0)} tok/s\n")
        f.write(f"每并发总词元吞吐量: {results.get('per_concurrency_total_throughput', 0)} tok/s/并发\n\n")
        
        # TTFT指标
        f.write("### 首词延迟 (TTFT)\n\n")
        f.write(f"平均TTFT (ms): {results.get('mean_ttft_ms', 0)}\n")
        f.write(f"中位数TTFT (ms): {results.get('median_ttft_ms', 0)}\n")
        f.write(f"P99 TTFT (ms): {results.get('p99_ttft_ms', 0)}\n\n")
        
        # TPOT指标
        f.write("### 每词延迟 (TPOT) (不含首词)\n\n")
        f.write(f"平均TPOT (ms): {results.get('mean_tpot_ms', 0)}\n")
        f.write(f"中位数TPOT (ms): {results.get('median_tpot_ms', 0)}\n")
        f.write(f"P99 TPOT (ms): {results.get('p99_tpot_ms', 0)}\n\n")
        
        # ITL指标
        f.write("### 词间延迟 (ITL)\n\n")
        f.write(f"平均ITL (ms): {results.get('mean_itl_ms', 0)}\n")
        f.write(f"中位数ITL (ms): {results.get('median_itl_ms', 0)}\n")
        f.write(f"P99 ITL (ms): {results.get('p99_itl_ms', 0)}\n")
    
    return round_md 