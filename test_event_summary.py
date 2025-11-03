#!/usr/bin/env python3
"""
事件AI摘要功能测试脚本
用于验证事件摘要生成功能是否正常工作
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from lifetrace_backend.event_summary_service import event_summary_service
from lifetrace_backend.storage import db_manager
from lifetrace_backend.models import Event

def test_event_summary_service():
    """测试事件摘要服务"""
    print("=" * 60)
    print("测试事件AI摘要功能")
    print("=" * 60)

    # 1. 查找一个已结束但没有摘要的事件
    print("\n1. 查找测试事件...")
    with db_manager.get_session() as session:
        event = session.query(Event).filter(
            Event.end_time.isnot(None),
            (Event.ai_title.is_(None)) | (Event.ai_title == '')
        ).first()

        if not event:
            print("  ⚠ 没有找到适合测试的事件")
            print("  提示：所有事件都已经有摘要了，或者没有已结束的事件")
            return False

        event_id = event.id
        app_name = event.app_name
        window_title = event.window_title
        print(f"  ✓ 找到事件 ID={event_id}")
        print(f"    应用: {app_name}")
        print(f"    窗口: {window_title}")

    # 2. 生成摘要
    print("\n2. 生成AI摘要...")
    success = event_summary_service.generate_event_summary(event_id)

    if not success:
        print("  ✗ 摘要生成失败")
        return False

    print("  ✓ 摘要生成成功")

    # 3. 验证结果
    print("\n3. 验证生成结果...")
    event_info = db_manager.get_event_summary(event_id)

    if not event_info:
        print("  ✗ 无法获取事件信息")
        return False

    ai_title = event_info.get('ai_title')
    ai_summary = event_info.get('ai_summary')

    print(f"  AI标题: {ai_title}")
    print(f"  AI摘要: {ai_summary}")

    if ai_title and ai_summary:
        print("  ✓ 摘要字段已正确填充")
    else:
        print("  ✗ 摘要字段为空")
        return False

    # 4. 检查字段长度
    print("\n4. 检查字段长度...")
    title_len = len(ai_title) if ai_title else 0
    summary_len = len(ai_summary) if ai_summary else 0

    print(f"  标题长度: {title_len} 字符")
    print(f"  摘要长度: {summary_len} 字符")

    if title_len <= 20 and summary_len <= 60:
        print("  ✓ 长度符合要求")
    else:
        print("  ⚠ 长度可能超出预期（但不影响功能）")

    print("\n" + "=" * 60)
    print("测试完成！功能正常工作 ✓")
    print("=" * 60)
    return True


def test_api_response():
    """测试API响应是否包含新字段"""
    print("\n" + "=" * 60)
    print("测试API响应格式")
    print("=" * 60)

    # 获取一个事件
    print("\n1. 获取事件列表...")
    events = db_manager.list_events(limit=1)

    if not events:
        print("  ⚠ 没有事件数据")
        return False

    event = events[0]
    print(f"  ✓ 获取到事件 ID={event['id']}")

    # 检查响应字段
    print("\n2. 检查响应字段...")
    has_ai_title = 'ai_title' in event
    has_ai_summary = 'ai_summary' in event

    print(f"  ai_title 字段: {'存在' if has_ai_title else '缺失'}")
    print(f"  ai_summary 字段: {'存在' if has_ai_summary else '缺失'}")

    if has_ai_title and has_ai_summary:
        print("  ✓ API响应格式正确")

        if event['ai_title']:
            print(f"\n  示例标题: {event['ai_title']}")
        if event['ai_summary']:
            print(f"  示例摘要: {event['ai_summary']}")

        return True
    else:
        print("  ✗ API响应缺少新字段")
        return False


def show_statistics():
    """显示摘要统计信息"""
    print("\n" + "=" * 60)
    print("事件摘要统计")
    print("=" * 60)

    with db_manager.get_session() as session:
        # 总事件数
        total = session.query(Event).count()

        # 已结束的事件
        finished = session.query(Event).filter(Event.end_time.isnot(None)).count()

        # 已生成摘要的事件
        with_summary = session.query(Event).filter(
            Event.ai_title.isnot(None),
            Event.ai_title != ''
        ).count()

        # 需要生成摘要的事件
        need_summary = session.query(Event).filter(
            Event.end_time.isnot(None),
            (Event.ai_title.is_(None)) | (Event.ai_title == '')
        ).count()

        print(f"\n总事件数: {total}")
        print(f"已结束事件: {finished}")
        print(f"已生成摘要: {with_summary}")
        print(f"需要生成: {need_summary}")

        if finished > 0:
            coverage = with_summary / finished * 100
            print(f"摘要覆盖率: {coverage:.1f}%")

        print("=" * 60)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='测试事件AI摘要功能')
    parser.add_argument('--stats-only', action='store_true', help='仅显示统计信息')
    args = parser.parse_args()

    if args.stats_only:
        show_statistics()
    else:
        # 显示统计
        show_statistics()

        # 运行测试
        print("\n\n")
        test_api_response()

        print("\n\n")
        test_event_summary_service()

        print("\n\n提示：")
        print("- 如果要批量生成历史事件摘要，运行：")
        print("  python -m lifetrace_backend.event_summary_commands generate-summaries")
        print("- 如果要查看详细统计，运行：")
        print("  python -m lifetrace_backend.event_summary_commands stats")
