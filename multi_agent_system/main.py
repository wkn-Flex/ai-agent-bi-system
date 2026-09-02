# -*- coding: utf-8 -*-
"""
主程序：组装6个Agent的Pipeline，执行端到端自动化数据分析
"""
import sys
import os

# 将项目根目录加入路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline import PipelineOrchestrator
from agents.requirement_agent import RequirementAgent
from agents.sql_generation_agent import SQLGenerationAgent
from agents.data_query_agent import DataQueryAgent
from agents.chart_generation_agent import ChartGenerationAgent
from agents.insight_analysis_agent import InsightAnalysisAgent
from agents.report_generation_agent import ReportGenerationAgent


def run_analysis(user_question: str, output_dir: str = "output"):
    """
    执行完整的多Agent自动化分析流程

    Args:
        user_question: 用户自然语言问题
        output_dir: 报告输出目录

    Returns:
        context: 执行完成后的完整上下文
    """
    # 1. 创建Pipeline编排器
    pipeline = PipelineOrchestrator()

    # 2. 按顺序添加6个Agent（对应题目要求的6个角色）
    pipeline.add_agent(RequirementAgent())       # Agent 1: 需求解析
    pipeline.add_agent(SQLGenerationAgent())      # Agent 2: SQL生成（Text-to-SQL）
    pipeline.add_agent(DataQueryAgent())          # Agent 3: 数据查询
    pipeline.add_agent(ChartGenerationAgent())    # Agent 4: 图表生成（自动化可视化）
    pipeline.add_agent(InsightAnalysisAgent())    # Agent 5: 洞察分析（归因分析）
    pipeline.add_agent(ReportGenerationAgent())   # Agent 6: 报告撰写

    # 3. 运行Pipeline
    context = pipeline.run(user_question)

    # 4. 保存报告
    if context.meta["pipeline_status"] == "success":
        os.makedirs(output_dir, exist_ok=True)

        # 保存HTML报告
        html_report = context.get_final_report()
        if html_report:
            html_path = os.path.join(output_dir, f"report_{context.meta['request_id']}.html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_report)
            print(f"\nHTML报告已保存: {html_path}")

        # 保存Markdown报告
        md_report = context.report_generation.get("markdown_content")
        if md_report:
            md_path = os.path.join(output_dir, f"report_{context.meta['request_id']}.md")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_report)
            print(f"Markdown报告已保存: {md_path}")

        # 保存上下文JSON（用于调试和追溯）
        import json
        context_path = os.path.join(output_dir, f"context_{context.meta['request_id']}.json")
        with open(context_path, "w", encoding="utf-8") as f:
            json.dump(context.to_dict(), f, ensure_ascii=False, indent=2, default=str)
        print(f"上下文数据已保存: {context_path}")

    return context


def main():
    """交互式主程序"""
    print("=" * 70)
    print("  基于AI Agent工作流的商业智能（BI）自动化数据分析系统")
    print("  多Agent协作：需求解析 → SQL生成 → 数据查询 → 图表生成 → 洞察分析 → 报告撰写")
    print("=" * 70)
    print()

    # 默认测试问题
    default_questions = [
        "2017年哪个地区的销售额最高？分析原因并给出建议",
        "分析2017年各产品类别的利润情况，找出利润最低的类别",
        "对比2016年和2017年的销售额变化趋势",
        "找出销售额异常的产品子类别，分析可能的原因",
        "分析各客户细分的销售额和利润贡献，给出优化建议",
    ]

    print("请选择测试问题（输入序号），或直接输入自定义问题：")
    for i, q in enumerate(default_questions, 1):
        print(f"  {i}. {q}")
    print()

    user_input = input("请输入: ").strip()

    if user_input.isdigit() and 1 <= int(user_input) <= len(default_questions):
        question = default_questions[int(user_input) - 1]
        print(f"\n已选择: {question}")
    elif user_input:
        question = user_input
    else:
        question = default_questions[0]
        print(f"\n使用默认问题: {question}")

    print()
    context = run_analysis(question)

    # 打印最终结果摘要
    print("\n" + "=" * 70)
    print("  分析完成！")
    print("=" * 70)
    print(f"  状态: {context.meta['pipeline_status']}")
    print(f"  总耗时: {context.meta['total_duration']}秒")
    print(f"  报告标题: {context.report_generation.get('report_title', 'N/A')}")
    print(f"  报告字数: {context.report_generation.get('word_count', 0)}字")
    print(f"  关键发现: {len(context.insight_analysis.get('key_findings', []))}条")
    print(f"  业务建议: {len(context.insight_analysis.get('recommendations', []))}条")
    print("=" * 70)


if __name__ == "__main__":
    main()
