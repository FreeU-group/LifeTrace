import json
import logging
import os
import sys
import threading
import time
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# 导入系统资源分析模块
import psutil
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from lifetrace_backend.app_icon_mapping import get_icon_filename
from lifetrace_backend.behavior_tracker import behavior_tracker
from lifetrace_backend.config import config
from lifetrace_backend.logging_config import setup_logging
from lifetrace_backend.multimodal_vector_service import create_multimodal_vector_service
from lifetrace_backend.rag_service import RAGService
from lifetrace_backend.simple_heartbeat import SimpleHeartbeatSender
from lifetrace_backend.simple_ocr import SimpleOCRProcessor
from lifetrace_backend.storage import db_manager
from lifetrace_backend.vector_service import create_vector_service

# 添加项目根目录到Python路径，以便直接运行此文件
if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

from fastapi.responses import RedirectResponse


# 导入系统资源分析模块
import sys

# 设置日志系统
logger_manager = setup_logging(config)
logger = logger_manager.get_server_logger()


# Pydantic模型
class SearchRequest(BaseModel):
    query: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    app_name: Optional[str] = None
    limit: int = 50


class ScreenshotResponse(BaseModel):
    id: int
    file_path: str
    app_name: Optional[str]
    window_title: Optional[str]
    created_at: datetime
    text_content: Optional[str]
    width: int
    height: int


class EventResponse(BaseModel):
    id: int
    app_name: Optional[str]
    window_title: Optional[str]
    start_time: datetime
    end_time: Optional[datetime]
    screenshot_count: int
    first_screenshot_id: Optional[int]
    ai_title: Optional[str] = None
    ai_summary: Optional[str] = None


class EventDetailResponse(BaseModel):
    id: int
    app_name: Optional[str]
    window_title: Optional[str]
    start_time: datetime
    end_time: Optional[datetime]
    screenshots: List[ScreenshotResponse]
    ai_title: Optional[str] = None
    ai_summary: Optional[str] = None


class StatisticsResponse(BaseModel):
    total_screenshots: int
    processed_screenshots: int
    pending_tasks: int
    today_screenshots: int
    processing_rate: float


class ConfigResponse(BaseModel):
    base_dir: str
    screenshots_dir: str
    database_path: str
    server: Dict[str, Any]
    record: Dict[str, Any]
    ocr: Dict[str, Any]
    storage: Dict[str, Any]


class SemanticSearchRequest(BaseModel):
    query: str
    top_k: int = 10
    use_rerank: bool = True
    retrieve_k: Optional[int] = None
    filters: Optional[Dict[str, Any]] = None


class SemanticSearchResult(BaseModel):
    text: str
    score: float
    metadata: Dict[str, Any]
    ocr_result: Optional[Dict[str, Any]] = None
    screenshot: Optional[Dict[str, Any]] = None


class MultimodalSearchRequest(BaseModel):
    query: str
    top_k: int = 10
    text_weight: Optional[float] = None
    image_weight: Optional[float] = None
    filters: Optional[Dict[str, Any]] = None


class MultimodalSearchResult(BaseModel):
    text: str
    combined_score: float
    text_score: float
    image_score: float
    text_weight: float
    image_weight: float
    metadata: Dict[str, Any]
    ocr_result: Optional[Dict[str, Any]] = None
    screenshot: Optional[Dict[str, Any]] = None


class VectorStatsResponse(BaseModel):
    enabled: bool
    collection_name: Optional[str] = None
    document_count: Optional[int] = None
    error: Optional[str] = None


class MultimodalStatsResponse(BaseModel):
    enabled: bool
    multimodal_available: bool
    text_weight: float
    image_weight: float
    text_database: Dict[str, Any]
    image_database: Dict[str, Any]
    error: Optional[str] = None


class ProcessInfo(BaseModel):
    pid: int
    name: str
    cmdline: str
    memory_mb: float
    memory_vms_mb: float
    cpu_percent: float


class SystemResourcesResponse(BaseModel):
    memory: Dict[str, float]
    cpu: Dict[str, Any]
    disk: Dict[str, Dict[str, float]]
    lifetrace_processes: List[ProcessInfo]
    storage: Dict[str, Any]
    summary: Dict[str, Any]
    timestamp: datetime


class ChatMessage(BaseModel):
    message: str


