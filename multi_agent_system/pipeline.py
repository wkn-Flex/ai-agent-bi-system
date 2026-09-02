# -*- coding: utf-8 -*-
"""
Pipeline编排器：按顺序执行Agent列表，管理上下文流转
"""
from datetime import datetime
from context import BIContext
from base_agent import BaseAgent


class PipelineOrchestrator:
    """
    顺序Pipeline编排器
    按照Agent添加顺序依次执行，每个Agent读写共享上下文
    """

    def __init__(self):
        self.agents: list[BaseAgent] = []

    def add_agent(self, agent: BaseAgent):
        self.agents.append(agent)
        return self

    def run(self, user_question: str) -> BIContext:
        context = BIContext(user_question)

        print("=" * 70)
        print(f"[Pipeline] 开始执行 | request_id={context.meta['request_id']}")
        print(f"[Pipeline] 用户问题: {user_question}")
        print(f"[Pipeline] Agent数量: {len(self.agents)}")
        print("=" * 70)

        for i, agent in enumerate(self.agents, 1):
            print(f"\n[{i}/{len(self.agents)}] {agent.agent_name} - {agent.description}")
            print("-" * 70)

            context = agent.run(context)

            # 检查是否需要追问用户
            if context.requirement.get("need_clarification"):
                print(f"\n[Pipeline] 需求解析Agent要求追问，暂停Pipeline")
                print(f"[Pipeline] 追问: {context.requirement['clarification_question']}")
                context.meta["pipeline_status"] = "need_clarification"
                break

            # 检查是否失败
            if context.meta["pipeline_status"] == "failed":
                print(f"\n[Pipeline] Agent {agent.agent_name} 执行失败，Pipeline终止")
                last_log = context.execution_log[-1] if context.execution_log else {}
                print(f"[Pipeline] 错误: {last_log.get('error', '未知错误')}")
                break

            print(f"[{i}/{len(self.agents)}] {agent.agent_name} 完成 ✓")

        # Pipeline结束
        context.meta["end_time"] = datetime.now().isoformat()
        if context.meta["pipeline_status"] == "running":
            context.meta["pipeline_status"] = "success"

        total_duration = (
            datetime.fromisoformat(context.meta["end_time"]) -
            datetime.fromisoformat(context.meta["start_time"])
        ).total_seconds()
        context.meta["total_duration"] = round(total_duration, 3)

        print("\n" + "=" * 70)
        print(f"[Pipeline] 执行完成 | 状态: {context.meta['pipeline_status']}")
        print(f"[Pipeline] 总耗时: {context.meta['total_duration']}秒")
        print(f"[Pipeline] 执行日志:")
        for log in context.execution_log:
            icon = "✓" if log["status"] == "success" else "✗"
            print(f"  {icon} {log['agent']}: {log['duration']}秒")
        print("=" * 70)

        return context
