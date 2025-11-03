#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LifeTrace 进程资源监控脚本
专门监控LifeTrace相关进程的CPU和内存使用情况
"""

import psutil
import time
import json
import csv
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import argparse
import signal
import sys


class LifeTraceMonitor:
    """LifeTrace进程资源监控器"""

    def __init__(self, interval: float = 1.0, duration: float = 3600):
        """
        初始化监控器

        Args:
            interval: 监控间隔(秒)
            duration: 总监控时长(秒)
        """
        self.interval = interval
        self.duration = duration
        self.running = False
        self.data = []
        self.start_time = None

    def get_lifetrace_processes(self) -> List[psutil.Process]:
        """获取LifeTrace相关进程"""
        lifetrace_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                name = proc.info['name'].lower() if proc.info['name'] else ''
                cmdline = ' '.join(proc.info['cmdline']).lower() if proc.info['cmdline'] else ''

                # 检查是否是LifeTrace相关进程
                is_lifetrace = (
                    'lifetrace' in name or 'lifetrace' in cmdline or
                    'LifeTrace' in cmdline or 'LifeTrace_app' in cmdline or
                    any('D:\\lifetrace\\LifeTrace_app' in part for part in proc.info['cmdline']) or
                    any('d:\\lifetrace\\lifetrace_app' in part.lower() for part in proc.info['cmdline'])
                )

                if is_lifetrace:
                    lifetrace_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return lifetrace_processes

    def get_process_metrics(self, proc: psutil.Process) -> Dict[str, Any]:
        """获取单个进程的指标"""
        try:
            # 获取CPU使用率
            cpu_percent = proc.cpu_percent(interval=0.1)

            # 获取内存使用
            memory_info = proc.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024

            # 获取进程状态
            status = proc.status()

            return {
                'pid': proc.pid,
                'name': proc.name(),
                'cpu_percent': cpu_percent,
                'memory_mb': memory_mb,
                'status': status,
                'cmdline': proc.cmdline(),
                'create_time': proc.create_time(),
                'threads': proc.num_threads()
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None

    def get_lifetrace_metrics(self) -> Dict[str, Any]:
        """获取LifeTrace进程指标"""
        try:
            processes = self.get_lifetrace_processes()
            process_metrics = []

            for proc in processes:
                metrics = self.get_process_metrics(proc)
                if metrics:
                    process_metrics.append(metrics)

            # 计算总资源使用
            total_cpu = sum(proc['cpu_percent'] for proc in process_metrics)
            total_memory = sum(proc['memory_mb'] for proc in process_metrics)

            return {
                'timestamp': datetime.now().isoformat(),
                'total_cpu_percent': total_cpu,
                'total_memory_mb': total_memory,
                'process_count': len(process_metrics),
                'processes': process_metrics
            }

        except Exception as e:
            print(f"获取LifeTrace进程指标时出错: {e}")
            return {}

    def start_monitoring(self):
        """开始监控"""
        self.running = True
        self.start_time = datetime.now()
        end_time = self.start_time + timedelta(seconds=self.duration)

        print(f"🚀 开始LifeTrace进程资源监控")
        print(f"⏰ 监控间隔: {self.interval}秒")
        print(f"⏱️  总时长: {self.duration}秒 ({timedelta(seconds=self.duration)})")
        print(f"⏰ 预计结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 60)

        try:
            while self.running and datetime.now() < end_time:
                metrics = self.get_lifetrace_metrics()
                if metrics:
                    self.data.append(metrics)

                    # 实时显示关键指标
                    total_cpu = metrics['total_cpu_percent']
                    total_memory = metrics['total_memory_mb']
                    process_count = metrics['process_count']

                    print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                          f"进程数: {process_count:2d} | "
                          f"总CPU: {total_cpu:5.1f}% | "
                          f"总内存: {total_memory:6.1f}MB")

                time.sleep(self.interval)

        except KeyboardInterrupt:
            print("\n⏹️  用户中断监控")
        except Exception as e:
            print(f"\n❌ 监控过程中出错: {e}")
        finally:
            self.stop_monitoring()

    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        print("\n✅ 监控已停止")

    def generate_report(self, output_dir: str = "reports"):
        """生成监控报告"""
        if not self.data:
            print("❌ 没有监控数据可生成报告")
            return

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 保存原始数据(JSON)
        json_file = os.path.join(output_dir, f"lifetrace_metrics_{timestamp}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

        # 保存CSV数据
        csv_file = os.path.join(output_dir, f"lifetrace_metrics_{timestamp}.csv")
        self._save_csv(csv_file)

        # 生成Markdown报告
        md_file = os.path.join(output_dir, f"lifetrace_monitor_report_{timestamp}.md")
        self._generate_markdown_report(md_file)

        print(f"📊 监控报告已生成:")
        print(f"   📄 JSON数据: {json_file}")
        print(f"   📊 CSV数据: {csv_file}")
        print(f"   📋 Markdown报告: {md_file}")

    def _save_csv(self, csv_file: str):
        """保存CSV格式数据"""
        if not self.data:
            return

        # 提取字段
        fieldnames = ['timestamp', 'total_cpu_percent', 'total_memory_mb', 'process_count']

        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for entry in self.data:
                writer.writerow({
                    'timestamp': entry['timestamp'],
                    'total_cpu_percent': entry['total_cpu_percent'],
                    'total_memory_mb': entry['total_memory_mb'],
                    'process_count': entry['process_count']
                })

    def _generate_markdown_report(self, md_file: str):
        """生成Markdown格式报告"""
        if not self.data:
            return

        # 计算统计信息
        cpu_values = [entry['total_cpu_percent'] for entry in self.data]
        memory_values = [entry['total_memory_mb'] for entry in self.data]

        avg_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else 0
        max_cpu = max(cpu_values) if cpu_values else 0
        min_cpu = min(cpu_values) if cpu_values else 0

        avg_memory = sum(memory_values) / len(memory_values) if memory_values else 0
        max_memory = max(memory_values) if memory_values else 0
        min_memory = min(memory_values) if memory_values else 0

        total_samples = len(self.data)
        duration_seconds = total_samples * self.interval

        # 进程统计
        process_stats = {}
        for entry in self.data:
            for proc in entry.get('processes', []):
                proc_name = proc['name']
                if proc_name not in process_stats:
                    process_stats[proc_name] = {
                        'cpu_values': [],
                        'memory_values': []
                    }
                process_stats[proc_name]['cpu_values'].append(proc['cpu_percent'])
                process_stats[proc_name]['memory_values'].append(proc['memory_mb'])

        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(f"# LifeTrace 进程资源监控报告\n\n")
            f.write(f"**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**监控开始时间**: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**监控时长**: {timedelta(seconds=duration_seconds)}\n\n")
            f.write(f"**采样间隔**: {self.interval}秒\n\n")
            f.write(f"**总采样数**: {total_samples}\n\n")

            f.write("## 📊 关键指标统计\n\n")
            f.write("| 指标 | 平均值 | 最大值 | 最小值 | 单位 |\n")
            f.write("|------|--------|--------|--------|------|\n")
            f.write(f"| CPU使用率 | {avg_cpu:.1f} | {max_cpu:.1f} | {min_cpu:.1f} | % |\n")
            f.write(f"| 内存使用 | {avg_memory:.1f} | {max_memory:.1f} | {min_memory:.1f} | MB |\n")

            if process_stats:
                f.write("\n## 🔍 进程资源使用统计\n\n")
                f.write("| 进程名 | 平均CPU | 最大CPU | 平均内存 | 最大内存 | 单位 |\n")
                f.write("|--------|---------|---------|----------|----------|------|\n")

                for proc_name, stats in process_stats.items():
                    avg_cpu_proc = sum(stats['cpu_values']) / len(stats['cpu_values']) if stats['cpu_values'] else 0
                    max_cpu_proc = max(stats['cpu_values']) if stats['cpu_values'] else 0
                    avg_mem_proc = sum(stats['memory_values']) / len(stats['memory_values']) if stats['memory_values'] else 0
                    max_mem_proc = max(stats['memory_values']) if stats['memory_values'] else 0

                    f.write(f"| {proc_name} | {avg_cpu_proc:.1f} | {max_cpu_proc:.1f} | {avg_mem_proc:.1f} | {max_mem_proc:.1f} | MB |\n")

            f.write("\n## 🎯 性能评估\n\n")
            f.write("### CPU性能评估\n\n")
            if avg_cpu < 10:
                f.write("✅ **优秀**: CPU占用率 < 10% (达到优秀标准)\n\n")
            elif avg_cpu < 20:
                f.write("👍 **良好**: CPU占用率 10-20% (达到良好标准)\n\n")
            elif avg_cpu < 30:
                f.write("⚠️ **可接受**: CPU占用率 20-30% (达到可接受标准)\n\n")
            else:
                f.write("❌ **需要优化**: CPU占用率 > 30% (超出可接受范围)\n\n")

            f.write("### 内存性能评估\n\n")
            if avg_memory < 500:
                f.write("✅ **优秀**: 内存占用 < 500MB (达到优秀标准)\n\n")
            elif avg_memory < 1000:
                f.write("👍 **良好**: 内存占用 500-1000MB (达到良好标准)\n\n")
            elif avg_memory < 2000:
                f.write("⚠️ **可接受**: 内存占用 1-2GB (达到可接受标准)\n\n")
            else:
                f.write("❌ **需要注意**: 内存占用 > 2GB (可能需要优化)\n\n")

            f.write("## 📋 原始数据文件\n\n")
            f.write("- `lifetrace_metrics_*.json`: 完整的监控数据(JSON格式)\n")
            f.write("- `lifetrace_metrics_*.csv`: 扁平化的监控数据(CSV格式)\n")
            f.write("- `lifetrace_monitor_report_*.md`: 本报告文件\n\n")

            f.write("## 🔧 使用说明\n\n")
            f.write("```bash\n")
            f.write("# 默认使用：12小时监控，10分钟采样间隔\n")
            f.write("python lifetrace_monitor.py\n\n")
            f.write("# 自定义时长和间隔\n")
            f.write("python lifetrace_monitor.py --duration 86400 --interval 300\n\n")
            f.write("# 指定输出目录\n")
            f.write("python lifetrace_monitor.py --output custom_reports\n")
            f.write("```\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='LifeTrace进程资源监控工具')
    parser.add_argument('--interval', type=float, default=600.0,
                       help='监控间隔(秒)，默认600秒(10分钟)')
    parser.add_argument('--duration', type=float, default=43200,
                       help='监控总时长(秒)，默认43200秒(12小时)')
    parser.add_argument('--output', type=str, default='tech_report',
                       help='报告输出目录，默认tech_report')

    args = parser.parse_args()

    # 创建监控器
    monitor = LifeTraceMonitor(interval=args.interval, duration=args.duration)

    # 设置信号处理
    def signal_handler(sig, frame):
        print("\n🛑 接收到中断信号，停止监控...")
        monitor.stop_monitoring()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # 开始监控
        monitor.start_monitoring()

        # 生成报告
        if monitor.data:
            print("\n📊 正在生成监控报告...")
            monitor.generate_report(args.output)
        else:
            print("❌ 没有收集到监控数据")

    except Exception as e:
        print(f"❌ 监控过程中发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
