#!/usr/bin/env python3
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from lifetrace_backend.config import config
from lifetrace_backend.logging_config import setup_logging
from lifetrace_backend.storage import db_manager
from lifetrace_backend.utils import ensure_dir

app = typer.Typer(help="LifeTrace 智能生活记录系统")
console = Console()

# 全局变量存储进程ID
PROCESSES = {"recorder": None, "processor": None, "server": None}


@app.command()
def init(
    base_dir: Optional[str] = typer.Option(None, help="基础目录路径"),
    force: bool = typer.Option(False, help="强制重新初始化"),
):
    """初始化LifeTrace系统"""

    if base_dir:
        config.set("base_dir", base_dir)

    # 确保目录存在
    ensure_dir(config.base_dir)
    ensure_dir(config.screenshots_dir)
    ensure_dir(os.path.join(config.base_dir, "logs"))
    ensure_dir(os.path.join(Path(__file__).parent.parent, "config"))
    ensure_dir(os.path.join(Path(__file__).parent.parent, "data"))

    # 初始化配置文件
    config_file = config.config_path
    if not os.path.exists(config_file) or force:
        config.save_config()
        rprint(f"[green]OK[/green] 配置文件已创建: \n{config_file}")
    else:
        rprint(f"[yellow]WARN[/yellow] 配置文件已存在: \n{config_file}")

    # 初始化数据库
    try:
        db_manager._init_database()
        rprint(f"[green]OK[/green] 数据库已初始化: {db_manager.database_url}")
    except Exception as e:
        rprint(f"[red]ERROR[/red] 数据库初始化失败: {e}")
        return

    # 设置日志
    logger_manager = setup_logging(config)
    logger = logger_manager.get_main_logger()  # noqa: F841

    rprint("\n[green]SUCCESS[/green] LifeTrace 初始化完成!")
    rprint(f"数据目录: {os.path.abspath(config.base_dir)}")
    rprint(f"截图目录: {os.path.abspath(os.path.join(config.base_dir, 'screenshots'))}")
    rprint(f"配置文件: {config_file}")
    rprint(f"数据库: {os.path.abspath(config.database_path)}")

    rprint("\n接下来可以运行:")
    rprint("  lifetrace start    # 启动所有服务")
    rprint("  lifetrace status   # 查看状态")
    rprint("  lifetrace web      # 仅启动Web界面")


@app.command()
def start(
    background: bool = typer.Option(True, help="后台运行"),
    recorder: bool = typer.Option(True, help="启动截图记录"),
    processor: bool = typer.Option(True, help="启动文件处理"),
    server: bool = typer.Option(True, help="启动Web服务器"),
):
    """启动LifeTrace服务"""

    if not _check_initialized():
        return

    rprint("[blue]正在启动 LifeTrace 服务...[/blue]")

    # 启动各个服务
    if recorder:
        _start_service("recorder", background)

    if processor:
        _start_service("processor", background)

    if server:
        _start_service("server", background)

    time.sleep(2)  # 等待服务启动

    # 显示状态
    _show_status()

    if not background:
        rprint("\n[yellow]按 Ctrl+C 停止所有服务[/yellow]")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            stop()


@app.command()
def stop():
    """停止所有LifeTrace服务"""
    rprint("[yellow]正在停止 LifeTrace 服务...[/yellow]")

    for service in ["server", "processor", "recorder"]:
        _stop_service(service)

    rprint("[green]OK 所有服务已停止[/green]")


@app.command()
def status():
    """查看服务状态"""
    _show_status()


@app.command()
def record(
    interval: int = typer.Option(1, help="截图间隔（秒）"),
    screens: str = typer.Option("all", help="屏幕列表，用逗号分隔或使用'all'"),
    debug: bool = typer.Option(False, help="启用调试日志"),
):
    """启动截图记录服务"""

    if not _check_initialized():
        return

    # 更新配置
    config.set("record.interval", interval)
    if screens.lower() == "all":
        config.set("record.screens", "all")
    else:
        screen_list = [int(s.strip()) for s in screens.split(",")]
        config.set("record.screens", screen_list)

    # 启动记录器
    from lifetrace_backend.recorder import main as recorder_main

    recorder_main()


