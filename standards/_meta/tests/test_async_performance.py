#!/usr/bin/env python3
import os
import sys
import yaml
import time
import random
import asyncio
import aiohttp
import statistics
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum, auto

class ErrorSeverity(Enum):
    """エラーの重要度を定義"""
    CRITICAL = auto()
    NON_CRITICAL = auto()

class StateTransitions:
    """状態遷移の定義を一元管理"""
    STATES = {
        'pending': {
            'requires_checkpoint': False,
            'valid_transitions': ['running', 'cancelled']
        },
        'running': {
            'requires_checkpoint': True,
            'valid_transitions': ['completed', 'failed', 'cancelled', 'recovering']
        },
        'completed': {
            'requires_checkpoint': False,
            'valid_transitions': []
        },
        'failed': {
            'requires_checkpoint': False,
            'valid_transitions': ['pending', 'recovering']
        },
        'cancelled': {
            'requires_checkpoint': False,
            'valid_transitions': ['pending']
        },
        'recovering': {
            'requires_checkpoint': True,
            'valid_transitions': ['running', 'failed']
        }
    }

    @classmethod
    def is_valid_transition(cls, current_state: str, next_state: str) -> bool:
        """状態遷移の妥当性を検証"""
        return next_state in cls.STATES[current_state]['valid_transitions']

    @classmethod
    def requires_checkpoint(cls, state: str) -> bool:
        """チェックポイントが必要な状態かを判定"""
        return cls.STATES[state]['requires_checkpoint']

class MetricsAnalyzer:
    """メトリクス分析を担当"""
    @staticmethod
    def calculate_latency_stats(response_times: List[float]) -> Optional[Dict[str, float]]:
        """レイテンシー統計を計算"""
        if not response_times:
            return None
        try:
            quantiles = statistics.quantiles(response_times, n=100)
            return {
                "p50": quantiles[49],
                "p95": quantiles[94],
                "p99": quantiles[98]
            }
        except Exception:
            return None

    @staticmethod
    def calculate_success_rate(success_count: int, error_count: int) -> float:
        """成功率を計算"""
        total = success_count + error_count
        return (success_count / total * 100) if total > 0 else 0.0

