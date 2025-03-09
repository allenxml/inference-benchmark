# -*- coding: utf-8 -*-
"""
指标计算模块，用于计算和分析性能指标。
"""
import warnings
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
from transformers import PreTrainedTokenizerBase

from core.request import RequestFuncOutput

# 毫秒到秒的转换系数
MILLISECONDS_TO_SECONDS_CONVERSION = 1000


@dataclass
class BenchmarkMetrics:
    """基准测试指标数据类"""
    completed: int
    total_input: int
    total_output: int
    request_throughput: float
    request_goodput: float
    output_throughput: float
    total_token_throughput: float
    mean_ttft_ms: float
    median_ttft_ms: float
    std_ttft_ms: float
    percentiles_ttft_ms: List[Tuple[float, float]]
    mean_tpot_ms: float
    median_tpot_ms: float
    std_tpot_ms: float
    percentiles_tpot_ms: List[Tuple[float, float]]
    mean_itl_ms: float
    median_itl_ms: float
    std_itl_ms: float
    percentiles_itl_ms: List[Tuple[float, float]]
    # E2EL表示每个请求的端到端延迟
    # 它是客户端从发送请求到接收完整响应所花费的时间
    mean_e2el_ms: float
    median_e2el_ms: float
    std_e2el_ms: float
    percentiles_e2el_ms: List[Tuple[float, float]]


def calculate_metrics(
    input_requests: List[Tuple[str, int, int, None]],
    outputs: List[RequestFuncOutput],
    dur_s: float,
    tokenizer: PreTrainedTokenizerBase,
    selected_percentile_metrics: List[str],
    selected_percentiles: List[float],
    goodput_config_dict: Dict[str, float],
) -> Tuple[BenchmarkMetrics, List[int]]:
    """
    计算基准测试指标
    
    Args:
        input_requests: 输入请求列表
        outputs: 请求输出结果列表
        dur_s: 测试持续时间（秒）
        tokenizer: 分词器
        selected_percentile_metrics: 选定的百分位指标
        selected_percentiles: 选定的百分位数
        goodput_config_dict: 吞吐量配置字典
        
    Returns:
        (指标对象, 实际输出长度列表)
    """
    actual_output_lens: List[int] = []
    total_input = 0
    completed = 0
    good_completed = 0
    itls: List[float] = []
    tpots: List[float] = []
    all_tpots: List[float] = []
    ttfts: List[float] = []
    e2els: List[float] = []
    
    for i in range(len(outputs)):
        if outputs[i].success:
            output_len = outputs[i].output_tokens

            if output_len is None:
                # 对于某些服务后端，我们使用分词器计算输出词元数量
                # 而不是查看len(outputs[i].itl)，因为多个输出词元可能被打包在一起
                # 注意：这可能会略微夸大输出词元数量
                output_len = len(
                    tokenizer(outputs[i].generated_text,
                              add_special_tokens=False).input_ids)
            actual_output_lens.append(output_len)
            total_input += input_requests[i][1]
            tpot = 0
            if output_len > 1:
                latency_minus_ttft = outputs[i].latency - outputs[i].ttft
                tpot = latency_minus_ttft / (output_len - 1)
                tpots.append(tpot)
            # 注意：如果output_len <= 1，我们将tpot视为0（用于goodput计算）
            all_tpots.append(tpot)
            itls += outputs[i].itl
            ttfts.append(outputs[i].ttft)
            e2els.append(outputs[i].latency)
            completed += 1
        else:
            actual_output_lens.append(0)

    if goodput_config_dict:
        valid_metrics = []
        slo_values = []

        if "ttft" in goodput_config_dict:
            valid_metrics.append(ttfts)
            slo_values.append(goodput_config_dict["ttft"] /
                              MILLISECONDS_TO_SECONDS_CONVERSION)
        if "tpot" in goodput_config_dict:
            valid_metrics.append(all_tpots)
            slo_values.append(goodput_config_dict["tpot"] /
                              MILLISECONDS_TO_SECONDS_CONVERSION)
        if "e2el" in goodput_config_dict:
            valid_metrics.append(e2els)
            slo_values.append(goodput_config_dict["e2el"] /
                              MILLISECONDS_TO_SECONDS_CONVERSION)

        for req_metric in zip(*valid_metrics):
            is_good_req = all([s >= r for s, r in zip(slo_values, req_metric)])
            if is_good_req:
                good_completed += 1

    if completed == 0:
        warnings.warn(
            "所有请求都失败了。这可能是由于基准测试参数配置错误导致的。",
            stacklevel=2)
    
    metrics = BenchmarkMetrics(
        completed=completed,
        total_input=total_input,
        total_output=sum(actual_output_lens),
        request_throughput=completed / dur_s,
        request_goodput=good_completed / dur_s,
        output_throughput=sum(actual_output_lens) / dur_s,
        total_token_throughput=(total_input + sum(actual_output_lens)) / dur_s,
        mean_ttft_ms=np.mean(ttfts or [0]) * 1000,
        std_ttft_ms=np.std(ttfts or [0]) * 1000,
        median_ttft_ms=np.median(ttfts or [0]) * 1000,
        percentiles_ttft_ms=[(p, np.percentile(ttfts or [0], p) * 1000)
                             for p in selected_percentiles],
        mean_tpot_ms=np.mean(tpots or [0]) * 1000,
        std_tpot_ms=np.std(tpots or [0]) * 1000,
        median_tpot_ms=np.median(tpots or [0]) * 1000,
        percentiles_tpot_ms=[(p, np.percentile(tpots or [0], p) * 1000)
                             for p in selected_percentiles],
        mean_itl_ms=np.mean(itls or [0]) * 1000,
        std_itl_ms=np.std(itls or [0]) * 1000,
        median_itl_ms=np.median(itls or [0]) * 1000,
        percentiles_itl_ms=[(p, np.percentile(itls or [0], p) * 1000)
                            for p in selected_percentiles],
        mean_e2el_ms=np.mean(e2els or [0]) * 1000,
        std_e2el_ms=np.std(e2els or [0]) * 1000,
        median_e2el_ms=np.median(e2els or [0]) * 1000,
        percentiles_e2el_ms=[(p, np.percentile(e2els or [0], p) * 1000)
                             for p in selected_percentiles],
    )

    return metrics, actual_output_lens


