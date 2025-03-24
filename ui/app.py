# -*- coding: utf-8 -*-
"""
主应用窗口模块，实现UI界面。
"""
import os
import sys
import asyncio
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import Dict, List, Any, Optional, Callable

# 导入配置管理模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config_manager import ConfigManager
from utils.security import SecureStorage, mask_sensitive_data
from utils.system_info import collect_system_info, format_system_info_markdown
from utils.email import EmailSender, create_round_email_body, create_final_email_body
from utils.file_utils import (create_log_directory, create_markdown_summary, 
                             create_round_markdown, write_json_file)
from core.benchmark import run_benchmark, sample_random_requests, save_benchmark_result

# 导入其他标签页模块
from ui.main_tab import MainTab
from ui.api_key_tab import ApiKeyTab
from ui.email_tab import EmailTab
from ui.scenarios_tab import ScenariosTab
from ui.logs_tab import LogsTab


class AsyncTkApp:
    """异步Tkinter应用类，处理异步操作"""
    
    def __init__(self, root):
        """
        初始化异步Tkinter应用
        
        Args:
            root: Tkinter根窗口
        """
        self.root = root
        self.loop = asyncio.new_event_loop()
        self.tasks = []
    
    def start(self):
        """启动异步事件循环"""
        def _asyncio_thread():
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        
        self.thread = threading.Thread(target=_asyncio_thread, daemon=True)
        self.thread.start()
    
    def stop(self):
        """停止异步事件循环"""
        if hasattr(self, 'thread'):
            for task in self.tasks:
                task.cancel()
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.thread.join(timeout=1.0)
    
    def create_task(self, coro):
        """
        创建异步任务
        
        Args:
            coro: 协程对象
            
        Returns:
            创建的任务
        """
        task = asyncio.run_coroutine_threadsafe(coro, self.loop)
        self.tasks.append(task)
        return task


