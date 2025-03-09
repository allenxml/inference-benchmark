#!/bin/bash

# -*- coding: utf-8 -*-

# 显示帮助信息的函数
show_help() {
  echo "用法: $0 [选项]"
  echo ""
  echo "vLLM基准测试脚本，执行一系列测试场景并发送邮件报告。"
  echo ""
  echo "基本选项:"
  echo "  -h, --help                   显示此帮助信息并退出"
  echo "  -u, --url URL                设置基础URL (默认: http://127.0.0.1:8000)"
  echo "  -m, --model MODEL            设置模型名称 (默认: test)"
  echo "  -t, --tokenizer PATH         设置分词器路径 (默认: /models/qwen-2.5-7b-instruct-1m/)"
  echo "  -b, --backend BACKEND        设置后端类型 (默认: openai)"
  echo ""
  echo "邮件选项:"
  echo "  -f, --email-from EMAIL       设置发件人邮箱地址 (默认: 17917306@qq.com)"
  echo "  -e, --email-to EMAILS        设置收件人邮箱地址，多个地址用逗号分隔 (默认: 17917306@qq.com)"
  echo "  --send-each, --send-email-each-round"
  echo "                               启用每轮测试后发送邮件 (默认: 启用)"
  echo "  --no-send-each, --no-send-email-each-round"
  echo "                               禁用每轮测试后发送邮件"
  echo "  --send-final, --send-email-final"
  echo "                               启用最终汇总邮件发送 (默认: 启用)"
  echo "  --no-send-final, --no-send-email-final"
  echo "                               禁用最终汇总邮件发送"
  echo ""
  echo "示例:"
  echo "  $0 -u http://localhost:8080 -m llama2 -t /path/to/tokenizer"
  echo "  $0 -e \"user1@example.com,user2@example.com\" --no-send-each"
  echo "  $0 -f \"myemail@example.com\" --no-send-final"
  echo ""
  echo "注意:"
  echo "  该脚本需要一个名为email_password.txt的文件，其中只包含发件人邮箱的密码。"
  echo "  当前脚本使用QQ邮箱的SMTP服务器发送邮件。如需使用其他邮箱，请修改脚本中的SMTP设置。"
}

# 设置基本变量
BASE_URL="http://127.0.0.1:8000"
MODEL="test"
TOKENIZER="/models/qwen-2.5-7b-instruct-1m/"
BACKEND="openai"
SCRIPT_PATH="/github/vllm/benchmarks/benchmark_serving_random.py"

# 邮件设置默认值
EMAIL_FROM="17917306@qq.com"
EMAIL_TO="17917306@qq.com"
SEND_EMAIL_EACH_ROUND=true
SEND_EMAIL_FINAL=true

# 解析命令行参数
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -h|--help)
      show_help
      exit 0
      ;;
    -u|--url)
      BASE_URL="$2"
      shift 2
      ;;
    -m|--model)
      MODEL="$2"
      shift 2
      ;;
    -t|--tokenizer)
      TOKENIZER="$2"
      shift 2
      ;;
    -b|--backend)
      BACKEND="$2"
      shift 2
      ;;
    -f|--email-from)
      EMAIL_FROM="$2"
      shift 2
      ;;
    -e|--email-to)
      EMAIL_TO="$2"
      shift 2
      ;;
    --send-each|--send-email-each-round)
      SEND_EMAIL_EACH_ROUND=true
      shift
      ;;
    --no-send-each|--no-send-email-each-round)
      SEND_EMAIL_EACH_ROUND=false
      shift
      ;;  
    --send-final|--send-email-final)
      SEND_EMAIL_FINAL=true
      shift
      ;;
    --no-send-final|--no-send-email-final)
      SEND_EMAIL_FINAL=false
      shift
      ;;
    *)
      # 其他参数忽略
      shift
      ;;
  esac
done

# 创建日志目录
LOG_DIR="benchmark_logs_$(date +%Y%m%d_%H%M%S)"
mkdir -p $LOG_DIR

# 添加UTF-8编码声明到Python脚本
if ! grep -q "# -*- coding: utf-8 -*-" $SCRIPT_PATH; then
  # 创建一个临时文件用于编辑
  TMP_FILE=$(mktemp)
  echo "# -*- coding: utf-8 -*-" > $TMP_FILE
  cat $SCRIPT_PATH >> $TMP_FILE
  # 使用临时文件替换原始文件
  mv $TMP_FILE $SCRIPT_PATH
  echo "已添加UTF-8编码声明到脚本文件"
fi

# 定义ANSI颜色代码
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# 打印当前配置信息
echo -e "${BLUE}基准测试配置:${NC}"
echo "基础URL: $BASE_URL"
echo "模型: $MODEL"
echo "分词器: $TOKENIZER"
echo "后端: $BACKEND"
echo "发件人: $EMAIL_FROM"
echo "收件人: $EMAIL_TO"
echo "每轮邮件: $([ "$SEND_EMAIL_EACH_ROUND" = true ] && echo "启用" || echo "禁用")"
echo "汇总邮件: $([ "$SEND_EMAIL_FINAL" = true ] && echo "启用" || echo "禁用")"
echo ""

# 创建汇总Markdown文件
SUMMARY_MD="$LOG_DIR/benchmark_summary.md"
touch $SUMMARY_MD
echo "# vLLM基准测试结果汇总报告" > $SUMMARY_MD
echo "" >> $SUMMARY_MD
echo "生成时间: $(date)" >> $SUMMARY_MD
echo "" >> $SUMMARY_MD

# 记录配置信息到Markdown
echo "## 测试配置" >> $SUMMARY_MD
echo "" >> $SUMMARY_MD
echo "- 基础URL: $BASE_URL" >> $SUMMARY_MD
echo "- 模型: $MODEL" >> $SUMMARY_MD
echo "- 分词器: $TOKENIZER" >> $SUMMARY_MD
echo "- 后端: $BACKEND" >> $SUMMARY_MD
echo "" >> $SUMMARY_MD

# 记录测试开始时间
START_TIMESTAMP=$(date)
echo -e "${BOLD}测试开始时间: $START_TIMESTAMP${NC}" | tee $LOG_DIR/summary.log
echo "## 测试开始时间: $START_TIMESTAMP" >> $SUMMARY_MD