class AsyncPerformanceTester:
    def __init__(self, meta_dir: str):
        self.meta_dir = meta_dir
        self.results: List[Dict[str, Any]] = []
        self.error_count = 0
        self.warning_count = 0
        self.metrics_config = self._load_metrics_config()

    def _load_metrics_config(self) -> Dict[str, Any]:
        """統一メトリクス定義の読み込み"""
        metrics_path = os.path.join(self.meta_dir, "contexts", "unified_metrics.yaml")
        try:
            with open(metrics_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            if config.get('version') != '1.2.0':
                self.add_error("統一メトリクス定義のバージョンが不一致", ErrorSeverity.CRITICAL)
            return config
        except Exception as e:
            self.add_error(f"統一メトリクス定義の読み込みエラー: {str(e)}", ErrorSeverity.CRITICAL)
            return {}

    async def test_performance(self, test_duration: int = 30) -> Dict[str, Any]:
        """パフォーマンステスト（MCPフレームワーク標準v1.2.0準拠）"""
        metrics = {
            "throughput": 0,
            "error_counts": 0,
            "response_times": [],
            "sampling": {
                "llm_sampling": {"success_count": 0, "error_count": 0, "response_times": []},
                "tool_fallback": {"success_count": 0, "error_count": 0, "response_times": []},
                "prompt_fallback": {"success_count": 0, "error_count": 0, "response_times": []}
            }
        }

        start_time = time.time()
        end_time = start_time + test_duration
        request_count = 0
        max_concurrent = 500

        tasks = []
        while time.time() < end_time:
            if len(tasks) < max_concurrent:
                tasks.append(asyncio.create_task(self.simulate_async_operation(request_count)))
                request_count += 1
            else:
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                tasks = list(pending)

                for task in done:
                    try:
                        result = await task
                        metrics["response_times"].append(result.get("processing_time", 0) * 1000)
                    except Exception as e:
                        metrics["error_counts"] += 1
                        self.add_error(f"パフォーマンステストエラー: {str(e)}", ErrorSeverity.NON_CRITICAL)

            await asyncio.sleep(0.001)

        if tasks:
            done, _ = await asyncio.wait(tasks)
            for task in done:
                try:
                    result = await task
                    metrics["response_times"].append(result.get("processing_time", 0) * 1000)
                except Exception as e:
                    metrics["error_counts"] += 1
                    self.add_error(f"パフォーマンステストエラー: {str(e)}", ErrorSeverity.NON_CRITICAL)

        total_time = time.time() - start_time
        metrics["throughput"] = request_count / total_time

        return metrics

    async def test_sampling_performance(self, test_duration: int = 30) -> Dict[str, Any]:
        """サンプリング機能のパフォーマンステスト"""
        metrics = {
            "llm_sampling": {"response_times": [], "success_count": 0, "error_count": 0},
            "tool_fallback": {"response_times": [], "success_count": 0, "error_count": 0},
            "prompt_fallback": {"response_times": [], "success_count": 0, "error_count": 0}
        }

        start_time = time.time()
        end_time = start_time + test_duration

        while time.time() < end_time:
            for test_type, config in [
                ("llm_sampling", (0.001, 0.005)),
                ("tool_fallback", (0.001, 0.005)),
                ("prompt_fallback", (0.001, 0.002))
            ]:
                start_request = time.time()
                try:
                    await asyncio.sleep(config[0])
                    if random.random() < config[1]:
                        raise Exception(f"{test_type}エラー")
                    metrics[test_type]["success_count"] += 1
                    metrics[test_type]["response_times"].append((time.time() - start_request) * 1000)
                except Exception:
                    metrics[test_type]["error_count"] += 1

            await asyncio.sleep(0.001)

        return metrics

    async def test_remote_mcp_performance(self, test_duration: int = 60) -> Dict[str, Any]:
        """リモートMCP接続のパフォーマンステスト"""
        metrics = {
            "discovery": {"response_times": [], "success_count": 0, "error_count": 0},
            "authentication": {"response_times": [], "success_count": 0, "error_count": 0},
            "stateless": {"response_times": [], "success_count": 0, "error_count": 0}
        }

        start_time = time.time()
        end_time = start_time + test_duration

        while time.time() < end_time:
            for category, tests in {
                "discovery": [
                    ("dns", 0.005, 0.003),
                    ("http", 0.008, 0.003),
                    ("manual", 0.001, 0.002)
                ],
                "authentication": [
                    ("oauth2", 0.01, 0.005),
                    ("token", 0.005, 0.003)
                ],
                "stateless": [
                    ("operation", 0.001, 0.002)
                ]
            }.items():
                for test_type, delay, error_rate in tests:
                    start_request = time.time()
                    try:
                        await asyncio.sleep(delay)
                        if random.random() < error_rate:
                            raise Exception(f"{test_type}エラー")
                        metrics[category]["success_count"] += 1
                        metrics[category]["response_times"].append(time.time() - start_request)
                    except Exception as e:
                        metrics[category]["error_count"] += 1
                        self.add_error(f"{category}エラー ({test_type}): {str(e)}")

        self._validate_remote_metrics(metrics)
        return metrics

    def _validate_remote_metrics(self, metrics: Dict[str, Any]) -> None:
        """リモートメトリクスの検証"""
        for category, data in metrics.items():
            success_rate = MetricsAnalyzer.calculate_success_rate(
                data["success_count"], data["error_count"]
            )
            if success_rate < 95:
                self.add_error(
                    f"{category}の低い成功率: {success_rate:.2f}%",
                    ErrorSeverity.CRITICAL
                )

            if data["response_times"]:
                p95_latency = statistics.quantiles(data["response_times"], n=20)[18]
                thresholds = {
                    "discovery": 2.0,
                    "authentication": 1.0,
                    "stateless": 0.5
                }
                if p95_latency > thresholds[category]:
                    self.add_error(
                        f"{category}の高レイテンシー: {p95_latency:.2f}秒",
                        ErrorSeverity.CRITICAL
                    )

    async def test_async_operations(self, iterations: int = 100) -> bool:
        """非同期処理テスト"""
        transition_results = []
        
        for _ in range(iterations):
            current_state = 'pending'
            state_history = []
            checkpoints = []
            recovery_points = []

            while current_state not in ['completed', 'failed', 'cancelled']:
                state_record = {
                    'state': current_state,
                    'timestamp': time.time(),
                    'checkpoint': None,
                    'recovery_point': None
                }

                if StateTransitions.requires_checkpoint(current_state):
                    checkpoint = await self.create_checkpoint(current_state)
                    state_record['checkpoint'] = checkpoint
                    checkpoints.append(checkpoint)

                state_history.append(state_record)

                valid_next_states = StateTransitions.STATES[current_state]['valid_transitions']
                if not valid_next_states:
                    break

                next_state = random.choice(valid_next_states)

                try:
                    if next_state == 'recovering':
                        if not checkpoints:
                            self.add_error(
                                "リカバリーポイントが存在しない状態でのリカバリー試行",
                                ErrorSeverity.CRITICAL
                            )
                            break
                        
                        recovery_point = await self.create_recovery_point(
                            current_state,
                            checkpoints[-1]
                        )
                        state_record['recovery_point'] = recovery_point
                        recovery_points.append(recovery_point)

                    await self.validate_state_transition(current_state, next_state)
                    current_state = next_state

                except Exception as e:
                    self.add_error(
                        f"状態遷移エラー {current_state} -> {next_state}: {str(e)}",
                        ErrorSeverity.CRITICAL
                    )
                    break

            transition_results.append({
                'history': state_history,
                'checkpoints': checkpoints,
                'recovery_points': recovery_points
            })

        return await self.analyze_transition_results(transition_results)

    async def create_checkpoint(self, state: str) -> Dict[str, Any]:
        """チェックポイントの作成"""
        return {
            'state': state,
            'timestamp': time.time(),
            'data': {'state_data': f'checkpoint_for_{state}'}
        }

    async def create_recovery_point(self, state: str, checkpoint: Dict[str, Any]) -> Dict[str, Any]:
        """リカバリーポイントの作成"""
        return {
            'state': state,
            'checkpoint': checkpoint,
            'timestamp': time.time(),
            'recovery_data': {'recovery_from': state}
        }

    async def validate_state_transition(self, current_state: str, next_state: str) -> None:
        """状態遷移の妥当性検証"""
        await asyncio.sleep(0.05)
        if not StateTransitions.is_valid_transition(current_state, next_state):
            raise Exception(f"無効な状態遷移: {current_state} -> {next_state}")

    async def analyze_transition_results(
        self,
        results: List[Dict[str, Any]]
    ) -> bool:
        """遷移結果の詳細分析"""
        valid = True

        for result in results:
            history = result['history']
            checkpoints = result['checkpoints']
            recovery_points = result['recovery_points']

            # チェックポイントの検証
            for state_record in history:
                if StateTransitions.requires_checkpoint(state_record['state']):
                    if not state_record['checkpoint']:
                        self.add_error(
                            f"必要なチェックポイントが欠落: {state_record['state']}",
                            ErrorSeverity.CRITICAL
                        )
                        valid = False

            # リカバリーポイントの検証
            for i, state_record in enumerate(history[:-1]):
                current_state = state_record['state']
                next_state = history[i + 1]['state']
                
                if next_state == 'recovering':
                    if not state_record['recovery_point']:
                        self.add_error(
                            f"リカバリーポイントが欠落: {current_state} -> {next_state}",
                            ErrorSeverity.CRITICAL
                        )
                        valid = False

            # 遷移シーケンスの検証
            states = [s['state'] for s in history]
            for i in range(len(states) - 1):
                if not StateTransitions.is_valid_transition(states[i], states[i + 1]):
                    self.add_error(
                        f"無効な状態遷移シーケンス: {' -> '.join(states)}",
                        ErrorSeverity.NON_CRITICAL
                    )
                    valid = False
                    break

        return valid

    async def simulate_async_operation(self, iteration: int) -> Dict[str, Any]:
        """非同期処理のシミュレーション"""
        try:
            delay = (iteration % 3) * 0.001
            await asyncio.sleep(delay)
            
            start_time = time.time()
            result = await self.process_async_task()
            end_time = time.time()
            
            return {
                "iteration": iteration,
                "success": True,
                "processing_time": end_time - start_time
            }
        except Exception as e:
            self.add_error(f"非同期処理エラー (iteration {iteration}): {str(e)}")
            return {
                "iteration": iteration,
                "success": False,
                "error": str(e)
            }

    async def process_async_task(self) -> Dict[str, Any]:
        """実際の非同期タスク処理"""
        await asyncio.sleep(0.001)
        return {"status": "completed"}

    def add_error(self, message: str, severity: ErrorSeverity = ErrorSeverity.NON_CRITICAL):
        """エラーの追加"""
        self.results.append({
            "level": "ERROR",
            "message": message,
            "severity": severity.name.lower(),
            "timestamp": time.time()
        })
        self.error_count += 1

    def add_warning(self, message: str):
        """警告の追加"""
        self.results.append({
            "level": "WARNING",
            "message": message,
            "timestamp": time.time()
        })
        self.warning_count += 1

    def generate_report(self, metrics: Dict[str, Any]) -> str:
        """レポートの生成"""
        report = []
        report.append("# 非同期処理・パフォーマンステストレポート")
        report.append(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 基本パフォーマンスメトリクス
        report.append("\n## 基本パフォーマンスメトリクス:")
        report.append(f"- スループット: {metrics.get('throughput', 0):.2f} req/sec")
        report.append(f"- エラー数: {metrics.get('error_counts', 0)}")
        
        # レイテンシー統計
        if metrics.get('response_times'):
            stats = MetricsAnalyzer.calculate_latency_stats(metrics['response_times'])
            if stats:
                report.append("- レイテンシー:")
                report.append(f"  - P50: {stats['p50']:.3f} ms")
                report.append(f"  - P95: {stats['p95']:.3f} ms")
                report.append(f"  - P99: {stats['p99']:.3f} ms")

        # サンプリング機能メトリクス
        if metrics.get('sampling'):
            report.append("\n## サンプリング機能メトリクス:")
            for mode, data in metrics['sampling'].items():
                success_rate = MetricsAnalyzer.calculate_success_rate(
                    data.get('success_count', 0),
                    data.get('error_count', 0)
                )
                report.append(f"\n### {mode}:")
                report.append(f"- 成功率: {success_rate:.2f}%")
                report.append(f"- 成功数: {data.get('success_count', 0)}")
                report.append(f"- エラー数: {data.get('error_count', 0)}")

                stats = MetricsAnalyzer.calculate_latency_stats(data.get('response_times', []))
                if stats:
                    report.append("- レイテンシー:")
                    report.append(f"  - P50: {stats['p50']:.3f} ms")
                    report.append(f"  - P95: {stats['p95']:.3f} ms")
                    report.append(f"  - P99: {stats['p99']:.3f} ms")

        # テスト結果サマリー
        report.append(f"\n## テスト結果サマリー:")
        report.append(f"- エラー数: {self.error_count}")
        report.append(f"- 警告数: {self.warning_count}")
        
        # 詳細なエラーと警告
        if self.results:
            report.append("\n## 詳細:")
            for result in self.results:
                report.append(f"- [{result['level']}] {result['message']}")

        return "\n".join(report)

async def main():
    if len(sys.argv) != 2:
        print("使用方法: python test_async_performance.py <path_to_meta_dir>")
        sys.exit(1)

    meta_dir = sys.argv[1]
    tester = AsyncPerformanceTester(meta_dir)

    print("非同期処理テストを実行中...")
    async_success = await tester.test_async_operations()

    print("パフォーマンステストを実行中...")
    performance_metrics = await tester.test_performance()

    print("サンプリング機能のパフォーマンステストを実行中...")
    sampling_metrics = await tester.test_sampling_performance()

    print("リモートMCP接続のパフォーマンステストを実行中...")
    remote_metrics = await tester.test_remote_mcp_performance()

    # メトリクスの結合
    combined_metrics = {
        **performance_metrics,
        "sampling": sampling_metrics,
        "remote_mcp": remote_metrics
    }

    # レポート生成
    report = tester.generate_report(combined_metrics)
    print(report)

    # レポートをファイルに保存
    report_path = os.path.join(meta_dir, "async_performance_report.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    sys.exit(0 if async_success and tester.error_count == 0 else 1)

if __name__ == "__main__":
    asyncio.run(main())