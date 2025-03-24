# -*- coding: utf-8 -*-
"""
邮件功能模块，用于发送测试结果邮件。
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional, Union


class EmailSender:
    """邮件发送类，提供邮件发送功能"""
    
    def __init__(self, config: Dict[str, Union[str, int, bool]]):
        """
        初始化邮件发送器
        
        Args:
            config: 邮件配置字典，包含以下字段：
                - email_from: 发件人邮箱
                - email_to: 收件人邮箱，多个收件人用逗号分隔
                - email_password: 邮箱密码
                - smtp_server: SMTP服务器地址
                - smtp_port: SMTP服务器端口
        """
        self.config = config
    
    def send_email(self, subject: str, body: str, attachments: Optional[List[str]] = None) -> bool:
        """
        发送邮件
        
        Args:
            subject: 邮件主题
            body: 邮件正文
            attachments: 附件文件路径列表
            
        Returns:
            是否发送成功
        """
        email_from = self.config.get("email_from")
        email_to = self.config.get("email_to")
        password = self.config.get("email_password")
        smtp_server = self.config.get("smtp_server", "smtp.qq.com")
        smtp_port = int(self.config.get("smtp_port", 465))
        
        if not email_from or not email_to or not password:
            print("错误: 邮箱配置不完整，无法发送邮件")
            return False
        
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = email_from
            msg['To'] = email_to
            msg['Subject'] = subject
            
            # 添加邮件正文
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # 添加附件
            if attachments:
                for attachment in attachments:
                    if os.path.exists(attachment):
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
    
    def send_email_with_file_body(self, subject: str, body_file: str, attachments: Optional[List[str]] = None) -> bool:
        """
        从文件读取正文内容并发送邮件
        
        Args:
            subject: 邮件主题
            body_file: 邮件正文文件路径
            attachments: 附件文件路径列表
            
        Returns:
            是否发送成功
        """
        try:
            with open(body_file, 'r', encoding='utf-8') as f:
                body = f.read()
            return self.send_email(subject, body, attachments)
        except Exception as e:
            print(f"读取邮件正文文件失败: {e}")
            return False


def create_round_email_body(scenario: Dict[str, Union[str, int, float]], results: Dict[str, Union[str, int, float]], duration: int, custom_content: str = "") -> str:
    """
    创建单轮测试的邮件正文
    
    Args:
        scenario: 测试场景配置
        results: 测试结果
        duration: 测试持续时间（秒）
        custom_content: 自定义邮件内容
        
    Returns:
        邮件正文
    """
    # 拼接自定义内容和测试结果
    test_content = f"""场景: 输入={scenario.get('input_len')}, 输出={scenario.get('output_len')}, 并发={scenario.get('concurrency')}, 请求={scenario.get('num_prompts')}, 范围={scenario.get('range_ratio')}, 前缀={scenario.get('prefix_len')}
执行时间: {duration} 秒

---------------请求统计----------------
成功请求数: {results.get('completed', 0)} ({results.get('success_rate', 0)}%)
失败请求数: {results.get('failed', 0)} ({results.get('failure_rate', 0)}%)
总请求数: {results.get('total_requests', 0)}

---------------吞吐量指标----------------
请求吞吐量: {results.get('request_throughput', 0)} req/s
输出词元吞吐量: {results.get('output_throughput', 0)} tok/s
每并发输出词元吞吐量: {results.get('per_concurrency_output_throughput', 0)} tok/s/并发
总词元吞吐量: {results.get('total_token_throughput', 0)} tok/s
每并发总词元吞吐量: {results.get('per_concurrency_total_throughput', 0)} tok/s/并发

---------------首词延迟 (TTFT)----------------
平均TTFT (ms): {results.get('mean_ttft_ms', 0)}
中位数TTFT (ms): {results.get('median_ttft_ms', 0)}
P99 TTFT (ms): {results.get('p99_ttft_ms', 0)}

-----每词延迟 (TPOT) (不含首词)------
平均TPOT (ms): {results.get('mean_tpot_ms', 0)}
中位数TPOT (ms): {results.get('median_tpot_ms', 0)}
P99 TPOT (ms): {results.get('p99_tpot_ms', 0)}

