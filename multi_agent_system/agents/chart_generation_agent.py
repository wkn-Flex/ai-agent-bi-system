# -*- coding: utf-8 -*-
"""
图表生成Agent（ChartGenerationAgent）
功能：根据查询结果特征和分析目标，自动选择图表类型并生成ECharts配置
支持：折线图、柱状图、饼图、散点图、热力图、表格
对应题目要求第3条：实现自动化可视化
"""
import json
from typing import Tuple, List, Dict, Any, Optional
from base_agent import BaseAgent
from context import BIContext


class ChartGenerationAgent(BaseAgent):
    agent_name = "chart_generation"
    description = "自动化可视化：智能识别维度度量，自动选择图表类型，生成ECharts配置"

    def _process(self, context: BIContext) -> Tuple[bool, str]:
        columns = context.data_query.get("columns", [])
        rows = context.data_query.get("rows", [])
        row_count = context.data_query.get("row_count", 0)

        # 空结果跳过
        if row_count == 0 or not rows:
            context.chart_generation["status"] = "skipped"
            context.chart_generation["skip_reason"] = "查询结果为空，无法生成图表"
            print(f"  跳过图表生成：查询结果为空")
            return True, ""

        # 单值结果跳过（用指标卡片展示）
        if row_count == 1 and len(columns) == 1:
            context.chart_generation["status"] = "skipped"
            context.chart_generation["skip_reason"] = "单值结果，使用指标卡片展示"
            print(f"  跳过图表生成：单值结果")
            return True, ""

        # 智能识别维度列和度量列
        dim_cols, metric_cols = self._identify_columns(columns, rows)
        print(f"  识别维度列: {dim_cols}")
        print(f"  识别度量列: {metric_cols}")

        # 如果没有度量列，跳过
        if not metric_cols:
            context.chart_generation["status"] = "skipped"
            context.chart_generation["skip_reason"] = "未识别到数值度量列，无法生成图表"
            print(f"  跳过图表生成：无数值度量列")
            return True, ""

        # 如果是明细数据（行数多且有维度列），自动聚合
        processed_rows = rows
        if len(rows) > 20 and dim_cols and metric_cols:
            processed_rows = self._aggregate_data(rows, dim_cols[0], metric_cols[0])
            print(f"  明细数据自动聚合：{len(rows)}行 → {len(processed_rows)}行")

        # 自动选择图表类型
        chart_type = self._select_chart_type(dim_cols, metric_cols, processed_rows, context)
        context.chart_generation["chart_type"] = chart_type

        # 生成图表标题
        chart_title = self._generate_chart_title(context, dim_cols, metric_cols)
        context.chart_generation["chart_title"] = chart_title

        # 生成ECharts配置
        echarts_config = self._generate_echarts_config(
            chart_type, dim_cols, metric_cols, processed_rows, chart_title
        )
        context.chart_generation["echarts_config"] = echarts_config

        # 提取x轴和y轴数据（供报告生成使用）
        self._extract_axis_data(chart_type, dim_cols, metric_cols, processed_rows, context)

        context.chart_generation["status"] = "success"
        print(f"  图表类型: {chart_type}")
        print(f"  图表标题: {chart_title}")
        print(f"  ECharts配置已生成")

        return True, ""

    def _identify_columns(self, columns: List[str], rows: List[Dict]) -> Tuple[List[str], List[str]]:
        """智能识别维度列（字符串/日期）和度量列（数值）"""
        dim_cols = []
        metric_cols = []
        date_keywords = ['date', 'year', 'month', 'time', '时间', '日期', '年份', '月份']

        for col in columns:
            # 检查列名是否包含日期关键词
            is_date_col = any(kw in col.lower() for kw in date_keywords)

            # 采样前10行判断数据类型
            sample_vals = [r.get(col) for r in rows[:10] if r.get(col) is not None]
            if not sample_vals:
                dim_cols.append(col)
                continue

            # 判断是否为数值类型
            numeric_count = 0
            for v in sample_vals:
                try:
                    float(v)
                    numeric_count += 1
                except (ValueError, TypeError):
                    pass

            is_numeric = numeric_count / len(sample_vals) > 0.8

            if is_numeric and not is_date_col:
                metric_cols.append(col)
            else:
                dim_cols.append(col)

        return dim_cols, metric_cols

    def _aggregate_data(self, rows: List[Dict], dim_col: str, metric_col: str) -> List[Dict]:
        """对明细数据按维度聚合（求和）"""
        agg = {}
        for row in rows:
            key = str(row.get(dim_col, "未知"))
            val = self._to_number(row.get(metric_col, 0))
            agg[key] = agg.get(key, 0) + val

        # 按值降序排列
        result = [
            {dim_col: k, metric_col: round(v, 2)}
            for k, v in sorted(agg.items(), key=lambda x: x[1], reverse=True)
        ]
        return result

    def _select_chart_type(self, dim_cols: List[str], metric_cols: List[str],
                            rows: List[Dict], context: BIContext) -> str:
        """根据数据特征自动选择图表类型"""
        intent = context.requirement.get("intent", "")
        row_count = len(rows)

        # 趋势分析意图 → 折线图
        if "趋势" in intent or "trend" in intent.lower():
            return "line"

        # 有日期维度 → 折线图
        date_keywords = ['date', 'year', 'month', 'time', '时间', '日期', '年份', '月份']
        for col in dim_cols:
            if any(kw in col.lower() for kw in date_keywords):
                return "line"

        # 1个维度+1个度量，类别数<=10 → 饼图
        if len(dim_cols) >= 1 and len(metric_cols) >= 1 and row_count <= 10:
            unique_vals = len(set(str(r.get(dim_cols[0], "")) for r in rows))
            if unique_vals <= 10 and unique_vals >= 2:
                return "pie"

        # 2个维度+1个度量 → 热力图
        if len(dim_cols) >= 2 and len(metric_cols) >= 1 and row_count >= 6:
            return "heatmap"

        # 2个数值度量，无维度 → 散点图
        if len(metric_cols) >= 2 and not dim_cols:
            return "scatter"

        # 默认柱状图（最通用）
        return "bar"

    def _generate_chart_title(self, context: BIContext, dim_cols: List[str], metric_cols: List[str]) -> str:
        """生成图表标题"""
        intent = context.requirement.get("intent", "")
        dim_str = "、".join(dim_cols[:2]) if dim_cols else "各维度"
        metric_str = "、".join(metric_cols[:2]) if metric_cols else "关键指标"

        # 中文字段名映射
        col_name_map = {
            'region': '地区', 'category': '产品类别', 'sub_category': '产品子类别',
            'segment': '客户细分', 'sales': '销售额', 'profit': '利润',
            'quantity': '数量', 'discount': '折扣', 'order_date': '订单日期',
            'ship_mode': '配送方式', 'city': '城市', 'state': '州',
            'customer_id': '客户ID', 'product_id': '产品ID', 'order_id': '订单ID',
            'total_sales': '总销售额', 'total_profit': '总利润', 'avg_sales': '平均销售额',
            'order_count': '订单数量', 'customer_count': '客户数量',
        }
        for en, zh in col_name_map.items():
            dim_str = dim_str.replace(en, zh)
            metric_str = metric_str.replace(en, zh)

        title_map = {
            "销售分析": f"{dim_str}{metric_str}分析",
            "趋势分析": f"{metric_str}趋势分析",
            "异常检测": f"{metric_str}异常检测",
            "对比分析": f"{dim_str}{metric_str}对比",
            "综合分析": f"{dim_str}{metric_str}综合分析",
            "客户分析": f"客户{metric_str}分析",
            "产品分析": f"产品{metric_str}分析",
        }
        return title_map.get(intent, f"{dim_str}{metric_str}分析")

    def _generate_echarts_config(self, chart_type: str, dim_cols: List[str],
                                   metric_cols: List[str], rows: List[Dict],
                                   title: str) -> Dict[str, Any]:
        """生成ECharts配置"""
        if chart_type in ["bar", "line"]:
            x_col = dim_cols[0] if dim_cols else "index"
            y_col = metric_cols[0]
            x_data = [str(r.get(x_col, "")) for r in rows]
            y_data = [self._to_number(r.get(y_col, 0)) for r in rows]

            return {
                "title": {"text": title, "left": "center", "textStyle": {"fontSize": 16}},
                "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow" if chart_type == "bar" else "line"}},
                "grid": {"left": "3%", "right": "4%", "bottom": "12%", "containLabel": True},
                "xAxis": {
                    "type": "category",
                    "data": x_data,
                    "axisLabel": {"rotate": 30 if len(x_data) > 5 else 0, "fontSize": 11},
                },
                "yAxis": {"type": "value", "name": y_col, "nameTextStyle": {"fontSize": 11}},
                "series": [{
                    "name": y_col,
                    "type": chart_type,
                    "data": y_data,
                    "barWidth": "50%" if chart_type == "bar" else None,
                    "smooth": True if chart_type == "line" else None,
                    "itemStyle": {"color": "#5470c6"} if chart_type == "bar" else {"color": "#5470c6"},
                    "areaStyle": {"opacity": 0.1} if chart_type == "line" else None,
                }],
            }

        elif chart_type == "pie":
            name_col = dim_cols[0]
            value_col = metric_cols[0]
            pie_data = [
                {"name": str(r.get(name_col, "")), "value": self._to_number(r.get(value_col, 0))}
                for r in rows
            ]
            return {
                "title": {"text": title, "left": "center", "textStyle": {"fontSize": 16}},
                "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
                "legend": {"orient": "vertical", "left": "left", "top": "middle", "textStyle": {"fontSize": 11}},
                "series": [{
                    "type": "pie",
                    "radius": ["40%", "65%"],
                    "center": ["60%", "55%"],
                    "data": pie_data,
                    "emphasis": {"itemStyle": {"shadowBlur": 10, "shadowOffsetX": 0, "shadowColor": "rgba(0, 0, 0, 0.5)"}},
                    "label": {"fontSize": 11},
                }],
            }

        elif chart_type == "scatter":
            x_col = metric_cols[0]
            y_col = metric_cols[1]
            scatter_data = [
                [self._to_number(r.get(x_col, 0)), self._to_number(r.get(y_col, 0))]
                for r in rows
            ]
            return {
                "title": {"text": title, "left": "center", "textStyle": {"fontSize": 16}},
                "tooltip": {"trigger": "item", "formatter": f"{x_col}: {{c[0]}}<br/>{y_col}: {{c[1]}}"},
                "grid": {"left": "3%", "right": "4%", "bottom": "10%", "containLabel": True},
                "xAxis": {"name": x_col, "type": "value", "nameTextStyle": {"fontSize": 11}},
                "yAxis": {"name": y_col, "type": "value", "nameTextStyle": {"fontSize": 11}},
                "series": [{"type": "scatter", "data": scatter_data, "symbolSize": 10, "itemStyle": {"color": "#5470c6"}}],
            }

        elif chart_type == "heatmap":
            x_col = dim_cols[0]
            y_col = dim_cols[1]
            value_col = metric_cols[0]
            x_cats = list(dict.fromkeys(str(r.get(x_col, "")) for r in rows))
            y_cats = list(dict.fromkeys(str(r.get(y_col, "")) for r in rows))
            heat_data = [
                [x_cats.index(str(r.get(x_col, ""))), y_cats.index(str(r.get(y_col, ""))),
                 self._to_number(r.get(value_col, 0))]
                for r in rows
            ]
            max_val = max([d[2] for d in heat_data]) if heat_data else 1
            return {
                "title": {"text": title, "left": "center", "textStyle": {"fontSize": 16}},
                "tooltip": {"position": "top"},
                "grid": {"left": "3%", "right": "4%", "bottom": "15%", "containLabel": True},
                "xAxis": {"type": "category", "data": x_cats, "splitArea": {"show": True}, "axisLabel": {"fontSize": 11}},
                "yAxis": {"type": "category", "data": y_cats, "splitArea": {"show": True}, "axisLabel": {"fontSize": 11}},
                "visualMap": {"min": 0, "max": max_val, "calculable": True, "orient": "horizontal", "left": "center", "bottom": "2%"},
                "series": [{"type": "heatmap", "data": heat_data, "label": {"show": True, "fontSize": 10}}],
            }

        # 兜底
        return {"title": {"text": title}, "series": [{"type": "bar", "data": []}]}

    def _extract_axis_data(self, chart_type: str, dim_cols: List[str], metric_cols: List[str],
                            rows: List[Dict], context: BIContext):
        """提取x轴和y轴数据供报告生成使用"""
        if chart_type in ["bar", "line"] and dim_cols and metric_cols:
            x_col = dim_cols[0]
            y_col = metric_cols[0]
            context.chart_generation["x_axis"] = {
                "name": x_col,
                "data": [str(r.get(x_col, "")) for r in rows]
            }
            context.chart_generation["y_axis"] = {
                "name": y_col,
                "data": [self._to_number(r.get(y_col, 0)) for r in rows]
            }

    def _to_number(self, val) -> float:
        """安全转换为数字"""
        try:
            return float(val) if val is not None else 0.0
        except (ValueError, TypeError):
            return 0.0

    def _get_output_summary(self, context: BIContext) -> str:
        return f"type={context.chart_generation['chart_type']}, status={context.chart_generation['status']}"