# 记录系统信息
SYS_INFO="$LOG_DIR/system_info.txt"
touch $SYS_INFO
echo "测试系统信息:" > $SYS_INFO
echo "日期: $(date)" >> $SYS_INFO
echo "主机名: $(hostname)" >> $SYS_INFO
echo "操作系统: $(uname -a)" >> $SYS_INFO
echo "CPU信息: $(cat /proc/cpuinfo | grep 'model name' | head -1 | cut -d':' -f2 | xargs)" >> $SYS_INFO
echo "核心数: $(nproc)" >> $SYS_INFO
echo "内存总量: $(free -h | grep Mem | awk '{print $2}')" >> $SYS_INFO

# 添加系统信息到Markdown - 修复了这部分
echo "" >> $SUMMARY_MD
echo "## 系统信息" >> $SUMMARY_MD
echo "" >> $SUMMARY_MD
echo "```" >> $SUMMARY_MD
cat $SYS_INFO >> $SUMMARY_MD
echo "```" >> $SUMMARY_MD
echo "" >> $SUMMARY_MD

# 检查是否有nvidia-smi并记录GPU信息 - 修复了这部分
if command -v nvidia-smi &> /dev/null; then
  echo "### GPU信息" >> $SUMMARY_MD
  echo "" >> $SUMMARY_MD
  
  # 安全获取GPU数量，默认为0
  gpu_count=0
  if nvidia-smi --query-gpu=count --format=csv,noheader &> /dev/null; then
    gpu_count=$(nvidia-smi --query-gpu=count --format=csv,noheader 2>/dev/null || echo "0")
  fi
  
  # 确保gpu_count是数字
  if ! [[ "$gpu_count" =~ ^[0-9]+$ ]]; then
    gpu_count=0
  fi
  
  # 对于每个GPU，收集核心信息
  if [ "$gpu_count" -gt 0 ]; then
    for ((i=0; i<$gpu_count; i++)); do
      # 获取GPU信息，添加错误处理
      gpu_name=$(nvidia-smi --query-gpu=name --format=csv,noheader -i $i 2>/dev/null || echo "未知GPU")
      driver_ver=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader -i $i 2>/dev/null || echo "未知")
      mem_total=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader -i $i 2>/dev/null || echo "未知")
      utilization=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader -i $i 2>/dev/null || echo "未知")
      temp=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader -i $i 2>/dev/null || echo "未知")
      
      # 这种格式在Markdown中非常清晰易读
      echo "**GPU $i: $gpu_name**" >> $SUMMARY_MD
      echo "- 驱动版本: $driver_ver" >> $SUMMARY_MD
      echo "- 显存总量: $mem_total" >> $SUMMARY_MD
      echo "- GPU利用率: $utilization" >> $SUMMARY_MD
      echo "- 温度: $temp" >> $SUMMARY_MD
      echo "" >> $SUMMARY_MD
    done
  else
    echo "未检测到可用GPU或无法访问nvidia-smi" >> $SUMMARY_MD
    echo "" >> $SUMMARY_MD
  fi
  
  # 同时也将GPU信息添加到系统信息文件
  echo "GPU信息:" >> $SYS_INFO
  nvidia-smi >> $SYS_INFO 2>/dev/null || echo "无法获取详细GPU信息" >> $SYS_INFO
else
  echo "### GPU信息" >> $SUMMARY_MD
  echo "" >> $SUMMARY_MD
  echo "系统未安装或无法访问nvidia-smi工具" >> $SUMMARY_MD
  echo "" >> $SUMMARY_MD
  
  echo "GPU信息: 系统未安装或无法访问nvidia-smi工具" >> $SYS_INFO
fi

# 定义测试场景参数集合
# 格式: "输入长度 输出长度 并发数 请求数 范围比率 前缀长度"
SCENARIOS=(
  "50 1024 4 20 1.0 0 "
#  "50 1024 8 40 1.0 0 "
#  "50 1024 16 80 1.0 0 "
#  "50 1024 32 160 1.0 0 "
#  "50 1024 64 320 1.0 0 "
#  "50 1024 128 640 1.0 0 "
#  "8192 1024 4 40 1.0 0 "
#  "8192 1024 8 80 1.0 0 "
#  "8192 1024 16 160 1.0 0"
#  "8192 1024 32 320 1.0 0"
#  "16384 2048 4 40 1.0 0 "
#  "16384 2048 8 80 1.0 0 "
)

# 添加测试场景信息到Markdown
echo "## 测试场景配置" >> $SUMMARY_MD
echo "" >> $SUMMARY_MD
echo "| 场景 | 输入长度 | 输出长度 | 并发数 | 请求数 | 范围比率 | 前缀长度 |" >> $SUMMARY_MD
echo "|------|----------|----------|--------|--------|----------|----------|" >> $SUMMARY_MD
SCENARIO_INDEX=0
for scenario in "${SCENARIOS[@]}"; do
  SCENARIO_INDEX=$((SCENARIO_INDEX + 1))
  read -r input_len output_len concurrency num_prompts range_ratio prefix_len burstiness <<< "$scenario"
  echo "| 场景$SCENARIO_INDEX | $input_len | $output_len | $concurrency | $num_prompts | $range_ratio | $prefix_len |" >> $SUMMARY_MD
done
echo "" >> $SUMMARY_MD

# 初始化汇总变量
TOTAL_PER_CONCURRENCY_OUTPUT_THROUGHPUT=0
TOTAL_PER_CONCURRENCY_TOKEN_THROUGHPUT=0
TOTAL_SUCCESS_RATE=0
SCENARIO_COUNT=0
FAILED_SCENARIOS=0
FAILED_SCENARIOS_INFO=""

# 创建延迟指标汇总文件
LATENCY_SUMMARY="$LOG_DIR/latency_summary.txt"
touch $LATENCY_SUMMARY
echo "延迟指标平均值:" > $LATENCY_SUMMARY
echo "指标 | 平均值 | 中位数 | P99" >> $LATENCY_SUMMARY
echo "-----|--------|--------|----" >> $LATENCY_SUMMARY

# 检查脚本参数需求
echo "检查Python脚本参数需求..."
python3 $SCRIPT_PATH --help > $LOG_DIR/help.txt 2>&1

