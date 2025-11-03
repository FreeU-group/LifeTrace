"""
事件摘要管理命令
提供批量生成和查看事件AI摘要的功能
"""

import logging
import sys
from pathlib import Path

from lifetrace_backend.event_summary_service import event_summary_service
from lifetrace_backend.models import Event
from lifetrace_backend.storage import db_manager

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def generate_all_event_summaries(force: bool = False, limit: int = None):
    """
    批量为历史事件生成摘要

    Args:
        force: 是否强制重新生成已有摘要的事件
        limit: 限制处理的事件数量（None表示处理所有）
    """
    logger.info("=" * 60)
    logger.info("开始批量生成事件摘要")
    logger.info(f"强制重新生成: {force}")
    logger.info(f"处理数量限制: {limit if limit else '无限制'}")
    logger.info("=" * 60)

    try:
        # 查询所有已结束的事件
        with db_manager.get_session() as session:
            query = session.query(Event).filter(Event.end_time.isnot(None))

            # 如果不强制重新生成，只处理没有AI标题的事件
            if not force:
                query = query.filter(
                    (Event.ai_title.is_(None)) | (Event.ai_title == "")
                )

            # 按时间倒序排列（优先处理最新的事件）
            query = query.order_by(Event.start_time.desc())

            # 应用数量限制
            if limit:
                query = query.limit(limit)

            events = query.all()
            total_count = len(events)

            if total_count == 0:
                logger.info("没有需要处理的事件")
                return

            logger.info(f"找到 {total_count} 个需要处理的事件")
            logger.info("-" * 60)

        # 统计信息
        success_count = 0
        failed_count = 0

        # 逐个处理事件
        for index, event in enumerate(events, 1):
            event_id = event.id
            app_name = event.app_name or "未知应用"
            start_time = (
                event.start_time.strftime("%Y-%m-%d %H:%M:%S")
                if event.start_time
                else "未知"
            )

            logger.info(
                f"[{index}/{total_count}] 处理事件 ID={event_id}, 应用={app_name}, 时间={start_time}"
            )

            try:
                # 生成摘要
                success = event_summary_service.generate_event_summary(event_id)

                if success:
                    success_count += 1
                    logger.info("  ✓ 成功生成摘要")
                else:
                    failed_count += 1
                    logger.warning("  ✗ 生成摘要失败")

            except Exception as e:
                failed_count += 1
                logger.error(f"  ✗ 处理失败: {e}", exc_info=True)

        # 输出统计结果
        logger.info("=" * 60)
        logger.info("批量生成完成")
        logger.info(f"总计: {total_count} 个事件")
        logger.info(f"成功: {success_count} 个")
        logger.info(f"失败: {failed_count} 个")
        logger.info(f"成功率: {success_count / total_count * 100:.1f}%")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"批量生成过程出错: {e}", exc_info=True)


def show_event_summary_stats():
    """显示事件摘要生成统计"""
    try:
        with db_manager.get_session() as session:
            # 总事件数
            total_events = session.query(Event).count()

            # 已结束的事件数
            finished_events = (
                session.query(Event).filter(Event.end_time.isnot(None)).count()
            )

            # 已生成摘要的事件数
            with_summary = (
                session.query(Event)
                .filter(Event.ai_title.isnot(None), Event.ai_title != "")
                .count()
            )

            # 需要生成摘要的事件数（已结束但未生成）
            need_summary = (
                session.query(Event)
                .filter(
                    Event.end_time.isnot(None),
                    (Event.ai_title.is_(None)) | (Event.ai_title == ""),
                )
                .count()
            )

            logger.info("=" * 60)
            logger.info("事件摘要统计")
            logger.info("=" * 60)
            logger.info(f"总事件数: {total_events}")
            logger.info(f"已结束事件: {finished_events}")
            logger.info(f"已生成摘要: {with_summary}")
            logger.info(f"需要生成摘要: {need_summary}")
            if finished_events > 0:
                logger.info(f"摘要覆盖率: {with_summary / finished_events * 100:.1f}%")
            logger.info("=" * 60)

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}", exc_info=True)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="LifeTrace 事件摘要管理命令")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # 批量生成摘要命令
    generate_parser = subparsers.add_parser(
        "generate-summaries", help="批量生成事件摘要"
    )
    generate_parser.add_argument(
        "--force", action="store_true", help="强制重新生成已有摘要的事件"
    )
    generate_parser.add_argument("--limit", type=int, help="限制处理的事件数量")

    # 查看统计信息命令
    stats_parser = subparsers.add_parser("stats", help="显示事件摘要统计信息")

    args = parser.parse_args()

    if args.command == "generate-summaries":
        generate_all_event_summaries(force=args.force, limit=args.limit)
    elif args.command == "stats":
        show_event_summary_stats()
    else:
        parser.print_help()
