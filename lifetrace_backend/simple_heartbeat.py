"""
简单的UDP心跳机制
解决文件竞争问题，提供可靠的服务监控
"""

import json
import os
import socket
import threading
import time
from typing import Dict, Optional


class SimpleHeartbeatSender:
    """简单的心跳发送器 - 集成到各个服务中"""

    def __init__(
        self,
        service_name: str,
        manager_host: str = "127.0.0.1",
        manager_port: int = 9999,
    ):
        self.service_name = service_name
        self.manager_host = manager_host
        self.manager_port = manager_port
        self.sock = None
        self.running = False
        self.thread = None

    def start(self, interval: float = 2.0):
        """启动心跳发送"""
        if self.running:
            return

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.running = True
            self.thread = threading.Thread(
                target=self._heartbeat_loop, args=(interval,), daemon=True
            )
            self.thread.start()
            print(f"[OK] {self.service_name} 心跳发送器已启动")
        except Exception as e:
            print(f"[ERROR] {self.service_name} 心跳发送器启动失败: {e}")

    def stop(self):
        """停止心跳发送器"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        print(f"[STOP] {self.service_name} 心跳发送器已停止")

    def _heartbeat_loop(self, interval: float):
        """心跳发送循环"""
        while self.running:
            try:
                self.send_heartbeat()
                time.sleep(interval)
            except Exception as e:
                print(f"WARNING: {self.service_name} 心跳发送失败: {e}")
                time.sleep(interval)

    def send_heartbeat(
        self, status: str = "healthy", extra_data: Optional[Dict] = None
    ):
        """发送单次心跳"""
        if not self.sock:
            return False

        try:
            heartbeat_data = {
                "service": self.service_name,
                "pid": os.getpid(),
                "timestamp": time.time(),
                "status": status,
                "data": extra_data or {},
            }

            message = json.dumps(heartbeat_data).encode("utf-8")
            self.sock.sendto(message, (self.manager_host, self.manager_port))
            return True
        except Exception as e:
            print(f"WARNING: {self.service_name} 发送心跳失败: {e}")
            return False


class SimpleHeartbeatReceiver:
    """简单的心跳接收器 - 在服务管理器中使用"""

    def __init__(self, port: int = 9999):
        self.port = port
        self.sock = None
        self.running = False
        self.thread = None
        self.services: Dict[str, Dict] = {}
        self.lock = threading.Lock()

    def start(self):
        """启动心跳接收"""
        if self.running:
            return

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind(("127.0.0.1", self.port))
            self.sock.settimeout(1.0)  # 1秒超时，避免阻塞

            self.running = True
            self.thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.thread.start()
            print(f"[OK] 心跳接收器已启动，监听端口: {self.port}")
        except Exception as e:
            print(f"[ERROR] 心跳接收器启动失败: {e}")

    def stop(self):
        """停止心跳接收"""
        self.running = False
        if self.sock:
            self.sock.close()
        if self.thread:
            self.thread.join(timeout=2.0)

    def _receive_loop(self):
        """心跳接收循环"""
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                heartbeat = json.loads(data.decode("utf-8"))

                with self.lock:
                    self.services[heartbeat["service"]] = {
                        "last_heartbeat": time.time(),
                        "status": heartbeat["status"],
                        "pid": heartbeat["pid"],
                        "data": heartbeat.get("data", {}),
                        "addr": addr,
                    }

            except socket.timeout:
                continue  # 正常超时，继续监听
            except Exception as e:
                if self.running:  # 只在运行时打印错误
                    print(f"WARNING: 心跳接收错误: {e}")

    def get_service_status(self, service_name: str) -> Optional[Dict]:
        """获取服务状态"""
        with self.lock:
            return self.services.get(service_name)

    def get_all_services(self) -> Dict[str, Dict]:
        """获取所有服务状态"""
        with self.lock:
            return self.services.copy()

    def is_service_alive(self, service_name: str, timeout: float = 10.0) -> bool:
        """检查服务是否存活"""
        service_info = self.get_service_status(service_name)
        if not service_info:
            return False

        time_since_last = time.time() - service_info["last_heartbeat"]
        return time_since_last <= timeout

    def get_dead_services(self, timeout: float = 10.0) -> list:
        """获取已死亡的服务列表"""
        dead_services = []
        current_time = time.time()

        with self.lock:
            for service_name, info in self.services.items():
                if current_time - info["last_heartbeat"] > timeout:
                    dead_services.append(service_name)

        return dead_services


# 全局心跳发送器实例（方便各服务使用）
_heartbeat_sender = None


def init_service_heartbeat(
    service_name: str, auto_start: bool = True
) -> SimpleHeartbeatSender:
    """初始化服务心跳发送器"""
    global _heartbeat_sender
    _heartbeat_sender = SimpleHeartbeatSender(service_name)
    if auto_start:
        _heartbeat_sender.start()
    return _heartbeat_sender


def get_heartbeat_sender() -> Optional[SimpleHeartbeatSender]:
    """获取当前心跳发送器"""
    return _heartbeat_sender


def send_heartbeat(status: str = "healthy", **kwargs):
    """快捷发送心跳方法"""
    if _heartbeat_sender:
        _heartbeat_sender.send_heartbeat(status, kwargs)
