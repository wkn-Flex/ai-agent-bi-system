# -*- coding: utf-8 -*-
"""
洞察分析Agent（InsightAnalysisAgent）
功能：基于查询结果，进行同比/环比分析、异常检测、原因归因，生成数据洞察和业务建议
对应题目要求第4条：实现洞察归因
"""
import json
from typing import Tuple, List, Dict, Any
from base_agent import BaseAgent
from context import BIContext
from utils.llm_client import get_llm


class InsightAnalysisAgent(BaseAgent):
    agent_name = "insight_analysis"
    description = "洞察归因：同比环比分析、异常检测、原因归因，生成数据洞察和业务建议"

    def __init__(self):
        self.llm = get_llm()

    def _process(self, context: BIContext) -> Tuple[bool, str]:
        columns = context.data_query.get("columns", [])
        rows = context.data_query.get("rows", [])
        row_count = context.data_query.get("row_count", 0)

        if row_count == 0:
            context.insight_analysis["status"] = "skipped"
            context.insight_analysis["summary"] = "查询结果为空，无法进行洞察分析"
            print(f"  跳过洞察分析：查询结果为空")
            return True, ""

        # 1. 生成数据概览总结
        summary = self._generate_summary(columns, rows, context)
        context.insight_analysis["summary"] = summary

        # 2. 异常检测（Z-score方法）
        anomalies = self._detect_anomalies(columns, rows)
        context.insight_analysis["anomalies"] = anomalies

        # 3. 趋势分析（如果有时间维度）
        trend = self._analyze_trend(columns, rows)
        context.insight_analysis["trend_analysis"] = trend

        # 4. 对比分析（排名、占比、极值）
        comparison = self._analyze_comparison(columns, rows)
        context.insight_analysis["comparison"] = comparison

        # 5. 调用LLM生成关键发现和业务建议
        key_findings, recommendations = self._generate_llm_insights(columns, rows, context, summary, anomalies, comparison)
        context.insight_analysis["key_findings"] = key_findings
        context.insight_analysis["recommendations"] = recommendations

        context.insight_analysis["status"] = "success"

        print(f"  数据概览: {summary[:80]}...")
        print(f"  关键发现: {len(key_findings)}条")
        print(f"  异常检测: {len(anomalies)}个异常点")
        print(f"  业务建议: {len(recommendations)}条")

        return True, ""

    def _generate_summary(self, columns: List[str], rows: List[Dict], context: BIContext) -> str:
        """生成数据概览总结"""
        metric_cols = []
        for col in columns:
            if rows and isinstance(rows[0].get(col), (int, float)):
                metric_cols.append(col)

        parts = [f"本次查询返回{len(rows)}行数据，包含{len(columns)}个字段（{', '.join(columns)}）。"]

        for col in metric_cols:
            values = [self._to_num(r.get(col, 0)) for r in rows]
            if values:
                total = sum(values)
                avg = total / len(values)
                max_val = max(values)
                min_val = min(values)
                parts.append(f"{col}：总计{total:,.2f}，平均{avg:,.2f}，最高{max_val:,.2f}，最低{min_val:,.2f}。")

        return "".join(parts)

    def _detect_anomalies(self, columns: List[str], rows: List[Dict]) -> List[Dict]:
        """Z-score异常检测"""
        anomalies = []
        for col in columns:
            if rows and isinstance(rows[0].get(col), (int, float)):
                values = [self._to_num(r.get(col, 0)) for r in rows]
                if len(values) < 3:
                    continue
                mean = sum(values) / len(values)
                variance = sum((x - mean) ** 2 for x in values) / len(values)
                std = variance ** 0.5
                if std == 0:
                    continue
                for i, (row, val) in enumerate(zip(rows, values)):
                    z_score = abs((val - mean) / std)
                    if z_score > 2.0:  # Z-score > 2 视为异常
                        dim_val = str(row.get(columns[0], "")) if columns else f"行{i}"
                        anomalies.append({
                            "dimension": columns[0] if columns else "row",
                            "value": dim_val,
                            "metric": col,
                            "metric_value": val,
                            "z_score": round(z_score, 2),
                            "description": f"{dim_val}的{col}为{val:,.2f}，Z-score={z_score:.2f}，显著偏离均值{mean:,.2f}",
                        })
        return anomalies[:10]  # 最多返回10个异常

    def _analyze_trend(self, columns: List[str], rows: List[Dict]) -> Dict:
        """趋势分析"""
        date_keywords = ['date', 'year', 'month', '时间', '日期', '年份', '月份']
        date_col = None
        for col in columns:
            if any(kw in col.lower() for kw in date_keywords):
                date_col = col
                break

        if not date_col or len(rows) < 2:
            return {"has_trend": False, "reason": "无时间维度或数据点不足"}

        metric_col = None
        for col in columns:
            if col != date_col and rows and isinstance(rows[0].get(col), (int, float)):
                metric_col = col
                break

        if not metric_col:
            return {"has_trend": False, "reason": "无数值度量列"}

        values = [self._to_num(r.get(metric_col, 0)) for r in rows]
        first_val = values[0]
        last_val = values[-1]
        change = last_val - first_val
        change_rate = (change / first_val * 100) if first_val != 0 else 0

        # 计算趋势方向
        if len(values) >= 3:
            increasing = sum(1 for i in range(1, len(values)) if values[i] > values[i-1])
            decreasing = sum(1 for i in range(1, len(values)) if values[i] < values[i-1])
            direction = "上升" if increasing > decreasing else ("下降" if decreasing > increasing else "波动")
        else:
            direction = "上升" if change > 0 else "下降"

        return {
            "has_trend": True,
            "date_column": date_col,
            "metric_column": metric_col,
            "first_value": first_val,
            "last_value": last_val,
            "change": change,
            "change_rate": round(change_rate, 2),
            "direction": direction,
            "description": f"{metric_col}从{first_val:,.2f}变化到{last_val:,.2f}，变化{change:,.2f}（{change_rate:+.2f}%），整体趋势{direction}",
        }

    def _analyze_comparison(self, columns: List[str], rows: List[Dict]) -> Dict:
        """对比分析：排名、占比、极值"""
        if len(columns) < 2 or not rows:
            return {"has_comparison": False, "reason": "数据不足"}

        dim_col = columns[0]
        metric_col = None
        for col in columns[1:]:
            if isinstance(rows[0].get(col), (int, float)):
                metric_col = col
                break

        if not metric_col:
            return {"has_comparison": False, "reason": "无数值度量列"}

        # 按度量值排序
        sorted_rows = sorted(rows, key=lambda r: self._to_num(r.get(metric_col, 0)), reverse=True)
        values = [self._to_num(r.get(metric_col, 0)) for r in sorted_rows]
        total = sum(values)

        # Top3和Bottom3
        top3 = [{"dimension": str(r.get(dim_col, "")), "value": self._to_num(r.get(metric_col, 0)),
                 "percentage": round(self._to_num(r.get(metric_col, 0)) / total * 100, 2) if total else 0}
                for r in sorted_rows[:3]]
        bottom3 = [{"dimension": str(r.get(dim_col, "")), "value": self._to_num(r.get(metric_col, 0)),
                    "percentage": round(self._to_num(r.get(metric_col, 0)) / total * 100, 2) if total else 0}
                   for r in sorted_rows[-3:]]

        # 集中度（Top3占比）
        top3_concentration = sum(item["percentage"] for item in top3)

        return {
            "has_comparison": True,
            "dimension_column": dim_col,
            "metric_column": metric_col,
            "total": total,
            "top3": top3,
            "bottom3": bottom3,
            "top3_concentration": round(top3_concentration, 2),
            "max_value": values[0] if values else 0,
            "min_value": values[-1] if values else 0,
            "max_min_ratio": round(values[0] / values[-1], 2) if values and values[-1] != 0 else 0,
            "description": f"{dim_col}维度下，{metric_col}最高为{sorted_rows[0].get(dim_col, '')}（{values[0]:,.2f}），最低为{sorted_rows[-1].get(dim_col, '')}（{values[-1]:,.2f}），Top3集中度{top3_concentration:.1f}%",
        }

    def _generate_llm_insights(self, columns, rows, context, summary, anomalies, comparison):
        """调用LLM生成关键发现和业务建议"""
        # 准备数据摘要（限制行数，避免token过多）
        data_preview = rows[:20]
        data_str = "\n".join([
            " | ".join(str(r.get(col, "")) for col in columns)
            for r in data_preview
        ])

        system_prompt = """你是一个资深商业智能（BI）数据分析师。
基于查询结果和统计分析，生成关键发现和业务建议。

要求：
1. 关键发现要具体、有数据支撑，不要泛泛而谈
2. 业务建议要可执行、有针对性
3. 用中文输出
4. 严格按照JSON格式输出，不要输出其他内容

输出格式：
{
    "key_findings": [
        {"finding": "发现描述", "evidence": "数据支撑", "importance": "high/medium/low"}
    ],
    "recommendations": ["建议1", "建议2", "建议3"]
}"""

        anomaly_str = "\n".join([a["description"] for a in anomalies[:5]]) if anomalies else "无明显异常"
        comparison_str = comparison.get("description", "无对比分析") if comparison else "无对比分析"
        trend_str = context.insight_analysis.get("trend_analysis", {}).get("description", "无趋势分析")

        user_prompt = f"""## 分析目标
{context.requirement.get('analysis_goal', context.user_input['question'])}

## 数据概览
{summary}

## 数据预览（前20行）
{' | '.join(columns)}
{data_str}

## 异常检测
{anomaly_str}

## 对比分析
{comparison_str}

## 趋势分析
{trend_str}

请基于以上信息，生成关键发现和业务建议（JSON格式）："""

        try:
            response = self.llm.chat(system_prompt, user_prompt)
            json_str = self._extract_json(response)
            result = json.loads(json_str)
            key_findings = result.get("key_findings", [])
            recommendations = result.get("recommendations", [])
            return key_findings[:5], recommendations[:5]
        except Exception as e:
            # LLM失败时的降级处理
            key_findings = [{"finding": f"数据概览：{summary[:100]}", "evidence": "统计计算", "importance": "medium"}]
            recommendations = ["建议进一步细化分析维度，深入挖掘数据背后的业务原因"]
            return key_findings, recommendations

    def _extract_json(self, text: str) -> str:
        import re
        try:
            json.loads(text)
            return text
        except:
            pass
        match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            return match.group(1)
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            return text[start:end+1]
        return text

    def _to_num(self, val) -> float:
        try:
            return float(val) if val is not None else 0.0
        except (ValueError, TypeError):
            return 0.0

    def _get_output_summary(self, context: BIContext) -> str:
        return f"findings={len(context.insight_analysis['key_findings'])}, recommendations={len(context.insight_analysis['recommendations'])}"
