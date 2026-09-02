# 最小闭环：Text-to-SQL 系统

基于 AI Agent 工作流的 BI 自动化数据分析与报告生成研究 —— 最小可运行闭环

## 功能

输入自然语言问题 → LLM 生成 SQL → 执行 SQL → 返回查询结果

支持 self-correction（SQL 执行失败时自动反馈错误信息给 LLM 重新生成）

## 项目结构

```
minimal_loop/
├── config.py           # 配置文件（数据库+LLM API）
├── llm_client.py       # LLM调用封装（支持DeepSeek/Qwen/OpenAI）
├── schema_manager.py   # 数据库Schema管理（读取表结构+格式化）
├── sql_generator.py    # SQL生成器（Prompt构建+LLM调用+self-correction）
├── sql_executor.py     # SQL执行器（安全检查+执行+结果格式化）
├── main.py             # 交互式主程序
├── test_cases.py       # 测试用例集（10个，3种难度）
├── run_test.py         # 自动测试脚本（统计准确率）
├── requirements.txt    # 依赖包清单
└── README.md           # 本文件
```

## 快速开始

### 1. 安装依赖

```
pip install -r requirements.txt
```

### 2. 配置数据库

确保 MySQL 已启动，且已执行 `superstore_bi建表脚本.sql` 创建数据库和表。

修改 `config.py` 中的数据库配置：

```
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',        # 改成你的用户名
    'password': 'root',    # 改成你的密码
    'database': 'superstore_bi',
    'charset': 'utf8mb4',
}
```

### 3. 配置 LLM API

修改 `config.py` 中的 LLM 配置，三选一：

**推荐：DeepSeek（便宜，新用户送 500 万 token）**

```
LLM_PROVIDER = 'deepseek'
DEEPSEEK_CONFIG = {
    'api_key': 'sk-你的APIKey',
    'base_url': 'https://api.deepseek.com',
    'model': 'deepseek-chat',
}
```

**通义千问（阿里云，新用户有免费额度）**

```
LLM_PROVIDER = 'qwen'
QWEN_CONFIG = {
    'api_key': 'sk-你的APIKey',
    'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    'model': 'qwen-plus',
}
```

**OpenAI（需海外网络）**

```
LLM_PROVIDER = 'openai'
OPENAI_CONFIG = {
    'api_key': 'sk-你的APIKey',
    'base_url': 'https://api.openai.com/v1',
    'model': 'gpt-4o-mini',
}
```

### 4. 运行交互式程序

```
python main.py
```

输入问题即可，例如：

* `2023年全年总销售额是多少？`
* `哪个地区的销售额最高？`
* `找出利润为负的产品类别`

输入 `schema` 查看数据库结构，输入 `exit` 退出。

### 5. 运行自动测试

```
python run_test.py
```

自动运行 10 个测试用例，输出：

* 执行成功率
* 首次成功率
* 平均重试次数
* 按难度分级统计
* 失败用例详情

## 测试用例说明

| 难度 | 数量 | 特点 |
| -- | -- | ---------------------- |
| 简单 | 3 | 单表聚合、条件过滤、排序 |
| 中等 | 4 | 多表 JOIN、分组聚合、日期函数 |
| 复杂 | 3 | 同比环比、HAVING 过滤、多指标综合分析 |

## 核心设计

### Self-Correction 机制

SQL 执行失败时，将错误信息反馈给 LLM，让其修正 SQL，最多重试 3 次。

### 安全检查

只允许 SELECT 查询，禁止 INSERT/UPDATE/DELETE/DROP 等写操作。

### Schema 增强

自动从 MySQL 读取表结构（字段名、类型、注释），格式化后注入 Prompt，帮助 LLM 生成准确的 SQL。

### 少样本示例

Prompt 中包含 3 个典型的问题 - SQL 对，帮助 LLM 理解查询风格。

## 后续扩展方向

1. 多 Agent 架构：将需求解析、SQL 生成、可视化、洞察分析、报告生成分解为独立 Agent
2. 自动化可视化：根据查询结果自动生成图表（ECharts/Plotly）
3. 洞察归因：自动计算同比环比、异常检测、维度下钻
4. 报告生成：自动生成包含文字分析 + 图表的 HTML/Markdown 报告
5. 人工确认节点：关键操作前增加人工审核