# -*- coding: utf-8 -*-
"""
数据查询Agent（DataQueryAgent）
功能：执行SQL查询（或验证SQL生成Agent的结果），格式化查询结果供下游Agent使用
对应题目要求第2条：对接示例数据库（销售/运营数据）
"""
from typing import Tuple
from base_agent import BaseAgent
from context import BIContext
from utils.sql_executor import get_sql_executor


class DataQueryAgent(BaseAgent):
    agent_name = "data_query"
    description = "执行SQL查询，格式化结果，提供给图表生成和洞察分析Agent"

    def __init__(self):
        self.executor = get_sql_executor()

    def _process(self, context: BIContext) -> Tuple[bool, str]:
        sql = context.sql_generation.get("sql")

        if not sql:
            return False, "SQL语句为空，SQL生成Agent未生成有效SQL"

        # 如果SQL生成Agent已经执行过（self-correction时执行了），直接验证结果
        if context.data_query.get("status") in ["success", "empty"] and context.data_query.get("rows"):
            print(f"  复用SQL生成Agent的查询结果（{context.data_query['row_count']}行）")
            context.data_query["status"] = "success" if context.data_query["row_count"] > 0 else "empty"
            return True, ""

        # 否则重新执行
        print(f"  执行SQL查询...")
        success, result = self.executor.execute(sql)

        if success:
            context.data_query["executed_sql"] = sql
            context.data_query["columns"] = result["columns"]
            context.data_query["rows"] = result["rows"]
            context.data_query["row_count"] = result["row_count"]
            context.data_query["status"] = "success" if result["row_count"] > 0 else "empty"

            if result["row_count"] == 0:
                print(f"  查询结果为空（0行）")
            else:
                print(f"  查询成功，返回{result['row_count']}行")
                # 打印前3行预览
                for i, row in enumerate(result["rows"][:3]):
                    print(f"    行{i+1}: {row}")

            return True, ""
        else:
            context.data_query["status"] = "error"
            context.data_query["error"] = result
            return False, f"SQL执行失败: {result}"

    def _get_input_summary(self, context: BIContext) -> str:
        return f"sql={context.sql_generation.get('sql', '')[:50]}"

    def _get_output_summary(self, context: BIContext) -> str:
        return f"rows={context.data_query['row_count']}, cols={len(context.data_query['columns'])}"