class ChatMessageWithContext(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    event_context: Optional[List[Dict[str, Any]]] = None  # 新增事件上下文


class ChatResponse(BaseModel):
    response: str
    timestamp: datetime
    query_info: Optional[Dict[str, Any]] = None
    retrieval_info: Optional[Dict[str, Any]] = None
    performance: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None


class NewChatRequest(BaseModel):
    session_id: Optional[str] = None


class NewChatResponse(BaseModel):
    session_id: str
    message: str
    timestamp: datetime


class BehaviorStatsResponse(BaseModel):
    behavior_records: List[Dict[str, Any]]
    daily_stats: List[Dict[str, Any]]
    action_distribution: Dict[str, int]
    hourly_activity: Dict[int, int]
    total_records: int


class DashboardStatsResponse(BaseModel):
    today_activity: Dict[str, int]
    weekly_trend: List[Dict[str, Any]]
    top_actions: List[Dict[str, Any]]
    performance_metrics: Dict[str, float]


class AppUsageStatsResponse(BaseModel):
    app_usage_summary: List[Dict[str, Any]]
    daily_app_usage: List[Dict[str, Any]]
    hourly_app_distribution: Dict[int, Dict[str, int]]
    top_apps_by_time: List[Dict[str, Any]]
    app_switching_patterns: List[Dict[str, Any]]
    total_apps_used: int
    total_usage_time: float

    class Config:
        arbitrary_types_allowed = True


# 创建FastAPI应用
app = FastAPI(
    title="LifeTrace API", description="智能生活记录系统 API", version="0.1.0"
)


# 确保响应使用UTF-8编码
class UTF8JSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(
            jsonable_encoder(content),
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")


# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8840",
        "http://127.0.0.1:8840",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 静态文件和模板
def get_resource_path(relative_path):
    """获取资源文件路径，兼容PyInstaller打包环境"""
    try:
        # PyInstaller创建临时文件夹，并将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# 尝试多个可能的模板路径
template_paths = [
    os.path.join(os.path.dirname(__file__), "templates"),  # 开发环境
    get_resource_path("lifetrace_backend/templates"),  # PyInstaller环境
    get_resource_path("templates"),  # 备用路径
]

static_paths = [
    os.path.join(os.path.dirname(__file__), "static"),  # 开发环境
    get_resource_path("lifetrace_backend/static"),  # PyInstaller环境
    get_resource_path("static"),  # 备用路径
]

# 查找存在的模板目录
templates_dir = None
for path in template_paths:
    if os.path.exists(path):
        templates_dir = path
        break

# 查找存在的静态文件目录
static_dir = None
for path in static_paths:
    if os.path.exists(path):
        static_dir = path
        break

if static_dir:
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 添加assets目录的静态文件访问
assets_paths = [
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets"),  # 开发环境
    get_resource_path("assets"),  # PyInstaller环境
]

assets_dir = None
for path in assets_paths:
    if os.path.exists(path):
        assets_dir = path
        break

if assets_dir:
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    print(f"Assets loaded from: {assets_dir}")

if templates_dir:
    templates = Jinja2Templates(directory=templates_dir)
    print(f"Templates loaded from: {templates_dir}")
else:
    templates = None
    print("No template directory found")

# 初始化OCR处理器
ocr_processor = SimpleOCRProcessor()

# 初始化向量数据库服务
vector_service = create_vector_service(config, db_manager)

# 初始化多模态向量数据库服务
multimodal_vector_service = create_multimodal_vector_service(config, db_manager)

# 初始化UDP心跳发送器
heartbeat_sender = SimpleHeartbeatSender("server")

# 初始化RAG服务 - 从配置文件读取API配置
rag_service = RAGService(
    db_manager=db_manager,
    api_key=config.llm_api_key,
    base_url=config.llm_base_url,
    model=config.llm_model,
)
logger.info(
    f"RAG服务初始化完成 - 模型: {config.llm_model}, Base URL: {config.llm_base_url}"
)

# 全局配置状态标志
is_llm_configured = config.is_configured()
logger.info(f"LLM配置状态: {'已配置' if is_llm_configured else '未配置，需要引导配置'}")

# 心跳任务控制
heartbeat_thread = None
heartbeat_stop_event = threading.Event()

# 会话管理
# 内存中的会话存储（生产环境建议使用Redis等持久化存储）
chat_sessions = defaultdict(
    dict
)  # session_id -> {"context": [], "created_at": datetime, "last_active": datetime}


def generate_session_id() -> str:
    """生成新的会话ID"""
    return str(uuid.uuid4())


def create_new_session(session_id: str = None) -> str:
    """创建新的聊天会话"""
    if not session_id:
        session_id = generate_session_id()

    chat_sessions[session_id] = {
        "context": [],
        "created_at": datetime.now(),
        "last_active": datetime.now(),
    }

    logger.info(f"创建新会话: {session_id}")
    return session_id


def clear_session_context(session_id: str) -> bool:
    """清除会话上下文"""
    if session_id in chat_sessions:
        chat_sessions[session_id]["context"] = []
        chat_sessions[session_id]["last_active"] = datetime.now()
        logger.info(f"清除会话上下文: {session_id}")
        return True
    return False


def get_session_context(session_id: str) -> List[Dict[str, Any]]:
    """获取会话上下文"""
    if session_id in chat_sessions:
        chat_sessions[session_id]["last_active"] = datetime.now()
        return chat_sessions[session_id]["context"]
    return []


def add_to_session_context(session_id: str, role: str, content: str):
    """添加消息到会话上下文"""
    if session_id not in chat_sessions:
        create_new_session(session_id)

    chat_sessions[session_id]["context"].append(
        {"role": role, "content": content, "timestamp": datetime.now()}
    )
    chat_sessions[session_id]["last_active"] = datetime.now()

    # 限制上下文长度，避免内存过度使用
    max_context_length = 50
    if len(chat_sessions[session_id]["context"]) > max_context_length:
        chat_sessions[session_id]["context"] = chat_sessions[session_id]["context"][
            -max_context_length:
        ]


def heartbeat_task_func():
    """心跳任务函数"""
    try:
        # 启动UDP心跳发送
        heartbeat_sender.start(interval=1.0)

        while not heartbeat_stop_event.is_set():
            # 获取系统资源信息
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()

            # 发送心跳（包含系统资源信息）
            heartbeat_sender.send_heartbeat(
                {
                    "status": "running",
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_used_mb": memory.used // (1024 * 1024),
                }
            )

            # 短暂休眠，避免过度占用CPU
            time.sleep(1.0)

    except KeyboardInterrupt:
        logger.info("收到停止信号，结束服务器心跳")
        heartbeat_sender.send_heartbeat(
            {"status": "stopped", "reason": "keyboard_interrupt"}
        )
    except Exception as e:
        logger.error(f"服务器心跳过程中发生错误: {e}")
        heartbeat_sender.send_heartbeat({"status": "error", "error": str(e)})
        # 不再重新抛出异常，避免导致服务器退出
    finally:
        logger.info("服务器心跳已停止")
        heartbeat_sender.stop()


def on_config_change(old_config: dict, new_config: dict):
    """配置变更回调函数"""
    global is_llm_configured, rag_service

    try:
        # 检查LLM配置是否变更
        old_llm = old_config.get("llm", {})
        new_llm = new_config.get("llm", {})

        if old_llm != new_llm:
            logger.info("检测到LLM配置变更")

            # 更新配置状态
            is_llm_configured = config.is_configured()
            logger.info(
                f"LLM配置状态已更新: {'已配置' if is_llm_configured else '未配置'}"
            )

            # 注意：根据计划，不重新初始化RAG服务
            logger.info("配置已更新，RAG服务将使用新配置（不重新初始化）")

        # 记录其他配置变更
        if old_config.get("server") != new_config.get("server"):
            logger.info("检测到服务器配置变更")

        if old_config.get("record") != new_config.get("record"):
            logger.info("检测到录制配置变更")

        if old_config.get("ocr") != new_config.get("ocr"):
            logger.info("检测到OCR配置变更")

    except Exception as e:
        logger.error(f"处理配置变更失败: {e}")


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    global heartbeat_thread
    logger.info("Web服务器启动，开始心跳记录")
    heartbeat_stop_event.clear()
    heartbeat_thread = threading.Thread(target=heartbeat_task_func, daemon=True)
    heartbeat_thread.start()

    # 启动配置文件监听
    config.register_callback(on_config_change)
    config.start_watching()
    logger.info("已启动配置文件监听")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    global heartbeat_thread
    logger.info("Web服务器关闭，停止心跳记录")
    heartbeat_stop_event.set()

    # 停止配置文件监听
    config.stop_watching()
    logger.info("已停止配置文件监听")


# 添加配置检测中间件
@app.middleware("http")
async def check_configuration_middleware(request: Request, call_next):
    """检查LLM配置状态，未配置时重定向到setup页面"""
    global is_llm_configured

    # 允许访问的路径（不需要LLM配置）
    allowed_paths = [
        "/setup",
        "/api/test-llm-config",
        "/api/save-and-init-llm",
        "/static",
        "/assets",
        "/api/get-config",
        "/api/save-config",
    ]

    # 如果未配置LLM
    if not is_llm_configured:
        path = request.url.path
        # 检查是否访问允许的路径
        if not any(path.startswith(allowed) for allowed in allowed_paths):
            # 重定向到setup页面
            return RedirectResponse(url="/setup", status_code=302)

    response = await call_next(request)
    return response


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """主页 - 聊天界面"""
    if templates:
        return templates.TemplateResponse("chat.html", {"request": request})
    else:
        return HTMLResponse(
            """
        <html>
            <head><title>LifeTrace Chat</title></head>
            <body>
                <h1>聊天功能暂不可用</h1>
                <p>模板文件未找到</p>
                <p><a href="/old_index">返回旧版首页</a></p>
            </body>
        </html>
        """
        )


@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    """聊天页面 - 重定向到主页"""
    if templates:
        return templates.TemplateResponse("chat.html", {"request": request})
    else:
        return HTMLResponse(
            """
        <html>
            <head><title>LifeTrace Chat</title></head>
            <body>
                <h1>聊天功能暂不可用</h1>
                <p>模板文件未找到</p>
                <p><a href="/">返回首页</a></p>
            </body>
        </html>
        """
        )


@app.get("/old_index", response_class=HTMLResponse)
async def old_index(request: Request):
    """旧版首页"""
    if templates:
        return templates.TemplateResponse("index.html", {"request": request})
    else:
        return HTMLResponse(
            """
        <html>
            <head><title>LifeTrace</title></head>
            <body>
                <h1>LifeTrace 智能生活记录系统</h1>
                <p><a href="/api/docs">API 文档</a></p>
                <p><a href="/api/screenshots">查看截图</a></p>
                <p><a href="/api/statistics">系统统计</a></p>
                <p><a href="/">智能聊天</a></p>
            </body>
        </html>
        """
        )


@app.get("/setup", response_class=HTMLResponse)
async def setup_page(request: Request):
    """初始配置引导页面"""
    if templates:
        return templates.TemplateResponse("setup.html", {"request": request})
    else:
        return HTMLResponse("<h1>配置页面加载失败</h1>")


@app.get("/chat/settings", response_class=HTMLResponse)
async def chat_settings_page(request: Request):
    """聊天设置页面"""
    if templates:
        return templates.TemplateResponse("settings.html", {"request": request})
    else:
        return HTMLResponse(
            """
        <html>
            <head><title>LifeTrace Settings</title></head>
            <body>
                <h1>设置页面暂不可用</h1>
                <p>模板文件未找到</p>
                <p><a href="/chat">返回聊天</a></p>
            </body>
        </html>
        """
        )


@app.get("/test-icons", response_class=HTMLResponse)
async def test_icons_page(request: Request):
    """图标测试页面"""
    if templates:
        return templates.TemplateResponse("test_icons.html", {"request": request})
    else:
        return HTMLResponse("<h1>测试页面未找到</h1>")


@app.get("/events", response_class=HTMLResponse)
async def events_page(request: Request):
    """事件管理页面"""
    if templates:
        return templates.TemplateResponse("events.html", {"request": request})
    else:
        return HTMLResponse(
            """
        <html>
            <head><title>LifeTrace Events</title></head>
            <body>
                <h1>事件管理页面暂不可用</h1>
                <p>模板文件未找到</p>
                <p><a href="/">返回首页</a></p>
            </body>
        </html>
        """
        )


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "database": "connected" if db_manager.engine else "disconnected",
        "ocr": "available" if ocr_processor.is_available() else "unavailable",
    }


@app.get("/api/statistics", response_model=StatisticsResponse)
async def get_statistics():
    """获取系统统计信息"""
    stats = db_manager.get_statistics()
    return StatisticsResponse(**stats)


@app.get("/api/config", response_model=ConfigResponse)
async def get_config():
    """获取配置信息"""
    return ConfigResponse(
        base_dir=config.base_dir,
        screenshots_dir=config.screenshots_dir,
        database_path=config.database_path,
        server={
            "host": config.get("server.host"),
            "port": config.get("server.port"),
            "debug": config.get("server.debug", False),
        },
        record={
            "interval": config.get("record.interval"),
            "screens": config.get("record.screens"),
            "format": config.get("record.format"),
        },
        ocr={
            "enabled": config.get("ocr.enabled"),
            "use_gpu": config.get("ocr.use_gpu"),
            "language": config.get("ocr.language"),
            "confidence_threshold": config.get("ocr.confidence_threshold"),
        },
        storage={
            "max_days": config.get("storage.max_days"),
            "deduplicate": config.get("storage.deduplicate"),
            "hash_threshold": config.get("storage.hash_threshold"),
        },
    )


@app.post("/api/test-llm-config")
async def test_llm_config(config_data: Dict[str, str]):
    """测试LLM配置是否可用（仅验证认证）"""
    try:
        from openai import OpenAI

        llm_key = config_data.get("llmKey", "")
        base_url = config_data.get("baseUrl", "")
        model = config_data.get("model", "qwen3-max")

        if not llm_key or not base_url:
            return {"success": False, "error": "LLM Key 和 Base URL 不能为空"}

        # 创建临时客户端进行测试
        client = OpenAI(api_key=llm_key, base_url=base_url)

        # 发送最小化测试请求验证认证
        response = client.chat.completions.create(  # noqa: F841
            model=model, messages=[{"role": "user", "content": "test"}], max_tokens=5
        )

        logger.info(f"LLM配置测试成功 - 模型: {model}")
        return {"success": True, "message": "配置验证成功"}

    except Exception as e:
        error_msg = str(e)
        logger.error(f"LLM配置测试失败: {error_msg}")
        return {"success": False, "error": error_msg}


@app.get("/api/get-config")
async def get_config():  # noqa: F811
    """获取当前配置"""
    try:
        return {
            "success": True,
            "config": {
                # UI配置
                "isDark": config.get("ui.dark_mode", False),
                "language": config.get("ui.language", "zh-CN"),
                "notifications": config.get("ui.notifications", True),
                "soundEnabled": config.get("ui.sound_enabled", True),
                "autoSave": config.get("ui.auto_save", True),
                # 录制配置
                "autoExcludeSelf": config.get("record.auto_exclude_self", True),
                "blacklistEnabled": config.get("record.blacklist.enabled", False),
                "blacklistApps": config.get("record.blacklist.apps", ""),
                "recordingEnabled": config.get("record.enabled", True),
                "recordInterval": config.get("record.interval", 1),
                "screenSelection": config.get("record.screens", "all"),
                # 存储配置
                "storageEnabled": config.get("storage.enabled", True),
                "maxDays": config.get("storage.max_days", 30),
                "deduplicateEnabled": config.get("storage.deduplicate", True),
                # LLM配置
                "llmKey": config.llm_api_key,
                "baseUrl": config.llm_base_url,
                "llmModel": config.llm_model,
                "model": config.llm_model,
                "temperature": config.llm_temperature,
                "maxTokens": config.llm_max_tokens,
                # 服务器配置
                "serverHost": config.server_host,
                "serverPort": config.server_port,
                # 聊天配置
                "localHistory": config.chat_local_history,
                "historyLimit": config.chat_history_limit,
            },
        }
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}") from e


