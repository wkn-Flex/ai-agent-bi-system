# -*- coding: utf-8 -*-
"""
配置文件模板：数据库 + LLM API + 系统参数
使用方法：复制本文件并重命名为 config.py，然后填入你自己的数据库密码和 API Key
    cp config.example.py config.py
注意：config.py 已在 .gitignore 中忽略，不会被提交到仓库
"""
import os

# ========== 数据库配置 ==========
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'YOUR_MYSQL_PASSWORD',          # 改成你的 MySQL 密码
    'database': 'superstore_bi',
    'charset': 'utf8mb4',
}

# ========== LLM API配置 ==========
LLM_PROVIDER = 'deepseek'  # deepseek / qwen / openai

DEEPSEEK_CONFIG = {
    # 推荐通过环境变量 DEEPSEEK_API_KEY 读取，也可直接填写字符串
    'api_key': os.getenv('DEEPSEEK_API_KEY', 'YOUR_DEEPSEEK_API_KEY'),
    'base_url': 'https://api.deepseek.com',
    'model': 'deepseek-chat',
    'temperature': 0.1,
    'max_tokens': 2048,
}

QWEN_CONFIG = {
    'api_key': os.getenv('DASHSCOPE_API_KEY', 'YOUR_DASHSCOPE_API_KEY'),
    'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    'model': 'qwen-plus',
    'temperature': 0.1,
    'max_tokens': 2048,
}

OPENAI_CONFIG = {
    'api_key': os.getenv('OPENAI_API_KEY', 'YOUR_OPENAI_API_KEY'),
    'base_url': 'https://api.openai.com/v1',
    'model': 'gpt-4o-mini',
    'temperature': 0.1,
    'max_tokens': 2048,
}

# ========== 系统参数 ==========
SYSTEM_CONFIG = {
    'sql_max_retry': 3,           # SQL生成最大重试次数
    'only_select': True,          # 只允许SELECT查询
    'result_max_rows': 100,       # 查询结果最大返回行数
    'insight_max_findings': 5,    # 洞察分析最大发现数
    'report_type': 'html',        # 报告类型：html / markdown
    'log_level': 'info',          # 日志级别
}
