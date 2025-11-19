"""上下文管理器 - 负责事件与任务关联相关的数据库操作"""

from datetime import datetime
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from lifetrace.storage.database_base import DatabaseBase
from lifetrace.storage.models import Event, EventTaskRelation, Task
from lifetrace.util.logging_config import get_logger

logger = get_logger()


class ContextManager:
    """上下文管理类 - 处理事件与任务的关联"""

    def __init__(self, db_base: DatabaseBase):
        self.db_base = db_base

    def list_contexts(
        self,
        associated: bool | None = None,
        task_id: int | None = None,
        project_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
        mapping_attempted: bool | None = None,
        used_in_summary: bool | None = None,
    ) -> list[dict[str, Any]]:
        """列出上下文记录（事件）

        Args:
            associated: 是否已关联任务（None表示全部，True表示已关联，False表示未关联）
            task_id: 按任务ID过滤
            project_id: 按项目ID过滤
            limit: 返回数量限制
            offset: 偏移量
            mapping_attempted: 是否已尝试过自动关联（None表示全部，True表示已尝试，False表示未尝试）
            used_in_summary: 是否已用于任务摘要（None表示全部，True表示已使用，False表示未使用）
        """
        try:
            with self.db_base.get_session() as session:
                # LEFT JOIN event_task_relations 以获取关联信息
                q = session.query(Event, EventTaskRelation).outerjoin(
                    EventTaskRelation, Event.id == EventTaskRelation.event_id
                )

                # 按关联状态过滤
                if associated is False:
                    q = q.filter(EventTaskRelation.task_id.is_(None))
                elif associated is True:
                    q = q.filter(EventTaskRelation.task_id.isnot(None))

                # 按任务ID过滤
                if task_id is not None:
                    q = q.filter(EventTaskRelation.task_id == task_id)

                # 按项目ID过滤
                if project_id is not None:
                    q = q.filter(EventTaskRelation.project_id == project_id)

                # 按自动关联尝试状态过滤
                if mapping_attempted is False:
                    q = q.filter(~Event.auto_association_attempted)
                elif mapping_attempted is True:
                    q = q.filter(Event.auto_association_attempted)

                # 按是否用于摘要过滤
                if used_in_summary is False:
                    q = q.filter(~EventTaskRelation.used_in_summary)
                elif used_in_summary is True:
                    q = q.filter(EventTaskRelation.used_in_summary)

                results = q.order_by(Event.start_time.desc()).offset(offset).limit(limit).all()

                return [
                    {
                        "id": e.id,
                        "app_name": e.app_name,
                        "window_title": e.window_title,
                        "start_time": e.start_time,
                        "end_time": e.end_time,
                        "ai_title": e.ai_title,
                        "ai_summary": e.ai_summary,
                        "task_id": assoc.task_id if assoc else None,
                        "project_id": assoc.project_id if assoc else None,
                        "created_at": e.created_at,
                        "auto_association_attempted": e.auto_association_attempted,
                    }
                    for e, assoc in results
                ]
        except SQLAlchemyError as e:
            logger.error(f"列出上下文记录失败: {e}")
            return []

    def count_contexts(
        self,
        associated: bool | None = None,
        task_id: int | None = None,
        project_id: int | None = None,
        mapping_attempted: bool | None = None,
        used_in_summary: bool | None = None,
    ) -> int:
        """统计上下文记录数量

        Args:
            associated: 是否已关联任务（None表示全部，True表示已关联，False表示未关联）
            task_id: 按任务ID过滤
            project_id: 按项目ID过滤
            mapping_attempted: 是否已尝试过自动关联（None表示全部，True表示已尝试，False表示未尝试）
            used_in_summary: 是否已用于任务摘要（None表示全部，True表示已使用，False表示未使用）
        """
        try:
            with self.db_base.get_session() as session:
                q = session.query(Event).outerjoin(
                    EventTaskRelation, Event.id == EventTaskRelation.event_id
                )

                if associated is False:
                    q = q.filter(EventTaskRelation.task_id.is_(None))
                elif associated is True:
                    q = q.filter(EventTaskRelation.task_id.isnot(None))

                if task_id is not None:
                    q = q.filter(EventTaskRelation.task_id == task_id)

                if project_id is not None:
                    q = q.filter(EventTaskRelation.project_id == project_id)

                if mapping_attempted is False:
                    q = q.filter(~Event.auto_association_attempted)
                elif mapping_attempted is True:
                    q = q.filter(Event.auto_association_attempted)

                if used_in_summary is False:
                    q = q.filter(~EventTaskRelation.used_in_summary)
                elif used_in_summary is True:
                    q = q.filter(EventTaskRelation.used_in_summary)

                return q.count()
        except SQLAlchemyError as e:
            logger.error(f"统计上下文记录数量失败: {e}")
            return 0

    def get_context(self, context_id: int) -> dict[str, Any] | None:
        """获取单个上下文记录"""
        try:
            with self.db_base.get_session() as session:
                result = (
                    session.query(Event, EventTaskRelation)
                    .outerjoin(EventTaskRelation, Event.id == EventTaskRelation.event_id)
                    .filter(Event.id == context_id)
                    .first()
                )

                if result:
                    event, assoc = result
                    return {
                        "id": event.id,
                        "app_name": event.app_name,
                        "window_title": event.window_title,
                        "start_time": event.start_time,
                        "end_time": event.end_time,
                        "ai_title": event.ai_title,
                        "ai_summary": event.ai_summary,
                        "task_id": assoc.task_id if assoc else None,
                        "project_id": assoc.project_id if assoc else None,
                        "created_at": event.created_at,
                    }
                return None
        except SQLAlchemyError as e:
            logger.error(f"获取上下文记录失败: {e}")
            return None

    def mark_context_as_used_in_summary(self, event_id: int) -> bool:
        """标记单个事件为已用于摘要

        Args:
            event_id: 事件ID

        Returns:
            是否成功
        """
        try:
            with self.db_base.get_session() as session:
                # 更新 event_task_relations 表
                updated = (
                    session.query(EventTaskRelation)
                    .filter(EventTaskRelation.event_id == event_id)
                    .update({EventTaskRelation.used_in_summary: True}, synchronize_session=False)
                )

                session.commit()
                if updated > 0:
                    logger.info(f"标记事件 {event_id} 为已用于摘要")
                return True

        except SQLAlchemyError as e:
            logger.error(f"标记事件为已用于摘要失败: {e}")
            return False

    def mark_contexts_used_in_summary(self, task_id: int, event_ids: list[int]) -> bool:
        """标记 event-task 关联为已用于摘要

        Args:
            task_id: 任务ID
            event_ids: 事件ID列表

        Returns:
            是否成功
        """
        try:
            with self.db_base.get_session() as session:
                # 批量更新 event_task_relations 表
                updated = (
                    session.query(EventTaskRelation)
                    .filter(
                        EventTaskRelation.task_id == task_id,
                        EventTaskRelation.event_id.in_(event_ids),
                    )
                    .update({EventTaskRelation.used_in_summary: True}, synchronize_session=False)
                )

                session.commit()
                logger.info(f"标记任务 {task_id} 的 {updated} 个事件关联为已用于摘要")
                return True

        except SQLAlchemyError as e:
            logger.error(f"标记事件关联为已用于摘要失败: {e}")
            return False

    def update_context_task(
        self, context_id: int, task_id: int | None, project_id: int | None = None
    ) -> bool:
        """更新上下文记录的任务关联

        注意：此方法已改为操作 event_task_relations 表

        Args:
            context_id: 上下文（事件）ID
            task_id: 任务ID（None表示解除关联）
            project_id: 项目ID（可选，如果不提供会从task推导）
        """
        try:
            with self.db_base.get_session() as session:
                event = session.query(Event).filter_by(id=context_id).first()
                if not event:
                    logger.warning(f"上下文记录不存在: {context_id}")
                    return False

                # 如果指定了task_id，验证任务是否存在并获取project_id
                if task_id is not None:
                    task = session.query(Task).filter_by(id=task_id).first()
                    if not task:
                        logger.warning(f"任务不存在: {task_id}")
                        return False
                    # 如果没有提供project_id，从task获取
                    if project_id is None:
                        project_id = task.project_id

                # 查找或创建关联记录
                assoc = session.query(EventTaskRelation).filter_by(event_id=context_id).first()
                if assoc:
                    # 更新现有关联
                    assoc.task_id = task_id
                    if project_id is not None:
                        assoc.project_id = project_id
                    assoc.association_method = "manual"
                    assoc.updated_at = datetime.now()
                else:
                    # 创建新关联
                    assoc = EventTaskRelation(
                        event_id=context_id,
                        task_id=task_id,
                        project_id=project_id,
                        association_method="manual",
                    )
                    session.add(assoc)

                session.flush()
                logger.info(
                    f"更新上下文记录 {context_id} 的任务关联: task_id={task_id}, project_id={project_id}"
                )
                return True
        except SQLAlchemyError as e:
            logger.error(f"更新上下文记录失败: {e}")
            return False

    def mark_context_mapping_attempted(self, context_id: int) -> bool:
        """标记上下文已尝试过自动关联

        无论自动关联成功与否，都应该调用此方法标记，避免重复处理浪费 token

        Args:
            context_id: 上下文（事件）ID

        Returns:
            是否成功标记
        """
        try:
            with self.db_base.get_session() as session:
                event = session.query(Event).filter_by(id=context_id).first()
                if not event:
                    logger.warning(f"上下文记录不存在: {context_id}")
                    return False

                event.auto_association_attempted = True
                session.flush()
                logger.debug(f"标记上下文 {context_id} 已尝试自动关联")
                return True
        except SQLAlchemyError as e:
            logger.error(f"标记上下文自动关联失败: {e}")
            return False

    def create_or_update_event_association(
        self,
        event_id: int,
        project_id: int | None = None,
        task_id: int | None = None,
        project_confidence: float | None = None,
        task_confidence: float | None = None,
        reasoning: str | None = None,
        association_method: str = "auto",
    ) -> bool:
        """创建或更新事件关联记录

        专门用于 task_context_mapper 保存 LLM 判断结果

        Args:
            event_id: 事件ID
            project_id: 项目ID
            task_id: 任务ID
            project_confidence: 项目判断置信度
            task_confidence: 任务判断置信度
            reasoning: LLM 判断理由
            association_method: 关联方式（auto/manual）

        Returns:
            是否成功
        """
        try:
            with self.db_base.get_session() as session:
                # 查找现有关联
                assoc = session.query(EventTaskRelation).filter_by(event_id=event_id).first()

                if assoc:
                    # 更新现有关联
                    if project_id is not None:
                        assoc.project_id = project_id
                    if task_id is not None:
                        assoc.task_id = task_id
                    if project_confidence is not None:
                        assoc.project_confidence = project_confidence
                    if task_confidence is not None:
                        assoc.task_confidence = task_confidence
                    if reasoning is not None:
                        assoc.reasoning = reasoning
                    assoc.association_method = association_method
                    assoc.updated_at = datetime.now()
                    logger.info(
                        f"更新事件关联: event_id={event_id}, project_id={project_id}, task_id={task_id}"
                    )
                else:
                    # 创建新关联
                    assoc = EventTaskRelation(
                        event_id=event_id,
                        project_id=project_id,
                        task_id=task_id,
                        project_confidence=project_confidence,
                        task_confidence=task_confidence,
                        reasoning=reasoning,
                        association_method=association_method,
                    )
                    session.add(assoc)
                    logger.info(
                        f"创建事件关联: event_id={event_id}, project_id={project_id}, task_id={task_id}"
                    )

                session.flush()
                return True
        except SQLAlchemyError as e:
            logger.error(f"创建或更新事件关联失败: {e}")
            return False