def format_metrics_dict(metrics: BenchmarkMetrics, actual_output_lens: List[int]) -> Dict[str, Any]:
    """
    将指标对象格式化为字典
    
    Args:
        metrics: 指标对象
        actual_output_lens: 实际输出长度列表
        
    Returns:
        格式化后的指标字典
    """
    result = {
        "completed": metrics.completed,
        "total_input_tokens": metrics.total_input,
        "total_output_tokens": metrics.total_output,
        "request_throughput": metrics.request_throughput,
        "request_goodput": metrics.request_goodput,
        "output_throughput": metrics.output_throughput,
        "total_token_throughput": metrics.total_token_throughput,
        "output_lens": actual_output_lens,
        
        # TTFT指标
        "mean_ttft_ms": metrics.mean_ttft_ms,
        "median_ttft_ms": metrics.median_ttft_ms,
        "std_ttft_ms": metrics.std_ttft_ms,
        
        # TPOT指标
        "mean_tpot_ms": metrics.mean_tpot_ms,
        "median_tpot_ms": metrics.median_tpot_ms,
        "std_tpot_ms": metrics.std_tpot_ms,
        
        # ITL指标
        "mean_itl_ms": metrics.mean_itl_ms,
        "median_itl_ms": metrics.median_itl_ms,
        "std_itl_ms": metrics.std_itl_ms,
        
        # E2EL指标
        "mean_e2el_ms": metrics.mean_e2el_ms,
        "median_e2el_ms": metrics.median_e2el_ms,
        "std_e2el_ms": metrics.std_e2el_ms,
    }
    
    # 添加百分位数指标
    for p, value in metrics.percentiles_ttft_ms:
        p_word = str(int(p)) if int(p) == p else str(p)
        result[f"p{p_word}_ttft_ms"] = value
    
    for p, value in metrics.percentiles_tpot_ms:
        p_word = str(int(p)) if int(p) == p else str(p)
        result[f"p{p_word}_tpot_ms"] = value
    
    for p, value in metrics.percentiles_itl_ms:
        p_word = str(int(p)) if int(p) == p else str(p)
        result[f"p{p_word}_itl_ms"] = value
    
    for p, value in metrics.percentiles_e2el_ms:
        p_word = str(int(p)) if int(p) == p else str(p)
        result[f"p{p_word}_e2el_ms"] = value
    
    return result


def calculate_per_concurrency_metrics(metrics: Dict[str, Any], concurrency: int) -> Dict[str, float]:
    """
    计算每并发指标
    
    Args:
        metrics: 指标字典
        concurrency: 并发数
        
    Returns:
        每并发指标字典
    """
    per_concurrency_metrics = {}
    
    if "output_throughput" in metrics and concurrency > 0:
        per_concurrency_metrics["per_concurrency_output_throughput"] = metrics["output_throughput"] / concurrency
    
    if "total_token_throughput" in metrics and concurrency > 0:
        per_concurrency_metrics["per_concurrency_total_throughput"] = metrics["total_token_throughput"] / concurrency
    
    return per_concurrency_metrics


def calculate_success_rate(completed: int, total: int) -> float:
    """
    计算成功率
    
    Args:
        completed: 成功完成的请求数
        total: 总请求数
        
    Returns:
        成功率（百分比）
    """
    if total == 0:
        return 0.0
    return (completed / total) * 100


def visualize_metrics(metrics_list: List[Dict[str, Any]], scenario_names: List[str], output_file: Optional[str] = None):
    """
    可视化指标
    
    Args:
        metrics_list: 指标字典列表
        scenario_names: 场景名称列表
        output_file: 输出文件路径，如果为None则显示图表
    """
    import matplotlib.pyplot as plt
    
    # 创建图表
    fig, axs = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('LLM基准测试结果', fontsize=16)
    
    # 吞吐量图表
    throughputs = [m.get("output_throughput", 0) for m in metrics_list]
    axs[0, 0].bar(scenario_names, throughputs)
    axs[0, 0].set_title('输出词元吞吐量')
    axs[0, 0].set_ylabel('词元/秒')
    axs[0, 0].tick_params(axis='x', rotation=45)
    
    # TTFT图表
    ttfts = [m.get("median_ttft_ms", 0) for m in metrics_list]
    axs[0, 1].bar(scenario_names, ttfts)
    axs[0, 1].set_title('首词延迟 (TTFT)')
    axs[0, 1].set_ylabel('毫秒')
    axs[0, 1].tick_params(axis='x', rotation=45)
    
    # TPOT图表
    tpots = [m.get("median_tpot_ms", 0) for m in metrics_list]
    axs[1, 0].bar(scenario_names, tpots)
    axs[1, 0].set_title('每词延迟 (TPOT)')
    axs[1, 0].set_ylabel('毫秒')
    axs[1, 0].tick_params(axis='x', rotation=45)
    
    # 每并发吞吐量图表
    per_concurrency = [m.get("per_concurrency_output_throughput", 0) for m in metrics_list]
    axs[1, 1].bar(scenario_names, per_concurrency)
    axs[1, 1].set_title('每并发输出词元吞吐量')
    axs[1, 1].set_ylabel('词元/秒/并发')
    axs[1, 1].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file)
    else:
        plt.show() 