import os
import sys
import time
import logging
from datetime import datetime
from typing import List, Optional
from pathlib import Path
import signal
from functools import wraps

# 添加项目根目录到Python路径，以便直接运行此文件
if __name__ == '__main__':
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

import mss
from PIL import Image
import imagehash

from lifetrace_backend.config import config
from lifetrace_backend.utils import ensure_dir, get_active_window_info, get_screenshot_filename
from lifetrace_backend.storage import db_manager
from lifetrace_backend.logging_config import setup_logging
from lifetrace_backend.simple_heartbeat import SimpleHeartbeatSender
from lifetrace_backend.app_mapping import expand_blacklist_apps

# 设置日志系统
logger_manager = setup_logging(config)
logger = logger_manager.get_recorder_logger()


class TimeoutError(Exception):
    """超时异常"""
    pass


def timeout_handler(signum, frame):
    """超时信号处理器"""
    raise TimeoutError("操作超时")


def with_timeout(timeout_seconds=5, operation_name="操作"):
    """超时装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 在Windows上，signal.alarm不可用，使用threading.Timer作为替代
            import threading
            result = [None]
            exception = [None]
            
            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout_seconds)
            
            if thread.is_alive():
                logger.warning(f"{operation_name}超时 ({timeout_seconds}秒)，操作可能仍在后台执行")
                # 注意：无法强制终止线程，只能记录超时
                return None
            
            if exception[0]:
                raise exception[0]
            
            return result[0]
        return wrapper
    return decorator


class ScreenRecorder:
    """屏幕录制器"""
    
    def __init__(self):
        self.config = config
        self.screenshots_dir = self.config.screenshots_dir
        self.interval = self.config.get('record.interval', 1)
        self.screens = self._get_screen_list()
        self.hash_threshold = self.config.get('storage.hash_threshold', 5)
        self.deduplicate = self.config.get('storage.deduplicate', True)
        
        # 超时配置
        self.file_io_timeout = self.config.get('record.file_io_timeout', 15)
        self.db_timeout = self.config.get('record.db_timeout', 20)
        self.window_info_timeout = self.config.get('record.window_info_timeout', 5)
        
        # 初始化截图目录
        ensure_dir(self.screenshots_dir)
        
        # 上一张截图的哈希值（用于去重）
        self.last_hashes = {}
        
        # 初始化UDP心跳发送器
        self.heartbeat_sender = SimpleHeartbeatSender('recorder')
        
        logger.info(f"超时配置 - 文件I/O: {self.file_io_timeout}s, 数据库: {self.db_timeout}s, 窗口信息: {self.window_info_timeout}s")
        
        logger.info(f"屏幕录制器初始化完成，监控屏幕: {self.screens}")
        
        # 注册配置变更回调
        self.config.register_callback(self._on_config_change)
    
    def _on_config_change(self, old_config: dict, new_config: dict):
        """配置变更回调函数"""
        try:
            # 更新截图间隔
            new_interval = new_config.get('record', {}).get('interval', 1)
            if new_interval != self.interval:
                old_interval = self.interval
                self.interval = new_interval
                logger.info(f"截图间隔已更新: {old_interval}s -> {new_interval}s")
            
            # 更新监控屏幕列表
            old_screens_config = old_config.get('record', {}).get('screens', 'all')
            new_screens_config = new_config.get('record', {}).get('screens', 'all')
            if old_screens_config != new_screens_config:
                old_screens = self.screens
                self.screens = self._get_screen_list()
                logger.info(f"监控屏幕已更新: {old_screens} -> {self.screens}")
            
            # 更新去重配置
            new_deduplicate = new_config.get('storage', {}).get('deduplicate', True)
            if new_deduplicate != self.deduplicate:
                self.deduplicate = new_deduplicate
                logger.info(f"去重功能已{'启用' if new_deduplicate else '禁用'}")
            
            # 更新去重阈值
            new_threshold = new_config.get('storage', {}).get('hash_threshold', 5)
            if new_threshold != self.hash_threshold:
                old_threshold = self.hash_threshold
                self.hash_threshold = new_threshold
                logger.info(f"去重阈值已更新: {old_threshold} -> {new_threshold}")
            
            # 更新黑名单配置
            old_blacklist = old_config.get('record', {}).get('blacklist', {})
            new_blacklist = new_config.get('record', {}).get('blacklist', {})
            if old_blacklist != new_blacklist:
                logger.info("黑名单配置已更新")
                if new_blacklist.get('enabled') != old_blacklist.get('enabled'):
                    enabled = new_blacklist.get('enabled', False)
                    logger.info(f"黑名单功能已{'启用' if enabled else '禁用'}")
            
            # 更新超时配置
            new_file_io_timeout = new_config.get('record', {}).get('file_io_timeout', 15)
            if new_file_io_timeout != self.file_io_timeout:
                self.file_io_timeout = new_file_io_timeout
                logger.info(f"文件I/O超时已更新: {new_file_io_timeout}s")
                
        except Exception as e:
            logger.error(f"处理配置变更失败: {e}")
    
    def _save_screenshot(self, screenshot, file_path: str) -> bool:
        """保存截图到文件"""
        @with_timeout(timeout_seconds=self.file_io_timeout, operation_name="保存截图文件")
        def _do_save():
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=file_path)
            return True
        
        try:
            result = _do_save()
            return result if result is not None else False
        except Exception as e:
            logger.error(f"保存截图失败 {file_path}: {e}")
            return False
    
    def _get_image_size(self, file_path: str) -> tuple:
        """获取图像尺寸"""
        @with_timeout(timeout_seconds=self.file_io_timeout, operation_name="读取图像尺寸")
        def _do_get_size():
            with Image.open(file_path) as img:
                return img.size
        
        try:
            result = _do_get_size()
            return result if result is not None else (0, 0)
        except Exception as e:
            logger.error(f"读取图像尺寸失败 {file_path}: {e}")
            return (0, 0)
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件MD5哈希"""
        @with_timeout(timeout_seconds=self.file_io_timeout, operation_name="计算文件哈希")
        def _do_calculate_hash():
            import hashlib
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        
        try:
            result = _do_calculate_hash()
            return result if result is not None else ""
        except Exception as e:
            logger.error(f"计算文件哈希失败 {file_path}: {e}")
            return ""
    
    def _save_to_database(self, file_path: str, file_hash: str, width: int, height: int, 
                         screen_id: int, app_name: str, window_title: str, timestamp) -> Optional[int]:
        """保存截图信息到数据库"""
        @with_timeout(timeout_seconds=self.db_timeout, operation_name="数据库操作")
        def _do_save_to_db():
            # 获取或创建事件（基于当前前台应用）
            event_id = db_manager.get_or_create_event(app_name or "未知应用", window_title or "未知窗口", timestamp)
            
            screenshot_id = db_manager.add_screenshot(
                file_path=file_path,
                file_hash=file_hash,
                width=width,
                height=height,
                screen_id=screen_id,
                app_name=app_name or "未知应用",
                window_title=window_title or "未知窗口",
                event_id=event_id
            )
            return screenshot_id
        
        try:
            result = _do_save_to_db()
            return result
        except Exception as e:
            logger.error(f"保存截图记录到数据库失败: {e}")
            return None
    
    def _get_window_info(self) -> tuple:
        """获取当前活动窗口信息"""
        @with_timeout(timeout_seconds=self.window_info_timeout, operation_name="获取窗口信息")
        def _do_get_window_info():
            return get_active_window_info()
        
        try:
            result = _do_get_window_info()
            return result if result is not None else ("未知应用", "未知窗口")
        except Exception as e:
            logger.error(f"获取窗口信息失败: {e}")
            return ("未知应用", "未知窗口")
    
    def _is_lifetrace_window(self, app_name: str, window_title: str) -> bool:
        """检查是否为LifeTrace相关窗口"""
        if not app_name and not window_title:
            return False
        
        # LifeTrace相关的应用名称模式
        lifetrace_app_patterns = [
            'python',
            'pythonw',
            'lifetrace',
            'electron',
            'chrome',
            'msedge',
            'firefox',
            'browser'
        ]
        
        # LifeTrace相关的窗口标题模式
        lifetrace_window_patterns = [
            'lifetrace',
            'localhost:8840',
            '127.0.0.1:8840',
            'lifetrace - intelligent life recording system',
            'lifetrace desktop',
            'lifetrace 智能生活记录系统',
            'lifetrace 桌面版',
            'lifetrace frontend',
            'lifetrace web interface'
        ]
        
        # 检查应用名
        if app_name:
            app_name_lower = app_name.lower()
            # 如果是浏览器类应用，需要进一步检查窗口标题
            browser_apps = ['chrome', 'msedge', 'firefox', 'electron']
            if any(browser in app_name_lower for browser in browser_apps):
                if window_title:
                    window_title_lower = window_title.lower()
                    for pattern in lifetrace_window_patterns:
                        if pattern in window_title_lower:
                            return True
            # 如果是Python相关应用，检查是否运行LifeTrace
            elif any(pattern in app_name_lower for pattern in ['python', 'pythonw']):
                if window_title:
                    window_title_lower = window_title.lower()
                    for pattern in lifetrace_window_patterns:
                        if pattern in window_title_lower:
                            return True
        
        # 检查窗口标题
        if window_title:
            window_title_lower = window_title.lower()
            for pattern in lifetrace_window_patterns:
                if pattern in window_title_lower:
                    return True
        
        return False
    
    def _is_app_blacklisted(self, app_name: str, window_title: str) -> bool:
        """检查应用是否在黑名单中"""
        # 首先检查是否启用自动排除LifeTrace自身窗口
        auto_exclude_self = self.config.get('record.auto_exclude_self', True)
        if auto_exclude_self and self._is_lifetrace_window(app_name, window_title):
            logger.info(f"检测到LifeTrace自身窗口 - 应用: '{app_name}', 窗口: '{window_title}', 跳过截图")
            return True
        
        # 检查黑名单功能是否启用
        blacklist_enabled = self.config.get('record.blacklist.enabled', False)
        if not blacklist_enabled:
            return False
        
        # 获取黑名单配置
        blacklist_apps = self.config.get('record.blacklist.apps', [])
        blacklist_windows = self.config.get('record.blacklist.windows', [])
        
        # 扩展黑名单应用列表（包含映射的应用名称）
        expanded_blacklist_apps = expand_blacklist_apps(blacklist_apps)
        
        # 检查应用名是否在黑名单中
        if app_name and expanded_blacklist_apps:
            app_name_lower = app_name.lower()
            for blacklist_app in expanded_blacklist_apps:
                if blacklist_app.lower() == app_name_lower or blacklist_app.lower() in app_name_lower:
                    logger.info(f"应用 '{app_name}' 在黑名单中，跳过截图")
                    return True
        
        # 检查窗口标题是否在黑名单中
        if window_title and blacklist_windows:
            window_title_lower = window_title.lower()
            for blacklist_window in blacklist_windows:
                if blacklist_window.lower() == window_title_lower or blacklist_window.lower() in window_title_lower:
                    logger.info(f"窗口 '{window_title}' 在黑名单中，跳过截图")
                    return True
        
        return False
    
    def _get_screen_list(self) -> List[int]:
        """获取要截图的屏幕列表"""
        screens_config = self.config.get('record.screens', 'all')
        print(screens_config)
        with mss.mss() as sct:
            monitor_count = len(sct.monitors) - 1  # 减1因为第0个是所有屏幕的组合
            
            if screens_config == 'all':
                return list(range(1, monitor_count + 1))
            elif isinstance(screens_config, list):
                return [s for s in screens_config if 1 <= s <= monitor_count]
            else:
                return [1] if monitor_count > 0 else []
    
    def _calculate_image_hash(self, image_path: str) -> str:
        """计算图像感知哈希值"""
        @with_timeout(timeout_seconds=self.file_io_timeout, operation_name="计算图像哈希")
        def _do_calculate_hash():
            with Image.open(image_path) as img:
                return str(imagehash.phash(img))
        
        try:
            result = _do_calculate_hash()
            return result if result is not None else ""
        except Exception as e:
            logging.error(f"计算图像哈希失败 {image_path}: {e}")
            return ""
    
    def _calculate_image_hash_from_memory(self, screenshot) -> str:
        """直接从内存中的截图计算图像感知哈希值"""
        @with_timeout(timeout_seconds=self.file_io_timeout, operation_name="从内存计算图像哈希")
        def _do_calculate_hash():
            # 将mss截图转换为PIL Image对象
            img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            return str(imagehash.phash(img))
        
        try:
            result = _do_calculate_hash()
            return result if result is not None else ""
        except Exception as e:
            logger.error(f"从内存计算图像哈希失败: {e}")
            return ""
    
    def _is_duplicate(self, screen_id: int, image_hash: str) -> bool:
        """检查是否为重复图像"""
        if not self.deduplicate:
            return False
            
        is_duplicate = False
        
        if screen_id not in self.last_hashes:
            # 第一次截图，不是重复
            self.last_hashes[screen_id] = image_hash
            # 初始化状态跟踪
            if not hasattr(self, '_last_duplicate_status'):
                self._last_duplicate_status = {}
            self._last_duplicate_status[screen_id] = False
            return False
        
        try:
            # 计算汉明距离
            current = imagehash.hex_to_hash(image_hash)
            previous = imagehash.hex_to_hash(self.last_hashes[screen_id])
            distance = current - previous
            
            is_duplicate = distance <= self.hash_threshold
            
            # 检查状态是否发生变化
            if not hasattr(self, '_last_duplicate_status'):
                self._last_duplicate_status = {}
                
            last_status = self._last_duplicate_status.get(screen_id, False)
            
            # 只有状态发生变化时才打印日志
            if is_duplicate and not last_status:
                logger.info(f"屏幕 {screen_id}: 开始重复截图")
                print(f"[去重] 屏幕 {screen_id}: 开始重复截图")
            elif not is_duplicate and last_status:
                logger.info(f"屏幕 {screen_id}: 重复结束，恢复截图")
                print(f"[去重] 屏幕 {screen_id}: 重复结束，恢复截图")
            elif is_duplicate and last_status:
                # 连续重复，可以选择性地每N次打印一次或者完全不打印
                pass
                
            # 更新状态记录
            self._last_duplicate_status[screen_id] = is_duplicate
            self.last_hashes[screen_id] = image_hash
                
        except Exception as e:
            logger.error(f"比较图像哈希失败: {e}")
            is_duplicate = False
        
        return is_duplicate
    
    def _capture_screen(self, screen_id: int, app_name: str = None, window_title: str = None) -> Optional[str]:
        """截取指定屏幕"""
        try:
            with mss.mss() as sct:
                if screen_id >= len(sct.monitors):
                    logger.warning(f"屏幕ID {screen_id} 不存在")
                    return None
                
                monitor = sct.monitors[screen_id]
                screenshot = sct.grab(monitor)
                
                # 生成文件名
                timestamp = datetime.now()
                filename = get_screenshot_filename(screen_id, timestamp)
                file_path = os.path.join(self.screenshots_dir, filename)
                
                # 优化：先从内存计算图像哈希，避免不必要的磁盘I/O
                image_hash = self._calculate_image_hash_from_memory(screenshot)
                if not image_hash:
                    logger.error(f"计算图像哈希失败，跳过: {filename}")
                    return None
                
                # 检查是否重复
                if self._is_duplicate(screen_id, image_hash):
                    # 重复图像直接返回，不保存到磁盘
                    logger.debug(f"检测到重复截图，跳过保存: {filename}")
                    return None
                
                # 更新哈希记录
                self.last_hashes[screen_id] = image_hash
                
                # 只有非重复图像才保存到磁盘
                if not self._save_screenshot(screenshot, file_path):
                    logger.error(f"保存截图失败: {filename}")
                    return None
                
                # 使用传入的窗口信息，如果没有则重新获取
                if app_name is None or window_title is None:
                    app_name, window_title = self._get_window_info()
                
                # 获取图像尺寸（带超时）
                width, height = self._get_image_size(file_path)
                
                # 计算文件哈希（带超时）
                file_hash = self._calculate_file_hash(file_path)
                if not file_hash:
                    logger.warning(f"计算文件哈希失败，使用空值: {filename}")
                    file_hash = ""
                
                # 保存截图信息到数据库（带超时）
                screenshot_id = self._save_to_database(
                    file_path, file_hash, width, height, 
                    screen_id, app_name, window_title, timestamp
                )
                
                if screenshot_id:
                    logger.debug(f"截图记录已保存到数据库: {screenshot_id}")
                else:
                    logger.warning(f"数据库保存失败，但文件已保存: {filename}")
                
                file_size = os.path.getsize(file_path)
                
                logger.info(f"截图保存: {filename} ({file_size} bytes) - {app_name}")
                
                return file_path
                
        except Exception as e:
            logger.error(f"截图失败 (屏幕 {screen_id}): {e}")
            return None
    
    def capture_all_screens(self) -> List[str]:
        """截取所有屏幕"""
        captured_files = []
        
        # 获取当前活动窗口信息，用于黑名单检查
        app_name, window_title = self._get_window_info()
        
        # 检查是否在黑名单中
        if self._is_app_blacklisted(app_name, window_title):
            logger.debug(f"当前应用 '{app_name}' 或窗口 '{window_title}' 在黑名单中，跳过所有屏幕截图")
            print(f"[黑名单] 跳过截图 - 应用: {app_name}, 窗口: {window_title}")
            
            # 关闭上一个未结束的事件（如果存在）
            # 这样可以确保从白名单应用切换到黑名单应用时，白名单应用的事件能正确结束
            try:
                db_manager.close_active_event()
                logger.debug("已关闭上一个活跃事件")
            except Exception as e:
                logger.error(f"关闭活跃事件失败: {e}")
            
            return captured_files
        
        # 记录应用使用信息到新表（在截图前记录，避免跳过和去重的影响）
        self._log_app_usage(app_name, window_title)
        
        for screen_id in self.screens:
            file_path = self._capture_screen(screen_id, app_name, window_title)
            if file_path:
                captured_files.append(file_path)

        return captured_files
    
    def _log_app_usage(self, app_name: str, window_title: str = None):
        """记录应用使用信息到新表"""
        try:
            # 计算持续时间（使用截图间隔作为估算）
            duration_seconds = self.interval
            
            # 记录到数据库
            log_id = db_manager.add_app_usage_log(
                app_name=app_name,
                window_title=window_title,
                duration_seconds=duration_seconds,
                screen_id=0,  # 默认屏幕ID，可以根据需要调整
                timestamp=datetime.now()
            )
            
            if log_id:
                logger.debug(f"应用使用记录已保存: {app_name} - {window_title} ({duration_seconds}s)")
            else:
                logger.warning(f"应用使用记录保存失败: {app_name}")
                
        except Exception as e:
            logger.error(f"记录应用使用信息失败: {e}")
    
    def start_recording(self):
        """开始录制"""
        logger.info("开始屏幕录制...")
        
        # 启动配置文件监听
        self.config.start_watching()
        logger.info("已启动配置文件监听")
        
        # 启动UDP心跳发送
        self.heartbeat_sender.start(interval=1.0)
        
        try:
            while True:
                start_time = time.time()
                
                # 发送心跳（包含额外数据）
                self.heartbeat_sender.send_heartbeat({
                    'status': 'running',
                    'screens': len(self.screens),
                    'interval': self.interval
                })
                
                # 截图
                captured_files = self.capture_all_screens()
                
                if captured_files:
                    logger.debug(f"本次截取了 {len(captured_files)} 张截图")
                
                # 计算下次截图时间
                elapsed = time.time() - start_time
                sleep_time = max(0, self.interval - elapsed)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    logger.warning(f"截图处理时间 ({elapsed:.2f}s) 超过间隔时间 ({self.interval}s)")
                    
        except KeyboardInterrupt:
            logger.info("收到停止信号，结束录制")
            self.heartbeat_sender.send_heartbeat({'status': 'stopped', 'reason': 'keyboard_interrupt'})
            self._print_final_stats()
        except Exception as e:
            logger.error(f"录制过程中发生错误: {e}")
            self.heartbeat_sender.send_heartbeat({'status': 'error', 'error': str(e)})
            self._print_final_stats()
            raise
        finally:
            # 停止配置文件监听
            self.config.stop_watching()
            logger.info("已停止配置文件监听")
            # 停止心跳发送
            self.heartbeat_sender.stop()
    
    def _print_final_stats(self):
        """输出最终统计信息"""
        logger.info("录制会话结束")
        print("录制结束")

def main():
    """主函数 - 命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LifeTrace Screen Recorder')
    parser.add_argument('--config', help='配置文件路径')
    parser.add_argument('--interval', type=int, help='截图间隔（秒）')
    parser.add_argument('--screens', help='要截图的屏幕，用逗号分隔或使用"all"')
    parser.add_argument('--debug', action='store_true', help='启用调试日志')
    
    args = parser.parse_args()
    
    # 日志已在模块顶部通过logging_config配置
    
    # 更新配置
    if args.interval:
        config.set('record.interval', args.interval)
    
    if args.screens:
        if args.screens.lower() == 'all':
            config.set('record.screens', 'all')
        else:
            screens = [int(s.strip()) for s in args.screens.split(',')]
            config.set('record.screens', screens)
    
    # 创建并启动录制器
    recorder = ScreenRecorder()
    recorder.start_recording()

if __name__ == '__main__':
    main()