class BenchmarkApp(tk.Tk):
    """基准测试应用主窗口类"""
    
    def __init__(self):
        """初始化应用主窗口"""
        super().__init__()
        
        # 设置窗口属性
        self.title("LLM服务基准测试工具 - 版本:1.1.0  作者:邢漫路 联系方式:17917306@qq.com")
        self.geometry("900x700")
        self.minsize(800, 600)
        
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        
        # 初始化安全存储
        self.secure_storage = SecureStorage()
        
        # 初始化异步应用
        self.async_app = AsyncTkApp(self)
        self.async_app.start()
        
        # 创建主框架
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建标签页
        self.create_tabs()
        
        # 创建状态栏
        self.create_statusbar()
        
        # 加载配置
        self.load_configs()
        
        # 绑定关闭事件
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # 绑定全局快捷键
        self.bind_global_shortcuts()
    
    def load_configs(self):
        """加载所有配置"""
        # 加载应用配置
        app_config = self.config_manager.app.get_all()
        
        # 更新主标签页配置
        self.main_tab.load_config(app_config)
        
        # 更新API密钥标签页配置
        self.api_key_tab.load_config(self.config_manager.api_keys)
        
        # 更新邮件标签页配置
        self.email_tab.load_config(self.config_manager.email.get_all())
        
        # 更新测试场景标签页配置
        self.scenarios_tab.load_config(self.config_manager.scenarios.get_scenarios())
    
    def save_configs(self):
        """保存所有配置"""
        # 保存应用配置
        app_config = self.main_tab.get_config()
        self.config_manager.app.update(app_config)
        
        # 保存邮件配置
        email_config = self.email_tab.get_config()
        self.config_manager.email.update(email_config)
        
        # 保存所有配置
        self.config_manager.save_all()
        
        # 更新状态栏
        self.status_var.set("配置已保存")
    
    def update_status(self, message: str):
        """
        更新状态栏消息
        
        Args:
            message: 状态消息
        """
        self.status_var.set(message)
    
    def log_message(self, message: str):
        """
        记录日志消息
        
        Args:
            message: 日志消息
        """
        self.logs_tab.add_log(message)
    
    def start_benchmark(self):
        """启动基准测试"""
        # 获取配置
        app_config = self.main_tab.get_config()
        selected_scenarios = self.main_tab.get_selected_scenarios()
        
        if not selected_scenarios:
            messagebox.showwarning("警告", "请至少选择一个测试场景")
            return
        
        # 获取所有测试场景
        all_scenarios = self.config_manager.scenarios.get_scenarios()
        scenarios_to_run = [all_scenarios[i] for i in selected_scenarios]
        
        # 获取API密钥
        backend = app_config.get("backend", "openai")
        api_key = self.config_manager.api_keys.get_key(backend)
        
        # 获取邮件配置
        email_config = self.email_tab.get_config()
        send_each = self.main_tab.send_each_var.get()
        send_final = self.main_tab.send_final_var.get()
        custom_email_content = email_config.get("custom_email_content", "")
        
        # 收集系统信息
        self.log_message("收集系统信息...")
        system_info = collect_system_info()
        
        # 创建日志目录
        log_dir = create_log_directory()
        self.log_message(f"创建日志目录: {log_dir}")
        
        # 创建摘要Markdown文件（初始版本，后续会更新）
        summary_md = create_markdown_summary(log_dir, "LLM服务基准测试结果汇总报告", app_config, system_info)
        self.log_message(f"创建摘要文件: {summary_md}")
        
        # 创建邮件发送器
        email_sender = None
        if send_each or send_final:
            if email_config.get("email_from") and email_config.get("email_to") and email_config.get("email_password"):
                email_sender = EmailSender(email_config)
                self.log_message("邮件发送器已初始化")
            else:
                self.log_message("警告: 邮箱配置不完整，无法发送邮件")
        
        # 启动测试线程
        threading.Thread(
            target=self._run_benchmark_thread,
            args=(app_config, scenarios_to_run, api_key, log_dir, summary_md, email_sender, send_each, send_final, system_info, custom_email_content),
            daemon=True
        ).start()
    
    def _run_benchmark_thread(self, app_config, scenarios, api_key, log_dir, summary_md, email_sender, send_each, send_final, system_info, custom_email_content):
        """
        运行基准测试线程
        
        Args:
            app_config: 应用配置
            scenarios: 测试场景列表
            api_key: API密钥
            log_dir: 日志目录
            summary_md: 摘要Markdown文件路径
            email_sender: 邮件发送器
            send_each: 是否发送每轮邮件
            send_final: 是否发送最终汇总邮件
            system_info: 系统信息
            custom_email_content: 邮件自定义内容
        """
        # 更新状态
        self.update_status("基准测试运行中...")
        self.log_message("开始基准测试...")
        
        # 记录测试开始时间
        import time
        from datetime import datetime
        start_time = datetime.now()
        start_timestamp = start_time.strftime("%Y-%m-%d %H:%M:%S")
        self.log_message(f"测试开始时间: {start_timestamp}")
        
        # 初始化汇总变量
        total_per_concurrency_output_throughput = 0
        total_per_concurrency_token_throughput = 0
        total_success_rate = 0
        scenario_count = 0
        failed_scenarios = 0
        failed_scenarios_info = []
        
        # 存储所有轮次的测试结果
        all_round_results = []
        
        # 运行每个测试场景
        for i, scenario in enumerate(scenarios):
            scenario_index = i + 1
            self.log_message(f"\n{'='*50}")
            self.log_message(f"执行测试场景: {scenario_index}/{len(scenarios)} - "
                            f"输入长度={scenario.get('input_len')}, "
                            f"输出长度={scenario.get('output_len')}, "
                            f"并发={scenario.get('concurrency')}, "
                            f"请求数={scenario.get('num_prompts')}, "
                            f"范围比率={scenario.get('range_ratio')}, "
                            f"前缀长度={scenario.get('prefix_len')}")
            self.log_message(f"{'='*50}")
            
            # 构建测试配置
            test_config = {
                "backend": app_config.get("backend", "openai"),
                "api_url": f"{app_config.get('base_url', '')}{app_config.get('endpoint', '/v1/completions')}",
                "base_url": app_config.get("base_url", ""),
                "model_id": app_config.get("model", ""),
                "model_name": app_config.get("model", ""),
                "tokenizer": None,  # 需要实现获取tokenizer的逻辑
                "logprobs": None,
                "best_of": 1,
                "request_rate": float("inf"),
                "burstiness": 1.0,
                "disable_tqdm": True,
                "profile": False,
                "selected_percentile_metrics": ["ttft", "tpot", "itl"],
                "selected_percentiles": [99],
                "ignore_eos": False,
                "goodput_config_dict": {},
                "max_concurrency": scenario.get("concurrency", 4),
                "api_key": api_key
            }
            
            # 生成随机请求
            try:
                # 这里需要实现获取tokenizer的逻辑
                # 暂时使用模拟数据
                from collections import namedtuple
                MockTokenizer = namedtuple('MockTokenizer', ['vocab_size', 'decode'])
                mock_tokenizer = MockTokenizer(
                    vocab_size=50000,
                    decode=lambda x: "".join([chr((i % 26) + 97) for i in x])
                )
                
                input_requests = sample_random_requests(
                    prefix_len=scenario.get("prefix_len", 0),
                    input_len=scenario.get("input_len", 50),
                    output_len=scenario.get("output_len", 1024),
                    num_prompts=scenario.get("num_prompts", 20),
                    range_ratio=scenario.get("range_ratio", 1.0),
                    tokenizer=mock_tokenizer
                )
                test_config["input_requests"] = input_requests
                test_config["tokenizer"] = mock_tokenizer
                
                # 运行基准测试
                start_time_scenario = time.time()
                task = self.async_app.create_task(run_benchmark(test_config, self.log_message))
                results = task.result()
                duration = time.time() - start_time_scenario
                
                # 处理结果
                if results:
                    # 保存本轮测试结果到列表中
                    all_round_results.append({
                        "scenario": scenario,
                        "results": results,
                        "duration": int(duration)
                    })
                    
                    # 创建单轮Markdown文件
                    round_md = create_round_markdown(log_dir, scenario_index, scenario, results, int(duration))
                    
                    # 记录到摘要日志
                    self.log_message(f"\n测试场景 {scenario_index} 完成，耗时 {duration:.2f} 秒")
                    self.log_message(f"成功请求数: {results.get('completed', 0)} ({results.get('success_rate', 0):.2f}%)")
                    self.log_message(f"输出词元吞吐量: {results.get('output_throughput', 0):.2f} tok/s")
                    self.log_message(f"每并发输出词元吞吐量: {results.get('per_concurrency_output_throughput', 0):.2f} tok/s/并发")
                    
                    # 累加汇总数据
                    total_per_concurrency_output_throughput += results.get('per_concurrency_output_throughput', 0)
                    total_per_concurrency_token_throughput += results.get('per_concurrency_total_throughput', 0)
                    total_success_rate += results.get('success_rate', 0)
                    scenario_count += 1
                    
                    # 保存结果
                    result_file = os.path.join(log_dir, f"result_{scenario_index}.json")
                    save_benchmark_result(results, test_config, result_file)
                    
                    # 发送每轮邮件
                    if send_each and email_sender:
                        # 准备邮件正文
                        round_email_body = create_round_email_body(scenario, results, int(duration), custom_email_content)
                        round_email_file = os.path.join(log_dir, f"email_round_{scenario_index}.txt")
                        with open(round_email_file, 'w', encoding='utf-8') as f:
                            f.write(round_email_body)
                        
                        # 发送邮件
                        round_email_subject = f"LLM基准测试 - 轮次 {scenario_index}/{len(scenarios)} - 并发{scenario.get('concurrency', 4)}"
                        email_sender.send_email_with_file_body(round_email_subject, round_email_file, [round_md])
                        self.log_message(f"已发送轮次 {scenario_index} 邮件")
                else:
                    # 记录失败信息
                    failed_scenarios += 1
                    error_msg = "未知错误，未返回结果"
                    failed_scenarios_info.append(f"场景 {scenario_index} (输入={scenario.get('input_len')}, 输出={scenario.get('output_len')}, 并发={scenario.get('concurrency')}): {error_msg}")
                    self.log_message(f"警告: 场景 {scenario_index} 执行失败")
            
            except Exception as e:
                # 记录异常信息
                failed_scenarios += 1
                error_msg = str(e)
                failed_scenarios_info.append(f"场景 {scenario_index} (输入={scenario.get('input_len')}, 输出={scenario.get('output_len')}, 并发={scenario.get('concurrency')}): {error_msg}")
                self.log_message(f"错误: 场景 {scenario_index} 执行异常: {error_msg}")
            
            # 等待一段时间，让系统稳定
            time.sleep(2)
        
        # 计算平均值
        if scenario_count > 0:
            avg_per_concurrency_output_throughput = total_per_concurrency_output_throughput / scenario_count
            avg_per_concurrency_token_throughput = total_per_concurrency_token_throughput / scenario_count
            avg_success_rate = total_success_rate / scenario_count
            
            self.log_message("\n" + "="*50)
            self.log_message(f"所有场景的平均指标 (共{scenario_count}个场景)")
            self.log_message(f"平均请求成功率: {avg_success_rate:.2f}%")
            self.log_message(f"平均每并发输出词元吞吐量: {avg_per_concurrency_output_throughput:.2f} tok/s/并发")
            self.log_message(f"平均每并发总词元吞吐量: {avg_per_concurrency_token_throughput:.2f} tok/s/并发")
            self.log_message("="*50)
        
        # 记录测试结束时间
        end_time = datetime.now()
        end_timestamp = end_time.strftime("%Y-%m-%d %H:%M:%S")
        self.log_message(f"\n测试结束时间: {end_timestamp}")
        
        # 创建汇总数据
        summary_data = {
            "start_time": start_timestamp,
            "end_time": end_timestamp,
            "avg_success_rate": avg_success_rate if scenario_count > 0 else 0,
            "avg_per_concurrency_output_throughput": avg_per_concurrency_output_throughput if scenario_count > 0 else 0,
            "avg_per_concurrency_token_throughput": avg_per_concurrency_token_throughput if scenario_count > 0 else 0,
            "failed_scenarios": failed_scenarios_info
        }
        
        # 保存汇总数据
        summary_file = os.path.join(log_dir, "summary.json")
        write_json_file(summary_file, summary_data)
        
        # 更新摘要Markdown文件，包含所有测试结果
        updated_summary_md = create_markdown_summary(
            log_dir, 
            "LLM服务基准测试结果汇总报告", 
            app_config, 
            system_info,
            all_round_results,
            summary_data
        )
        
        # 发送最终汇总邮件
        if send_final and email_sender:
            # 准备邮件正文
            final_email_body = create_final_email_body(summary_data, scenario_count, failed_scenarios, all_round_results, custom_email_content)
            final_email_file = os.path.join(log_dir, "email_final.txt")
            with open(final_email_file, 'w', encoding='utf-8') as f:
                f.write(final_email_body)
            
            # 发送邮件
            final_email_subject = f"LLM基准测试结果汇总 - {start_time.strftime('%Y-%m-%d')}"
            email_sender.send_email_with_file_body(final_email_subject, final_email_file, [updated_summary_md])
            self.log_message("已发送最终汇总邮件")
        
        # 更新状态
        self.update_status("基准测试完成")
        self.log_message(f"所有测试已完成！结果保存在: {log_dir}")
    
    def on_close(self):
        """关闭应用"""
        # 保存配置
        self.save_configs()
        
        # 停止异步应用
        self.async_app.stop()
        
        # 销毁窗口
        self.destroy()
    
    def create_tabs(self):
        """创建标签页"""
        # 创建主标签页
        self.main_tab = MainTab(self.notebook, self)
        self.api_key_tab = ApiKeyTab(self.notebook, self)
        self.email_tab = EmailTab(self.notebook, self)
        self.scenarios_tab = ScenariosTab(self.notebook, self)
        self.logs_tab = LogsTab(self.notebook, self)
        
        # 添加标签页到notebook
        self.notebook.add(self.main_tab, text="主页")
        self.notebook.add(self.api_key_tab, text="API密钥管理")
        self.notebook.add(self.email_tab, text="邮件配置")
        self.notebook.add(self.scenarios_tab, text="测试场景")
        self.notebook.add(self.logs_tab, text="日志")
    
    def create_statusbar(self):
        """创建状态栏"""
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        self.status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def bind_global_shortcuts(self):
        """绑定全局快捷键"""
        # 开始测试的快捷键 (Ctrl+R)
        self.bind('<Control-r>', lambda e: self.start_benchmark())
        
        # 在激活的标签页上执行关键操作的快捷键
        self.bind('<F1>', lambda e: self.show_help())
        
        # 在状态栏显示快捷键提示
        self.update_status("提示: 使用Ctrl+R启动测试, Ctrl+N添加场景, Ctrl+E编辑场景, Ctrl+D删除场景")
    
    def show_help(self):
        """显示帮助信息"""
        help_text = """
快捷键说明:

全局:
- Ctrl+R: 启动测试
- F1: 显示此帮助

场景管理:
- Ctrl+N: 添加新场景
- Ctrl+E: 编辑选中场景
- Ctrl+D: 删除选中场景
- Ctrl+S: 保存配置
- Ctrl+A: 全选场景
        """
        messagebox.showinfo("快捷键帮助", help_text)


def main():
    """主函数"""
    app = BenchmarkApp()
    app.mainloop()


if __name__ == "__main__":
    main() 