# 基于AI Agent工作流的商业智能（BI）自动化数据分析系统

## 项目简介

本系统是一个基于多Agent协作的商业智能自动化分析平台，用户通过自然语言提出分析需求，系统通过6个Agent协作自动完成数据查询、可视化、归因分析和报告生成。

## 系统架构

### 6个Agent角色（顺序Pipeline）

| 序号 | Agent名称 | 文件 | 职责 |
|------|-----------|------|------|
| 1 | 需求解析Agent | agents/requirement_agent.py | 解析用户需求，提取分析意图、目标、维度、指标 |
| 2 | SQL生成Agent | agents/sql_generation_agent.py | Text-to-SQL，将自然语言转换为SQL，支持self-correction |
| 3 | 数据查询Agent | agents/data_query_agent.py | 执行SQL查询，格式化结果 |
| 4 | 图表生成Agent | agents/chart_generation_agent.py | 自动选择图表类型，生成ECharts配置 |
| 5 | 洞察分析Agent | agents/insight_analysis_agent.py | 同比环比、异常检测、原因归因、业务建议 |
| 6 | 报告撰写Agent | agents/report_generation_agent.py | 生成结构化HTML/Markdown分析报告 |

### Agent间通信协议

所有Agent共享同一个上下文对象（BIContext），通过字段读写进行通信。上下文包含9层字段：
- 元信息层、用户输入层
- 需求解析输出、SQL生成输出、数据查询输出
- 图表生成输出、洞察分析输出、报告撰写输出
- 执行日志层

## 目录结构

```
multi_agent_system/
├── config.py                    # 配置文件（数据库+LLM API）
├── context.py                   # 通信协议：共享上下文
├── base_agent.py                # Agent基类
├── pipeline.py                  # Pipeline编排器
├── main.py                      # 主程序（交互式）
├── run_tests.py                 # 自动测试脚本
├── requirements.txt             # 依赖清单
├── README.md                    # 说明文档
├── agents/                      # 6个Agent
│   ├── __init__.py
│   ├── requirement_agent.py     # 需求解析Agent
│   ├── sql_generation_agent.py  # SQL生成Agent
│   ├── data_query_agent.py      # 数据查询Agent
│   ├── chart_generation_agent.py # 图表生成Agent
│   ├── insight_analysis_agent.py # 洞察分析Agent
│   └── report_generation_agent.py # 报告撰写Agent
└── utils/                       # 工具模块
    ├── __init__.py
    ├── llm_client.py            # LLM调用封装
    ├── schema_manager.py        # 数据库Schema管理
    └── sql_executor.py          # SQL执行器（含安全检查）
```

## 环境要求

- Python 3.8+
- MySQL 5.7+（需导入Superstore数据集）
- DeepSeek API Key（或其他兼容OpenAI格式的LLM API）

## 安装依赖

```bash
pip install openai pymysql
```

## 配置

1. 复制配置模板并修改：
   ```bash
   cp config.example.py config.py
   ```

2. 修改 `config.py` 中的数据库配置和 LLM API Key。

## 运行

### 交互式运行

```bash
python main.py
```

### 自动测试（10个测试用例）

```bash
python run_tests.py
```

## 支持的图表类型

- 柱状图（bar）：类别对比
- 折线图（line）：趋势分析
- 饼图（pie）：占比分析
- 散点图（scatter）：相关性分析
- 热力图（heatmap）：二维矩阵分析

## 评估指标

对应题目要求第6条：
1. **SQL生成准确率**：成功生成可执行SQL的比例
2. **分析任务完成率**：完整Pipeline执行成功的比例
3. **报告可读性**：人工评分（报告结构、洞察质量、建议可执行性）
4. **端到端耗时**：从用户输入到报告生成的总时间

## 数据集

使用Kaggle Sample Superstore数据集（9994行，19列），已导入MySQL的superstore_bi数据库，包含4张表：
- customers（793条客户记录）
- products（1862条产品记录）
- orders（5009条订单记录）
- order_items（9994条订单项记录）