# 初始化默认参数字典
declare -A DEFAULT_PARAMS=(
  ["dataset-name"]="random"
  ["profile"]=""
  ["request-rate"]="inf"
)

# 检查哪些参数在help中被标记为必需
grep -o "\-\-[a-zA-Z0-9\-]*" $LOG_DIR/help.txt | sort | uniq > $LOG_DIR/all_params.txt

# 检查参数是否存在于帮助文本中
check_param_exists() {
  local param=$1
  if grep -q "\-\-$param" $LOG_DIR/help.txt; then
    return 0  # 参数存在
  else
    return 1  # 参数不存在
  fi
}

# 函数：发送邮件
send_email() {
  local subject="$1"
  local body_file="$2"
  local attachment="$3"
  
  # 从外部文件读取邮箱密码
  local PASSWORD_FILE="email_password.txt"
  if [ ! -f $PASSWORD_FILE ]; then
    echo "错误: 邮箱密码文件 $PASSWORD_FILE 不存在"
    echo "请创建文件并仅输入密码内容，不要有多余字符"
    return 1
  fi

  # 读取密码
  local EMAIL_PASSWORD=$(cat $PASSWORD_FILE)
  
  # 使用Python发送邮件
  echo "使用Python发送邮件..."
  python3 - << EOF
import smtplib
import email.message
import base64
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# 邮件设置
sender = "$EMAIL_FROM"
receivers = "$EMAIL_TO".split(',')  # 支持多收件人
password = """$EMAIL_PASSWORD"""
subject = "$subject"

# 创建邮件
msg = MIMEMultipart()
msg['From'] = sender
msg['To'] = "$EMAIL_TO"
msg['Subject'] = subject

# 读取邮件内容
with open("$body_file", 'r') as f:
    body = f.read()

# 添加邮件正文
msg.attach(MIMEText(body, 'plain'))

# 添加附件（如果存在）
if "$attachment" and os.path.exists("$attachment"):
    try:
        with open("$attachment", "rb") as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            filename = os.path.basename("$attachment")
            part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
            msg.attach(part)
            print(f"已添加附件: {filename}")
    except Exception as e:
        print(f"添加附件时出错: {e}")

# 连接邮件服务器并发送
try:
    server = smtplib.SMTP_SSL('smtp.qq.com', 465)
    server.login(sender, password)
    server.sendmail(sender, receivers, msg.as_string())
    server.quit()
    print("邮件发送成功！")
except Exception as e:
    print(f"邮件发送失败: {e}")
EOF
  
  echo "邮件已发送到 $EMAIL_TO"
}