@app.command()
def process(
    interval: int = typer.Option(5, help="检查间隔（秒）"),
    workers: int = typer.Option(2, help="工作线程数"),
    debug: bool = typer.Option(False, help="启用调试日志"),
):
    """启动文件处理服务"""

    if not _check_initialized():
        return

    # 更新配置
    config.set("processing.max_workers", workers)

    # 启动处理器
    from lifetrace_backend.processor import main as processor_main

    processor_main()


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="服务器地址"),
    port: int = typer.Option(8840, help="服务器端口"),
    debug: bool = typer.Option(False, help="启用调试模式"),
):
    """启动Web服务器"""

    if not _check_initialized():
        return

    # 更新配置
    config.set("server.host", host)
    config.set("server.port", port)
    config.set("server.debug", debug)

    # 启动服务器
    from lifetrace_backend.server import main as server_main

    server_main()


@app.command()
def simple_ocr(
    interval: float = typer.Option(0.5, help="检查间隔（秒）"),
    debug: bool = typer.Option(False, help="启用调试日志"),
):
    """启动简化OCR处理服务（推荐使用）"""

    if not _check_initialized():
        return

    # 更新配置
    config.set("ocr.check_interval", interval)

    from lifetrace_backend.simple_ocr import main as simple_ocr_main

    simple_ocr_main()


@app.command()
def ocr(
    interval: float = typer.Option(0.5, help="检查间隔（秒）"),
    debug: bool = typer.Option(False, help="启用调试日志"),
):
    """启动OCR处理服务（简化版）"""

    if not _check_initialized():
        return

    # 更新配置
    config.set("ocr.check_interval", interval)

    from lifetrace_backend.simple_ocr import SimpleOCRProcessor

    processor = SimpleOCRProcessor()
    processor.start()


@app.command()
def web():
    """仅启动Web界面（不启动其他服务）"""
    serve()


@app.command()
def stats():
    """显示系统统计信息"""

    if not _check_initialized():
        return

    try:
        stats = db_manager.get_statistics()

        table = Table(title="LifeTrace 系统统计")
        table.add_column("项目", style="cyan")
        table.add_column("数值", style="green")

        table.add_row("总截图数", str(stats.get("total_screenshots", 0)))
        table.add_row("已处理", str(stats.get("processed_screenshots", 0)))
        table.add_row("待处理任务", str(stats.get("pending_tasks", 0)))
        table.add_row("今日截图", str(stats.get("today_screenshots", 0)))
        table.add_row("处理进度", f"{stats.get('processing_rate', 0):.1f}%")

        console.print(table)

        # OCR统计
        from .simple_ocr import SimpleOCRProcessor

        ocr_processor = SimpleOCRProcessor()
        ocr_stats = ocr_processor.get_statistics()

        ocr_table = Table(title="OCR 处理统计")
        ocr_table.add_column("项目", style="cyan")
        ocr_table.add_column("数值", style="green")

        ocr_table.add_row("OCR状态", "启用" if ocr_stats["enabled"] else "禁用")
        ocr_table.add_row("检查间隔", f"{ocr_stats['check_interval']} 秒")
        ocr_table.add_row("支持语言", ", ".join(ocr_stats["supported_languages"]))
        ocr_table.add_row("已处理文件", str(ocr_stats["processed_files_count"]))

        console.print(ocr_table)

    except Exception as e:
        rprint(f"[red]获取统计信息失败: {e}[/red]")


