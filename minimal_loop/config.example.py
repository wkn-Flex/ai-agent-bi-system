# -*- coding: utf-8 -*-
"""
配置文件模板：数据库连接 + LLM API配置
使用方法：复制本文件并重命名为 config.py，然后填入你自己的配置
    cp config.example.py config.py
注意：config.py 已在 .gitignore 中忽略，不会被提交到仓库
"""
import os

# ========== 数据库配置 ==========
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',            # 改成你的MySQL用户名
    'password': 'YOUR_MYSQL_PASSWORD',   # 改成你的MySQL密码
    'database': 'superstore_bi',
    'charset': 'utf8mb4',
}

# ========== LLM API配置 ==========
# 支持三种模型，选择一种即可，修改 LLM_PROVIDER 切换
LLM_PROVIDER = 'deepseek'  # 可选: 'deepseek' / 'qwen' / 'openai'

# DeepSeek配置 注册地址: https://platform.deepseek.com/
DEEPSEEK_CONFIG = {
    'api_key': os.getenv('DEEPSEEK_API_KEY', 'YOUR_DEEPSEEK_API_KEY'),
    'base_url': 'https://api.deepseek.com',
    'model': 'deepseek-chat',
    'temperature': 0.1,  # SQL生成需要低温度，保证稳定性
    'max_tokens': 2048,
}

# 通义千问配置（阿里云）注册地址: https://bailian.console.aliyun.com/
QWEN_CONFIG = {
    'api_key': os.getenv('DASHSCOPE_API_KEY', 'YOUR_DASHSCOPE_API_KEY'),
    'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    'model': 'qwen-plus',  # 可选: qwen-turbo / qwen-plus / qwen-max
    'temperature': 0.1,
    'max_tokens': 2048,
}

# OpenAI配置（需要海外网络和API Key）
OPENAI_CONFIG = {
    'api_key': os.getenv('OPENAI_API_KEY', 'YOUR_OPENAI_API_KEY'),
    'base_url': 'https://api.openai.com/v1',
    'model': 'gpt-4o-mini',
    'temperature': 0.1,
    'max_tokens': 2048,
}

# ========== SQL生成配置 ==========
SQL_CONFIG = {
    'max_retry': 3,          # SQL执行失败后最大重试次数（self-correction）
    'only_select': True,     # 只允许SELECT查询，禁止写操作
    'result_max_rows': 100,  # 查询结果最大返回行数
}

# ========== 少样本示例配置 ==========
FEW_SHOT_EXAMPLES = [
    {
        'question': '全年总销售额是多少？',
        'sql': """SELECT SUM(oi.sales) AS total_sales
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE YEAR(o.order_date) = 2017;"""
    },
    {
        'question': '哪个地区的销售额最高？',
        'sql': """SELECT c.region, SUM(oi.sales) AS total_sales
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY c.region
ORDER BY total_sales DESC
LIMIT 1;"""
    },
    {
        'question': '找出利润为负的产品类别，按亏损总额排序',
        'sql': """SELECT p.category, SUM(oi.profit) AS total_profit
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.category
HAVING total_profit < 0
ORDER BY total_profit ASC;"""
    },
]
