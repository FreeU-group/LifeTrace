"""OCR管理器 - 负责OCR结果相关的数据库操作"""

from datetime import datetime
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from lifetrace.storage.database_base import DatabaseBase
from lifetrace.storage.models import OCRResult, Screenshot
from lifetrace.util.logging_config import get_logger

logger = get_logger()


class OCRManager:
    """OCR结果管理类"""

    def __init__(self, db_base: DatabaseBase):
        self.db_base = db_base

    def add_ocr_result(
        self,
        screenshot_id: int,
        text_content: str,
        confidence: float = 0.0,
        language: str = "ch",
        processing_time: float = 0.0,
    ) -> int | None:
        """添加OCR结果"""
        try:
            with self.db_base.get_session() as session:
                ocr_result = OCRResult(
                    screenshot_id=screenshot_id,
                    text_content=text_content,
                    confidence=confidence,
                    language=language,
                    processing_time=processing_time,
                )

                session.add(ocr_result)
                session.flush()

                # 更新截图处理状态
                screenshot = session.query(Screenshot).filter_by(id=screenshot_id).first()
                if screenshot:
                    screenshot.is_processed = True
                    screenshot.processed_at = datetime.now()

                logger.debug(f"添加OCR结果: {ocr_result.id}")
                return ocr_result.id

        except SQLAlchemyError as e:
            logger.error(f"添加OCR结果失败: {e}")
            return None

    def get_ocr_results_by_screenshot(self, screenshot_id: int) -> list[dict[str, Any]]:
        """根据截图ID获取OCR结果"""
        try:
            with self.db_base.get_session() as session:
                ocr_results = session.query(OCRResult).filter_by(screenshot_id=screenshot_id).all()

                # 转换为字典列表
                results = []
                for ocr in ocr_results:
                    results.append(
                        {
                            "id": ocr.id,
                            "screenshot_id": ocr.screenshot_id,
                            "text_content": ocr.text_content,
                            "confidence": ocr.confidence,
                            "language": ocr.language,
                            "processing_time": ocr.processing_time,
                            "created_at": ocr.created_at,
                        }
                    )

                return results

        except SQLAlchemyError as e:
            logger.error(f"获取OCR结果失败: {e}")
            return []
