"""
用户行为跟踪服务
负责记录和分析用户行为数据
"""

import json
from datetime import date, datetime
from typing import Any, Dict, List

from sqlalchemy import desc, func

from .models import DailyStats, UserBehaviorStats
from .storage import db_manager


class BehaviorTracker:
    """用户行为跟踪器"""

    def __init__(self):
        self.db_manager = db_manager

    def track_action(
        self,
        action_type: str,
        action_details: Dict[str, Any] = None,
        session_id: str = None,
        user_agent: str = None,
        ip_address: str = None,
        response_time: float = None,
        success: bool = True,
    ) -> bool:
        """
        记录用户行为

        Args:
            action_type: 行为类型 (search, chat, view_screenshot, etc.)
            action_details: 行为详细信息
            session_id: 会话ID
            user_agent: 用户代理
            ip_address: IP地址
            response_time: 响应时间（毫秒）
            success: 操作是否成功
        """
        try:
            with self.db_manager.get_session() as session:
                behavior_record = UserBehaviorStats(
                    action_type=action_type,
                    action_details=(
                        json.dumps(action_details) if action_details else None
                    ),
                    session_id=session_id,
                    user_agent=user_agent,
                    ip_address=ip_address,
                    response_time=response_time,
                    success=success,
                )
                session.add(behavior_record)
                session.commit()

                # 异步更新每日统计
                self._update_daily_stats(action_type, session_id, response_time)

                return True
        except Exception as e:
            print(f"记录用户行为失败: {e}")
            return False

    def _update_daily_stats(
        self, action_type: str, session_id: str = None, response_time: float = None
    ):
        """更新每日统计数据"""
        try:
            today = date.today().strftime("%Y-%m-%d")

            with self.db_manager.get_session() as session:
                # 获取或创建今日统计记录
                daily_stat = session.query(DailyStats).filter_by(date=today).first()
                if not daily_stat:
                    daily_stat = DailyStats(date=today)
                    session.add(daily_stat)

                # 更新对应的统计数据
                if action_type == "search":
                    daily_stat.total_searches = (daily_stat.total_searches or 0) + 1
                elif action_type == "chat":
                    daily_stat.total_chats = (daily_stat.total_chats or 0) + 1
                elif action_type == "view_screenshot":
                    daily_stat.total_screenshots_viewed = (
                        daily_stat.total_screenshots_viewed or 0
                    ) + 1

                # 更新响应时间
                if response_time is not None:
                    daily_stat.avg_response_time = (
                        (daily_stat.avg_response_time or 0)
                        * (daily_stat.total_actions or 0)
                        + response_time
                    ) / ((daily_stat.total_actions or 0) + 1)

                # 更新总操作数
                daily_stat.total_actions = (daily_stat.total_actions or 0) + 1

                session.commit()
        except Exception as e:
            print(f"更新每日统计失败: {e}")

    def get_behavior_stats(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        action_type: str = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        获取用户行为统计数据

        Args:
            start_date: 开始日期
            end_date: 结束日期
            action_type: 行为类型过滤
            limit: 返回记录数限制
        """
        try:
            with self.db_manager.get_session() as session:
                query = session.query(UserBehaviorStats)

                if start_date:
                    query = query.filter(UserBehaviorStats.created_at >= start_date)
                if end_date:
                    query = query.filter(UserBehaviorStats.created_at <= end_date)
                if action_type:
                    query = query.filter(UserBehaviorStats.action_type == action_type)

                records = (
                    query.order_by(desc(UserBehaviorStats.created_at))
                    .limit(limit)
                    .all()
                )

                return [
                    {
                        "id": record.id,
                        "action_type": record.action_type,
                        "action_details": (
                            json.loads(record.action_details)
                            if record.action_details
                            else None
                        ),
                        "session_id": record.session_id,
                        "response_time": record.response_time,
                        "success": record.success,
                        "created_at": record.created_at.isoformat(),
                    }
                    for record in records
                ]
        except Exception as e:
            print(f"获取行为统计失败: {e}")
            return []

    def get_daily_stats(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        获取每日统计数据

        Args:
            days: 获取最近多少天的数据
        """
        try:
            with self.db_manager.get_session() as session:
                records = (
                    session.query(DailyStats)
                    .order_by(desc(DailyStats.date))
                    .limit(days)
                    .all()
                )

                return [
                    {
                        "date": record.date,
                        "total_searches": record.total_searches,
                        "total_chats": record.total_chats,
                        "total_screenshots_viewed": record.total_screenshots_viewed,
                        "total_sessions": record.total_sessions,
                        "avg_response_time": record.avg_response_time,
                        "most_active_hour": record.most_active_hour,
                        "top_search_keywords": (
                            json.loads(record.top_search_keywords)
                            if record.top_search_keywords
                            else []
                        ),
                    }
                    for record in records
                ]
        except Exception as e:
            print(f"获取每日统计失败: {e}")
            return []

    def get_action_type_distribution(self, days: int = 7) -> Dict[str, int]:
        """获取行为类型分布统计"""
        try:
            from datetime import timedelta

            start_date = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            start_date = start_date - timedelta(days=days)

            with self.db_manager.get_session() as session:
                results = (
                    session.query(
                        UserBehaviorStats.action_type,
                        func.count(UserBehaviorStats.id).label("count"),
                    )
                    .filter(UserBehaviorStats.created_at >= start_date)
                    .group_by(UserBehaviorStats.action_type)
                    .all()
                )

                return {result.action_type: result.count for result in results}
        except Exception as e:
            print(f"获取行为类型分布失败: {e}")
            return {}

    def get_hourly_activity(self, days: int = 7) -> Dict[int, int]:
        """获取小时活动分布"""
        try:
            from datetime import timedelta

            start_date = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            start_date = start_date - timedelta(days=days)

            with self.db_manager.get_session() as session:
                results = (
                    session.query(
                        func.extract("hour", UserBehaviorStats.created_at).label(
                            "hour"
                        ),
                        func.count(UserBehaviorStats.id).label("count"),
                    )
                    .filter(UserBehaviorStats.created_at >= start_date)
                    .group_by(func.extract("hour", UserBehaviorStats.created_at))
                    .all()
                )

                # 初始化24小时数据
                hourly_data = {i: 0 for i in range(24)}
                for result in results:
                    hourly_data[int(result.hour)] = result.count

                return hourly_data
        except Exception as e:
            print(f"获取小时活动分布失败: {e}")
            return {i: 0 for i in range(24)}


# 全局行为跟踪器实例
behavior_tracker = BehaviorTracker()
