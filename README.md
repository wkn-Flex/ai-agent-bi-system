# 基于 AI Agent 工作流的 BI 自动化数据分析与报告生成系统

本科毕业设计。用户用**自然语言**提出业务分析问题，系统通过六个 AI Agent 顺序协作，自动完成「需求解析 → SQL 生成 → 数据查询 → 图表生成 → 洞察归因 → 报告撰写」的端到端流程，最终产出含可交互图表的 HTML / Markdown 分析报告。

## 目录结构

```
.
├── multi_agent_system/          # 完整多 Agent 系统（核心）
│   ├── agents/                  # 六个 Agent
│   │   ├── requirement_agent.py       # 需求解析
│   │   ├── sql_generation_agent.py    # Text-to-SQL（含自我修正）
│   │   ├── data_query_agent.py        # 数据查询
│   │   ├── chart_generation_agent.py  # 自动选图 + ECharts 配置
│   │   ├── insight_analysis_agent.py  # 异常检测/趋势/对比/归因
│   │   └── report_generation_agent.py # HTML/Markdown 报告
│   ├── utils/                   # LLM 客户端、模式管理、SQL 执行器
│   ├── context.py               # Agent 间共享上下文（通信协议）
│   ├── base_agent.py            # Agent 抽象基类
│   ├── pipeline.py              # 顺序流水线编排器
│   ├── main.py                  # 交互式主程序
│   ├── run_tests.py             # 10 用例自动化测试
│   └── config.example.py        # 配置模板（复制为 config.py 使用）
├── minimal_loop/                # 最小闭环验证版（Text-to-SQL 原型）
├── superstore_bi建表脚本.sql     # MySQL 建库建表脚本（4 张表）
└── import_superstore_to_mysql.py # Kaggle Superstore 数据集清洗导入脚本
```

## 技术栈

| 层次 | 技术 |
|---|---|
| 语言 | Python 3 |
| 大语言模型 | DeepSeek-Chat（OpenAI 兼容接口，可切换通义千问/OpenAI） |
| 数据库 | MySQL 5.7（PyMySQL 驱动） |
| 可视化 | Apache ECharts 5 |
| 协作模式 | 自研轻量级顺序 Pipeline（未使用 AutoGen/LangChain） |

## 快速开始

### 1. 准备数据库

在 MySQL 中执行建表脚本，得到 `customers / products / orders / order_items` 四张表：

```bash
mysql -u root -p < superstore_bi建表脚本.sql
```

从 Kaggle 下载 [Sample Superstore](https://www.kaggle.com/datasets) 数据集后，修改导入脚本中的 CSV 路径并运行：

```bash
python import_superstore_to_mysql.py
```

### 2. 安装依赖并配置密钥

```bash
cd multi_agent_system
pip install openai pymysql
cp config.example.py config.py   # Windows: copy config.example.py config.py
```

编辑 `config.py`，填入你的 MySQL 密码和 DeepSeek API Key（也可用环境变量 `DEEPSEEK_API_KEY`）。

### 3. 运行

```bash
# 交互式分析
python main.py

# 批量测试（10 个用例 + 评估指标）
python run_tests.py
```

生成的报告位于 `output/` 目录，用浏览器打开 HTML 即可查看可交互图表。

## 六个 Agent 的职责

1. **需求解析 Agent**：自然语言 → 意图/维度/指标/时间范围（结构化 JSON）
2. **SQL 生成 Agent**：Text-to-SQL，执行失败时根据报错自我修正（最多 3 次）
3. **数据查询 Agent**：执行 SQL，标准化结果集
4. **图表生成 Agent**：自动识别维度/度量列，智能选择柱状/折线/饼图/散点/热力图
5. **洞察分析 Agent**：Z-score 异常检测 + 趋势/对比分析 + LLM 原因归因与建议
6. **报告撰写 Agent**：整合全流程，输出七章节 HTML / Markdown 报告

## 安全说明

- SQL 执行器内置写操作关键字黑名单，仅允许 `SELECT / WITH` 查询，防止模型生成破坏性语句。
- `config.py` 含个人 API Key 与数据库密码，已通过 `.gitignore` 排除，仓库中只提供 `config.example.py` 模板。

## 数据集

Kaggle Sample Superstore，9994 条交易记录、时间跨度 2014–2017，规范化为四张关系表（客户 793 / 产品 1862 / 订单 5009 / 订单项 9994）。
