# -*- coding: utf-8 -*-
"""
需求解析Agent（RequirementAgent）
功能：解析用户自然语言问题，提取分析意图、目标、时间范围、维度、指标
对应题目要求第1条：定义各Agent角色（需求解析）
"""
import json
import re
from typing import Tuple
from base_agent import BaseAgent
from context import BIContext
from utils.llm_client import get_llm


class RequirementAgent(BaseAgent):
    agent_name = "requirement"
    description = "解析用户需求，提取分析意图、目标、维度和指标"

    def __init__(self):
        self.llm = get_llm()

    def _process(self, context: BIContext) -> Tuple[bool, str]:
        question = context.user_input["question"]

        system_prompt = """你是一个商业智能（BI）需求分析专家。
你的任务是解析用户的自然语言分析需求，提取结构化的分析参数。

请严格按照以下JSON格式输出（不要输出其他内容）：
{
    "intent": "意图分类（销售分析/趋势分析/异常检测/对比分析/综合分析/客户分析/产品分析）",
    "analysis_goal": "用一句话描述分析目标",
    "time_range": {"start": "开始日期(YYYY-MM-DD)或null", "end": "结束日期(YYYY-MM-DD)或null"},
    "dimensions": ["分析维度列表，如region/category/segment/product"],
    "metrics": ["分析指标列表，如sales/profit/quantity/discount"],
    "missing_info": ["缺失的关键信息列表，如没有则为空数组"],
    "need_clarification": false,
    "clarification_question": "需要追问用户的问题，如不需要则为null",
    "confidence": 0.0
}

注意：
1. 数据日期范围是2014-2017年，如果用户提到其他年份，在missing_info中说明
2. "销售额"对应sales，"利润"对应profit，"数量"对应quantity，"折扣"对应discount
3. "地区"对应region，"产品类别"对应category，"客户细分"对应segment
4. 如果问题信息足够，need_clarification设为false
5. confidence是你对解析结果的置信度，0-1之间"""

        user_prompt = f"用户问题：{question}\n\n请解析该需求并输出JSON："

        try:
            response = self.llm.chat(system_prompt, user_prompt)
            # 提取JSON
            json_str = self._extract_json(response)
            result = json.loads(json_str)

            # 写入上下文
            context.requirement["intent"] = result.get("intent", "综合分析")
            context.requirement["analysis_goal"] = result.get("analysis_goal", question)
            context.requirement["time_range"] = result.get("time_range", {"start": None, "end": None})
            context.requirement["dimensions"] = result.get("dimensions", [])
            context.requirement["metrics"] = result.get("metrics", [])
            context.requirement["missing_info"] = result.get("missing_info", [])
            context.requirement["need_clarification"] = result.get("need_clarification", False)
            context.requirement["clarification_question"] = result.get("clarification_question")
            context.requirement["confidence"] = result.get("confidence", 0.8)

            return True, ""

        except json.JSONDecodeError as e:
            return False, f"JSON解析失败: {e}"
        except Exception as e:
            return False, f"需求解析失败: {e}"

    def _extract_json(self, text: str) -> str:
        """从LLM回复中提取JSON字符串"""
        # 尝试直接解析
        try:
            json.loads(text)
            return text
        except:
            pass
        # 提取 ```json ... ``` 块
        match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            return match.group(1)
        # 提取第一个 { 到最后一个 }
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            return text[start:end+1]
        return text

    def _get_output_summary(self, context: BIContext) -> str:
        return f"intent={context.requirement['intent']}, goal={context.requirement['analysis_goal'][:40]}"
