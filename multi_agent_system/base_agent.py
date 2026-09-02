# -*- coding: utf-8 -*-
"""
Agent基类：定义统一的输入输出接口和执行流程
"""
from abc import ABC, abstractmethod
from typing import Tuple
import time
from context import BIContext


class BaseAgent(ABC):
    """
    Agent基类 —— 所有Agent继承此类
    统一执行流程：计时 → 核心处理 → 日志记录 → 错误处理
    """

    agent_name: str = "base"
    description: str = ""

    @abstractmethod
    def _process(self, context: BIContext) -> Tuple[bool, str]:
        """核心处理逻辑（子类实现）"""
        pass

    def run(self, context: BIContext) -> BIContext:
        """Agent执行入口（编排器调用）"""
        start_time = time.time()
        context.meta["current_agent"] = self.agent_name

        input_summary = self._get_input_summary(context)

        try:
            success, error_msg = self._process(context)
            duration = time.time() - start_time

            if success:
                output_summary = self._get_output_summary(context)
                context.log_agent_execution(
                    self.agent_name, "success", duration,
                    input_summary, output_summary
                )
            else:
                context.log_agent_execution(
                    self.agent_name, "failed", duration,
                    input_summary, "", error_msg
                )
                context.meta["pipeline_status"] = "failed"

        except Exception as e:
            duration = time.time() - start_time
            context.log_agent_execution(
                self.agent_name, "failed", duration,
                input_summary, "", str(e)
            )
            context.meta["pipeline_status"] = "failed"

        return context

    def _get_input_summary(self, context: BIContext) -> str:
        return f"question={context.user_input['question'][:50]}"

    def _get_output_summary(self, context: BIContext) -> str:
        return ""