@app.post("/api/save-and-init-llm")
async def save_and_init_llm(config_data: Dict[str, str]):
    """保存配置并重新初始化LLM服务"""
    global is_llm_configured, rag_service

    try:
        # 验证必需字段
        required_fields = ["llmKey", "baseUrl", "model"]
        missing_fields = [f for f in required_fields if not config_data.get(f)]
        if missing_fields:
            return {
                "success": False,
                "error": f"缺少必需字段: {', '.join(missing_fields)}",
            }

        # 验证字段类型和内容
        if (
            not isinstance(config_data.get("llmKey"), str)
            or not config_data.get("llmKey").strip()
        ):
            return {"success": False, "error": "LLM Key必须是非空字符串"}

        if (
            not isinstance(config_data.get("baseUrl"), str)
            or not config_data.get("baseUrl").strip()
        ):
            return {"success": False, "error": "Base URL必须是非空字符串"}

        if (
            not isinstance(config_data.get("model"), str)
            or not config_data.get("model").strip()
        ):
            return {"success": False, "error": "模型名称必须是非空字符串"}

        # 1. 先测试配置
        test_result = await test_llm_config(config_data)
        if not test_result["success"]:
            return test_result

        # 2. 保存配置到文件
        save_result = await save_config(
            {
                "llmKey": config_data.get("llmKey"),
                "baseUrl": config_data.get("baseUrl"),
                "llmModel": config_data.get("model"),
            }
        )

        if not save_result.get("success"):
            return {"success": False, "error": "保存配置失败"}

        # 3. 重新加载配置
        config._config = config._load_config()
        logger.info("配置已重新加载")

        # 4. 重新初始化RAG服务
        rag_service = RAGService(
            db_manager=db_manager,
            api_key=config.llm_api_key,
            base_url=config.llm_base_url,
            model=config.llm_model,
        )
        logger.info(f"RAG服务已重新初始化 - 模型: {config.llm_model}")

        # 5. 更新配置状态
        is_llm_configured = True
        logger.info("LLM配置状态已更新为：已配置")

        return {"success": True, "message": "配置保存成功，正在跳转..."}

    except Exception as e:
        error_msg = str(e)
        logger.error(f"保存并初始化LLM失败: {error_msg}")
        return {"success": False, "error": error_msg}