# 遍历执行每个测试场景
SCENARIO_INDEX=0
TOTAL_SCENARIOS=${#SCENARIOS[@]}

for scenario in "${SCENARIOS[@]}"; do
  SCENARIO_INDEX=$((SCENARIO_INDEX + 1))
  
  # 解析参数
  read -r input_len output_len concurrency num_prompts range_ratio prefix_len burstiness <<< "$scenario"
  
  # 为当前场景创建Markdown部分
  echo "## 场景 $SCENARIO_INDEX: 输入=$input_len, 输出=$output_len, 并发=$concurrency, 请求=$num_prompts" >> $SUMMARY_MD
  echo "" >> $SUMMARY_MD
  
  # 检查并限制范围比率不超过1.0
  if (( $(awk -v r="$range_ratio" 'BEGIN {print (r > 1.0) ? 1 : 0}') )); then
    echo "警告: 范围比率 $range_ratio 大于1.0，已自动调整为1.0"
    range_ratio=1.0
  fi
  
  # 确保前缀长度不超过输入长度
  if [ $prefix_len -gt $input_len ]; then
    echo "警告: 前缀长度 $prefix_len 大于输入长度 $input_len，已自动调整为 $input_len"
    prefix_len=$input_len
  fi
  
  echo -e "\n${BLUE}==================================================${NC}"
  echo -e "${BLUE}执行测试场景: $SCENARIO_INDEX/$TOTAL_SCENARIOS - 输入长度=$input_len, 输出长度=$output_len, 并发=$concurrency, 请求数=$num_prompts, 范围比率=$range_ratio, 前缀长度=$prefix_len, 突发度=$burstiness${NC}"
  echo -e "${BLUE}==================================================${NC}"
  
  # 构建日志文件名
  LOG_FILE="$LOG_DIR/benchmark_in${input_len}_out${output_len}_conc${concurrency}_req${num_prompts}_range${range_ratio}_prefix${prefix_len}_burst${burstiness}.log"
  
  # 构建基础命令
  BASE_CMD="python3 $SCRIPT_PATH --backend $BACKEND --base-url $BASE_URL --model $MODEL --tokenizer $TOKENIZER"
  
  # 添加其他参数（使用默认值检查）
  PARAMS=""
  
  # 检查并添加随机输入长度
  if check_param_exists "random-input-len"; then
    PARAMS="$PARAMS --random-input-len $input_len"
  fi
  
  # 检查并添加随机输出长度
  if check_param_exists "random-output-len"; then
    PARAMS="$PARAMS --random-output-len $output_len"
  fi
  
  # 检查并添加最大并发
  if check_param_exists "max-concurrency"; then
    PARAMS="$PARAMS --max-concurrency $concurrency"
  fi
  
  # 检查并添加请求数量
  if check_param_exists "num-prompts"; then
    PARAMS="$PARAMS --num-prompts $num_prompts"
  fi
  
  # 检查并添加随机范围比率
  if check_param_exists "random-range-ratio"; then
    PARAMS="$PARAMS --random-range-ratio $range_ratio"
  fi
  
  # 检查并添加随机前缀长度
  if check_param_exists "random-prefix-len"; then
    PARAMS="$PARAMS --random-prefix-len $prefix_len"
  fi
  
  # 检查并添加请求速率（特殊处理，总是添加以避免错误）
  PARAMS="$PARAMS --request-rate ${DEFAULT_PARAMS["request-rate"]}"
  
  # 检查并添加数据集名称
  if check_param_exists "dataset-name"; then
    PARAMS="$PARAMS --dataset-name ${DEFAULT_PARAMS["dataset-name"]}"
  fi
  
  # 检查并添加profile参数
  if check_param_exists "profile"; then
    PARAMS="$PARAMS --profile"
  fi
  
  # 构建完整命令
  CMD="$BASE_CMD $PARAMS"
  
  echo "运行命令: $CMD"
  echo "正在执行...日志文件: $LOG_FILE"
  
  # 执行命令并记录日志
  START_TIME=$(date +%s)
  $CMD | tee $LOG_FILE
  CMD_STATUS=${PIPESTATUS[0]}
  END_TIME=$(date +%s)
  
  # 计算执行时间
  DURATION=$((END_TIME - START_TIME))
  
  # 记录到摘要日志
  echo "" | tee -a $LOG_DIR/summary.log
  # 使用红色突出显示场景标题行
  echo -e "${RED}${BOLD}场景: 输入=$input_len, 输出=$output_len, 并发=$concurrency, 请求=$num_prompts, 范围=$range_ratio, 前缀=$prefix_len, 突发度=$burstiness${NC}" | tee -a $LOG_DIR/summary.log
  echo "执行时间: $DURATION 秒" | tee -a $LOG_DIR/summary.log
  
  # 创建单个场景的Markdown文件
  ROUND_MD="$LOG_DIR/round_${SCENARIO_INDEX}.md"
  touch $ROUND_MD
  echo "# 场景 $SCENARIO_INDEX 测试结果" > $ROUND_MD
  echo "" >> $ROUND_MD
  echo "**场景**: 输入=$input_len, 输出=$output_len, 并发=$concurrency, 请求=$num_prompts, 范围=$range_ratio, 前缀=$prefix_len, 突发度=$burstiness" >> $ROUND_MD
  echo "" >> $ROUND_MD
  echo "**执行时间**: $DURATION 秒" >> $ROUND_MD
  echo "" >> $ROUND_MD
  
  # 添加到总的Markdown
  echo "**执行时间**: $DURATION 秒" >> $SUMMARY_MD
  echo "" >> $SUMMARY_MD
  
  # 检查命令执行状态
  if [ $CMD_STATUS -ne 0 ]; then
    echo -e "${RED}警告: 命令执行失败，返回代码: $CMD_STATUS${NC}" | tee -a $LOG_DIR/summary.log
    echo "检查日志文件以获取更多信息: $LOG_FILE"
    echo -e "${YELLOW}跳过当前场景，继续下一个...${NC}"
    
    # 记录失败信息
    FAILED_SCENARIOS=$((FAILED_SCENARIOS + 1))
    ERROR_MSG=$(grep -i "error\|exception\|failed" $LOG_FILE | head -3 | tr '\n' ' ')
    if [ -z "$ERROR_MSG" ]; then
      ERROR_MSG="未知错误，返回代码 $CMD_STATUS"
    fi
    FAILED_SCENARIOS_INFO="$FAILED_SCENARIOS_INFO\n- 场景 (输入=$input_len, 输出=$output_len, 并发=$concurrency): $ERROR_MSG"
    
    # 记录到单个场景Markdown
    echo "### 警告: 命令执行失败，返回代码: $CMD_STATUS" >> $ROUND_MD
    echo "" >> $ROUND_MD
    echo "错误信息: $ERROR_MSG" >> $ROUND_MD
    echo "" >> $ROUND_MD
    
    # 记录到总的Markdown
    echo "### 警告: 命令执行失败，返回代码: $CMD_STATUS" >> $SUMMARY_MD
    echo "" >> $SUMMARY_MD
    echo "错误信息: $ERROR_MSG" >> $SUMMARY_MD
    echo "" >> $SUMMARY_MD
    
    # 如果启用每轮邮件，则发送失败轮次邮件
    if [ "$SEND_EMAIL_EACH_ROUND" = true ]; then
      # 准备失败轮次邮件正文
      ROUND_EMAIL_BODY="$LOG_DIR/email_round_${SCENARIO_INDEX}.txt"
      touch $ROUND_EMAIL_BODY
      echo "场景: 输入=$input_len, 输出=$output_len, 并发=$concurrency, 请求=$num_prompts, 范围=$range_ratio, 前缀=$prefix_len, 突发度=$burstiness" > $ROUND_EMAIL_BODY
      echo "执行时间: $DURATION 秒" >> $ROUND_EMAIL_BODY
      echo "警告: 命令执行失败，返回代码: $CMD_STATUS" >> $ROUND_EMAIL_BODY
      echo "错误信息: $ERROR_MSG" >> $ROUND_EMAIL_BODY
      
      # 创建描述性的附件名称（添加失败标识）
      DESCRIPTIVE_ATTACHMENT_NAME="vLLM测试_输入${input_len}_输出${output_len}_并发${concurrency}_失败.md"
      
      # 创建一个临时文件，复制原始Markdown内容
      cp "$ROUND_MD" "$LOG_DIR/$DESCRIPTIVE_ATTACHMENT_NAME"
      
      # 发送失败轮次邮件
      ROUND_EMAIL_SUBJECT="vLLM基准测试 - 轮次 $SCENARIO_INDEX/$TOTAL_SCENARIOS (失败) - 并发$concurrency - $(date +%Y-%m-%d_%H:%M)"
      send_email "$ROUND_EMAIL_SUBJECT" "$ROUND_EMAIL_BODY" "$LOG_DIR/$DESCRIPTIVE_ATTACHMENT_NAME"
    fi
    
    continue
  fi
  
  # 提取指标
  if [ -f $LOG_FILE ]; then
    # 提取成功请求数和总请求数
    SUCCESSFUL_REQUESTS=$(grep "Successful requests:" $LOG_FILE | awk '{print $3}')
    SUCCESSFUL_REQUESTS_PCT=$(grep "Successful requests:" $LOG_FILE | awk '{print $4}' | sed 's/[()%]//g')
    FAILED_REQUESTS=$(grep "Failed requests:" $LOG_FILE | awk '{print $3}')
    FAILED_REQUESTS_PCT=$(grep "Failed requests:" $LOG_FILE | awk '{print $4}' | sed 's/[()%]//g')
    TOTAL_REQUESTS=$(grep "Total requests:" $LOG_FILE | awk '{print $3}')
    
    # 如果百分比不存在或为空，则手动计算
    if [ -z "$SUCCESSFUL_REQUESTS_PCT" ] || [ "$SUCCESSFUL_REQUESTS_PCT" = "%" ]; then
      if [ ! -z "$SUCCESSFUL_REQUESTS" ] && [ ! -z "$TOTAL_REQUESTS" ] && [ "$TOTAL_REQUESTS" -ne 0 ]; then
        SUCCESSFUL_REQUESTS_PCT=$(awk -v s="$SUCCESSFUL_REQUESTS" -v t="$TOTAL_REQUESTS" 'BEGIN {printf "%.2f", (s/t)*100}')
      else
        SUCCESSFUL_REQUESTS_PCT="0.00"
      fi
    fi
    
    # 同样处理失败率
    if [ -z "$FAILED_REQUESTS_PCT" ] || [ "$FAILED_REQUESTS_PCT" = "%" ]; then
      if [ ! -z "$FAILED_REQUESTS" ] && [ ! -z "$TOTAL_REQUESTS" ] && [ "$TOTAL_REQUESTS" -ne 0 ]; then
        FAILED_REQUESTS_PCT=$(awk -v f="$FAILED_REQUESTS" -v t="$TOTAL_REQUESTS" 'BEGIN {printf "%.2f", (f/t)*100}')
      else
        FAILED_REQUESTS_PCT="0.00"
      fi
    fi
    
    # 累加成功率以计算平均值
    if [ ! -z "$SUCCESSFUL_REQUESTS_PCT" ]; then
      TOTAL_SUCCESS_RATE=$(awk -v a=$TOTAL_SUCCESS_RATE -v b=$SUCCESSFUL_REQUESTS_PCT 'BEGIN {print a + b}')
    fi
    
    # 基本吞吐量指标
    THROUGHPUT=$(grep "Request throughput" $LOG_FILE | awk '{print $NF}')
    OUTPUT_THROUGHPUT=$(grep "Output token throughput" $LOG_FILE | awk '{print $NF}')
    TOTAL_THROUGHPUT=$(grep "Total Token throughput" $LOG_FILE | awk '{print $NF}')
    
    # 计算每并发的吞吐量
    PER_CONCURRENCY_OUTPUT_THROUGHPUT=$(awk -v throughput="$OUTPUT_THROUGHPUT" -v concurrency="$concurrency" 'BEGIN {printf "%.2f", throughput / concurrency}')
    PER_CONCURRENCY_TOTAL_THROUGHPUT=$(awk -v throughput="$TOTAL_THROUGHPUT" -v concurrency="$concurrency" 'BEGIN {printf "%.2f", throughput / concurrency}')
    
    # TTFT 指标
    MEAN_TTFT=$(grep "Mean TTFT" $LOG_FILE | awk '{print $NF}')
    MEDIAN_TTFT=$(grep "Median TTFT" $LOG_FILE | awk '{print $NF}')
    P99_TTFT=$(grep "P99 TTFT" $LOG_FILE | awk '{print $NF}')
    
    # TPOT 指标
    MEAN_TPOT=$(grep "Mean TPOT" $LOG_FILE | awk '{print $NF}')
    MEDIAN_TPOT=$(grep "Median TPOT" $LOG_FILE | awk '{print $NF}')
    P99_TPOT=$(grep "P99 TPOT" $LOG_FILE | awk '{print $NF}')
    
    # ITL 指标
    MEAN_ITL=$(grep "Mean ITL" $LOG_FILE | awk '{print $NF}')
    MEDIAN_ITL=$(grep "Median ITL" $LOG_FILE | awk '{print $NF}')
    P99_ITL=$(grep "P99 ITL" $LOG_FILE | awk '{print $NF}')
    
    # 记录延迟指标到汇总文件
    echo "TTFT | $MEAN_TTFT | $MEDIAN_TTFT | $P99_TTFT" >> $LATENCY_SUMMARY
    echo "TPOT | $MEAN_TPOT | $MEDIAN_TPOT | $P99_TPOT" >> $LATENCY_SUMMARY
    echo "ITL | $MEAN_ITL | $MEDIAN_ITL | $P99_ITL" >> $LATENCY_SUMMARY
    
    # 写入请求成功率到摘要 - 使用默认颜色
    echo "---------------请求统计----------------" | tee -a $LOG_DIR/summary.log
    if [ ! -z "$SUCCESSFUL_REQUESTS" ]; then
      echo "成功请求数: $SUCCESSFUL_REQUESTS ($SUCCESSFUL_REQUESTS_PCT%)" | tee -a $LOG_DIR/summary.log
    fi
    if [ ! -z "$FAILED_REQUESTS" ]; then
      echo "失败请求数: $FAILED_REQUESTS ($FAILED_REQUESTS_PCT%)" | tee -a $LOG_DIR/summary.log
    fi
    if [ ! -z "$TOTAL_REQUESTS" ]; then
      echo "总请求数: $TOTAL_REQUESTS" | tee -a $LOG_DIR/summary.log
    fi
    
    # Markdown请求统计
    echo "### 请求统计" >> $ROUND_MD
    echo "" >> $ROUND_MD
    if [ ! -z "$SUCCESSFUL_REQUESTS" ]; then
      echo "成功请求数: $SUCCESSFUL_REQUESTS ($SUCCESSFUL_REQUESTS_PCT%)" >> $ROUND_MD
    fi
    if [ ! -z "$FAILED_REQUESTS" ]; then
      echo "失败请求数: $FAILED_REQUESTS ($FAILED_REQUESTS_PCT%)" >> $ROUND_MD
    fi
    if [ ! -z "$TOTAL_REQUESTS" ]; then
      echo "总请求数: $TOTAL_REQUESTS" >> $ROUND_MD
    fi
    echo "" >> $ROUND_MD
    
    # 同样添加到总的Markdown
    echo "### 请求统计" >> $SUMMARY_MD
    echo "" >> $SUMMARY_MD
    if [ ! -z "$SUCCESSFUL_REQUESTS" ]; then
      echo "成功请求数: $SUCCESSFUL_REQUESTS ($SUCCESSFUL_REQUESTS_PCT%)" >> $SUMMARY_MD
    fi
    if [ ! -z "$FAILED_REQUESTS" ]; then
      echo "失败请求数: $FAILED_REQUESTS ($FAILED_REQUESTS_PCT%)" >> $SUMMARY_MD
    fi
    if [ ! -z "$TOTAL_REQUESTS" ]; then
      echo "总请求数: $TOTAL_REQUESTS" >> $SUMMARY_MD
    fi
    echo "" >> $SUMMARY_MD
    
    # 写入基本吞吐量到摘要 - 使用默认颜色
    echo "---------------吞吐量指标----------------" | tee -a $LOG_DIR/summary.log
    if [ ! -z "$THROUGHPUT" ]; then
      echo "请求吞吐量: $THROUGHPUT req/s" | tee -a $LOG_DIR/summary.log
    fi
    if [ ! -z "$OUTPUT_THROUGHPUT" ]; then
      echo "输出词元吞吐量: $OUTPUT_THROUGHPUT tok/s" | tee -a $LOG_DIR/summary.log
      echo "每并发输出词元吞吐量: $PER_CONCURRENCY_OUTPUT_THROUGHPUT tok/s/并发" | tee -a $LOG_DIR/summary.log
      # 累加总和以计算平均值
      TOTAL_PER_CONCURRENCY_OUTPUT_THROUGHPUT=$(awk -v a=$TOTAL_PER_CONCURRENCY_OUTPUT_THROUGHPUT -v b=$PER_CONCURRENCY_OUTPUT_THROUGHPUT 'BEGIN {print a + b}')
    fi
    if [ ! -z "$TOTAL_THROUGHPUT" ]; then
      echo "总词元吞吐量: $TOTAL_THROUGHPUT tok/s" | tee -a $LOG_DIR/summary.log
      echo "每并发总词元吞吐量: $PER_CONCURRENCY_TOTAL_THROUGHPUT tok/s/并发" | tee -a $LOG_DIR/summary.log
      # 累加总和以计算平均值
      TOTAL_PER_CONCURRENCY_TOKEN_THROUGHPUT=$(awk -v a=$TOTAL_PER_CONCURRENCY_TOKEN_THROUGHPUT -v b=$PER_CONCURRENCY_TOTAL_THROUGHPUT 'BEGIN {print a + b}')
    fi
    
    # Markdown吞吐量指标
    echo "### 吞吐量指标" >> $ROUND_MD
    echo "" >> $ROUND_MD
    if [ ! -z "$THROUGHPUT" ]; then
      echo "请求吞吐量: $THROUGHPUT req/s" >> $ROUND_MD
    fi
    if [ ! -z "$OUTPUT_THROUGHPUT" ]; then
      echo "输出词元吞吐量: $OUTPUT_THROUGHPUT tok/s" >> $ROUND_MD
      echo "每并发输出词元吞吐量: $PER_CONCURRENCY_OUTPUT_THROUGHPUT tok/s/并发" >> $ROUND_MD
    fi
    if [ ! -z "$TOTAL_THROUGHPUT" ]; then
      echo "总词元吞吐量: $TOTAL_THROUGHPUT tok/s" >> $ROUND_MD
      echo "每并发总词元吞吐量: $PER_CONCURRENCY_TOTAL_THROUGHPUT tok/s/并发" >> $ROUND_MD
    fi
    echo "" >> $ROUND_MD
    
    # 同样添加到总的Markdown
    echo "### 吞吐量指标" >> $SUMMARY_MD
    echo "" >> $SUMMARY_MD
    if [ ! -z "$THROUGHPUT" ]; then
      echo "请求吞吐量: $THROUGHPUT req/s" >> $SUMMARY_MD
    fi
    if [ ! -z "$OUTPUT_THROUGHPUT" ]; then
      echo "输出词元吞吐量: $OUTPUT_THROUGHPUT tok/s" >> $SUMMARY_MD
      echo "每并发输出词元吞吐量: $PER_CONCURRENCY_OUTPUT_THROUGHPUT tok/s/并发" >> $SUMMARY_MD
    fi
    if [ ! -z "$TOTAL_THROUGHPUT" ]; then
      echo "总词元吞吐量: $TOTAL_THROUGHPUT tok/s" >> $SUMMARY_MD
      echo "每并发总词元吞吐量: $PER_CONCURRENCY_TOTAL_THROUGHPUT tok/s/并发" >> $SUMMARY_MD
    fi
    echo "" >> $SUMMARY_MD
    
    # 写入TTFT指标到摘要 - 使用默认颜色
    echo "---------------首词延迟 (TTFT)----------------" | tee -a $LOG_DIR/summary.log
    if [ ! -z "$MEAN_TTFT" ]; then
      echo "平均TTFT (ms): $MEAN_TTFT" | tee -a $LOG_DIR/summary.log
    fi
    if [ ! -z "$MEDIAN_TTFT" ]; then
      echo "中位数TTFT (ms): $MEDIAN_TTFT" | tee -a $LOG_DIR/summary.log
    fi
    if [ ! -z "$P99_TTFT" ]; then
      echo "P99 TTFT (ms): $P99_TTFT" | tee -a $LOG_DIR/summary.log
    fi
    
    # Markdown TTFT指标
    echo "### 首词延迟 (TTFT)" >> $ROUND_MD
    echo "" >> $ROUND_MD
    if [ ! -z "$MEAN_TTFT" ]; then
      echo "平均TTFT (ms): $MEAN_TTFT" >> $ROUND_MD
    fi
    if [ ! -z "$MEDIAN_TTFT" ]; then
      echo "中位数TTFT (ms): $MEDIAN_TTFT" >> $ROUND_MD
    fi
    if [ ! -z "$P99_TTFT" ]; then
      echo "P99 TTFT (ms): $P99_TTFT" >> $ROUND_MD
    fi
    echo "" >> $ROUND_MD
    
    # 同样添加到总的Markdown
    echo "### 首词延迟 (TTFT)" >> $SUMMARY_MD
    echo "" >> $SUMMARY_MD
    if [ ! -z "$MEAN_TTFT" ]; then
      echo "平均TTFT (ms): $MEAN_TTFT" >> $SUMMARY_MD
    fi
    if [ ! -z "$MEDIAN_TTFT" ]; then
      echo "中位数TTFT (ms): $MEDIAN_TTFT" >> $SUMMARY_MD
    fi
    if [ ! -z "$P99_TTFT" ]; then
      echo "P99 TTFT (ms): $P99_TTFT" >> $SUMMARY_MD
    fi
    echo "" >> $SUMMARY_MD
    
    # 写入TPOT指标到摘要 - 使用默认颜色
    echo "-----每词延迟 (TPOT) (不含首词)------" | tee -a $LOG_DIR/summary.log
    if [ ! -z "$MEAN_TPOT" ]; then
      echo "平均TPOT (ms): $MEAN_TPOT" | tee -a $LOG_DIR/summary.log
    fi
    if [ ! -z "$MEDIAN_TPOT" ]; then
      echo "中位数TPOT (ms): $MEDIAN_TPOT" | tee -a $LOG_DIR/summary.log
    fi
    if [ ! -z "$P99_TPOT" ]; then
      echo "P99 TPOT (ms): $P99_TPOT" | tee -a $LOG_DIR/summary.log
    fi
    
    # Markdown TPOT指标
    echo "### 每词延迟 (TPOT) (不含首词)" >> $ROUND_MD
    echo "" >> $ROUND_MD
    if [ ! -z "$MEAN_TPOT" ]; then
      echo "平均TPOT (ms): $MEAN_TPOT" >> $ROUND_MD
    fi
    if [ ! -z "$MEDIAN_TPOT" ]; then
      echo "中位数TPOT (ms): $MEDIAN_TPOT" >> $ROUND_MD
    fi
    if [ ! -z "$P99_TPOT" ]; then
      echo "P99 TPOT (ms): $P99_TPOT" >> $ROUND_MD
    fi
    echo "" >> $ROUND_MD
    
    # 同样添加到总的Markdown
    echo "### 每词延迟 (TPOT) (不含首词)" >> $SUMMARY_MD
    echo "" >> $SUMMARY_MD
    if [ ! -z "$MEAN_TPOT" ]; then
      echo "平均TPOT (ms): $MEAN_TPOT" >> $SUMMARY_MD
    fi
    if [ ! -z "$MEDIAN_TPOT" ]; then
      echo "中位数TPOT (ms): $MEDIAN_TPOT" >> $SUMMARY_MD
    fi
    if [ ! -z "$P99_TPOT" ]; then
      echo "P99 TPOT (ms): $P99_TPOT" >> $SUMMARY_MD
    fi
    echo "" >> $SUMMARY_MD
    
    # 写入ITL指标到摘要 - 使用默认颜色
    echo "---------------词间延迟 (ITL)----------------" | tee -a $LOG_DIR/summary.log
    if [ ! -z "$MEAN_ITL" ]; then
      echo "平均ITL (ms): $MEAN_ITL" | tee -a $LOG_DIR/summary.log
    fi
    if [ ! -z "$MEDIAN_ITL" ]; then
      echo "中位数ITL (ms): $MEDIAN_ITL" | tee -a $LOG_DIR/summary.log
    fi
    if [ ! -z "$P99_ITL" ]; then
      echo "P99 ITL (ms): $P99_ITL" | tee -a $LOG_DIR/summary.log
    fi
    
    # Markdown ITL指标
    echo "### 词间延迟 (ITL)" >> $ROUND_MD
    echo "" >> $ROUND_MD
    if [ ! -z "$MEAN_ITL" ]; then
      echo "平均ITL (ms): $MEAN_ITL" >> $ROUND_MD
    fi
    if [ ! -z "$MEDIAN_ITL" ]; then
      echo "中位数ITL (ms): $MEDIAN_ITL" >> $ROUND_MD
    fi
    if [ ! -z "$P99_ITL" ]; then
      echo "P99 ITL (ms): $P99_ITL" >> $ROUND_MD
    fi
    echo "" >> $ROUND_MD
    
    # 同样添加到总的Markdown
    echo "### 词间延迟 (ITL)" >> $SUMMARY_MD
    echo "" >> $SUMMARY_MD
    if [ ! -z "$MEAN_ITL" ]; then
      echo "平均ITL (ms): $MEAN_ITL" >> $SUMMARY_MD
    fi
    if [ ! -z "$MEDIAN_ITL" ]; then
      echo "中位数ITL (ms): $MEDIAN_ITL" >> $SUMMARY_MD
    fi
    if [ ! -z "$P99_ITL" ]; then
      echo "P99 ITL (ms): $P99_ITL" >> $SUMMARY_MD
    fi
    echo "" >> $SUMMARY_MD
    
    # 增加场景计数
    SCENARIO_COUNT=$((SCENARIO_COUNT + 1))
    
    # 如果启用了每轮发送邮件，则发送当前轮次邮件
    if [ "$SEND_EMAIL_EACH_ROUND" = true ]; then
      # 准备邮件正文
      ROUND_EMAIL_BODY="$LOG_DIR/email_round_${SCENARIO_INDEX}.txt"
      touch $ROUND_EMAIL_BODY
      cat > $ROUND_EMAIL_BODY << EOF
场景: 输入=$input_len, 输出=$output_len, 并发=$concurrency, 请求=$num_prompts, 范围=$range_ratio, 前缀=$prefix_len, 突发度=$burstiness
执行时间: $DURATION 秒
---------------请求统计----------------
成功请求数: $SUCCESSFUL_REQUESTS ($SUCCESSFUL_REQUESTS_PCT%)
失败请求数: $FAILED_REQUESTS ($FAILED_REQUESTS_PCT%)
总请求数: $TOTAL_REQUESTS
---------------吞吐量指标----------------
请求吞吐量: $THROUGHPUT req/s
输出词元吞吐量: $OUTPUT_THROUGHPUT tok/s
每并发输出词元吞吐量: $PER_CONCURRENCY_OUTPUT_THROUGHPUT tok/s/并发
总词元吞吐量: $TOTAL_THROUGHPUT tok/s
每并发总词元吞吐量: $PER_CONCURRENCY_TOTAL_THROUGHPUT tok/s/并发
---------------首词延迟 (TTFT)----------------
平均TTFT (ms): $MEAN_TTFT
中位数TTFT (ms): $MEDIAN_TTFT
P99 TTFT (ms): $P99_TTFT
-----每词延迟 (TPOT) (不含首词)------
平均TPOT (ms): $MEAN_TPOT
中位数TPOT (ms): $MEDIAN_TPOT
P99 TPOT (ms): $P99_TPOT
---------------词间延迟 (ITL)----------------
平均ITL (ms): $MEAN_ITL
中位数ITL (ms): $MEDIAN_ITL
P99 ITL (ms): $P99_ITL
EOF

      # 创建描述性的附件名称
      DESCRIPTIVE_ATTACHMENT_NAME="vLLM测试_输入${input_len}_输出${output_len}_并发${concurrency}.md"
      
      # 创建一个临时文件，复制原始Markdown内容
      cp "$ROUND_MD" "$LOG_DIR/$DESCRIPTIVE_ATTACHMENT_NAME"
      
      # 发送当前轮次邮件，使用新的描述性附件名称
      ROUND_EMAIL_SUBJECT="vLLM基准测试 - 轮次 $SCENARIO_INDEX/$TOTAL_SCENARIOS - 并发$concurrency - $(date +%Y-%m-%d_%H:%M)"
      send_email "$ROUND_EMAIL_SUBJECT" "$ROUND_EMAIL_BODY" "$LOG_DIR/$DESCRIPTIVE_ATTACHMENT_NAME"
    fi
  fi
  
  echo -e "${BLUE}==================================================${NC}"
  echo "测试场景完成。等待5秒后执行下一个场景..."
  echo ""
  
  # 在Markdown文件中添加分隔符
  echo "---" >> $SUMMARY_MD
  echo "" >> $SUMMARY_MD
  
  # 等待一段时间，让系统稳定
  sleep 5
done

# 计算平均值 - 使用awk而不是bc
if [ $SCENARIO_COUNT -gt 0 ]; then
  AVG_PER_CONCURRENCY_OUTPUT_THROUGHPUT=$(awk -v tot=$TOTAL_PER_CONCURRENCY_OUTPUT_THROUGHPUT -v cnt=$SCENARIO_COUNT 'BEGIN {printf "%.2f", tot / cnt}')
  AVG_PER_CONCURRENCY_TOKEN_THROUGHPUT=$(awk -v tot=$TOTAL_PER_CONCURRENCY_TOKEN_THROUGHPUT -v cnt=$SCENARIO_COUNT 'BEGIN {printf "%.2f", tot / cnt}')
  AVG_SUCCESS_RATE=$(awk -v tot=$TOTAL_SUCCESS_RATE -v cnt=$SCENARIO_COUNT 'BEGIN {printf "%.2f", tot / cnt}')
  
  echo "" | tee -a $LOG_DIR/summary.log
  echo -e "=================================================" | tee -a $LOG_DIR/summary.log
  echo -e "所有场景的平均指标 (共$SCENARIO_COUNT个场景)" | tee -a $LOG_DIR/summary.log
  echo -e "${GREEN}平均请求成功率: ${AVG_SUCCESS_RATE}%${NC}" | tee -a $LOG_DIR/summary.log
  echo -e "${YELLOW}平均每并发输出词元吞吐量: $AVG_PER_CONCURRENCY_OUTPUT_THROUGHPUT tok/s/并发${NC}" | tee -a $LOG_DIR/summary.log
  echo -e "${RED}平均每并发总词元吞吐量: $AVG_PER_CONCURRENCY_TOKEN_THROUGHPUT tok/s/并发${NC}" | tee -a $LOG_DIR/summary.log
  echo -e "=================================================" | tee -a $LOG_DIR/summary.log
  
  # 添加到Markdown汇总
  echo "## 总体结果摘要" >> $SUMMARY_MD
  echo "" >> $SUMMARY_MD
  echo "- **测试场景数量:** $SCENARIO_COUNT 成功, $FAILED_SCENARIOS 失败" >> $SUMMARY_MD
  echo "- **平均请求成功率:** $AVG_SUCCESS_RATE%" >> $SUMMARY_MD
  echo "- **平均每并发输出词元吞吐量:** $AVG_PER_CONCURRENCY_OUTPUT_THROUGHPUT tok/s/并发" >> $SUMMARY_MD
  echo "- **平均每并发总词元吞吐量:** $AVG_PER_CONCURRENCY_TOKEN_THROUGHPUT tok/s/并发" >> $SUMMARY_MD
  echo "" >> $SUMMARY_MD
fi

# 记录测试结束时间
END_TIMESTAMP=$(date)
echo "" | tee -a $LOG_DIR/summary.log
echo -e "${BOLD}测试结束时间: $END_TIMESTAMP${NC}" | tee -a $LOG_DIR/summary.log
echo "所有测试场景已完成。摘要日志: $LOG_DIR/summary.log"

# 添加测试结束时间到Markdown
echo "## 测试结束时间: $END_TIMESTAMP" >> $SUMMARY_MD
echo "" >> $SUMMARY_MD

# 创建一个无颜色版本的摘要日志
cat $LOG_DIR/summary.log | sed 's/\x1B\[[0-9;]*[mK]//g' > $LOG_DIR/summary_plain.log
echo "同时生成了无颜色版摘要日志: $LOG_DIR/summary_plain.log"

# 如果需要发送最终汇总邮件
if [ "$SEND_EMAIL_FINAL" = true ]; then
  # 准备邮件正文
  EMAIL_BODY="$LOG_DIR/email_final.txt"
  touch $EMAIL_BODY
  
  # 从Markdown文件提取纯文本内容
  cat $SUMMARY_MD | sed 's/^#//' | sed 's/^###//' | sed 's/^##//' | sed 's/^\*//' | sed 's/^\*\*//' | sed 's/^-//' > $EMAIL_BODY
  
  # 创建描述性的附件名称
  SUMMARY_ATTACHMENT_NAME="vLLM基准测试报告_$(date +%Y%m%d_%H%M%S).md"
  cp "$SUMMARY_MD" "$LOG_DIR/$SUMMARY_ATTACHMENT_NAME"
  
  # 设置邮件信息
  EMAIL_SUBJECT="vLLM基准测试结果汇总 - $(date +%Y-%m-%d) - $([ $FAILED_SCENARIOS -gt 0 ] && echo "有$FAILED_SCENARIOS个失败" || echo "全部成功")"

  # 发送最终汇总邮件
  send_email "$EMAIL_SUBJECT" "$EMAIL_BODY" "$LOG_DIR/$SUMMARY_ATTACHMENT_NAME"
fi

# 测试完成提示
echo -e "\n${GREEN}所有测试已完成！${NC}"
echo "摘要报告: $LOG_DIR/summary.log"
echo "Markdown报告: $SUMMARY_MD"
