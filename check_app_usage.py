#!/usr/bin/env python3
"""
检查AppUsageLog表中的数据
"""

import sys
sys.path.append('.')

from lifetrace_backend.storage import db_manager
from lifetrace_backend.models import AppUsageLog
from datetime import datetime, timedelta

def check_app_usage_data():
    try:
        with db_manager.get_session() as session:
            # 检查总记录数
            total_count = session.query(AppUsageLog).count()
            print(f"AppUsageLog总记录数: {total_count}")

            if total_count == 0:
                print("❌ AppUsageLog表中没有数据！")
                return

            # 检查最近的记录
            recent_logs = session.query(AppUsageLog).order_by(AppUsageLog.timestamp.desc()).limit(5).all()
            print("\n最近5条记录:")
            for log in recent_logs:
                print(f"  App: {log.app_name}, Time: {log.timestamp}, Duration: {log.duration_seconds}s")

            # 检查小时分布数据
            print("\n检查小时分布数据:")
            from sqlalchemy import func
            hourly_stats = session.query(
                func.extract('hour', AppUsageLog.timestamp).label('hour'),
                func.sum(AppUsageLog.duration_seconds).label('total_duration')
            ).group_by(
                func.extract('hour', AppUsageLog.timestamp)
            ).all()

            print("小时分布统计:")
            for stat in hourly_stats:
                hour = int(stat.hour)
                duration = stat.total_duration
                print(f"  {hour:02d}:00 - {duration}秒 ({duration/3600:.2f}小时)")

            # 检查最近7天的数据
            seven_days_ago = datetime.now() - timedelta(days=7)
            recent_count = session.query(AppUsageLog).filter(
                AppUsageLog.timestamp >= seven_days_ago
            ).count()
            print(f"\n最近7天的记录数: {recent_count}")

    except Exception as e:
        print(f"检查数据时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_app_usage_data()