---------------词间延迟 (ITL)----------------
平均ITL (ms): {results.get('mean_itl_ms', 0)}
中位数ITL (ms): {results.get('median_itl_ms', 0)}
P99 ITL (ms): {results.get('p99_itl_ms', 0)}
"""

    # 如果有自定义内容，添加到测试结果前面
    if custom_content:
        body = f"{custom_content}\n\n{'-' * 50}\n\n{test_content}"
    else:
        body = test_content
        
    return body


def create_final_email_body(summary: Dict[str, Union[str, int, float]], scenarios_count: int, failed_count: int, all_round_results: List[Dict] = None, custom_content: str = "") -> str:
    """
    创建最终汇总邮件正文
    
    Args:
        summary: 测试汇总结果
        scenarios_count: 测试场景数量
        failed_count: 失败场景数量
        all_round_results: 所有轮次的测试结果和场景信息
        custom_content: 自定义邮件内容
        
    Returns:
        邮件正文
    """
    # 基本摘要信息
    test_content = f"""LLM基准测试结果汇总

测试开始时间: {summary.get('start_time', '')}
测试结束时间: {summary.get('end_time', '')}

测试场景数量: {scenarios_count} 成功, {failed_count} 失败

平均请求成功率: {summary.get('avg_success_rate', 0)}%
平均每并发输出词元吞吐量: {summary.get('avg_per_concurrency_output_throughput', 0)} tok/s/并发
平均每并发总词元吞吐量: {summary.get('avg_per_concurrency_token_throughput', 0)} tok/s/并发

"""

    # 如果有轮次结果，添加所有轮次的详细信息
    if all_round_results and len(all_round_results) > 0:
        test_content += "\n\n==================== 各轮次详细测试结果 ====================\n\n"
        
        for i, round_data in enumerate(all_round_results):
            scenario = round_data.get("scenario", {})
            results = round_data.get("results", {})
            duration = round_data.get("duration", 0)
            
            if not scenario or not results:
                continue
                
            test_content += f"""
==================== 轮次 {i+1} ====================

场景: 输入={scenario.get('input_len')}, 输出={scenario.get('output_len')}, 并发={scenario.get('concurrency')}, 请求={scenario.get('num_prompts')}, 范围={scenario.get('range_ratio')}, 前缀={scenario.get('prefix_len')}
执行时间: {duration} 秒

---------------请求统计----------------
成功请求数: {results.get('completed', 0)} ({results.get('success_rate', 0)}%)
失败请求数: {results.get('failed', 0)} ({results.get('failure_rate', 0)}%)
总请求数: {results.get('total_requests', 0)}

---------------吞吐量指标----------------
请求吞吐量: {results.get('request_throughput', 0)} req/s
输出词元吞吐量: {results.get('output_throughput', 0)} tok/s
每并发输出词元吞吐量: {results.get('per_concurrency_output_throughput', 0)} tok/s/并发
总词元吞吐量: {results.get('total_token_throughput', 0)} tok/s
每并发总词元吞吐量: {results.get('per_concurrency_total_throughput', 0)} tok/s/并发

---------------首词延迟 (TTFT)----------------
平均TTFT (ms): {results.get('mean_ttft_ms', 0)}
中位数TTFT (ms): {results.get('median_ttft_ms', 0)}
P99 TTFT (ms): {results.get('p99_ttft_ms', 0)}

-----每词延迟 (TPOT) (不含首词)------
平均TPOT (ms): {results.get('mean_tpot_ms', 0)}
中位数TPOT (ms): {results.get('median_tpot_ms', 0)}
P99 TPOT (ms): {results.get('p99_tpot_ms', 0)}

---------------词间延迟 (ITL)----------------
平均ITL (ms): {results.get('mean_itl_ms', 0)}
中位数ITL (ms): {results.get('median_itl_ms', 0)}
P99 ITL (ms): {results.get('p99_itl_ms', 0)}
"""

    # 如果有自定义内容，添加到测试结果前面
    if custom_content:
        body = f"{custom_content}\n\n{'-' * 50}\n\n{test_content}"
    else:
        body = test_content
    
    return body 