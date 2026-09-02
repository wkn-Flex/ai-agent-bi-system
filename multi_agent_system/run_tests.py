# -*- coding: utf-8 -*-
"""
自动测试脚本：运行多个测试用例，评估系统性能
对应题目要求第6条：评估指标（SQL生成准确率、分析任务完成率、报告可读性、端到端耗时）
"""
import sys
import os
import time
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import run_analysis


# 测试用例集（覆盖不同分析场景）
TEST_CASES = [
    # 简单查询
    {"id": 1, "category": "简单查询", "question": "2017年的总销售额是多少？", "expect_sql": True},
    {"id": 2, "category": "简单查询", "question": "2017年哪个地区的销售额最高？", "expect_sql": True},

    # 聚合分析
    {"id": 3, "category": "聚合分析", "question": "分析2017年各产品类别的销售额和利润", "expect_sql": True},
    {"id": 4, "category": "聚合分析", "question": "各客户细分的订单数量和平均销售额", "expect_sql": True},

    # 趋势分析
    {"id": 5, "category": "趋势分析", "question": "2017年各月的销售额变化趋势", "expect_sql": True},
    {"id": 6, "category": "趋势分析", "question": "对比2016年和2017年的季度销售额", "expect_sql": True},

    # 异常检测
    {"id": 7, "category": "异常检测", "question": "找出利润为负的产品类别，分析原因", "expect_sql": True},
    {"id": 8, "category": "异常检测", "question": "哪些产品的折扣率异常高？对利润有什么影响？", "expect_sql": True},

    # 综合分析
    {"id": 9, "category": "综合分析", "question": "分析2017年西部地区销售业绩下滑的原因，并给出改进建议", "expect_sql": True},
    {"id": 10, "category": "综合分析", "question": "哪些产品类别最有增长潜力？基于历史数据给出投资建议", "expect_sql": True},
]


def run_tests():
    """运行所有测试用例"""
    print("=" * 80)
    print("  多Agent BI自动化分析系统 - 自动测试")
    print("=" * 80)
    print(f"  测试用例数量: {len(TEST_CASES)}")
    print(f"  开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    results = []
    total_start = time.time()

    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n{'='*80}")
        print(f"  测试用例 [{i}/{len(TEST_CASES)}] - {test_case['category']}")
        print(f"  问题: {test_case['question']}")
        print(f"{'='*80}")

        case_start = time.time()
        try:
            context = run_analysis(test_case["question"], output_dir="output/test")
            case_duration = time.time() - case_start

            # 评估指标
            sql_success = context.sql_generation.get("status") == "success"
            data_success = context.data_query.get("status") in ["success", "empty"]
            report_success = context.report_generation.get("status") == "success"
            pipeline_success = context.meta.get("pipeline_status") == "success"

            result = {
                "id": test_case["id"],
                "category": test_case["category"],
                "question": test_case["question"],
                "sql_success": sql_success,
                "sql_attempts": context.sql_generation.get("attempts", 0),
                "data_success": data_success,
                "data_rows": context.data_query.get("row_count", 0),
                "report_success": report_success,
                "report_words": context.report_generation.get("word_count", 0),
                "pipeline_success": pipeline_success,
                "duration": round(case_duration, 2),
                "error": context.sql_generation.get("error") if not sql_success else None,
            }
            results.append(result)

            print(f"\n  结果: {'✓ 成功' if pipeline_success else '✗ 失败'}")
            print(f"  SQL生成: {'✓' if sql_success else '✗'} (尝试{result['sql_attempts']}次)")
            print(f"  数据查询: {'✓' if data_success else '✗'} ({result['data_rows']}行)")
            print(f"  报告生成: {'✓' if report_success else '✗'} ({result['report_words']}字)")
            print(f"  耗时: {result['duration']}秒")

        except Exception as e:
            case_duration = time.time() - case_start
            result = {
                "id": test_case["id"],
                "category": test_case["category"],
                "question": test_case["question"],
                "sql_success": False,
                "data_success": False,
                "report_success": False,
                "pipeline_success": False,
                "duration": round(case_duration, 2),
                "error": str(e),
            }
            results.append(result)
            print(f"\n  结果: ✗ 异常 - {e}")

    total_duration = time.time() - total_start

    # 汇总统计
    print("\n" + "=" * 80)
    print("  测试结果汇总")
    print("=" * 80)

    total = len(results)
    sql_success_count = sum(1 for r in results if r["sql_success"])
    pipeline_success_count = sum(1 for r in results if r["pipeline_success"])
    avg_duration = sum(r["duration"] for r in results) / total if total else 0
    avg_attempts = sum(r.get("sql_attempts", 0) for r in results) / total if total else 0

    print(f"  总测试用例: {total}")
    print(f"  SQL生成准确率: {sql_success_count}/{total} = {sql_success_count/total*100:.1f}%")
    print(f"  分析任务完成率: {pipeline_success_count}/{total} = {pipeline_success_count/total*100:.1f}%")
    print(f"  平均SQL尝试次数: {avg_attempts:.1f}次")
    print(f"  平均端到端耗时: {avg_duration:.1f}秒")
    print(f"  总测试耗时: {total_duration:.1f}秒")

    # 按类别统计
    print("\n  按类别统计:")
    categories = {}
    for r in results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = {"total": 0, "success": 0}
        categories[cat]["total"] += 1
        if r["pipeline_success"]:
            categories[cat]["success"] += 1

    for cat, stats in categories.items():
        rate = stats["success"] / stats["total"] * 100 if stats["total"] else 0
        print(f"    {cat}: {stats['success']}/{stats['total']} = {rate:.1f}%")

    # 失败用例详情
    failed = [r for r in results if not r["pipeline_success"]]
    if failed:
        print("\n  失败用例详情:")
        for r in failed:
            print(f"    [{r['id']}] {r['question'][:50]}...")
            print(f"         错误: {r.get('error', '未知')}")

    # 保存测试结果
    os.makedirs("output", exist_ok=True)
    result_path = "output/test_results.json"
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump({
            "summary": {
                "total": total,
                "sql_accuracy": sql_success_count / total if total else 0,
                "task_completion_rate": pipeline_success_count / total if total else 0,
                "avg_attempts": avg_attempts,
                "avg_duration": avg_duration,
                "total_duration": total_duration,
            },
            "results": results,
        }, f, ensure_ascii=False, indent=2)
    print(f"\n  测试结果已保存: {result_path}")
    print("=" * 80)

    return results


if __name__ == "__main__":
    run_tests()