@app.command()
def cleanup(
    days: int = typer.Option(30, help="保留天数"),
    confirm: bool = typer.Option(False, help="跳过确认"),
):
    """清理旧数据"""

    if not _check_initialized():
        return

    if not confirm:
        if not typer.confirm(f"确定要删除 {days} 天前的所有数据吗？"):
            rprint("操作已取消")
            return

    try:
        rprint(f"[yellow]正在清理 {days} 天前的数据...[/yellow]")
        db_manager.cleanup_old_data(days)
        rprint("[green]✓ 数据清理完成[/green]")
    except Exception as e:
        rprint(f"[red]清理失败: {e}[/red]")


@app.command()
def config_show():
    """显示当前配置"""

    table = Table(title="LifeTrace 配置")
    table.add_column("配置项", style="cyan")
    table.add_column("值", style="green")

    table.add_row("基础目录", config.base_dir)
    table.add_row("截图目录", config.screenshots_dir)
    table.add_row("数据库路径", config.database_path)
    table.add_row(
        "服务器地址", f"{config.get('server.host')}:{config.get('server.port')}"
    )
    table.add_row("截图间隔", f"{config.get('record.interval')} 秒")
    table.add_row("OCR启用", "是" if config.get("ocr.enabled") else "否")
    table.add_row("OCR检查间隔", f"{config.get('ocr.check_interval')} 秒")
    table.add_row("数据保留", f"{config.get('storage.max_days')} 天")

    console.print(table)


def _check_initialized() -> bool:
    """检查是否已初始化"""
    if not os.path.exists(config.database_path):
        rprint("[red]系统未初始化，请先运行: lifetrace init[/red]")
        return False
    return True


def _start_service(service: str, background: bool = True) -> bool:
    """启动服务"""
    if _is_service_running(service):
        rprint(f"[yellow]WARN {service} 服务已在运行[/yellow]")
        return True

    try:
        if service == "recorder":
            cmd = [sys.executable, "-m", "lifetrace.recorder"]
        elif service == "processor":
            cmd = [sys.executable, "-m", "lifetrace.processor"]
        elif service == "server":
            cmd = [sys.executable, "-m", "lifetrace.server"]
        else:
            rprint(f"[red]未知服务: {service}[/red]")
            return False

        if background:
            process = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            PROCESSES[service] = process.pid
            rprint(f"[green]OK {service} 服务已启动 (PID: {process.pid})[/green]")
        else:
            subprocess.run(cmd)

        return True

    except Exception as e:
        rprint(f"[red]启动 {service} 服务失败: {e}[/red]")
        return False


def _stop_service(service: str) -> bool:
    """停止服务"""
    pid = PROCESSES.get(service)
    if not pid:
        return True

    try:
        os.kill(pid, signal.SIGTERM)
        PROCESSES[service] = None
        rprint(f"[green]OK {service} 服务已停止[/green]")
        return True
    except ProcessLookupError:
        PROCESSES[service] = None
        return True
    except Exception as e:
        rprint(f"[red]停止 {service} 服务失败: {e}[/red]")
        return False


def _is_service_running(service: str) -> bool:
    """检查服务是否运行"""
    pid = PROCESSES.get(service)
    if not pid:
        return False

    try:
        os.kill(pid, 0)  # 发送信号0检查进程是否存在
        return True
    except ProcessLookupError:
        PROCESSES[service] = None
        return False
    except Exception:
        return False


def _show_status():
    """显示服务状态"""
    table = Table(title="LifeTrace 服务状态")
    table.add_column("服务", style="cyan")
    table.add_column("状态", style="green")
    table.add_column("PID", style="yellow")

    for service in ["recorder", "processor", "server"]:
        if _is_service_running(service):
            status = "RUNNING"
            pid = str(PROCESSES[service])
        else:
            status = "STOPPED"
            pid = "-"

        table.add_row(service.capitalize(), status, pid)

    console.print(table)


def main():
    """主入口函数"""
    app()


if __name__ == "__main__":
    main()
