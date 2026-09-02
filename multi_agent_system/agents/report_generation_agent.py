# -*- coding: utf-8 -*-
"""
报告撰写Agent（ReportGenerationAgent）
功能：整合分析过程、图表、洞察，生成结构化的Markdown/HTML分析报告
对应题目要求第5条：实现报告自动生成
"""
import json
from typing import Tuple, List, Dict
from datetime import datetime
from base_agent import BaseAgent
from context import BIContext


class ReportGenerationAgent(BaseAgent):
    agent_name = "report_generation"
    description = "报告自动生成：整合分析过程、图表、洞察，生成结构化HTML/Markdown报告"

    def _process(self, context: BIContext) -> Tuple[bool, str]:
        report_title = self._generate_title(context)
        context.report_generation["report_title"] = report_title

        sections = self._generate_sections(context)
        context.report_generation["sections"] = sections

        markdown_content = self._generate_markdown(report_title, sections, context)
        context.report_generation["markdown_content"] = markdown_content

        html_content = self._generate_html(report_title, sections, context)
        context.report_generation["html_content"] = html_content

        word_count = len(markdown_content)
        context.report_generation["word_count"] = word_count

        context.report_generation["status"] = "success"

        print(f"  报告标题: {report_title}")
        print(f"  报告章节: {len(sections)}个")
        print(f"  报告字数: {word_count}字")
        print(f"  HTML报告已生成（含ECharts图表渲染）")

        return True, ""

    def _generate_title(self, context: BIContext) -> str:
        intent = context.requirement.get("intent", "数据分析")
        goal = context.requirement.get("analysis_goal", context.user_input["question"])
        return f"{intent}报告：{goal[:40]}"

    def _generate_sections(self, context: BIContext) -> List[Dict]:
        sections = []
        sections.append({"title": "一、报告概述", "content": self._build_overview_section(context)})
        sections.append({"title": "二、分析目标与方法", "content": self._build_method_section(context)})
        sections.append({"title": "三、数据查询结果", "content": self._build_data_section(context)})
        if context.chart_generation.get("status") == "success":
            sections.append({"title": "四、可视化分析", "content": self._build_chart_section(context)})
        sections.append({"title": "五、数据洞察与归因", "content": self._build_insight_section(context)})
        sections.append({"title": "六、业务建议", "content": self._build_recommendation_section(context)})
        sections.append({"title": "附录：系统执行信息", "content": self._build_appendix_section(context)})
        return sections

    def _build_overview_section(self, context: BIContext) -> str:
        question = context.user_input["question"]
        intent = context.requirement.get("intent", "")
        goal = context.requirement.get("analysis_goal", "")
        summary = context.insight_analysis.get("summary", "数据查询成功")
        return f"""本报告基于AI Agent工作流的商业智能自动化分析系统生成。

**用户原始问题**：{question}

**分析意图**：{intent}

**分析目标**：{goal}

**数据概览**：{summary}

本报告通过多Agent协作（需求解析→SQL生成→数据查询→图表生成→洞察分析→报告撰写），实现从自然语言到数据洞察的端到端自动化分析。"""

    def _build_method_section(self, context: BIContext) -> str:
        dimensions = context.requirement.get("dimensions", [])
        metrics = context.requirement.get("metrics", [])
        time_range = context.requirement.get("time_range", {})
        sql = context.sql_generation.get("sql", "")
        attempts = context.sql_generation.get("attempts", 0)

        dim_str = "、".join(dimensions) if dimensions else "未明确指定"
        metric_str = "、".join(metrics) if metrics else "未明确指定"
        time_str = f"{time_range.get('start', '未限定')} 至 {time_range.get('end', '未限定')}"

        return f"""**分析维度**：{dim_str}

**分析指标**：{metric_str}

**时间范围**：{time_str}

**分析方法**：
1. 需求解析Agent提取分析参数
2. SQL生成Agent将自然语言转换为SQL查询（Text-to-SQL），支持自动修正（共尝试{attempts}次）
3. 数据查询Agent执行SQL并返回结构化结果
4. 图表生成Agent根据数据特征自动选择可视化方式
5. 洞察分析Agent进行同比环比、异常检测、原因归因
6. 报告撰写Agent整合所有分析结果生成结构化报告

**执行的SQL语句**：
```sql
{sql}
```"""

    def _build_data_section(self, context: BIContext) -> str:
        columns = context.data_query.get("columns", [])
        rows = context.data_query.get("rows", [])
        row_count = context.data_query.get("row_count", 0)

        if row_count == 0:
            return "查询结果为空，无数据可展示。"

        display_rows = rows[:15]
        table_lines = []
        table_lines.append("| " + " | ".join(columns) + " |")
        table_lines.append("|" + "|".join(["---"] * len(columns)) + "|")
        for row in display_rows:
            table_lines.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")

        table_str = "\n".join(table_lines)
        more_note = f"\n\n*注：仅显示前15行，共{row_count}行数据。*" if row_count > 15 else ""
        return f"本次查询共返回 **{row_count}** 行数据，包含 **{len(columns)}** 个字段。\n\n{table_str}{more_note}"

    def _build_chart_section(self, context: BIContext) -> str:
        chart_type = context.chart_generation.get("chart_type", "")
        chart_title = context.chart_generation.get("chart_title", "")

        type_map = {
            "bar": "柱状图", "line": "折线图", "pie": "饼图",
            "scatter": "散点图", "heatmap": "热力图", "table": "数据表格",
        }
        type_name = type_map.get(chart_type, chart_type)

        content = f"**图表类型**：{type_name}\n\n**图表标题**：{chart_title}\n\n"

        if chart_type in ["bar", "line"]:
            x_data = context.chart_generation.get("x_axis", {}).get("data", [])
            y_data = context.chart_generation.get("y_axis", {}).get("data", [])
            x_name = context.chart_generation.get("x_axis", {}).get("name", "")
            y_name = context.chart_generation.get("y_axis", {}).get("name", "")
            if x_data and y_data:
                content += "**图表数据**：\n\n"
                content += f"| {x_name} | {y_name} |\n|---|---|\n"
                for x, y in zip(x_data, y_data):
                    content += f"| {x} | {y:,.2f} |\n"

        content += "\n*下方为交互式ECharts图表，可悬停查看详细数据。*"
        return content

    def _build_insight_section(self, context: BIContext) -> str:
        key_findings = context.insight_analysis.get("key_findings", [])
        anomalies = context.insight_analysis.get("anomalies", [])
        trend = context.insight_analysis.get("trend_analysis", {})
        comparison = context.insight_analysis.get("comparison", {})

        content = ""

        if key_findings:
            content += "**关键发现**：\n\n"
            for i, finding in enumerate(key_findings, 1):
                importance = finding.get("importance", "medium")
                imp_map = {"high": "高", "medium": "中", "low": "低"}
                content += f"{i}. 【重要性：{imp_map.get(importance, '中')}】{finding.get('finding', '')}\n"
                if finding.get("evidence"):
                    content += f"   - 数据支撑：{finding['evidence']}\n"
            content += "\n"

        if anomalies:
            content += "**异常检测结果**：\n\n"
            for a in anomalies[:5]:
                content += f"- {a.get('description', '')}\n"
            content += "\n"

        if trend and trend.get("has_trend"):
            content += f"**趋势分析**：{trend.get('description', '')}\n\n"

        if comparison and comparison.get("has_comparison"):
            content += f"**对比分析**：{comparison.get('description', '')}\n\n"
            if comparison.get("top3"):
                content += "Top 3排名：\n"
                for i, item in enumerate(comparison["top3"], 1):
                    content += f"  {i}. {item['dimension']}：{item['value']:,.2f}（占比{item['percentage']}%）\n"
            content += "\n"

        if not content:
            content = "本次分析未生成显著的数据洞察。"

        return content

    def _build_recommendation_section(self, context: BIContext) -> str:
        recommendations = context.insight_analysis.get("recommendations", [])
        if not recommendations:
            return "基于本次分析，暂无针对性业务建议。建议进一步细化分析维度，深入挖掘数据背后的业务原因。"
        content = "基于以上数据分析和洞察，提出以下业务建议：\n\n"
        for i, rec in enumerate(recommendations, 1):
            content += f"{i}. {rec}\n"
        return content

    def _build_appendix_section(self, context: BIContext) -> str:
        meta = context.meta
        execution_log = context.execution_log
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 计算总耗时（从开始到现在）
        try:
            start = datetime.fromisoformat(meta.get("start_time", now))
            total_duration = (datetime.now() - start).total_seconds()
        except:
            total_duration = 0

        content = f"**请求ID**：{meta.get('request_id', '')}\n\n"
        content += f"**开始时间**：{meta.get('start_time', '')}\n\n"
        content += f"**报告生成时间**：{now}\n\n"
        content += f"**总耗时**：{total_duration:.1f}秒\n\n"
        content += f"**Pipeline状态**：{meta.get('pipeline_status', 'success')}\n\n"

        if execution_log:
            content += "**各Agent执行日志**：\n\n"
            content += "| Agent | 状态 | 耗时(秒) |\n|---|---|---|\n"
            for log in execution_log:
                status = "成功" if log["status"] == "success" else ("跳过" if log["status"] == "skipped" else "失败")
                content += f"| {log['agent']} | {status} | {log['duration']} |\n"

        return content

    def _generate_markdown(self, title: str, sections: List[Dict], context: BIContext) -> str:
        lines = [f"# {title}", ""]
        lines.append(f"*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        lines.append("*基于AI Agent工作流的商业智能自动化分析系统生成*")
        lines.append("")
        lines.append("---")
        lines.append("")
        for section in sections:
            lines.append(f"## {section['title']}")
            lines.append("")
            lines.append(section['content'])
            lines.append("")
            lines.append("---")
            lines.append("")
        return "\n".join(lines)

    def _generate_html(self, title: str, sections: List[Dict], context: BIContext) -> str:
        """生成HTML报告（含ECharts图表渲染）"""

        def esc(text):
            return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        def md_to_html(md_text):
            """Markdown到HTML转换"""
            lines = md_text.split("\n")
            html_lines = []
            in_code = False
            in_table = False
            in_ol = False
            in_ul = False

            for line in lines:
                # 代码块
                if line.strip().startswith("```"):
                    if in_code:
                        html_lines.append("</code></pre>")
                        in_code = False
                    else:
                        html_lines.append('<pre style="background:#f5f5f5;padding:12px;border-radius:4px;overflow-x:auto;"><code>')
                        in_code = True
                    continue
                if in_code:
                    html_lines.append(esc(line))
                    continue

                # 表格行
                if "|" in line and line.strip().startswith("|"):
                    if not in_table:
                        html_lines.append('<table style="border-collapse:collapse;width:100%;margin:10px 0;">')
                        in_table = True
                        is_header = True
                    else:
                        is_header = False
                    if set(line.replace("|", "").strip()) <= set("-: "):
                        continue
                    cells = [c.strip() for c in line.strip("|").split("|")]
                    tag = "th" if is_header else "td"
                    bg = ' style="background:#16213e;color:#fff;padding:10px;text-align:left;"' if is_header else ' style="border:1px solid #ddd;padding:8px;"'
                    html_lines.append("<tr>" + "".join(f'<{tag}{bg}>{esc(c)}</{tag}>' for c in cells) + "</tr>")
                    continue
                elif in_table:
                    html_lines.append("</table>")
                    in_table = False

                # 无序列表
                if line.strip().startswith(("- ", "* ")):
                    if in_ol:
                        html_lines.append("</ol>")
                        in_ol = False
                    if not in_ul:
                        html_lines.append('<ul style="margin:10px 0;padding-left:25px;">')
                        in_ul = True
                    item = line.strip()[2:]
                    html_lines.append(f'<li style="margin:5px 0;">{self._inline_format(item)}</li>')
                    continue
                elif in_ul and not line.strip().startswith(("- ", "* ")):
                    if not (line.strip() and line.strip()[0].isdigit() and ". " in line[:5]):
                        html_lines.append("</ul>")
                        in_ul = False

                # 有序列表
                if line.strip() and line.strip()[0].isdigit() and ". " in line[:5]:
                    if in_ul:
                        html_lines.append("</ul>")
                        in_ul = False
                    if not in_ol:
                        html_lines.append('<ol style="margin:10px 0;padding-left:25px;">')
                        in_ol = True
                    item = line.split(". ", 1)[1] if ". " in line else line
                    html_lines.append(f'<li style="margin:5px 0;">{self._inline_format(item)}</li>')
                    continue
                elif in_ol and not (line.strip() and line.strip()[0].isdigit() and ". " in line[:5]):
                    if not line.strip().startswith(("- ", "* ")):
                        html_lines.append("</ol>")
                        in_ol = False

                # 空行
                if not line.strip():
                    html_lines.append("")
                    continue

                # 普通段落
                html_lines.append(f'<p style="margin:8px 0;line-height:1.6;">{self._inline_format(line)}</p>')

            if in_table:
                html_lines.append("</table>")
            if in_ul:
                html_lines.append("</ul>")
            if in_ol:
                html_lines.append("</ol>")
            return "\n".join(html_lines)

        # 构建HTML
        html_parts = [
            "<!DOCTYPE html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="UTF-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            f"<title>{esc(title)}</title>",
            # 引入ECharts CDN
            '<script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>',
            "<style>",
            "body{font-family:'Microsoft YaHei','PingFang SC',sans-serif;max-width:960px;margin:0 auto;padding:30px;background:#fafafa;color:#333;}",
            ".report-container{background:#fff;padding:40px;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,0.1);}",
            "h1{color:#1a1a2e;border-bottom:3px solid #16213e;padding-bottom:15px;margin-top:0;font-size:24px;}",
            "h2{color:#16213e;margin-top:30px;border-left:4px solid #0f3460;padding-left:12px;font-size:18px;}",
            ".meta-info{color:#666;font-size:14px;margin-bottom:20px;}",
            "hr{border:none;border-top:1px solid #eee;margin:20px 0;}",
            "table{border-collapse:collapse;width:100%;margin:10px 0;font-size:14px;}",
            "th{background:#16213e;color:#fff;padding:10px;text-align:left;}",
            "td{border:1px solid #ddd;padding:8px;}",
            "tr:nth-child(even){background:#f9f9f9;}",
            "pre{background:#f5f5f5;padding:15px;border-radius:4px;overflow-x:auto;font-size:13px;}",
            "code{font-family:'Consolas','Monaco',monospace;}",
            ".chart-container{width:100%;height:400px;margin:20px 0;border:1px solid #eee;border-radius:4px;}",
            ".chart-note{color:#999;font-size:12px;text-align:center;margin-top:5px;}",
            "</style>",
            "</head>",
            "<body>",
            '<div class="report-container">',
            f"<h1>{esc(title)}</h1>",
            f'<p class="meta-info">报告生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | 基于AI Agent工作流的商业智能自动化分析系统</p>',
            "<hr>",
        ]

        chart_div_id = 0
        for section in sections:
            html_parts.append(f"<h2>{esc(section['title'])}</h2>")
            html_parts.append(md_to_html(section['content']))

            # 如果是可视化分析章节且有ECharts配置，插入图表容器
            if "可视化分析" in section['title'] and context.chart_generation.get("status") == "success":
                echarts_config = context.chart_generation.get("echarts_config")
                if echarts_config:
                    chart_div_id += 1
                    div_id = f"chart_{chart_div_id}"
                    html_parts.append(f'<div id="{div_id}" class="chart-container"></div>')
                    html_parts.append('<p class="chart-note">交互式ECharts图表（可悬停查看详情）</p>')
                    # 插入图表渲染脚本
                    config_json = json.dumps(echarts_config, ensure_ascii=False)
                    html_parts.append("<script>")
                    html_parts.append(f"var chartDom_{chart_div_id} = document.getElementById('{div_id}');")
                    html_parts.append(f"var myChart_{chart_div_id} = echarts.init(chartDom_{chart_div_id});")
                    html_parts.append(f"var option_{chart_div_id} = {config_json};")
                    html_parts.append(f"myChart_{chart_div_id}.setOption(option_{chart_div_id});")
                    html_parts.append("window.addEventListener('resize', function(){")
                    html_parts.append(f"  myChart_{chart_div_id}.resize();")
                    html_parts.append("});")
                    html_parts.append("</script>")

            html_parts.append("<hr>")

        html_parts.append("</div>")
        html_parts.append("</body>")
        html_parts.append("</html>")

        return "\n".join(html_parts)

    def _inline_format(self, text: str) -> str:
        import re
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
        return text

    def _get_output_summary(self, context: BIContext) -> str:
        return f"title={context.report_generation['report_title'][:30]}, words={context.report_generation['word_count']}"
