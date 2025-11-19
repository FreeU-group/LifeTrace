"""项目管理器 - 负责项目相关的数据库操作"""

from datetime import datetime
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from lifetrace.storage.database_base import DatabaseBase
from lifetrace.storage.models import Project
from lifetrace.util.logging_config import get_logger

logger = get_logger()


class ProjectManager:
    """项目管理类"""

    def __init__(self, db_base: DatabaseBase):
        self.db_base = db_base

    def create_project(self, name: str, goal: str = None) -> int | None:
        """创建新项目"""
        try:
            with self.db_base.get_session() as session:
                project = Project(name=name, goal=goal)
                session.add(project)
                session.flush()
                logger.info(f"创建项目: {project.id} - {name}")
                return project.id
        except SQLAlchemyError as e:
            logger.error(f"创建项目失败: {e}")
            return None

    def get_project(self, project_id: int) -> dict[str, Any] | None:
        """获取单个项目"""
        try:
            with self.db_base.get_session() as session:
                project = session.query(Project).filter_by(id=project_id).first()
                if project:
                    return {
                        "id": project.id,
                        "name": project.name,
                        "goal": project.goal,
                        "created_at": project.created_at,
                        "updated_at": project.updated_at,
                    }
                return None
        except SQLAlchemyError as e:
            logger.error(f"获取项目失败: {e}")
            return None

    def list_projects(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """列出所有项目"""
        try:
            with self.db_base.get_session() as session:
                projects = (
                    session.query(Project)
                    .order_by(Project.created_at.desc())
                    .offset(offset)
                    .limit(limit)
                    .all()
                )
                return [
                    {
                        "id": p.id,
                        "name": p.name,
                        "goal": p.goal,
                        "created_at": p.created_at,
                        "updated_at": p.updated_at,
                    }
                    for p in projects
                ]
        except SQLAlchemyError as e:
            logger.error(f"列出项目失败: {e}")
            return []

    def update_project(self, project_id: int, name: str = None, goal: str = None) -> bool:
        """更新项目"""
        try:
            with self.db_base.get_session() as session:
                project = session.query(Project).filter_by(id=project_id).first()
                if not project:
                    logger.warning(f"项目不存在: {project_id}")
                    return False

                if name is not None:
                    project.name = name
                if goal is not None:
                    project.goal = goal

                project.updated_at = datetime.now()
                session.flush()
                logger.info(f"更新项目: {project_id}")
                return True
        except SQLAlchemyError as e:
            logger.error(f"更新项目失败: {e}")
            return False

    def delete_project(self, project_id: int) -> bool:
        """删除项目"""
        try:
            with self.db_base.get_session() as session:
                project = session.query(Project).filter_by(id=project_id).first()
                if not project:
                    logger.warning(f"项目不存在: {project_id}")
                    return False

                session.delete(project)
                session.flush()
                logger.info(f"删除项目: {project_id}")
                return True
        except SQLAlchemyError as e:
            logger.error(f"删除项目失败: {e}")
            return False
