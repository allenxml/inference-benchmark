# -*- coding: utf-8 -*-
"""
基准测试核心模块，实现主要的测试逻辑。
"""
import asyncio
import gc
import json
import os
import random
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Callable

import numpy as np
from tqdm.asyncio import tqdm
from transformers import PreTrainedTokenizerBase

from core.request import (ASYNC_REQUEST_FUNCS, RequestFuncInput, RequestFuncOutput, 
                         get_request)
from core.metrics import (BenchmarkMetrics, calculate_metrics, format_metrics_dict,
                         calculate_per_concurrency_metrics, calculate_success_rate)


def sample_random_requests(
    prefix_len: int,
    input_len: int,
    output_len: int,
    num_prompts: int,
    range_ratio: float,
    tokenizer: PreTrainedTokenizerBase,
) -> List[Tuple[str, int, int, None]]:
    """
    生成随机请求
    
    Args:
        prefix_len: 前缀长度
        input_len: 输入长度
        output_len: 输出长度
        num_prompts: 提示数量
        range_ratio: 范围比率
        tokenizer: 分词器
        
    Returns:
        随机请求列表
    """
    prefix_token_ids = np.random.randint(0,
                                         tokenizer.vocab_size,
                                         size=prefix_len).tolist()

    input_lens = np.random.randint(
        int(input_len * range_ratio),
        input_len + 1,
        size=num_prompts,
    )
    output_lens = np.random.randint(
        int(output_len * range_ratio),
        output_len + 1,
        size=num_prompts,
    )
    offsets = np.random.randint(0, tokenizer.vocab_size, size=num_prompts)
    input_requests = []
    for i in range(num_prompts):
        prompt = tokenizer.decode(prefix_token_ids +
                                  [(offsets[i] + i + j) % tokenizer.vocab_size
                                   for j in range(input_lens[i])])

        input_requests.append((prompt, int(prefix_len + input_lens[i]),
                               int(output_lens[i]), None))

    return input_requests


