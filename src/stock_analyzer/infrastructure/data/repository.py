"""
数据库仓储层

提供数据库连接管理和数据访问操作
"""

import atexit
import hashlib
import json
import logging
import re
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Any

import pandas as pd
from sqlalchemy import and_, create_engine, desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from stock_analyzer.config import get_config
from stock_analyzer.infrastructure.data.models import AnalysisHistory, Base, NewsIntel, StockDaily

if TYPE_CHECKING:
    from stock_analyzer.infrastructure.external.search.models import SearchResponse

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    数据库管理器 - 单例模式

    职责：
    1. 管理数据库连接池
    2. 提供 Session 上下文管理
    3. 封装数据存取操作
    """

    _instance: DatabaseManager | None = None

    def __new__(cls, *args, **kwargs):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_url: str | None = None):
        """
        初始化数据库管理器

        Args:
            db_url: 数据库连接 URL（可选，默认从配置读取）
        """
        if self._initialized:
            return

        if db_url is None:
            config = get_config()
            db_url = config.get_db_url()

        # 创建数据库引擎
        self._engine = create_engine(
            db_url,
            echo=False,  # 设为 True 可查看 SQL 语句
            pool_pre_ping=True,  # 连接健康检查
        )

        # 创建 Session 工厂
        self._SessionLocal = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
        )

        # 创建所有表
        Base.metadata.create_all(self._engine)

        self._initialized = True
        logger.info(f"数据库初始化完成: {db_url}")

        # 注册退出钩子，确保程序退出时关闭数据库连接
        atexit.register(DatabaseManager._cleanup_engine, self._engine)

    @classmethod
    def get_instance(cls) -> DatabaseManager:
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """重置单例（用于测试）"""
        if cls._instance is not None:
            cls._instance._engine.dispose()
            cls._instance = None

    @classmethod
    def _cleanup_engine(cls, engine) -> None:
        """
        清理数据库引擎（atexit 钩子）

        确保程序退出时关闭所有数据库连接，避免 ResourceWarning
        """
        try:
            if engine is not None:
                engine.dispose()
                logger.debug("数据库引擎已清理")
        except Exception as e:
            logger.warning(f"清理数据库引擎时出错: {e}")

    def get_session(self) -> Session:
        """
        获取数据库 Session

        使用示例:
            with db.get_session() as session:
                # 执行查询
                session.commit()  # 如果需要
        """
        session = self._SessionLocal()
        try:
            return session
        except Exception:
            session.close()
            raise

    def has_today_data(self, code: str, target_date: date | None = None) -> bool:
        """
        检查是否已有指定日期的数据

        Args:
            code: 股票代码
            target_date: 目标日期（默认今天）

        Returns:
            是否存在数据
        """
        if target_date is None:
            target_date = date.today()

        with self.get_session() as session:
            result = session.execute(
                select(StockDaily).where(and_(StockDaily.code == code, StockDaily.date == target_date))
            ).scalar_one_or_none()

            return result is not None

    def get_latest_data(self, code: str, days: int = 2) -> list[StockDaily]:
        """
        获取最近 N 天的数据

        Args:
            code: 股票代码
            days: 获取天数

        Returns:
            StockDaily 对象列表（按日期降序）
        """
        with self.get_session() as session:
            results = (
                session.execute(
                    select(StockDaily).where(StockDaily.code == code).order_by(desc(StockDaily.date)).limit(days)
                )
                .scalars()
                .all()
            )

            return list(results)

    def get_daily_data(self, code: str, days: int = 30) -> pd.DataFrame | None:
        """
        获取最近 N 天的日线数据

        Args:
            code: 股票代码
            days: 获取天数（默认30天）

        Returns:
            DataFrame 包含日线数据，或 None 如果没有数据
        """
        records = self.get_latest_data(code, days)

        if not records:
            return None

        # 转换为 DataFrame
        data = [record.to_dict() for record in records]
        df = pd.DataFrame(data)

        # 按日期升序排列（从旧到新）
        if "date" in df.columns:
            df = df.sort_values("date").reset_index(drop=True)

        return df

    def save_daily_data(self, df: pd.DataFrame, code: str, data_source: str = "Unknown") -> int:
        """
        保存日线数据到数据库

        Args:
            df: 包含日线数据的 DataFrame
            code: 股票代码
            data_source: 数据来源名称

        Returns:
            新增/更新的记录数
        """
        if df is None or df.empty:
            logger.warning(f"保存数据为空，跳过 {code}")
            return 0

        saved_count = 0

        with self.get_session() as session:
            try:
                for _, row in df.iterrows():
                    # 解析日期
                    row_date = row.get("date")
                    if isinstance(row_date, str):
                        row_date = datetime.strptime(row_date, "%Y-%m-%d").date()
                    elif isinstance(row_date, (datetime, pd.Timestamp)):
                        row_date = row_date.date()

                    # 检查是否已存在
                    existing = session.execute(
                        select(StockDaily).where(and_(StockDaily.code == code, StockDaily.date == row_date))
                    ).scalar_one_or_none()

                    if existing:
                        # 更新现有记录
                        existing.open = row.get("open")
                        existing.high = row.get("high")
                        existing.low = row.get("low")
                        existing.close = row.get("close")
                        existing.volume = row.get("volume")
                        existing.amount = row.get("amount")
                        existing.pct_chg = row.get("pct_chg")
                        existing.ma5 = row.get("ma5")
                        existing.ma10 = row.get("ma10")
                        existing.ma20 = row.get("ma20")
                        existing.volume_ratio = row.get("volume_ratio")
                        existing.data_source = data_source
                        existing.updated_at = datetime.now()
                    else:
                        # 创建新记录
                        record = StockDaily(
                            code=code,
                            date=row_date,
                            open=row.get("open"),
                            high=row.get("high"),
                            low=row.get("low"),
                            close=row.get("close"),
                            volume=row.get("volume"),
                            amount=row.get("amount"),
                            pct_chg=row.get("pct_chg"),
                            ma5=row.get("ma5"),
                            ma10=row.get("ma10"),
                            ma20=row.get("ma20"),
                            volume_ratio=row.get("volume_ratio"),
                            data_source=data_source,
                        )
                        session.add(record)
                        saved_count += 1

                session.commit()
                logger.info(f"保存 {code} 数据成功，新增 {saved_count} 条")

            except Exception as e:
                session.rollback()
                logger.error(f"保存 {code} 数据失败: {e}")
                raise

        return saved_count

    def save_news_intel(
        self,
        code: str,
        name: str,
        dimension: str,
        query: str,
        response: SearchResponse,
        query_context: dict[str, str] | None = None,
    ) -> int:
        """
        保存新闻情报到数据库

        Args:
            code: 股票代码
            name: 股票名称
            dimension: 搜索维度
            query: 搜索查询
            response: 搜索响应
            query_context: 查询上下文

        Returns:
            保存的记录数
        """
        if not response or not response.results:
            return 0

        saved_count = 0

        with self.get_session() as session:
            try:
                for item in response.results:
                    title = (item.title or "").strip()
                    url = (item.url or "").strip()
                    source = (item.source or "").strip()
                    snippet = (item.snippet or "").strip()
                    published_date = self._parse_published_date(item.published_date)

                    if not title and not url:
                        continue

                    url_key = url or self._build_fallback_url_key(
                        code=code, title=title, source=source, published_date=published_date
                    )

                    # 优先按 URL 或兜底键去重
                    existing = session.execute(select(NewsIntel).where(NewsIntel.url == url_key)).scalar_one_or_none()

                    if existing:
                        existing.name = name or existing.name
                        existing.dimension = dimension or existing.dimension
                        existing.query = query or existing.query
                        existing.provider = response.provider or existing.provider
                        existing.snippet = snippet or existing.snippet
                        existing.source = source or existing.source
                        existing.published_date = published_date or existing.published_date
                        existing.fetched_at = datetime.now()

                        if query_context:
                            existing.query_id = query_context.get("query_id") or existing.query_id
                            existing.query_source = query_context.get("query_source") or existing.query_source
                            existing.requester_platform = (
                                query_context.get("requester_platform") or existing.requester_platform
                            )
                            existing.requester_user_id = (
                                query_context.get("requester_user_id") or existing.requester_user_id
                            )
                            existing.requester_user_name = (
                                query_context.get("requester_user_name") or existing.requester_user_name
                            )
                            existing.requester_chat_id = (
                                query_context.get("requester_chat_id") or existing.requester_chat_id
                            )
                            existing.requester_message_id = (
                                query_context.get("requester_message_id") or existing.requester_message_id
                            )
                            existing.requester_query = query_context.get("requester_query") or existing.requester_query
                    else:
                        try:
                            with session.begin_nested():
                                record = NewsIntel(
                                    code=code,
                                    name=name,
                                    dimension=dimension,
                                    query=query,
                                    provider=response.provider,
                                    title=title,
                                    snippet=snippet,
                                    url=url_key,
                                    source=source,
                                    published_date=published_date,
                                    fetched_at=datetime.now(),
                                    query_id=(query_context or {}).get("query_id"),
                                    query_source=(query_context or {}).get("query_source"),
                                    requester_platform=(query_context or {}).get("requester_platform"),
                                    requester_user_id=(query_context or {}).get("requester_user_id"),
                                    requester_user_name=(query_context or {}).get("requester_user_name"),
                                    requester_chat_id=(query_context or {}).get("requester_chat_id"),
                                    requester_message_id=(query_context or {}).get("requester_message_id"),
                                    requester_query=(query_context or {}).get("requester_query"),
                                )
                                session.add(record)
                                session.flush()
                            saved_count += 1
                        except IntegrityError:
                            logger.debug("新闻情报重复（已跳过）: %s %s", code, url_key)

                session.commit()
                logger.info(f"保存新闻情报成功: {code}, 新增 {saved_count} 条")

            except Exception as e:
                session.rollback()
                logger.error(f"保存新闻情报失败: {e}")
                raise

        return saved_count

    def get_recent_news(self, code: str, days: int = 7, limit: int = 20) -> list[NewsIntel]:
        """
        获取指定股票最近 N 天的新闻情报
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        with self.get_session() as session:
            results = (
                session.execute(
                    select(NewsIntel)
                    .where(and_(NewsIntel.code == code, NewsIntel.fetched_at >= cutoff_date))
                    .order_by(desc(NewsIntel.fetched_at))
                    .limit(limit)
                )
                .scalars()
                .all()
            )

            return list(results)

    def save_analysis_history(
        self,
        result: Any,
        query_id: str,
        report_type: str,
        news_content: str | None,
        context_snapshot: dict[str, Any] | None = None,
        save_snapshot: bool = True,
    ) -> int:
        """
        保存分析结果历史记录
        """
        if result is None:
            return 0

        sniper_points = self._extract_sniper_points(result)
        raw_result = self._build_raw_result(result)
        context_text = None
        if save_snapshot and context_snapshot is not None:
            context_text = self._safe_json_dumps(context_snapshot)

        record = AnalysisHistory(
            query_id=query_id,
            code=result.code,
            name=result.name,
            report_type=report_type,
            sentiment_score=result.sentiment_score,
            operation_advice=result.operation_advice,
            trend_prediction=result.trend_prediction,
            analysis_summary=result.analysis_summary,
            raw_result=self._safe_json_dumps(raw_result),
            news_content=news_content,
            context_snapshot=context_text,
            ideal_buy=sniper_points.get("ideal_buy"),
            secondary_buy=sniper_points.get("secondary_buy"),
            stop_loss=sniper_points.get("stop_loss"),
            take_profit=sniper_points.get("take_profit"),
            created_at=datetime.now(),
        )

        with self.get_session() as session:
            try:
                session.add(record)
                session.commit()
                return 1
            except Exception as e:
                session.rollback()
                logger.error(f"保存分析历史失败: {e}")
                return 0

    def get_analysis_history(
        self,
        code: str | None = None,
        query_id: str | None = None,
        days: int = 30,
        limit: int = 50,
    ) -> list[AnalysisHistory]:
        """
        查询分析历史记录
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        with self.get_session() as session:
            conditions = [AnalysisHistory.created_at >= cutoff_date]
            if code:
                conditions.append(AnalysisHistory.code == code)
            if query_id:
                conditions.append(AnalysisHistory.query_id == query_id)

            results = (
                session.execute(
                    select(AnalysisHistory)
                    .where(and_(*conditions))
                    .order_by(desc(AnalysisHistory.created_at))
                    .limit(limit)
                )
                .scalars()
                .all()
            )

            return list(results)

    def get_data_range(self, code: str, start_date: date, end_date: date) -> list[StockDaily]:
        """
        获取指定日期范围的数据
        """
        with self.get_session() as session:
            results = (
                session.execute(
                    select(StockDaily)
                    .where(
                        and_(
                            StockDaily.code == code,
                            StockDaily.date >= start_date,
                            StockDaily.date <= end_date,
                        )
                    )
                    .order_by(StockDaily.date)
                )
                .scalars()
                .all()
            )

            return list(results)

    def get_analysis_context(self, code: str, target_date: date | None = None) -> dict[str, Any] | None:
        """
        获取分析所需的上下文数据

        返回今日数据 + 昨日数据的对比信息
        """
        if target_date is None:
            target_date = date.today()

        # 获取最近2天数据
        recent_data = self.get_latest_data(code, days=2)

        if not recent_data:
            logger.warning(f"未找到 {code} 的数据")
            return None

        today_data = recent_data[0]
        yesterday_data = recent_data[1] if len(recent_data) > 1 else None

        context = {
            "code": code,
            "date": today_data.date.isoformat(),
            "today": today_data.to_dict(),
        }

        if yesterday_data:
            context["yesterday"] = yesterday_data.to_dict()

            # 计算相比昨日的变化
            if yesterday_data.volume and yesterday_data.volume > 0:
                context["volume_change_ratio"] = round(today_data.volume / yesterday_data.volume, 2)

            if yesterday_data.close and yesterday_data.close > 0:
                context["price_change_ratio"] = round(
                    (today_data.close - yesterday_data.close) / yesterday_data.close * 100, 2
                )

            # 均线形态判断
            context["ma_status"] = self._analyze_ma_status(today_data)

        return context

    def _analyze_ma_status(self, data: StockDaily) -> str:
        """
        分析均线形态
        """
        close = data.close or 0
        ma5 = data.ma5 or 0
        ma10 = data.ma10 or 0
        ma20 = data.ma20 or 0

        if close > ma5 > ma10 > ma20 > 0:
            return "多头排列 📈"
        elif close < ma5 < ma10 < ma20 and ma20 > 0:
            return "空头排列 📉"
        elif close > ma5 and ma5 > ma10:
            return "短期向好 🔼"
        elif close < ma5 and ma5 < ma10:
            return "短期走弱 🔽"
        else:
            return "震荡整理 ↔️"

    @staticmethod
    def _parse_published_date(value: str | None) -> datetime | None:
        """
        解析发布时间字符串
        """
        if not value:
            return None

        if isinstance(value, datetime):
            return value

        text = str(value).strip()
        if not text:
            return None

        # 优先尝试 ISO 格式
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            pass

        for fmt in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d %H:%M",
            "%Y/%m/%d",
        ):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue

        return None

    @staticmethod
    def _safe_json_dumps(data: Any) -> str:
        """
        安全序列化为 JSON 字符串
        """
        try:
            return json.dumps(data, ensure_ascii=False, default=str)
        except Exception:
            return json.dumps(str(data), ensure_ascii=False)

    @staticmethod
    def _build_raw_result(result: Any) -> dict[str, Any]:
        """
        生成完整分析结果字典
        """
        data = result.to_dict() if hasattr(result, "to_dict") else {}
        data.update(
            {
                "data_sources": getattr(result, "data_sources", ""),
                "raw_response": getattr(result, "raw_response", None),
            }
        )
        return data

    @staticmethod
    def _parse_sniper_value(value: Any) -> float | None:
        """
        解析狙击点位数值
        """
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)

        text = str(value).replace(",", "").strip()
        if not text:
            return None

        match = re.search(r"-?\d+(?:\.\d+)?", text)
        if not match:
            return None
        try:
            return float(match.group())
        except ValueError:
            return None

    def _extract_sniper_points(self, result: Any) -> dict[str, float | None]:
        """
        抽取狙击点位数据
        """
        raw_points = {}
        if hasattr(result, "get_sniper_points"):
            raw_points = result.get_sniper_points() or {}

        return {
            "ideal_buy": self._parse_sniper_value(raw_points.get("ideal_buy")),
            "secondary_buy": self._parse_sniper_value(raw_points.get("secondary_buy")),
            "stop_loss": self._parse_sniper_value(raw_points.get("stop_loss")),
            "take_profit": self._parse_sniper_value(raw_points.get("take_profit")),
        }

    @staticmethod
    def _build_fallback_url_key(code: str, title: str, source: str, published_date: datetime | None) -> str:
        """
        生成无 URL 时的去重键
        """
        date_str = published_date.isoformat() if published_date else ""
        raw_key = f"{code}|{title}|{source}|{date_str}"
        digest = hashlib.md5(raw_key.encode("utf-8")).hexdigest()
        return f"no-url:{code}:{digest}"


def get_db() -> DatabaseManager:
    """获取数据库管理器实例的快捷方式"""
    return DatabaseManager.get_instance()