@app.post("/api/save-config")
async def save_config(settings: Dict[str, Any]):
    """保存配置到config.yaml文件"""
    try:
        import yaml

        # 读取当前配置文件
        config_path = config.config_path

        # 如果配置文件不存在，创建默认配置
        if not os.path.exists(config_path):
            config.save_config()

        # 读取现有配置
        with open(config_path, "r", encoding="utf-8") as f:
            current_config = yaml.safe_load(f) or {}

        # 更新配置项
        # 映射前端设置到配置文件结构
        config_mapping = {
            "isDark": "ui.dark_mode",
            "darkMode": "ui.dark_mode",
            "language": "ui.language",
            "blacklistEnabled": "record.blacklist.enabled",
            "blacklistApps": "record.blacklist.apps",
            "recordingEnabled": "record.enabled",
            "recordInterval": "record.interval",
            "screenSelection": "record.screens",
            "storageEnabled": "storage.enabled",
            "maxDays": "storage.max_days",
            "deduplicateEnabled": "storage.deduplicate",
            "model": "llm.model",
            "temperature": "llm.temperature",
            "maxTokens": "llm.max_tokens",
            "notifications": "ui.notifications",
            "soundEnabled": "ui.sound_enabled",
            "autoSave": "ui.auto_save",
            "localHistory": "chat.local_history",
            "historyLimit": "chat.history_limit",
            # API配置
            "llmKey": "llm.llm_key",
            "baseUrl": "llm.base_url",
            "llmModel": "llm.model",
            # 服务器配置
            "serverHost": "server.host",
            "serverPort": "server.port",
            "autoExcludeSelf": "record.auto_exclude_self",
        }

        # 更新配置
        for frontend_key, config_key in config_mapping.items():
            if frontend_key in settings:
                # 处理嵌套配置键
                keys = config_key.split(".")
                current = current_config
                for key in keys[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                current[keys[-1]] = settings[frontend_key]

        # 保存配置文件
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(current_config, f, allow_unicode=True, sort_keys=False)

        logger.info(f"配置已保存到: {config_path}")
        return {"success": True, "message": "配置保存成功"}

    except Exception as e:
        logger.error(f"保存配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"保存配置失败: {str(e)}") from e


@app.post("/api/chat", response_model=ChatResponse, response_class=UTF8JSONResponse)
async def chat_with_llm(message: ChatMessage, request: Request):
    """与LLM聊天接口 - 集成RAG功能"""
    start_time = datetime.now()
    session_id = None
    success = False

    try:
        logger.info(f"收到聊天消息: {message.message}")

        # 获取请求信息
        user_agent = request.headers.get("user-agent", "")
        client_ip = request.client.host if request.client else "unknown"

        # 使用RAG服务处理查询
        rag_result = await rag_service.process_query(message.message)

        # 计算响应时间
        response_time = (datetime.now() - start_time).total_seconds() * 1000

        if rag_result.get("success", False):
            success = True  # noqa: F841
            response = ChatResponse(
                response=rag_result["response"],
                timestamp=datetime.now(),
                query_info=rag_result.get("query_info"),
                retrieval_info=rag_result.get("retrieval_info"),
                performance=rag_result.get("performance"),
            )

            # 记录用户行为
            behavior_tracker.track_action(
                action_type="chat",
                action_details={
                    "query": message.message,
                    "response_length": len(rag_result["response"]),
                    "success": True,
                },
                session_id=session_id,
                user_agent=user_agent,
                ip_address=client_ip,
                response_time=response_time,
            )

            return response
        else:
            # 如果RAG处理失败，返回错误信息
            error_msg = rag_result.get(
                "response", "处理您的查询时出现了错误，请稍后重试。"
            )

            # 记录失败的用户行为
            behavior_tracker.track_action(
                action_type="chat",
                action_details={
                    "query": message.message,
                    "error": rag_result.get("error"),
                    "success": False,
                },
                session_id=session_id,
                user_agent=user_agent,
                ip_address=client_ip,
                response_time=response_time,
            )

            return ChatResponse(
                response=error_msg,
                timestamp=datetime.now(),
                query_info={
                    "original_query": message.message,
                    "error": rag_result.get("error"),
                },
            )

    except Exception as e:
        logger.error(f"聊天处理失败: {e}")

        # 记录异常的用户行为
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        behavior_tracker.track_action(
            action_type="chat",
            action_details={
                "query": message.message,
                "error": str(e),
                "success": False,
            },
            session_id=session_id,
            user_agent=request.headers.get("user-agent", "") if request else "",
            ip_address=request.client.host if request and request.client else "unknown",
            response_time=response_time,
        )

        return ChatResponse(
            response="抱歉，系统暂时无法处理您的请求，请稍后重试。",
            timestamp=datetime.now(),
            query_info={"original_query": message.message, "error": str(e)},
        )


# 新增：流式输出接口
@app.post("/api/chat/stream")
async def chat_with_llm_stream(message: ChatMessage):
    """与LLM聊天接口（流式输出）"""
    try:
        logger.info(f"[stream] 收到聊天消息: {message.message}")

        # 使用RAG服务的流式处理方法，避免重复的意图识别
        rag_result = await rag_service.process_query_stream(message.message)

        if not rag_result.get("success", False):
            # 如果RAG处理失败，返回错误信息
            error_msg = rag_result.get(
                "response", "处理您的查询时出现了错误，请稍后重试。"
            )

            async def error_generator():
                yield error_msg

            return StreamingResponse(
                error_generator(), media_type="text/plain; charset=utf-8"
            )

        # 获取构建好的messages和temperature
        messages = rag_result.get("messages", [])
        temperature = rag_result.get("temperature", 0.7)

        # 3) 调用LLM流式API并逐块返回
        def token_generator():
            try:
                if not rag_service.llm_client.is_available():
                    yield "抱歉，LLM服务当前不可用，请稍后重试。"
                    return

                # 使用LLM客户端进行流式生成
                response = rag_service.llm_client.client.chat.completions.create(
                    model=rag_service.llm_client.model,
                    messages=messages,
                    temperature=temperature,
                    stream=True,
                    stream_options={"include_usage": True},  # 请求包含usage信息
                )

                total_content = ""
                usage_info = None

                for chunk in response:
                    # 检查是否有usage信息（通常在最后一个chunk中）
                    if hasattr(chunk, "usage") and chunk.usage:
                        usage_info = chunk.usage

                    # 检查choices是否存在且不为空
                    if (
                        chunk.choices
                        and len(chunk.choices) > 0
                        and chunk.choices[0].delta.content
                    ):
                        content = chunk.choices[0].delta.content
                        total_content += content
                        yield content

                # 流式响应结束后记录token使用量
                if usage_info:
                    try:
                        from lifetrace_backend.token_usage_logger import log_token_usage

                        log_token_usage(
                            model=rag_service.llm_client.model,
                            input_tokens=usage_info.prompt_tokens,
                            output_tokens=usage_info.completion_tokens,
                            endpoint="stream_chat",
                            user_query=message.message,
                            response_type="stream",
                            additional_info={
                                "total_tokens": usage_info.total_tokens,
                                "temperature": temperature,
                                "response_length": len(total_content),
                            },
                        )
                        logger.info(
                            f"[stream] Token使用量已记录: input={usage_info.prompt_tokens}, output={usage_info.completion_tokens}"
                        )
                    except Exception as log_error:
                        logger.error(f"[stream] 记录token使用量失败: {log_error}")

            except Exception as e:
                logger.error(f"[stream] 生成失败: {e}")
                yield "\n[提示] 流式生成出现异常，已结束。"

        headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
        return StreamingResponse(
            token_generator(), media_type="text/plain; charset=utf-8", headers=headers
        )

    except Exception as e:
        logger.error(f"[stream] 聊天处理失败: {e}")
        raise HTTPException(status_code=500, detail="流式聊天处理失败")


@app.post("/api/chat/stream-with-context")
async def chat_with_context_stream(message: ChatMessageWithContext):
    """带事件上下文的流式聊天接口"""
    try:
        logger.info(
            f"[stream-with-context] 收到消息: {message.message}, 上下文事件数: {len(message.event_context or [])}"
        )

        # 构建上下文文本
        context_text = ""
        if message.event_context:
            context_parts = []
            for ctx in message.event_context:
                event_text = f"事件ID: {ctx['event_id']}\n{ctx['text']}\n"
                context_parts.append(event_text)
            context_text = "\n---\n".join(context_parts)

        # 构建带上下文的prompt
        if context_text:
            enhanced_message = f"""用户提供了以下事件上下文（来自屏幕记录的OCR文本）：

===== 事件上下文开始 =====
{context_text}
===== 事件上下文结束 =====

用户问题：{message.message}

请基于上述事件上下文回答用户问题。"""
        else:
            enhanced_message = message.message

        # 使用RAG服务的流式处理方法
        rag_result = await rag_service.process_query_stream(enhanced_message)

        if not rag_result.get("success", False):
            # 如果RAG处理失败，返回错误信息
            error_msg = rag_result.get(
                "response", "处理您的查询时出现了错误，请稍后重试。"
            )

            async def error_generator():
                yield error_msg

            return StreamingResponse(
                error_generator(), media_type="text/plain; charset=utf-8"
            )

        # 获取构建好的messages和temperature
        messages = rag_result.get("messages", [])
        temperature = rag_result.get("temperature", 0.7)

        # 调用LLM流式API并逐块返回
        def token_generator():
            try:
                if not rag_service.llm_client.is_available():
                    yield "抱歉，LLM服务当前不可用，请稍后重试。"
                    return

                # 使用LLM客户端进行流式生成
                response = rag_service.llm_client.client.chat.completions.create(
                    model=rag_service.llm_client.model,
                    messages=messages,
                    temperature=temperature,
                    stream=True,
                    stream_options={"include_usage": True},  # 请求包含usage信息
                )

                total_content = ""
                usage_info = None

                for chunk in response:
                    # 检查是否有usage信息（通常在最后一个chunk中）
                    if hasattr(chunk, "usage") and chunk.usage:
                        usage_info = chunk.usage

                    # 检查choices是否存在且不为空
                    if (
                        chunk.choices
                        and len(chunk.choices) > 0
                        and chunk.choices[0].delta.content
                    ):
                        content = chunk.choices[0].delta.content
                        total_content += content
                        yield content

                # 流式响应结束后记录token使用量
                if usage_info:
                    try:
                        from lifetrace_backend.token_usage_logger import log_token_usage

                        log_token_usage(
                            model=rag_service.llm_client.model,
                            input_tokens=usage_info.prompt_tokens,
                            output_tokens=usage_info.completion_tokens,
                            endpoint="stream_chat_with_context",
                            user_query=message.message,
                            response_type="stream",
                            additional_info={
                                "total_tokens": usage_info.total_tokens,
                                "temperature": temperature,
                                "response_length": len(total_content),
                                "context_events_count": len(
                                    message.event_context or []
                                ),
                            },
                        )
                        logger.info(
                            f"[stream-with-context] Token使用量已记录: input={usage_info.prompt_tokens}, output={usage_info.completion_tokens}"
                        )
                    except Exception as log_error:
                        logger.error(
                            f"[stream-with-context] 记录token使用量失败: {log_error}"
                        )

            except Exception as e:
                logger.error(f"[stream-with-context] 生成失败: {e}")
                yield "\n[提示] 流式生成出现异常，已结束。"

        headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
        return StreamingResponse(
            token_generator(), media_type="text/plain; charset=utf-8", headers=headers
        )

    except Exception as e:
        logger.error(f"[stream-with-context] 聊天处理失败: {e}")
        raise HTTPException(status_code=500, detail="带上下文的流式聊天处理失败")


@app.post(
    "/api/chat/new", response_model=NewChatResponse, response_class=UTF8JSONResponse
)
async def create_new_chat(request: NewChatRequest = None):
    """创建新对话会话"""
    try:
        # 如果提供了session_id，清除其上下文；否则创建新会话
        if request and request.session_id:
            if clear_session_context(request.session_id):
                session_id = request.session_id
                message = "会话上下文已清除"
            else:
                # 会话不存在，创建新的
                session_id = create_new_session()
                message = "创建新对话会话"
        else:
            session_id = create_new_session()
            message = "创建新对话会话"

        logger.info(f"新对话会话: {session_id}")
        return NewChatResponse(
            session_id=session_id, message=message, timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"创建新对话失败: {e}")
        raise HTTPException(status_code=500, detail="创建新对话失败")


@app.delete("/api/chat/session/{session_id}")
async def clear_chat_session(session_id: str):
    """清除指定会话的上下文"""
    try:
        success = clear_session_context(session_id)
        if success:
            return {
                "success": True,
                "message": f"会话 {session_id} 的上下文已清除",
                "timestamp": datetime.now(),
            }
        else:
            raise HTTPException(status_code=404, detail="会话不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清除会话上下文失败: {e}")
        raise HTTPException(status_code=500, detail="清除会话上下文失败")


@app.get("/api/chat/history")
async def get_chat_history(session_id: Optional[str] = Query(None)):
    """获取聊天历史记录"""
    try:
        if session_id:
            # 返回指定会话的历史记录
            context = get_session_context(session_id)
            return {
                "session_id": session_id,
                "history": context,
                "message": f"会话 {session_id} 的历史记录",
            }
        else:
            # 返回所有会话的摘要信息
            sessions_info = []
            for sid, session_data in chat_sessions.items():
                sessions_info.append(
                    {
                        "session_id": sid,
                        "created_at": session_data["created_at"],
                        "last_active": session_data["last_active"],
                        "message_count": len(session_data["context"]),
                    }
                )
            return {"sessions": sessions_info, "message": "所有会话摘要"}
    except Exception as e:
        logger.error(f"获取聊天历史失败: {e}")
        raise HTTPException(status_code=500, detail="获取聊天历史失败")


@app.get("/api/chat/suggestions")
async def get_query_suggestions(
    partial_query: str = Query("", description="部分查询文本"),
):
    """获取查询建议"""
    try:
        suggestions = rag_service.get_query_suggestions(partial_query)
        return {"suggestions": suggestions, "partial_query": partial_query}
    except Exception as e:
        logger.error(f"获取查询建议失败: {e}")
        raise HTTPException(status_code=500, detail="获取查询建议失败")


@app.get("/api/chat/query-types")
async def get_supported_query_types():
    """获取支持的查询类型"""
    try:
        return rag_service.get_supported_query_types()
    except Exception as e:
        logger.error(f"获取查询类型失败: {e}")
        raise HTTPException(status_code=500, detail="获取查询类型失败")


@app.get("/api/rag/health")
async def rag_health_check():
    """RAG服务健康检查"""
    try:
        return rag_service.health_check()
    except Exception as e:
        logger.error(f"RAG健康检查失败: {e}")
        return {
            "rag_service": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


@app.post("/api/search", response_model=List[ScreenshotResponse])
async def search_screenshots(search_request: SearchRequest, request: Request):
    """搜索截图"""
    start_time = datetime.now()

    try:
        # 获取请求信息
        user_agent = request.headers.get("user-agent", "")
        client_ip = request.client.host if request.client else "unknown"

        results = db_manager.search_screenshots(
            query=search_request.query,
            start_date=search_request.start_date,
            end_date=search_request.end_date,
            app_name=search_request.app_name,
            limit=search_request.limit,
        )

        # 计算响应时间
        response_time = (datetime.now() - start_time).total_seconds() * 1000

        # 记录用户行为
        behavior_tracker.track_action(
            action_type="search",
            action_details={
                "query": search_request.query,
                "app_name": search_request.app_name,
                "results_count": len(results),
                "limit": search_request.limit,
                "success": True,
            },
            user_agent=user_agent,
            ip_address=client_ip,
            response_time=response_time,
        )

        return [ScreenshotResponse(**result) for result in results]

    except Exception as e:
        logging.error(f"搜索截图失败: {e}")

        # 记录失败的用户行为
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        behavior_tracker.track_action(
            action_type="search",
            action_details={
                "query": search_request.query,
                "app_name": search_request.app_name,
                "error": str(e),
                "success": False,
            },
            user_agent=request.headers.get("user-agent", "") if request else "",
            ip_address=request.client.host if request and request.client else "unknown",
            response_time=response_time,
        )

        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/screenshots", response_model=List[ScreenshotResponse])
async def get_screenshots(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    app_name: Optional[str] = Query(None),
):
    """获取截图列表"""
    try:
        # 解析日期
        start_dt = None
        end_dt = None

        if start_date:
            start_dt = datetime.fromisoformat(start_date)
        if end_date:
            end_dt = datetime.fromisoformat(end_date)

        # 搜索截图 - 直接传递offset和limit给数据库查询
        results = db_manager.search_screenshots(
            start_date=start_dt,
            end_date=end_dt,
            app_name=app_name,
            limit=limit,
            offset=offset,  # 新增offset参数
        )

        return [ScreenshotResponse(**result) for result in results]

    except Exception as e:
        logging.error(f"获取截图列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/events", response_model=List[EventResponse])
async def list_events(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    app_name: Optional[str] = Query(None),
):
    """获取事件列表（事件=前台应用使用阶段），用于事件级别展示与检索"""
    try:
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        events = db_manager.list_events(
            limit=limit,
            offset=offset,
            start_date=start_dt,
            end_date=end_dt,
            app_name=app_name,
        )
        return [EventResponse(**e) for e in events]
    except Exception as e:
        logging.error(f"获取事件列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/events/{event_id}", response_model=EventDetailResponse)
async def get_event_detail(event_id: int):
    """获取事件详情（包含该事件下的截图列表）"""
    try:
        # 读取事件摘要
        event_summary = db_manager.get_event_summary(event_id)
        if not event_summary:
            raise HTTPException(status_code=404, detail="事件不存在")

        # 读取截图
        screenshots = db_manager.get_event_screenshots(event_id)
        screenshots_resp = [
            ScreenshotResponse(
                id=s["id"],
                file_path=s["file_path"],
                app_name=s["app_name"],
                window_title=s["window_title"],
                created_at=s["created_at"],
                text_content=None,
                width=s["width"],
                height=s["height"],
            )
            for s in screenshots
        ]

        return EventDetailResponse(
            id=event_summary["id"],
            app_name=event_summary["app_name"],
            window_title=event_summary["window_title"],
            start_time=event_summary["start_time"],
            end_time=event_summary["end_time"],
            screenshots=screenshots_resp,
            ai_title=event_summary.get("ai_title"),
            ai_summary=event_summary.get("ai_summary"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"获取事件详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/events/{event_id}/context")
async def get_event_context(event_id: int):
    """获取事件的OCR文本上下文"""
    try:
        # 获取事件信息
        event_summary = db_manager.get_event_summary(event_id)
        if not event_summary:
            raise HTTPException(status_code=404, detail="事件不存在")

        # 获取事件下所有截图
        screenshots = db_manager.get_event_screenshots(event_id)

        # 聚合OCR文本
        ocr_texts = []
        for screenshot in screenshots:
            ocr_results = db_manager.get_ocr_results_by_screenshot(screenshot["id"])
            if ocr_results:
                # 取第一个OCR结果的文本内容（通常一个截图只有一个OCR结果）
                for ocr in ocr_results:
                    if ocr.get("text_content"):
                        ocr_texts.append(ocr["text_content"])
                        break  # 只取第一个有内容的结果

        return {
            "event_id": event_id,
            "app_name": event_summary.get("app_name"),
            "window_title": event_summary.get("window_title"),
            "start_time": event_summary.get("start_time"),
            "end_time": event_summary.get("end_time"),
            "ocr_texts": ocr_texts,
            "screenshot_count": len(screenshots),
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"获取事件上下文失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/events/{event_id}/generate-summary")
async def generate_event_summary(event_id: int):
    """手动触发单个事件的摘要生成"""
    try:
        from lifetrace_backend.event_summary_service import event_summary_service

        # 检查事件是否存在
        event_info = db_manager.get_event_summary(event_id)
        if not event_info:
            raise HTTPException(status_code=404, detail="事件不存在")

        # 生成摘要
        success = event_summary_service.generate_event_summary(event_id)

        if success:
            # 获取更新后的事件信息
            updated_event = db_manager.get_event_summary(event_id)
            return {
                "success": True,
                "event_id": event_id,
                "ai_title": updated_event.get("ai_title"),
                "ai_summary": updated_event.get("ai_summary"),
            }
        else:
            raise HTTPException(status_code=500, detail="摘要生成失败")

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"生成事件摘要失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/event-search", response_model=List[EventResponse])
async def search_events(search_request: SearchRequest):
    """事件级简单文本搜索：按OCR分组后返回事件摘要"""
    try:
        results = db_manager.search_events_simple(
            query=search_request.query, limit=search_request.limit
        )
        return [EventResponse(**r) for r in results]
    except Exception as e:
        logging.error(f"搜索事件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/screenshots/{screenshot_id}")
async def get_screenshot(screenshot_id: int):
    """获取单个截图详情"""
    screenshot = db_manager.get_screenshot_by_id(screenshot_id)

    if not screenshot:
        raise HTTPException(status_code=404, detail="截图不存在")

    # 获取OCR结果
    ocr_data = None
    try:
        with db_manager.get_session() as session:
            from lifetrace_backend.models import OCRResult

            ocr_result = (
                session.query(OCRResult).filter_by(screenshot_id=screenshot_id).first()
            )

            # 在session内提取数据
            if ocr_result:
                ocr_data = {
                    "text_content": ocr_result.text_content,
                    "confidence": ocr_result.confidence,
                    "language": ocr_result.language,
                    "processing_time": ocr_result.processing_time,
                }
    except Exception as e:
        logging.warning(f"获取OCR结果失败: {e}")

    # screenshot已经是字典格式，直接使用
    result = screenshot.copy()
    result["ocr_result"] = ocr_data

    return result


@app.get("/api/screenshots/{screenshot_id}/image")
async def get_screenshot_image(screenshot_id: int, request: Request):
    """获取截图图片文件"""
    start_time = time.time()

    try:
        screenshot = db_manager.get_screenshot_by_id(screenshot_id)

        if not screenshot:
            # 记录失败的查看截图行为
            behavior_tracker.track_action(
                action_type="view_screenshot",
                action_details={
                    "screenshot_id": screenshot_id,
                    "success": False,
                    "error": "截图不存在",
                },
                user_agent=request.headers.get("user-agent", ""),
                ip_address=request.client.host if request.client else "",
                response_time=time.time() - start_time,
            )
            raise HTTPException(status_code=404, detail="截图不存在")

        file_path = screenshot["file_path"]
        if not os.path.exists(file_path):
            # 记录失败的查看截图行为
            behavior_tracker.track_action(
                action_type="view_screenshot",
                action_details={
                    "screenshot_id": screenshot_id,
                    "success": False,
                    "error": "图片文件不存在",
                },
                user_agent=request.headers.get("user-agent", ""),
                ip_address=request.client.host if request.client else "",
                response_time=time.time() - start_time,
            )
            raise HTTPException(status_code=404, detail="图片文件不存在")

        # 记录成功的查看截图行为
        behavior_tracker.track_action(
            action_type="view_screenshot",
            action_details={
                "screenshot_id": screenshot_id,
                "app_name": screenshot.get("app_name", ""),
                "window_title": screenshot.get("window_title", ""),
                "success": True,
            },
            user_agent=request.headers.get("user-agent", ""),
            ip_address=request.client.host if request.client else "",
            response_time=time.time() - start_time,
        )

        return FileResponse(
            file_path,
            media_type="image/png",
            filename=f"screenshot_{screenshot_id}.png",
        )

    except HTTPException:
        raise
    except Exception as e:
        # 记录异常的查看截图行为
        behavior_tracker.track_action(
            action_type="view_screenshot",
            action_details={
                "screenshot_id": screenshot_id,
                "success": False,
                "error": str(e),
            },
            user_agent=request.headers.get("user-agent", ""),
            ip_address=request.client.host if request.client else "",
            response_time=time.time() - start_time,
        )
        logger.error(f"获取截图图像时发生错误: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@app.get("/api/screenshots/{screenshot_id}/path")
async def get_screenshot_path(screenshot_id: int):
    """获取截图文件路径"""
    screenshot = db_manager.get_screenshot_by_id(screenshot_id)

    if not screenshot:
        raise HTTPException(status_code=404, detail="截图不存在")

    file_path = screenshot["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="图片文件不存在")

    return {"screenshot_id": screenshot_id, "file_path": file_path, "exists": True}


@app.get("/api/app-icon/{app_name}")
async def get_app_icon(app_name: str):
    """
    获取应用图标
    根据映射表返回对应的图标文件

    Args:
        app_name: 应用名称

    Returns:
        图标文件
    """
    try:
        # 根据映射表获取图标文件名
        icon_filename = get_icon_filename(app_name)

        if not icon_filename:
            raise HTTPException(status_code=404, detail="图标未找到")

        # 构建图标文件路径
        # 获取项目根目录
        current_dir = Path(__file__).parent
        project_root = current_dir.parent
        icon_path = project_root / "assets" / "icons" / "apps" / icon_filename

        if not icon_path.exists():
            logger.warning(f"图标文件不存在: {icon_path}")
            raise HTTPException(status_code=404, detail="图标文件不存在")

        # 返回图标文件
        return FileResponse(
            str(icon_path),
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=86400"},  # 缓存1天
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取应用图标失败 {app_name}: {e}")
        raise HTTPException(status_code=500, detail=f"获取图标失败: {str(e)}")


@app.post("/api/ocr/process")
async def process_ocr(screenshot_id: int):
    """手动触发OCR处理"""
    if not ocr_processor.is_available():
        raise HTTPException(status_code=503, detail="OCR服务不可用")

    screenshot = db_manager.get_screenshot_by_id(screenshot_id)
    if not screenshot:
        raise HTTPException(status_code=404, detail="截图不存在")

    if screenshot["is_processed"]:
        raise HTTPException(status_code=400, detail="截图已经处理过")

    try:
        # 执行OCR处理
        ocr_result = ocr_processor.process_image(screenshot["file_path"])

        if ocr_result["success"]:
            # 保存OCR结果
            db_manager.add_ocr_result(
                screenshot_id=screenshot["id"],
                text_content=ocr_result["text_content"],
                confidence=ocr_result["confidence"],
                language=ocr_result.get("language", "ch"),
                processing_time=ocr_result["processing_time"],
            )

            return {
                "success": True,
                "text_content": ocr_result["text_content"],
                "confidence": ocr_result["confidence"],
                "processing_time": ocr_result["processing_time"],
            }
        else:
            raise HTTPException(status_code=500, detail=ocr_result["error"])

    except Exception as e:
        logging.error(f"OCR处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ocr/statistics")
async def get_ocr_statistics():
    """获取OCR处理统计"""
    return ocr_processor.get_statistics()


@app.post("/api/cleanup")
async def cleanup_old_data(days: int = Query(30, ge=1)):
    """清理旧数据"""
    try:
        db_manager.cleanup_old_data(days)
        return {"success": True, "message": f"清理了 {days} 天前的数据"}
    except Exception as e:
        logging.error(f"清理数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/queue/status")
async def get_queue_status():
    """获取处理队列状态"""
    try:
        with db_manager.get_session() as session:
            from lifetrace_backend.models import ProcessingQueue

            pending_count = (
                session.query(ProcessingQueue).filter_by(status="pending").count()
            )
            processing_count = (
                session.query(ProcessingQueue).filter_by(status="processing").count()
            )
            completed_count = (
                session.query(ProcessingQueue).filter_by(status="completed").count()
            )
            failed_count = (
                session.query(ProcessingQueue).filter_by(status="failed").count()
            )

            return {
                "pending": pending_count,
                "processing": processing_count,
                "completed": completed_count,
                "failed": failed_count,
                "total": pending_count
                + processing_count
                + completed_count
                + failed_count,
            }

    except Exception as e:
        logging.error(f"获取队列状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/semantic-search", response_model=List[SemanticSearchResult])
async def semantic_search(request: SemanticSearchRequest):
    """语义搜索 OCR 结果"""
    try:
        if not vector_service.is_enabled():
            raise HTTPException(status_code=503, detail="向量数据库服务不可用")

        results = vector_service.semantic_search(
            query=request.query,
            top_k=request.top_k,
            use_rerank=request.use_rerank,
            retrieve_k=request.retrieve_k,
            filters=request.filters,
        )

        # 转换为响应格式
        search_results = []
        for result in results:
            search_result = SemanticSearchResult(
                text=result.get("text", ""),
                score=result.get("score", 0.0),
                metadata=result.get("metadata", {}),
                ocr_result=result.get("ocr_result"),
                screenshot=result.get("screenshot"),
            )
            search_results.append(search_result)

        return search_results

    except Exception as e:
        logging.error(f"语义搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/event-semantic-search", response_model=List[EventResponse])
async def event_semantic_search(request: SemanticSearchRequest):
    """事件级语义搜索（基于事件聚合文本）"""
    try:
        if not vector_service.is_enabled():
            raise HTTPException(status_code=503, detail="向量数据库服务不可用")
        raw_results = vector_service.semantic_search_events(
            query=request.query, top_k=request.top_k
        )

        # semantic_search_events 现在直接返回格式化的事件数据
        events_resp: List[EventResponse] = []
        for event_data in raw_results:
            # 检查是否已经是完整的事件数据格式
            if "id" in event_data and "app_name" in event_data:
                # 直接使用返回的事件数据
                events_resp.append(EventResponse(**event_data))
            else:
                # 向后兼容：如果是旧格式，使用原来的逻辑
                metadata = event_data.get("metadata", {})
                event_id = metadata.get("event_id")
                if not event_id:
                    continue
                matched = db_manager.get_event_summary(int(event_id))
                if matched:
                    events_resp.append(EventResponse(**matched))

        return events_resp
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"事件语义搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/multimodal-search", response_model=List[MultimodalSearchResult])
async def multimodal_search(request: MultimodalSearchRequest):
    """多模态搜索 (图像+文本)"""
    try:
        if not multimodal_vector_service.is_enabled():
            raise HTTPException(status_code=503, detail="多模态向量数据库服务不可用")

        results = multimodal_vector_service.multimodal_search(
            query=request.query,
            top_k=request.top_k,
            text_weight=request.text_weight,
            image_weight=request.image_weight,
            filters=request.filters,
        )

        # 转换为响应格式
        search_results = []
        for result in results:
            search_result = MultimodalSearchResult(
                text=result.get("text", ""),
                combined_score=result.get("combined_score", 0.0),
                text_score=result.get("text_score", 0.0),
                image_score=result.get("image_score", 0.0),
                text_weight=result.get("text_weight", 0.6),
                image_weight=result.get("image_weight", 0.4),
                metadata=result.get("metadata", {}),
                ocr_result=result.get("ocr_result"),
                screenshot=result.get("screenshot"),
            )
            search_results.append(search_result)

        return search_results

    except Exception as e:
        logging.error(f"多模态搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/vector-stats", response_model=VectorStatsResponse)
async def get_vector_stats():
    """获取向量数据库统计信息"""
    try:
        stats = vector_service.get_stats()
        return VectorStatsResponse(**stats)

    except Exception as e:
        logging.error(f"获取向量数据库统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/multimodal-stats", response_model=MultimodalStatsResponse)
async def get_multimodal_stats():
    """获取多模态向量数据库统计信息"""
    try:
        stats = multimodal_vector_service.get_stats()
        return MultimodalStatsResponse(**stats)

    except Exception as e:
        logging.error(f"获取多模态统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/multimodal-sync")
async def sync_multimodal_database(
    limit: Optional[int] = Query(None, description="同步的最大记录数"),
    force_reset: bool = Query(False, description="是否强制重置多模态向量数据库"),
):
    """同步 SQLite 数据库到多模态向量数据库"""
    try:
        if not multimodal_vector_service.is_enabled():
            raise HTTPException(status_code=503, detail="多模态向量数据库服务不可用")

        synced_count = multimodal_vector_service.sync_from_database(
            limit=limit, force_reset=force_reset
        )

        return {"message": "多模态同步完成", "synced_count": synced_count}

    except Exception as e:
        logging.error(f"多模态同步失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/vector-sync")
async def sync_vector_database(
    limit: Optional[int] = Query(None, description="同步的最大记录数"),
    force_reset: bool = Query(False, description="是否强制重置向量数据库"),
):
    """同步 SQLite 数据库到向量数据库"""
    try:
        if not vector_service.is_enabled():
            raise HTTPException(status_code=503, detail="向量数据库服务不可用")

        synced_count = vector_service.sync_from_database(
            limit=limit, force_reset=force_reset
        )

        return {"message": "同步完成", "synced_count": synced_count}

    except Exception as e:
        logging.error(f"向量数据库同步失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/vector-reset")
async def reset_vector_database():
    """重置向量数据库"""
    try:
        if not vector_service.is_enabled():
            raise HTTPException(status_code=503, detail="向量数据库服务不可用")

        success = vector_service.reset()

        if success:
            return {"message": "向量数据库重置成功"}
        else:
            raise HTTPException(status_code=500, detail="向量数据库重置失败")

    except Exception as e:
        logging.error(f"向量数据库重置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 系统资源监控路由
@app.get("/system-monitor", response_class=HTMLResponse)
async def system_monitor_page(request: Request):
    """系统资源监控页面"""
    # 直接返回HTML内容，不使用模板
    return HTMLResponse(
        """
        <!DOCTYPE html>
        <html>
        <head>
            <title>LifeTrace 系统资源监控</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; }
                .card { background: white; border-radius: 8px; padding: 20px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .header { text-align: center; color: #333; }
                .metric { display: inline-block; margin: 10px; padding: 15px; background: #f8f9fa; border-radius: 5px; min-width: 150px; }
                .metric-value { font-size: 24px; font-weight: bold; color: #007bff; }
                .metric-label { font-size: 14px; color: #666; }
                .process-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
                .process-table th, .process-table td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
                .process-table th { background-color: #f8f9fa; }
                .status-good { color: #28a745; }
                .status-warning { color: #ffc107; }
                .status-danger { color: #dc3545; }
                .refresh-btn { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
                .refresh-btn:hover { background: #0056b3; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="header">LifeTrace 系统资源监控</h1>
                <div class="card">
                    <button class="refresh-btn" onclick="loadSystemResources()">刷新数据</button>
                    <div id="system-resources">加载中...</div>
                </div>
            </div>
            <script>
                async function loadSystemResources() {
                    try {
                        const response = await fetch('/api/system-resources');
                        const data = await response.json();
                        displaySystemResources(data);
                    } catch (error) {
                        document.getElementById('system-resources').innerHTML = '<p style="color: red;">加载失败: ' + error.message + '</p>';
                    }
                }

                function displaySystemResources(data) {
                    const container = document.getElementById('system-resources');
                    const timestamp = new Date(data.timestamp).toLocaleString('zh-CN');

                    let html = `
                        <p><strong>更新时间:</strong> ${timestamp}</p>

                        <h3>系统整体资源</h3>
                        <div>
                            <div class="metric">
                                <div class="metric-value">${data.memory.percent.toFixed(1)}%</div>
                                <div class="metric-label">内存使用率</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${data.memory.used_gb.toFixed(1)}GB</div>
                                <div class="metric-label">已用内存</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${data.cpu.percent.toFixed(1)}%</div>
                                <div class="metric-label">CPU使用率</div>
                            </div>
                        </div>

                        <h3>LifeTrace 进程 (${data.lifetrace_processes.length}个)</h3>
                        <table class="process-table">
                            <thead>
                                <tr>
                                    <th>PID</th>
                                    <th>进程名</th>
                                    <th>内存(MB)</th>
                                    <th>CPU(%)</th>
                                    <th>命令行</th>
                                </tr>
                            </thead>
                            <tbody>`;

                    data.lifetrace_processes.forEach(proc => {
                        const memoryClass = proc.memory_mb > 500 ? 'status-danger' : proc.memory_mb > 200 ? 'status-warning' : 'status-good';
                        const cpuClass = proc.cpu_percent > 50 ? 'status-danger' : proc.cpu_percent > 20 ? 'status-warning' : 'status-good';

                        html += `
                            <tr>
                                <td>${proc.pid}</td>
                                <td>${proc.name}</td>
                                <td class="${memoryClass}">${proc.memory_mb.toFixed(1)}</td>
                                <td class="${cpuClass}">${proc.cpu_percent.toFixed(1)}</td>
                                <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis;">${proc.cmdline}</td>
                            </tr>`;
                    });

                    html += `
                            </tbody>
                        </table>

                        <h3>资源使用总结</h3>
                        <div>
                            <div class="metric">
                                <div class="metric-value">${data.summary.total_memory_mb.toFixed(1)}MB</div>
                                <div class="metric-label">LifeTrace总内存</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${data.summary.total_cpu_percent.toFixed(1)}%</div>
                                <div class="metric-label">LifeTrace总CPU</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${data.summary.total_storage_mb.toFixed(1)}MB</div>
                                <div class="metric-label">数据存储</div>
                            </div>
                        </div>

                        <h3>磁盘使用情况</h3>
                        <table class="process-table">
                            <thead>
                                <tr>
                                    <th>磁盘</th>
                                    <th>总容量(GB)</th>
                                    <th>已用(GB)</th>
                                    <th>可用(GB)</th>
                                    <th>使用率</th>
                                </tr>
                            </thead>
                            <tbody>`;

                    Object.entries(data.disk).forEach(([device, usage]) => {
                        const percentClass = usage.percent > 90 ? 'status-danger' : usage.percent > 70 ? 'status-warning' : 'status-good';
                        html += `
                            <tr>
                                <td>${device}</td>
                                <td>${usage.total_gb.toFixed(1)}</td>
                                <td>${usage.used_gb.toFixed(1)}</td>
                                <td>${usage.free_gb.toFixed(1)}</td>
                                <td class="${percentClass}">${usage.percent.toFixed(1)}%</td>
                            </tr>`;
                    });

                    html += `
                            </tbody>
                        </table>`;

                    container.innerHTML = html;
                }

                // 页面加载时自动刷新数据
                loadSystemResources();

                // 每30秒自动刷新
                setInterval(loadSystemResources, 30000);
            </script>
        </body>
        </html>
        """
    )


@app.get("/api/system-resources", response_model=SystemResourcesResponse)
async def get_system_resources():
    """获取系统资源使用情况"""
    try:
        # 获取LifeTrace相关进程
        lifetrace_processes = []
        total_memory = 0
        total_cpu = 0

        for proc in psutil.process_iter(["pid", "name", "cmdline", "memory_info"]):
            try:
                cmdline = " ".join(proc.info["cmdline"]) if proc.info["cmdline"] else ""

                if any(
                    keyword in cmdline.lower()
                    for keyword in [
                        "lifetrace",
                        "recorder.py",
                        "processor.py",
                        "server.py",
                        "start_all_services.py",
                    ]
                ):
                    # 使用非阻塞的CPU百分比获取，避免卡死
                    try:
                        cpu_percent = proc.cpu_percent(interval=None)  # 非阻塞调用
                    except:  # noqa: E722
                        cpu_percent = 0.0
                    memory_mb = proc.info["memory_info"].rss / 1024 / 1024
                    memory_vms_mb = proc.info["memory_info"].vms / 1024 / 1024

                    process_info = ProcessInfo(
                        pid=proc.info["pid"],
                        name=proc.info["name"],
                        cmdline=cmdline,
                        memory_mb=memory_mb,
                        memory_vms_mb=memory_vms_mb,
                        cpu_percent=cpu_percent,
                    )
                    lifetrace_processes.append(process_info)
                    total_memory += memory_mb
                    total_cpu += cpu_percent

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        # 获取系统资源信息
        memory = psutil.virtual_memory()
        # 使用非阻塞的CPU百分比获取，避免卡死
        cpu_percent = psutil.cpu_percent(interval=None)  # 非阻塞调用
        cpu_count = psutil.cpu_count()

        # 获取磁盘信息
        disk_usage = {}
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_usage[partition.device] = {
                    "total_gb": usage.total / 1024**3,
                    "used_gb": usage.used / 1024**3,
                    "free_gb": usage.free / 1024**3,
                    "percent": (usage.used / usage.total) * 100,
                }
            except PermissionError:
                continue

        # 获取数据库和截图存储信息
        db_path = Path(config.database_path)
        db_size_mb = db_path.stat().st_size / 1024 / 1024 if db_path.exists() else 0

        screenshots_path = Path(config.screenshots_dir)
        screenshots_size_mb = 0
        screenshots_count = 0
        if screenshots_path.exists():
            for file_path in screenshots_path.glob("*.png"):
                if file_path.is_file():
                    screenshots_size_mb += file_path.stat().st_size / 1024 / 1024
                    screenshots_count += 1

        total_storage_mb = db_size_mb + screenshots_size_mb

        return SystemResourcesResponse(
            memory={
                "total_gb": memory.total / 1024**3,
                "available_gb": memory.available / 1024**3,
                "used_gb": (memory.total - memory.available) / 1024**3,
                "percent": memory.percent,
            },
            cpu={"percent": cpu_percent, "count": cpu_count},
            disk=disk_usage,
            lifetrace_processes=lifetrace_processes,
            storage={
                "database_mb": db_size_mb,
                "screenshots_mb": screenshots_size_mb,
                "screenshots_count": screenshots_count,
                "total_mb": total_storage_mb,
            },
            summary={
                "total_memory_mb": total_memory,
                "total_cpu_percent": total_cpu,
                "process_count": len(lifetrace_processes),
                "total_storage_mb": total_storage_mb,
            },
            timestamp=datetime.now(),
        )

    except Exception as e:
        logging.error(f"获取系统资源信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 日志查看路由
@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    """日志查看页面"""
    if templates is not None:
        return templates.TemplateResponse("logs.html", {"request": request})
    else:
        return HTMLResponse("<h1>模板系统未初始化</h1>", status_code=500)


@app.get("/api/logs/files")
async def get_log_files():
    """获取日志文件列表"""
    try:
        # 使用配置中的日志目录
        logs_dir = Path(config.base_dir) / "logs"
        if not logs_dir.exists():
            return []

        log_files = []
        # 递归扫描所有子目录中的.log文件
        for file_path in logs_dir.rglob("*.log"):
            # 获取相对于logs目录的路径
            relative_path = file_path.relative_to(logs_dir)
            # 获取文件大小
            file_size = file_path.stat().st_size
            size_str = f"{file_size // 1024}KB" if file_size > 1024 else f"{file_size}B"

            log_files.append(
                {
                    "name": str(relative_path),
                    "path": str(file_path),
                    "size": size_str,
                    "category": relative_path.parent.name
                    if relative_path.parent.name != "."
                    else "root",
                }
            )

        return sorted(log_files, key=lambda x: x["name"])
    except Exception as e:
        logger.error(f"获取日志文件列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/logs/content", response_class=PlainTextResponse)
async def get_log_content(file: str = Query(..., description="日志文件相对路径")):
    """获取日志文件内容"""
    try:
        # 使用配置中的日志目录
        logs_dir = Path(config.base_dir) / "logs"

        log_file = logs_dir / file

        # 安全检查：确保文件在logs目录内
        if not str(log_file.resolve()).startswith(str(logs_dir.resolve())):
            raise HTTPException(status_code=400, detail="无效的文件路径")

        if not log_file.exists():
            raise HTTPException(status_code=404, detail="日志文件不存在")

        # 读取文件内容（最后1000行）
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # 只返回最后1000行，避免内存问题
            if len(lines) > 1000:
                lines = lines[-1000:]
            return "".join(lines)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"读取日志文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 用户行为统计API
@app.get("/api/behavior-stats", response_model=BehaviorStatsResponse)
async def get_behavior_stats(
    days: int = Query(7, description="获取最近多少天的数据"),
    action_type: Optional[str] = Query(None, description="行为类型过滤"),
    limit: int = Query(100, description="返回记录数限制"),
):
    """获取用户行为统计数据"""
    try:
        start_date = datetime.now() - timedelta(days=days)

        # 获取行为记录
        behavior_records = behavior_tracker.get_behavior_stats(
            start_date=start_date, action_type=action_type, limit=limit
        )

        # 获取每日统计
        daily_stats = behavior_tracker.get_daily_stats(days=days)

        # 获取行为类型分布
        action_distribution = behavior_tracker.get_action_type_distribution(days=days)

        # 获取小时活动分布
        hourly_activity = behavior_tracker.get_hourly_activity(days=days)

        return BehaviorStatsResponse(
            behavior_records=behavior_records,
            daily_stats=daily_stats,
            action_distribution=action_distribution,
            hourly_activity=hourly_activity,
            total_records=len(behavior_records),
        )
    except Exception as e:
        logger.error(f"获取行为统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取行为统计失败: {str(e)}")


@app.get("/api/dashboard-stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats():
    """获取仪表板统计数据"""
    try:
        # 今日活动统计
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_records = behavior_tracker.get_behavior_stats(
            start_date=today, limit=1000
        )

        today_activity = {}
        for record in today_records:
            action_type = record["action_type"]
            today_activity[action_type] = today_activity.get(action_type, 0) + 1

        # 一周趋势
        weekly_trend = []
        for i in range(7):
            day_start = today - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            day_records = behavior_tracker.get_behavior_stats(
                start_date=day_start, end_date=day_end, limit=1000
            )
            weekly_trend.append(
                {
                    "date": day_start.strftime("%Y-%m-%d"),
                    "total_actions": len(day_records),
                    "searches": len(
                        [r for r in day_records if r["action_type"] == "search"]
                    ),
                    "chats": len(
                        [r for r in day_records if r["action_type"] == "chat"]
                    ),
                    "views": len(
                        [
                            r
                            for r in day_records
                            if r["action_type"] == "view_screenshot"
                        ]
                    ),
                }
            )

        # 热门操作
        action_distribution = behavior_tracker.get_action_type_distribution(days=7)
        top_actions = [
            {"action": action, "count": count}
            for action, count in sorted(
                action_distribution.items(), key=lambda x: x[1], reverse=True
            )[:5]
        ]

        # 性能指标
        performance_metrics = {
            "avg_response_time": sum(
                [
                    r.get("response_time", 0)
                    for r in today_records
                    if r.get("response_time")
                ]
            )
            / max(len([r for r in today_records if r.get("response_time")]), 1),
            "success_rate": len([r for r in today_records if r.get("success", True)])
            / max(len(today_records), 1)
            * 100,
            "total_sessions": len(
                set([r.get("session_id") for r in today_records if r.get("session_id")])
            ),
        }

        return DashboardStatsResponse(
            today_activity=today_activity,
            weekly_trend=weekly_trend,
            top_actions=top_actions,
            performance_metrics=performance_metrics,
        )
    except Exception as e:
        logger.error(f"获取仪表板统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取仪表板统计失败: {str(e)}")


@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    """用户行为分析页面"""
    if not templates:
        raise HTTPException(status_code=404, detail="模板目录不存在")

    return templates.TemplateResponse("analytics.html", {"request": request})


@app.get("/app-usage", response_class=HTMLResponse)
async def app_usage_page(request: Request):
    """应用使用分析页面"""
    if not templates:
        raise HTTPException(status_code=404, detail="模板目录不存在")

    return templates.TemplateResponse("app_usage.html", {"request": request})


@app.get("/api/app-usage-stats", response_model=AppUsageStatsResponse)
async def get_app_usage_stats(
    days: int = Query(7, description="统计天数", ge=1, le=365),
):
    """获取应用使用统计数据"""
    try:
        # 使用新的AppUsageLog表获取统计数据
        stats_data = db_manager.get_app_usage_stats(days=days)

        # 转换数据格式以匹配前端期望
        app_usage_list = []
        for app_name, app_data in stats_data["app_usage_summary"].items():
            formatted_data = {
                "app_name": app_data["app_name"],
                "total_time": app_data["total_time"],
                "session_count": app_data["session_count"],
                "avg_session_time": app_data["total_time"] / app_data["session_count"]
                if app_data["session_count"] > 0
                else 0,
                "first_used": app_data["last_used"].isoformat(),
                "last_used": app_data["last_used"].isoformat(),
                "total_time_formatted": f"{app_data['total_time'] / 3600:.1f}小时",
                "avg_session_time_formatted": f"{(app_data['total_time'] / app_data['session_count'] if app_data['session_count'] > 0 else 0) / 60:.1f}分钟",
            }
            app_usage_list.append(formatted_data)

        # 按使用时长排序
        app_usage_list.sort(key=lambda x: x["total_time"], reverse=True)

        # 前10个应用
        top_apps_by_time = app_usage_list[:10]

        # 每日应用使用数据格式化
        daily_app_usage_list = []
        for date, apps in stats_data["daily_usage"].items():
            daily_data = {"date": date, "apps": []}
            for app_name, duration in apps.items():
                daily_data["apps"].append(
                    {
                        "app_name": app_name,
                        "duration": duration,
                        "duration_formatted": f"{duration / 3600:.1f}小时",
                    }
                )
            daily_data["apps"].sort(key=lambda x: x["duration"], reverse=True)
            daily_app_usage_list.append(daily_data)

        daily_app_usage_list.sort(key=lambda x: x["date"])

        # 小时分布数据转换
        hourly_app_distribution = {}
        for hour in range(24):
            hourly_app_distribution[hour] = {}
            if hour in stats_data["hourly_usage"]:
                for app_name, duration in stats_data["hourly_usage"][hour].items():
                    hourly_app_distribution[hour][app_name] = int(duration)

        return AppUsageStatsResponse(
            app_usage_summary=app_usage_list,
            daily_app_usage=daily_app_usage_list,
            hourly_app_distribution=hourly_app_distribution,
            top_apps_by_time=top_apps_by_time,
            app_switching_patterns=[],  # 暂时为空，可以后续添加
            total_apps_used=stats_data["total_apps"],
            total_usage_time=stats_data["total_time"],
        )

    except Exception as e:
        logger.error(f"获取应用使用统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取应用使用统计失败: {str(e)}")


# ======================================
# 计划编辑器API
# ======================================


# 数据模型
class TodoItem(BaseModel):
    id: str
    title: str
    checked: bool
    content: Optional[str] = None


class PlanContent(BaseModel):
    title: str
    description: str
    todos: List[TodoItem]


# 创建plans目录
PLANS_DIR = Path(config.base_dir) / "plans"
PLANS_DIR.mkdir(exist_ok=True)

# 创建plan_images目录
PLAN_IMAGES_DIR = Path(config.base_dir) / "plan_images"
PLAN_IMAGES_DIR.mkdir(exist_ok=True)


@app.post("/api/plan/save")
async def save_plan(plan: PlanContent):
    """保存计划到文件"""
    try:
        plan_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = PLANS_DIR / f"{plan_id}.json"

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(plan.dict(), f, ensure_ascii=False, indent=2)

        logger.info(f"计划已保存: {plan_id}")
        return {"plan_id": plan_id, "message": "保存成功"}
    except Exception as e:
        logger.error(f"保存计划失败: {e}")
        raise HTTPException(status_code=500, detail=f"保存计划失败: {str(e)}")


@app.get("/api/plan/load")
async def load_plan(plan_id: str):
    """加载指定计划"""
    try:
        file_path = PLANS_DIR / f"{plan_id}.json"
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="计划不存在")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"加载计划失败: {e}")
        raise HTTPException(status_code=500, detail=f"加载计划失败: {str(e)}")


@app.get("/api/plan/list")
async def list_plans():
    """列出所有计划"""
    try:
        plans = []
        for file_path in PLANS_DIR.glob("*.json"):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                plans.append(
                    {
                        "plan_id": file_path.stem,
                        "title": data.get("title", "未命名计划"),
                        "created_at": file_path.stem,  # 从文件名提取时间
                    }
                )

        plans.sort(key=lambda x: x["created_at"], reverse=True)
        return {"plans": plans}
    except Exception as e:
        logger.error(f"列出计划失败: {e}")
        raise HTTPException(status_code=500, detail=f"列出计划失败: {str(e)}")


@app.post("/api/plan/upload-image")
async def upload_plan_image(image: UploadFile = File(...)):
    """上传计划中的图片"""
    try:
        # 生成唯一文件名
        file_ext = image.filename.split(".")[-1] if "." in image.filename else "png"
        file_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"
        filename = f"{file_id}.{file_ext}"
        file_path = PLAN_IMAGES_DIR / filename

        # 保存文件
        content = await image.read()
        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(f"图片已上传: {filename}")
        return {"url": f"/api/plan/images/{filename}"}
    except Exception as e:
        logger.error(f"上传图片失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传图片失败: {str(e)}")


@app.get("/api/plan/images/{filename}")
async def get_plan_image(filename: str):
    """获取计划图片"""
    file_path = PLAN_IMAGES_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="图片不存在")
    return FileResponse(file_path)


def main():
    """主函数 - 命令行入口"""
    import argparse

    import uvicorn

    parser = argparse.ArgumentParser(description="LifeTrace Web Server")
    parser.add_argument("--host", default="127.0.0.1", help="服务器地址")
    parser.add_argument("--port", type=int, default=8840, help="服务器端口")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")

    args = parser.parse_args()

    # 日志已在模块顶部通过logging_config配置

    # 使用配置中的服务器设置，但命令行参数优先
    host = args.host or config.get("server.host", "127.0.0.1")
    port = args.port or config.get("server.port", 8840)
    debug = args.debug or config.get("server.debug", False)

    logging.info(f"启动LifeTrace Web服务器: http://{host}:{port}")

    # 启动服务器
    uvicorn.run(app, host=host, port=port, reload=debug, access_log=debug)


if __name__ == "__main__":
    main()
