# -*- coding: utf-8 -*-
"""
SQL生成Agent（SQLGenerationAgent）
功能：将自然语言问题转换为SQL查询语句，支持self-correction自动重试
对应题目要求第2条：实现Text-to-SQL
"""
import re
from typing import Tuple
from datetime import datetime
from base_agent import BaseAgent
from context import BIContext
from utils.llm_client import get_llm
from utils.schema_manager import get_schema_manager
from utils.sql_executor import get_sql_executor
from config import SYSTEM_CONFIG


class SQLGenerationAgent(BaseAgent):
    agent_name = "sql_generation"
    description = "Text-to-SQL：将自然语言问题转换为SQL查询，支持自动修正"

    def __init__(self):
        self.llm = get_llm()
        self.schema_mgr = get_schema_manager()
        self.executor = get_sql_executor()
        self.schema_text = self.schema_mgr.get_full_schema_text()

    def _process(self, context: BIContext) -> Tuple[bool, str]:
        # 优先使用需求解析的分析目标，否则用原始问题
        analysis_goal = context.requirement.get("analysis_goal") or context.user_input["question"]
        max_attempts = SYSTEM_CONFIG['sql_max_retry']

        for attempt in range(1, max_attempts + 1):
            context.sql_generation["attempts"] = attempt

            # 构建Prompt
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(context, analysis_goal, attempt)

            # 调用LLM
            raw_response = self.llm.chat(system_prompt, user_prompt)
            sql = self._extract_sql(raw_response)

            context.sql_generation["sql"] = sql
            context.sql_generation["generation_history"].append({
                "attempt": attempt,
                "sql": sql,
                "timestamp": datetime.now().isoformat(),
            })

            # 执行SQL验证（self-correction）
            success, result = self.executor.execute(sql)

            if success:
                context.sql_generation["status"] = "success"
                context.sql_generation["error"] = None
                # 把查询结果暂存到上下文，供数据查询Agent使用
                context.data_query["executed_sql"] = sql
                context.data_query["columns"] = result["columns"]
                context.data_query["rows"] = result["rows"]
                context.data_query["row_count"] = result["row_count"]
                context.data_query["status"] = "success" if result["row_count"] > 0 else "empty"
                return True, ""
            else:
                context.sql_generation["error"] = result
                if attempt < max_attempts:
                    continue  # 重试

        context.sql_generation["status"] = "failed"
        return False, f"SQL生成失败（{max_attempts}次尝试后仍失败）: {context.sql_generation.get('error')}"

    def _build_system_prompt(self) -> str:
        return """你是一个专业的商业智能SQL工程师，擅长将业务分析问题转换为准确的MySQL查询语句。

数据库包含4张表：
- customers（客户表）：customer_id, segment, city, state, region, country
- products（产品表）：product_id, product_name, category, sub_category
- orders（订单表）：order_id, order_date, ship_date, ship_mode, customer_id
- order_items（订单项表）：id, order_id, product_id, sales, quantity, discount, profit

表关系：
- customers.customer_id → orders.customer_id (1:N)
- orders.order_id → order_items.order_id (1:N)
- products.product_id → order_items.product_id (1:N)

【重要规则】
1. 只输出SQL语句本身，不要任何解释、注释或Markdown代码块
2. 只允许SELECT查询
3. 多表查询必须使用JOIN，不要用逗号隐式连接
4. 日期字段用order_date，使用YEAR()、MONTH()等函数
5. 销售额用sales，利润用profit，数量用quantity，折扣用discount
6. 数据日期范围是2014-2017年

【聚合查询规则 - 非常重要】
7. 对于"哪个地区/类别最高/最低"、"各维度对比"、"排名"、"趋势"、"占比"等分析类问题，必须使用GROUP BY聚合查询，返回聚合后的汇总数据，不要返回明细数据
8. 聚合函数：总销售额用SUM(sales)，总利润用SUM(profit)，订单数用COUNT(DISTINCT order_id)，平均销售额用AVG(sales)
9. 聚合列必须使用AS别名，如 SUM(sales) AS total_sales, SUM(profit) AS total_profit
10. 按维度GROUP BY，按度量ORDER BY DESC，通常LIMIT 20以内
11. 只有用户明确要求"查看明细"、"列出订单"时才返回原始明细数据

【示例】
- 问"2017年哪个地区销售额最高" → SELECT c.region, SUM(oi.sales) AS total_sales FROM order_items oi JOIN orders o ON oi.order_id=o.order_id JOIN customers c ON o.customer_id=c.customer_id WHERE YEAR(o.order_date)=2017 GROUP BY c.region ORDER BY total_sales DESC
- 问"各产品类别的利润" → SELECT p.category, SUM(oi.profit) AS total_profit FROM order_items oi JOIN products p ON oi.product_id=p.product_id GROUP BY p.category ORDER BY total_profit DESC
- 问"2017年各月销售额趋势" → SELECT MONTH(o.order_date) AS month, SUM(oi.sales) AS total_sales FROM order_items oi JOIN orders o ON oi.order_id=o.order_id WHERE YEAR(o.order_date)=2017 GROUP BY MONTH(o.order_date) ORDER BY month"""

    def _build_user_prompt(self, context: BIContext, analysis_goal: str, attempt: int) -> str:
        parts = [
            f"## 数据库Schema\n{self.schema_text}",
            f"\n## 分析目标\n{analysis_goal}",
        ]

        # 附加维度和指标信息
        if context.requirement.get("dimensions"):
            parts.append(f"\n## 分析维度\n{', '.join(context.requirement['dimensions'])}")
        if context.requirement.get("metrics"):
            parts.append(f"\n## 分析指标\n{', '.join(context.requirement['metrics'])}")

        # 如果是重试，附加上一次错误
        if attempt > 1 and context.sql_generation.get("error"):
            parts.append(f"\n## 上一次SQL执行错误\n{context.sql_generation['error']}\n请根据错误信息修正SQL。")

        parts.append("\n请生成SQL查询语句:")
        return "\n".join(parts)

    def _extract_sql(self, text: str) -> str:
        text = re.sub(r'```sql\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'```\s*', '', text)
        text = re.sub(r'`', '', text)
        if ';' in text:
            text = text[:text.index(';')]
        return text.strip()

    def _get_output_summary(self, context: BIContext) -> str:
        return f"sql={context.sql_generation['sql'][:50]}, attempts={context.sql_generation['attempts']}"
