# -*- coding: utf-8 -*-
"""
请求处理模块，用于发送API请求。
"""
import json
import time
import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Callable

import aiohttp
from tqdm.asyncio import tqdm


@dataclass
class RequestFuncInput:
    """请求函数输入参数"""
    model: str
    prompt: str
    api_url: str
    prompt_len: int
    output_len: int
    logprobs: Optional[int] = None
    best_of: int = 1
    multi_modal_content: Optional[Any] = None
    ignore_eos: bool = False
    model_name: Optional[str] = None
    api_key: Optional[str] = None


@dataclass
class RequestFuncOutput:
    """请求函数输出结果"""
    success: bool
    generated_text: str = ""
    prompt_len: int = 0
    output_tokens: Optional[int] = None
    latency: float = 0
    ttft: float = 0
    itl: Optional[List[float]] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.itl is None:
            self.itl = []


def retry_async(max_attempts: int = 3, delay: float = 1.0):
    """
    异步重试装饰器
    
    Args:
        max_attempts: 最大尝试次数
        delay: 重试延迟（秒）
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            attempts = 0
            last_exception = None
            
            while attempts < max_attempts:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    last_exception = e
                    if attempts < max_attempts:
                        await asyncio.sleep(delay)
            
            # 所有尝试都失败，返回错误结果
            if isinstance(args[0], RequestFuncInput):
                return RequestFuncOutput(
                    success=False,
                    prompt_len=args[0].prompt_len,
                    error=f"重试{max_attempts}次后失败: {str(last_exception)}"
                )
            raise last_exception
        
        return wrapper
    return decorator


@retry_async(max_attempts=3)
async def openai_request(request_func_input: RequestFuncInput, pbar: Optional[tqdm] = None) -> RequestFuncOutput:
    """
    OpenAI API请求函数
    
    Args:
        request_func_input: 请求输入参数
        pbar: 进度条对象
        
    Returns:
        请求输出结果
    """
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
                prev_token_time = start_time
                
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


# vLLM使用与OpenAI兼容的API，所以直接使用openai_request
vllm_request = openai_request

# 定义异步请求函数字典
ASYNC_REQUEST_FUNCS = {
    "openai": openai_request,
    "vllm": vllm_request,
}


async def get_request(
    input_requests: List[Tuple[str, int, int, None]],
    request_rate: float,
    burstiness: float = 1.0,
):
    """
    异步生成请求，按指定速率发送
    
    Args:
        input_requests: 输入请求列表
        request_rate: 请求速率（请求/秒）
        burstiness: 突发因子，默认为1.0（泊松过程）
        
    Yields:
        请求元组 (prompt, prompt_len, output_len, multi_modal_content)
    """
    import numpy as np
    
    input_requests = iter(input_requests)

    # 计算尺度参数theta以保持所需的请求速率
    assert burstiness > 0, f"突发因子必须为正数，但给定了 {burstiness}"
    theta = 1.0 / (request_rate * burstiness)

    for request in input_requests:
        yield request

        if request_rate == float("inf"):
            # 如果请求速率是无穷大，则不需要等待
            continue

        # 从gamma分布采样请求间隔
        # 如果burstiness为1，则遵循指数分布
        interval = np.random.gamma(shape=burstiness, scale=theta)
        # 下一个请求将在间隔后发送
        await asyncio.sleep(interval) 