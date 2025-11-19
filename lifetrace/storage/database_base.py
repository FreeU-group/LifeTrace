"""数据库基础管理器 - 负责数据库初始化和会话管理"""

import os
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from lifetrace.storage.models import Base
from lifetrace.util.config import config
from lifetrace.util.logging_config import get_logger
from lifetrace.util.utils import ensure_dir

logger = get_logger()


class DatabaseBase:
    """数据库基础管理类 - 处理数据库初始化和会话管理"""

    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._init_database()

    def _init_database(self):
        """初始化数据库"""
        try:
            # 检查数据库文件是否已存在
            db_exists = os.path.exists(config.database_path)

            # 确保数据库目录存在
            ensure_dir(os.path.dirname(config.database_path))

            # 创建引擎
            self.engine = create_engine(
                "sqlite:///" + config.database_path, echo=False, pool_pre_ping=True
            )

            # 创建会话工厂
            self.SessionLocal = sessionmaker(bind=self.engine)

            # 创建表
            Base.metadata.create_all(bind=self.engine)

            # 只在数据库不存在时（新创建）打印日志
            if not db_exists:
                logger.info(f"数据库初始化完成: {config.database_path}")

            # 性能优化：添加关键索引
            self._create_performance_indexes()

        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise

    def _create_performance_indexes(self):
        """创建性能优化索引"""
        try:
            with self.engine.connect() as conn:
                # 获取现有索引列表（只获取索引名称）
                existing_indexes = [
                    row[0]
                    for row in conn.execute(
                        text(
                            "SELECT name FROM sqlite_master WHERE type='index' AND name IS NOT NULL"
                        )
                    ).fetchall()
                ]
                # 定义需要创建的索引
                indexes_to_create = [
                    (
                        "idx_ocr_results_screenshot_id",
                        "CREATE INDEX IF NOT EXISTS idx_ocr_results_screenshot_id ON ocr_results(screenshot_id)",
                    ),
                    (
                        "idx_screenshots_created_at",
                        "CREATE INDEX IF NOT EXISTS idx_screenshots_created_at ON screenshots(created_at)",
                    ),
                    (
                        "idx_screenshots_app_name",
                        "CREATE INDEX IF NOT EXISTS idx_screenshots_app_name ON screenshots(app_name)",
                    ),
                    (
                        "idx_screenshots_event_id",
                        "CREATE INDEX IF NOT EXISTS idx_screenshots_event_id ON screenshots(event_id)",
                    ),
                ]

                # 创建索引
                created_count = 0
                for index_name, create_sql in indexes_to_create:
                    if index_name not in existing_indexes:
                        conn.execute(text(create_sql))
                        created_count += 1
                        logger.info(f"已创建性能索引: {index_name}")

                conn.commit()

                # 只在有索引被创建时打印完成信息
                if created_count > 0:
                    logger.info(f"性能索引检查完成，创建了 {created_count} 个索引")

        except Exception as e:
            logger.warning(f"创建性能索引失败: {e}")
            raise

    @contextmanager
    def get_session(self):
        """获取数据库会话上下文管理器"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            session.close()


# 数据库会话生成器（用于依赖注入）
def get_db(db_base: DatabaseBase):
    """获取数据库会话的生成器函数"""
    session = db_base.SessionLocal()
    try:
        yield session
    finally:
        session.close()