async def run_benchmark(
    config: Dict[str, Any],
    log_callback: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """
    运行基准测试
    
    Args:
        config: 配置字典，包含以下字段：
            - backend: 后端类型
            - api_url: API URL
            - base_url: 基础URL
            - model_id: 模型ID
            - model_name: 模型名称
            - tokenizer: 分词器
            - input_requests: 输入请求列表
            - logprobs: 日志概率
            - best_of: 最佳数量
            - request_rate: 请求速率
            - burstiness: 突发因子
            - disable_tqdm: 是否禁用进度条
            - profile: 是否启用性能分析
            - selected_percentile_metrics: 选定的百分位指标
            - selected_percentiles: 选定的百分位数
            - ignore_eos: 是否忽略EOS
            - goodput_config_dict: 吞吐量配置字典
            - max_concurrency: 最大并发数
            - lora_modules: LoRA模块列表
            - api_key: API密钥
        log_callback: 日志回调函数
        
    Returns:
        测试结果字典
    """
    if log_callback:
        log_callback("开始基准测试...")
    
    backend = config.get("backend", "openai")
    api_url = config.get("api_url", "")
    base_url = config.get("base_url", "")
    model_id = config.get("model_id", "")
    model_name = config.get("model_name", model_id)
    tokenizer = config.get("tokenizer")
    input_requests = config.get("input_requests", [])
    logprobs = config.get("logprobs")
    best_of = config.get("best_of", 1)
    request_rate = config.get("request_rate", float("inf"))
    burstiness = config.get("burstiness", 1.0)
    disable_tqdm = config.get("disable_tqdm", False)
    profile = config.get("profile", False)
    selected_percentile_metrics = config.get("selected_percentile_metrics", ["ttft", "tpot", "itl"])
    selected_percentiles = config.get("selected_percentiles", [99])
    ignore_eos = config.get("ignore_eos", False)
    goodput_config_dict = config.get("goodput_config_dict", {})
    max_concurrency = config.get("max_concurrency")
    lora_modules = config.get("lora_modules")
    api_key = config.get("api_key")
    
    if backend in ASYNC_REQUEST_FUNCS:
        request_func = ASYNC_REQUEST_FUNCS[backend]
    else:
        error_msg = f"未知后端: {backend}"
        if log_callback:
            log_callback(error_msg)
        raise ValueError(error_msg)
    
    if log_callback:
        log_callback("开始初始单一提示测试运行...")
    
    # 初始测试运行
    test_prompt, test_prompt_len, test_output_len, test_mm_content = input_requests[0]
    test_input = RequestFuncInput(
        model=model_id,
        model_name=model_name,
        prompt=test_prompt,
        api_url=api_url,
        prompt_len=test_prompt_len,
        output_len=test_output_len,
        logprobs=logprobs,
        best_of=best_of,
        multi_modal_content=test_mm_content,
        ignore_eos=ignore_eos,
        api_key=api_key,
    )
    
    test_output = await request_func(request_func_input=test_input)
    if not test_output.success:
        error_msg = f"初始测试运行失败 - 请确保基准测试参数正确指定。错误: {test_output.error}"
        if log_callback:
            log_callback(error_msg)
        raise ValueError(error_msg)
    else:
        if log_callback:
            log_callback("初始测试运行完成。开始主基准测试运行...")
    
    if lora_modules:
        # 为每个输入请求随机选择一个LoRA模块
        lora_modules = iter(
            [random.choice(lora_modules) for _ in range(len(input_requests))])
    
    if profile:
        if log_callback:
            log_callback("启动性能分析器...")
        
        profile_input = RequestFuncInput(
            model=model_id,
            model_name=model_name,
            prompt=test_prompt,
            api_url=base_url + "/start_profile",
            prompt_len=test_prompt_len,
            output_len=test_output_len,
            logprobs=logprobs,
            best_of=best_of,
            multi_modal_content=test_mm_content,
            ignore_eos=ignore_eos,
            api_key=api_key,
        )
        profile_output = await request_func(request_func_input=profile_input)
        if profile_output.success:
            if log_callback:
                log_callback("性能分析器已启动")
    
    if burstiness == 1.0:
        distribution = "泊松过程"
    else:
        distribution = "Gamma分布"
    
    if log_callback:
        log_callback(f"流量请求速率: {request_rate}")
        log_callback(f"突发因子: {burstiness} ({distribution})")
        log_callback(f"最大请求并发数: {max_concurrency}")
    
    pbar = None if disable_tqdm else tqdm(total=len(input_requests))
    
    semaphore = (asyncio.Semaphore(max_concurrency)
                 if max_concurrency else None)
    
    async def limited_request_func(request_func_input, pbar):
        if semaphore is None:
            return await request_func(request_func_input=request_func_input,
                                      pbar=pbar)
        async with semaphore:
            return await request_func(request_func_input=request_func_input,
                                      pbar=pbar)
    
    # 避免GC处理"静态"数据 - 减少暂停时间
    gc.collect()
    gc.freeze()
    
    benchmark_start_time = time.perf_counter()
    tasks: List[asyncio.Task] = []
    
    async for request in get_request(input_requests, request_rate, burstiness):
        prompt, prompt_len, output_len, mm_content = request
        req_model_id, req_model_name = model_id, model_name
        if lora_modules:
            req_lora_module = next(lora_modules)
            req_model_id, req_model_name = req_lora_module, req_lora_module
        
        request_func_input = RequestFuncInput(
            model=req_model_id,
            model_name=req_model_name,
            prompt=prompt,
            api_url=api_url,
            prompt_len=prompt_len,
            output_len=output_len,
            logprobs=logprobs,
            best_of=best_of,
            multi_modal_content=mm_content,
            ignore_eos=ignore_eos,
            api_key=api_key,
        )
        tasks.append(
            asyncio.create_task(
                limited_request_func(request_func_input=request_func_input,
                                     pbar=pbar)))
    
    outputs: List[RequestFuncOutput] = await asyncio.gather(*tasks)
    
    if profile:
        if log_callback:
            log_callback("停止性能分析器...")
        
        profile_input = RequestFuncInput(
            model=model_id,
            model_name=model_name,
            prompt=test_prompt,
            api_url=base_url + "/stop_profile",
            prompt_len=test_prompt_len,
            output_len=test_output_len,
            logprobs=logprobs,
            best_of=best_of,
            multi_modal_content=test_mm_content,
            ignore_eos=ignore_eos,
            api_key=api_key,
        )
        profile_output = await request_func(request_func_input=profile_input)
        if profile_output.success:
            if log_callback:
                log_callback("性能分析器已停止")
    
    if pbar is not None:
        pbar.close()
    
    benchmark_duration = time.perf_counter() - benchmark_start_time
    
    metrics, actual_output_lens = calculate_metrics(
        input_requests=input_requests,
        outputs=outputs,
        dur_s=benchmark_duration,
        tokenizer=tokenizer,
        selected_percentile_metrics=selected_percentile_metrics,
        selected_percentiles=selected_percentiles,
        goodput_config_dict=goodput_config_dict,
    )
    
    # 格式化结果
    result = format_metrics_dict(metrics, actual_output_lens)
    
    # 添加其他信息
    result["duration"] = benchmark_duration
    result["input_lens"] = [output.prompt_len for output in outputs]
    result["ttfts"] = [output.ttft for output in outputs]
    result["itls"] = [output.itl for output in outputs]
    result["generated_texts"] = [output.generated_text for output in outputs]
    result["errors"] = [output.error for output in outputs]
    
    # 计算每并发指标
    if max_concurrency:
        per_concurrency_metrics = calculate_per_concurrency_metrics(result, max_concurrency)
        result.update(per_concurrency_metrics)
    
    # 计算成功率和失败率
    total_requests = len(outputs)
    failed_requests = total_requests - metrics.completed
    result["total_requests"] = total_requests
    result["failed"] = failed_requests
    result["success_rate"] = calculate_success_rate(metrics.completed, total_requests)
    result["failure_rate"] = calculate_success_rate(failed_requests, total_requests)
    
    # 打印结果摘要
    if log_callback:
        log_callback("=" * 50)
        log_callback(" 服务基准测试结果 ".center(50, "="))
        log_callback(f"成功请求数: {metrics.completed}")
        log_callback(f"基准测试持续时间 (s): {benchmark_duration:.2f}")
        log_callback(f"总输入词元数: {metrics.total_input}")
        log_callback(f"总生成词元数: {metrics.total_output}")
        log_callback(f"请求吞吐量 (req/s): {metrics.request_throughput:.2f}")
        
        if goodput_config_dict:
            log_callback(f"请求有效吞吐量 (req/s): {metrics.request_goodput:.2f}")
        
        log_callback(f"输出词元吞吐量 (tok/s): {metrics.output_throughput:.2f}")
        log_callback(f"总词元吞吐量 (tok/s): {metrics.total_token_throughput:.2f}")
        
        if max_concurrency:
            log_callback(f"每并发输出词元吞吐量 (tok/s/并发): {result.get('per_concurrency_output_throughput', 0):.2f}")
            log_callback(f"每并发总词元吞吐量 (tok/s/并发): {result.get('per_concurrency_total_throughput', 0):.2f}")
        
        # 打印延迟指标
        if "ttft" in selected_percentile_metrics:
            log_callback("-" * 50)
            log_callback("首词延迟 (TTFT)")
            log_callback(f"平均TTFT (ms): {metrics.mean_ttft_ms:.2f}")
            log_callback(f"中位数TTFT (ms): {metrics.median_ttft_ms:.2f}")
            for p, value in metrics.percentiles_ttft_ms:
                p_word = str(int(p)) if int(p) == p else str(p)
                log_callback(f"P{p_word} TTFT (ms): {value:.2f}")
        
        if "tpot" in selected_percentile_metrics:
            log_callback("-" * 50)
            log_callback("每词延迟 (TPOT) (不含首词)")
            log_callback(f"平均TPOT (ms): {metrics.mean_tpot_ms:.2f}")
            log_callback(f"中位数TPOT (ms): {metrics.median_tpot_ms:.2f}")
            for p, value in metrics.percentiles_tpot_ms:
                p_word = str(int(p)) if int(p) == p else str(p)
                log_callback(f"P{p_word} TPOT (ms): {value:.2f}")
        
        if "itl" in selected_percentile_metrics:
            log_callback("-" * 50)
            log_callback("词间延迟 (ITL)")
            log_callback(f"平均ITL (ms): {metrics.mean_itl_ms:.2f}")
            log_callback(f"中位数ITL (ms): {metrics.median_itl_ms:.2f}")
            for p, value in metrics.percentiles_itl_ms:
                p_word = str(int(p)) if int(p) == p else str(p)
                log_callback(f"P{p_word} ITL (ms): {value:.2f}")
        
        if "e2el" in selected_percentile_metrics:
            log_callback("-" * 50)
            log_callback("端到端延迟 (E2EL)")
            log_callback(f"平均E2EL (ms): {metrics.mean_e2el_ms:.2f}")
            log_callback(f"中位数E2EL (ms): {metrics.median_e2el_ms:.2f}")
            for p, value in metrics.percentiles_e2el_ms:
                p_word = str(int(p)) if int(p) == p else str(p)
                log_callback(f"P{p_word} E2EL (ms): {value:.2f}")
        
        log_callback("=" * 50)
    
    return result


def save_benchmark_result(result: Dict[str, Any], config: Dict[str, Any], file_path: str) -> None:
    """
    保存基准测试结果
    
    Args:
        result: 测试结果字典
        config: 配置字典
        file_path: 文件路径
    """
    # 创建结果JSON
    result_json = {}
    
    # 设置
    current_dt = datetime.now().strftime("%Y%m%d-%H%M%S")
    result_json["date"] = current_dt
    result_json["backend"] = config.get("backend", "")
    result_json["model_id"] = config.get("model_id", "")
    result_json["tokenizer_id"] = config.get("tokenizer_id", "")
    result_json["best_of"] = config.get("best_of", 1)
    result_json["num_prompts"] = config.get("num_prompts", 0)
    
    # 元数据
    metadata = config.get("metadata", {})
    for key, value in metadata.items():
        result_json[key] = value
    
    # 流量
    result_json["request_rate"] = (config.get("request_rate") if config.get("request_rate", float("inf"))
                                  < float("inf") else "inf")
    result_json["burstiness"] = config.get("burstiness", 1.0)
    result_json["max_concurrency"] = config.get("max_concurrency")
    
    # 合并测试结果
    result_json.update(result)
    
    # 保存到文件
    with open(file_path, "w", encoding='utf-8') as outfile:
        json.dump(result_json, outfile, ensure_ascii=False, indent=2) 