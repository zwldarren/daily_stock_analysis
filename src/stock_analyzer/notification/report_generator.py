"""
报告生成器

负责生成各种格式的分析报告
"""

import logging
from datetime import datetime

from stock_analyzer.ai.models import AnalysisResult

logger = logging.getLogger(__name__)


class ReportGenerator:
    """报告生成器"""

    @staticmethod
    def generate_daily_report(results: list[AnalysisResult], report_date: str | None = None) -> str:
        """
        生成 Markdown 格式的日报（详细版）

        Args:
            results: 分析结果列表
            report_date: 报告日期（默认今天）

        Returns:
            Markdown 格式的日报内容
        """
        if report_date is None:
            report_date = datetime.now().strftime("%Y-%m-%d")

        # 标题
        report_lines = [
            f"# 📅 {report_date} 股票智能分析报告",
            "",
            f"> 共分析 **{len(results)}** 只股票 | 报告生成时间：{datetime.now().strftime('%H:%M:%S')}",
            "",
            "---",
            "",
        ]

        # 按评分排序（高分在前）
        sorted_results = sorted(results, key=lambda x: x.sentiment_score, reverse=True)

        # 统计信息
        buy_count = sum(1 for r in results if getattr(r, "decision_type", "") == "buy")
        sell_count = sum(1 for r in results if getattr(r, "decision_type", "") == "sell")
        hold_count = sum(1 for r in results if getattr(r, "decision_type", "") in ("hold", ""))
        avg_score = sum(r.sentiment_score for r in results) / len(results) if results else 0

        report_lines.extend(
            [
                "## 📊 操作建议汇总",
                "",
                "| 指标 | 数值 |",
                "|------|------|",
                f"| 🟢 建议买入/加仓 | **{buy_count}** 只 |",
                f"| 🟡 建议持有/观望 | **{hold_count}** 只 |",
                f"| 🔴 建议减仓/卖出 | **{sell_count}** 只 |",
                f"| 📈 平均看多评分 | **{avg_score:.1f}** 分 |",
                "",
                "---",
                "",
                "## 📈 个股详细分析",
                "",
            ]
        )

        # 逐个股票的详细分析
        for result in sorted_results:
            emoji = result.get_emoji()
            confidence_stars = result.get_confidence_stars() if hasattr(result, "get_confidence_stars") else "⭐⭐"

            report_lines.extend(
                [
                    f"### {emoji} {result.name} ({result.code})",
                    "",
                    f"**操作建议：{result.operation_advice}** | "
                    f"**综合评分：{result.sentiment_score}分** | "
                    f"**趋势预测：{result.trend_prediction}** | "
                    f"**置信度：{confidence_stars}**",
                    "",
                ]
            )

            # 核心看点
            if hasattr(result, "key_points") and result.key_points:
                report_lines.extend(
                    [
                        f"**🎯 核心看点**：{result.key_points}",
                        "",
                    ]
                )

            # 买入/卖出理由
            if hasattr(result, "buy_reason") and result.buy_reason:
                report_lines.extend(
                    [
                        f"**💡 操作理由**：{result.buy_reason}",
                        "",
                    ]
                )

            # 走势分析
            if hasattr(result, "trend_analysis") and result.trend_analysis:
                report_lines.extend(
                    [
                        "#### 📉 走势分析",
                        f"{result.trend_analysis}",
                        "",
                    ]
                )

            # 短期/中期展望
            outlook_lines = []
            if hasattr(result, "short_term_outlook") and result.short_term_outlook:
                outlook_lines.append(f"- **短期（1-3日）**：{result.short_term_outlook}")
            if hasattr(result, "medium_term_outlook") and result.medium_term_outlook:
                outlook_lines.append(f"- **中期（1-2周）**：{result.medium_term_outlook}")
            if outlook_lines:
                report_lines.extend(
                    [
                        "#### 🔮 市场展望",
                        *outlook_lines,
                        "",
                    ]
                )

            # 技术面分析
            tech_lines = []
            if result.technical_analysis:
                tech_lines.append(f"**综合**：{result.technical_analysis}")
            if hasattr(result, "ma_analysis") and result.ma_analysis:
                tech_lines.append(f"**均线**：{result.ma_analysis}")
            if hasattr(result, "volume_analysis") and result.volume_analysis:
                tech_lines.append(f"**量能**：{result.volume_analysis}")
            if hasattr(result, "pattern_analysis") and result.pattern_analysis:
                tech_lines.append(f"**形态**：{result.pattern_analysis}")
            if tech_lines:
                report_lines.extend(
                    [
                        "#### 📊 技术面分析",
                        *tech_lines,
                        "",
                    ]
                )

            # 基本面分析
            fund_lines = []
            if hasattr(result, "fundamental_analysis") and result.fundamental_analysis:
                fund_lines.append(result.fundamental_analysis)
            if hasattr(result, "sector_position") and result.sector_position:
                fund_lines.append(f"**板块地位**：{result.sector_position}")
            if hasattr(result, "company_highlights") and result.company_highlights:
                fund_lines.append(f"**公司亮点**：{result.company_highlights}")
            if fund_lines:
                report_lines.extend(
                    [
                        "#### 🏢 基本面分析",
                        *fund_lines,
                        "",
                    ]
                )

            # 消息面/情绪面
            news_lines = []
            if result.news_summary:
                news_lines.append(f"**新闻摘要**：{result.news_summary}")
            if hasattr(result, "market_sentiment") and result.market_sentiment:
                news_lines.append(f"**市场情绪**：{result.market_sentiment}")
            if hasattr(result, "hot_topics") and result.hot_topics:
                news_lines.append(f"**相关热点**：{result.hot_topics}")
            if news_lines:
                report_lines.extend(
                    [
                        "#### 📰 消息面/情绪面",
                        *news_lines,
                        "",
                    ]
                )

            # 综合分析
            if result.analysis_summary:
                report_lines.extend(
                    [
                        "#### 📝 综合分析",
                        result.analysis_summary,
                        "",
                    ]
                )

            # 风险提示
            if hasattr(result, "risk_warning") and result.risk_warning:
                report_lines.extend(
                    [
                        f"⚠️ **风险提示**：{result.risk_warning}",
                        "",
                    ]
                )

            # 数据来源说明
            if hasattr(result, "search_performed") and result.search_performed:
                report_lines.append("*🔍 已执行联网搜索*")
            if hasattr(result, "data_sources") and result.data_sources:
                report_lines.append(f"*📋 数据来源：{result.data_sources}*")

            # 错误信息（如果有）
            if not result.success and result.error_message:
                report_lines.extend(
                    [
                        "",
                        f"❌ **分析异常**：{result.error_message[:100]}",
                    ]
                )

            report_lines.extend(
                [
                    "",
                    "---",
                    "",
                ]
            )

        # 底部信息
        report_lines.extend(
            [
                "",
                f"*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            ]
        )

        return "\n".join(report_lines)

    @staticmethod
    def generate_dashboard_report(results: list[AnalysisResult], report_date: str | None = None) -> str:
        """
        生成决策仪表盘格式的日报

        Args:
            results: 分析结果列表
            report_date: 报告日期（默认今天）

        Returns:
            Markdown 格式的决策仪表盘日报
        """
        if report_date is None:
            report_date = datetime.now().strftime("%Y-%m-%d")

        # 按评分排序（高分在前）
        sorted_results = sorted(results, key=lambda x: x.sentiment_score, reverse=True)

        # 统计信息
        buy_count = sum(1 for r in results if getattr(r, "decision_type", "") == "buy")
        sell_count = sum(1 for r in results if getattr(r, "decision_type", "") == "sell")
        hold_count = sum(1 for r in results if getattr(r, "decision_type", "") in ("hold", ""))

        report_lines = [
            f"# 🎯 {report_date} 决策仪表盘",
            "",
            f"> 共分析 **{len(results)}** 只股票 | 🟢买入:{buy_count} 🟡观望:{hold_count} 🔴卖出:{sell_count}",
            "",
        ]

        # 分析结果摘要
        if results:
            report_lines.extend(
                [
                    "## 📊 分析结果摘要",
                    "",
                ]
            )
            for r in sorted_results:
                emoji = r.get_emoji()
                report_lines.append(
                    f"{emoji} **{r.name}({r.code})**: {r.operation_advice} | "
                    f"评分 {r.sentiment_score} | {r.trend_prediction}"
                )
            report_lines.extend(
                [
                    "",
                    "---",
                    "",
                ]
            )

        # 逐个股票的决策仪表盘
        for result in sorted_results:
            signal_text, signal_emoji, signal_tag = ReportGenerator._get_signal_level(result)
            dashboard = result.dashboard if hasattr(result, "dashboard") and result.dashboard else {}

            # 股票名称
            stock_name = result.name if result.name and not result.name.startswith("股票") else f"股票{result.code}"

            report_lines.extend(
                [
                    f"## {signal_emoji} {stock_name} ({result.code})",
                    "",
                ]
            )

            # 舆情与基本面概览
            intel = dashboard.get("intelligence", {}) if dashboard else {}
            if intel:
                report_lines.extend(
                    [
                        "### 📰 重要信息速览",
                        "",
                    ]
                )

                if intel.get("sentiment_summary"):
                    report_lines.append(f"**💭 舆情情绪**: {intel['sentiment_summary']}")

                if intel.get("earnings_outlook"):
                    report_lines.append(f"**📊 业绩预期**: {intel['earnings_outlook']}")

                risk_alerts = intel.get("risk_alerts", [])
                if risk_alerts:
                    report_lines.append("")
                    report_lines.append("**🚨 风险警报**:")
                    for alert in risk_alerts:
                        report_lines.append(f"- {alert}")

                catalysts = intel.get("positive_catalysts", [])
                if catalysts:
                    report_lines.append("")
                    report_lines.append("**✨ 利好催化**:")
                    for cat in catalysts:
                        report_lines.append(f"- {cat}")

                if intel.get("latest_news"):
                    report_lines.append("")
                    report_lines.append(f"**📢 最新动态**: {intel['latest_news']}")

                report_lines.append("")

            # 核心结论
            core = dashboard.get("core_conclusion", {}) if dashboard else {}
            one_sentence = core.get("one_sentence", result.analysis_summary)
            time_sense = core.get("time_sensitivity", "本周内")
            pos_advice = core.get("position_advice", {})

            report_lines.extend(
                [
                    "### 📌 核心结论",
                    "",
                    f"**{signal_emoji} {signal_text}** | {result.trend_prediction}",
                    "",
                    f"> **一句话决策**: {one_sentence}",
                    "",
                    f"⏰ **时效性**: {time_sense}",
                    "",
                ]
            )

            # 持仓分类建议
            if pos_advice:
                report_lines.extend(
                    [
                        "| 持仓情况 | 操作建议 |",
                        "|---------|---------|",
                        f"| 🆕 **空仓者** | {pos_advice.get('no_position', result.operation_advice)} |",
                        f"| 💼 **持仓者** | {pos_advice.get('has_position', '继续持有')} |",
                        "",
                    ]
                )

            # 数据透视
            data_persp = dashboard.get("data_perspective", {}) if dashboard else {}
            if data_persp:
                trend_data = data_persp.get("trend_status", {})
                price_data = data_persp.get("price_position", {})
                vol_data = data_persp.get("volume_analysis", {})
                chip_data = data_persp.get("chip_structure", {})

                report_lines.extend(
                    [
                        "### 📊 数据透视",
                        "",
                    ]
                )

                if trend_data:
                    is_bullish = "✅ 是" if trend_data.get("is_bullish", False) else "❌ 否"
                    report_lines.extend(
                        [
                            f"**均线排列**: {trend_data.get('ma_alignment', 'N/A')} | "
                            f"多头排列: {is_bullish} | "
                            f"趋势强度: {trend_data.get('trend_score', 'N/A')}/100",
                            "",
                        ]
                    )

                if price_data:
                    bias_status = price_data.get("bias_status", "N/A")
                    bias_emoji = "✅" if bias_status == "安全" else ("⚠️" if bias_status == "警戒" else "🚨")
                    report_lines.extend(
                        [
                            "| 价格指标 | 数值 |",
                            "|---------|------|",
                            f"| 当前价 | {price_data.get('current_price', 'N/A')} |",
                            f"| MA5 | {price_data.get('ma5', 'N/A')} |",
                            f"| MA10 | {price_data.get('ma10', 'N/A')} |",
                            f"| MA20 | {price_data.get('ma20', 'N/A')} |",
                            f"| 乖离率(MA5) | {price_data.get('bias_ma5', 'N/A')}% {bias_emoji}{bias_status} |",
                            f"| 支撑位 | {price_data.get('support_level', 'N/A')} |",
                            f"| 压力位 | {price_data.get('resistance_level', 'N/A')} |",
                            "",
                        ]
                    )

                if vol_data:
                    report_lines.extend(
                        [
                            f"**量能**: 量比 {vol_data.get('volume_ratio', 'N/A')} "
                            f"({vol_data.get('volume_status', '')}) | "
                            f"换手率 {vol_data.get('turnover_rate', 'N/A')}%",
                            f"💡 *{vol_data.get('volume_meaning', '')}*",
                            "",
                        ]
                    )

                if chip_data:
                    chip_health = chip_data.get("chip_health", "N/A")
                    chip_emoji = "✅" if chip_health == "健康" else ("⚠️" if chip_health == "一般" else "🚨")
                    report_lines.extend(
                        [
                            f"**筹码**: 获利比例 {chip_data.get('profit_ratio', 'N/A')} | "
                            f"平均成本 {chip_data.get('avg_cost', 'N/A')} | "
                            f"集中度 {chip_data.get('concentration', 'N/A')} "
                            f"{chip_emoji}{chip_health}",
                            "",
                        ]
                    )

            # 作战计划
            battle = dashboard.get("battle_plan", {}) if dashboard else {}
            if battle:
                report_lines.extend(
                    [
                        "### 🎯 作战计划",
                        "",
                    ]
                )

                sniper = battle.get("sniper_points", {})
                if sniper:
                    report_lines.extend(
                        [
                            "**📍 狙击点位**",
                            "",
                            "| 点位类型 | 价格 |",
                            "|---------|------|",
                            f"| 🎯 理想买入点 | {sniper.get('ideal_buy', 'N/A')} |",
                            f"| 🔵 次优买入点 | {sniper.get('secondary_buy', 'N/A')} |",
                            f"| 🛑 止损位 | {sniper.get('stop_loss', 'N/A')} |",
                            f"| 🎊 目标位 | {sniper.get('take_profit', 'N/A')} |",
                            "",
                        ]
                    )

                position = battle.get("position_strategy", {})
                if position:
                    report_lines.extend(
                        [
                            f"**💰 仓位建议**: {position.get('suggested_position', 'N/A')}",
                            f"- 建仓策略: {position.get('entry_plan', 'N/A')}",
                            f"- 风控策略: {position.get('risk_control', 'N/A')}",
                            "",
                        ]
                    )

                checklist = battle.get("action_checklist", []) if battle else []
                if checklist:
                    report_lines.extend(
                        [
                            "**✅ 检查清单**",
                            "",
                        ]
                    )
                    for item in checklist:
                        report_lines.append(f"- {item}")
                    report_lines.append("")

            report_lines.extend(
                [
                    "---",
                    "",
                ]
            )

        # 底部
        report_lines.extend(
            [
                "",
                f"*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            ]
        )

        return "\n".join(report_lines)

    @staticmethod
    def generate_single_stock_report(result: AnalysisResult) -> str:
        """
        生成单只股票的分析报告（用于单股推送模式）

        Args:
            result: 单只股票的分析结果

        Returns:
            Markdown 格式的单股报告
        """
        report_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        signal_text, signal_emoji, _ = ReportGenerator._get_signal_level(result)
        dashboard = result.dashboard if hasattr(result, "dashboard") and result.dashboard else {}
        core = dashboard.get("core_conclusion", {}) if dashboard else {}
        battle = dashboard.get("battle_plan", {}) if dashboard else {}
        intel = dashboard.get("intelligence", {}) if dashboard else {}

        # 股票名称
        stock_name = result.name if result.name and not result.name.startswith("股票") else f"股票{result.code}"

        lines = [
            f"## {signal_emoji} {stock_name} ({result.code})",
            "",
            f"> {report_date} | 评分: **{result.sentiment_score}** | {result.trend_prediction}",
            "",
        ]

        # 核心决策（一句话）
        one_sentence = core.get("one_sentence", result.analysis_summary) if core else result.analysis_summary
        if one_sentence:
            lines.extend(
                [
                    "### 📌 核心结论",
                    "",
                    f"**{signal_text}**: {one_sentence}",
                    "",
                ]
            )

        # 重要信息（舆情+基本面）
        info_added = False
        if intel:
            if intel.get("earnings_outlook"):
                if not info_added:
                    lines.append("### 📰 重要信息")
                    lines.append("")
                    info_added = True
                lines.append(f"📊 **业绩预期**: {intel['earnings_outlook'][:100]}")

            if intel.get("sentiment_summary"):
                if not info_added:
                    lines.append("### 📰 重要信息")
                    lines.append("")
                    info_added = True
                lines.append(f"💭 **舆情情绪**: {intel['sentiment_summary'][:80]}")

            risks = intel.get("risk_alerts", [])
            if risks:
                if not info_added:
                    lines.append("### 📰 重要信息")
                    lines.append("")
                    info_added = True
                lines.append("")
                lines.append("🚨 **风险警报**:")
                for risk in risks[:3]:
                    lines.append(f"- {risk[:60]}")

            catalysts = intel.get("positive_catalysts", [])
            if catalysts:
                lines.append("")
                lines.append("✨ **利好催化**:")
                for cat in catalysts[:3]:
                    lines.append(f"- {cat[:60]}")

        if info_added:
            lines.append("")

        # 狙击点位
        sniper = battle.get("sniper_points", {}) if battle else {}
        if sniper:
            lines.extend(
                [
                    "### 🎯 操作点位",
                    "",
                    "| 买点 | 止损 | 目标 |",
                    "|------|------|------|",
                ]
            )
            ideal_buy = sniper.get("ideal_buy", "-")
            stop_loss = sniper.get("stop_loss", "-")
            take_profit = sniper.get("take_profit", "-")
            lines.append(f"| {ideal_buy} | {stop_loss} | {take_profit} |")
            lines.append("")

        # 持仓建议
        pos_advice = core.get("position_advice", {}) if core else {}
        if pos_advice:
            lines.extend(
                [
                    "### 💼 持仓建议",
                    "",
                    f"- 🆕 **空仓者**: {pos_advice.get('no_position', result.operation_advice)}",
                    f"- 💼 **持仓者**: {pos_advice.get('has_position', '继续持有')}",
                    "",
                ]
            )

        lines.extend(
            [
                "---",
                "*AI生成，仅供参考，不构成投资建议*",
            ]
        )

        return "\n".join(lines)

    @staticmethod
    def _get_signal_level(result: AnalysisResult) -> tuple[str, str, str]:
        """
        根据操作建议获取信号等级和颜色

        Returns:
            (信号文字, emoji, 颜色标记)
        """
        advice = result.operation_advice
        score = result.sentiment_score

        if advice in ["强烈买入"] or score >= 80:
            return ("强烈买入", "💚", "强买")
        elif advice in ["买入", "加仓"] or score >= 65:
            return ("买入", "🟢", "买入")
        elif advice in ["持有"] or 55 <= score < 65:
            return ("持有", "🟡", "持有")
        elif advice in ["观望"] or 45 <= score < 55:
            return ("观望", "⚪", "观望")
        elif advice in ["减仓"] or 35 <= score < 45:
            return ("减仓", "🟠", "减仓")
        elif advice in ["卖出", "强烈卖出"] or score < 35:
            return ("卖出", "🔴", "卖出")
        else:
            return ("观望", "⚪", "观望")
