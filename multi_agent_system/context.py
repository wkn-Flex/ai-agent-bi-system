# -*- coding: utf-8 -*-
"""
Agent间通信协议：共享上下文（Shared Context）
所有Agent通过读写此对象的字段进行通信
"""
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional


class BIContext:
    """
    多Agent共享上下文 —— Agent间通信协议核心数据结构
    字段分层：元信息层 → 用户输入层 → 各Agent输出层 → 执行日志层
    """

    def __init__(self, user_question: str):
        # ===== 1. 元信息层 =====
        self.meta = {
            "request_id": str(uuid.uuid4())[:8],
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "total_duration": None,
            "current_agent": None,
            "pipeline_status": "running",  # running / success / failed / need_clarification
        }

        # ===== 2. 用户输入层 =====
        self.user_input = {
            "question": user_question,
            "language": "zh-CN",
        }

        # ===== 3. 需求解析Agent输出 =====
        self.requirement = {
            "intent": None,               # 销售分析/趋势分析/异常检测/对比分析/综合分析
            "analysis_goal": None,        # 分析目标描述
            "time_range": {"start": None, "end": None},
            "dimensions": [],              # 分析维度
            "metrics": [],                 # 分析指标
            "missing_info": [],            # 缺失信息
            "need_clarification": False,   # 是否需要追问
            "clarification_question": None,
            "confidence": 0.0,
        }

        # ===== 4. SQL生成Agent输出 =====
        self.sql_generation = {
            "sql": None,
            "attempts": 0,
            "max_attempts": 3,
            "generation_history": [],
            "status": "pending",           # pending / success / failed
            "error": None,
        }

        # ===== 5. 数据查询Agent输出 =====
        self.data_query = {
            "executed_sql": None,
            "columns": [],
            "rows": [],
            "row_count": 0,
            "execution_time": 0.0,
            "status": "pending",           # pending / success / empty / error
            "error": None,
        }

        # ===== 6. 图表生成Agent输出 =====
        self.chart_generation = {
            "chart_type": None,            # bar / line / pie / table / scatter / heatmap
            "chart_title": None,
            "x_axis": {"name": None, "data": []},
            "y_axis": {"name": None, "data": []},
            "echarts_config": None,
            "status": "pending",           # pending / success / skipped / error
            "skip_reason": None,
            "error": None,
        }

        # ===== 7. 洞察分析Agent输出 =====
        self.insight_analysis = {
            "summary": None,
            "key_findings": [],
            "anomalies": [],
            "trend_analysis": None,
            "comparison": {},
            "recommendations": [],
            "status": "pending",
            "error": None,
        }

        # ===== 8. 报告撰写Agent输出 =====
        self.report_generation = {
            "report_title": None,
            "report_type": "html",
            "sections": [],
            "html_content": None,
            "markdown_content": None,
            "word_count": 0,
            "status": "pending",
            "error": None,
        }

        # ===== 9. 执行日志层 =====
        self.execution_log = []

    def log_agent_execution(self, agent_name, status, duration,
                             input_summary="", output_summary="", error=None):
        """记录Agent执行日志"""
        self.execution_log.append({
            "agent": agent_name,
            "status": status,
            "duration": round(duration, 3),
            "timestamp": datetime.now().isoformat(),
            "input_summary": input_summary[:100],
            "output_summary": output_summary[:100],
            "error": error,
        })

    def to_dict(self):
        return {
            "meta": self.meta,
            "user_input": self.user_input,
            "requirement": self.requirement,
            "sql_generation": self.sql_generation,
            "data_query": self.data_query,
            "chart_generation": self.chart_generation,
            "insight_analysis": self.insight_analysis,
            "report_generation": self.report_generation,
            "execution_log": self.execution_log,
        }

    def get_final_report(self):
        return self.report_generation.get("html_content")
