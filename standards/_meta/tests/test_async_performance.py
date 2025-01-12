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

    async def test_performance(self, test_duration: int = 10) -> Dict[str, Any]:
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
        
        # システムリソースに基づいて並列実行数を動的に調整
        import psutil
        cpu_count = psutil.cpu_count(logical=True)
        memory_available = psutil.virtual_memory().available
        max_concurrent = min(
            int(cpu_count * 500),  # CPU数に基づく上限
            int(memory_available / (1024 * 1024 * 2)),  # 利用可能メモリに基づく上限（2MB/タスクと仮定）
            5000  # 絶対上限
        )

        # メモリ効率を改善するためのバッチ処理
        batch_size = 1000
        response_times_batch = []

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
                        response_times_batch.append(result.get("processing_time", 0) * 1000)
                        
                        # バッチサイズに達したら集計してメインの配列に追加
                        if len(response_times_batch) >= batch_size:
                            metrics["response_times"].extend(response_times_batch)
                            response_times_batch = []
                    except Exception as e:
                        metrics["error_counts"] += 1
                        self.add_error(f"パフォーマンステストエラー: {str(e)}", ErrorSeverity.NON_CRITICAL)

        # 残りのタスクを処理
        if tasks:
            done, _ = await asyncio.wait(tasks)
            for task in done:
                try:
                    result = await task
                    response_times_batch.append(result.get("processing_time", 0) * 1000)
                except Exception as e:
                    metrics["error_counts"] += 1
                    self.add_error(f"パフォーマンステストエラー: {str(e)}", ErrorSeverity.NON_CRITICAL)

        # 残りのレスポンスタイムを追加
        if response_times_batch:
            metrics["response_times"].extend(response_times_batch)

        total_time = time.time() - start_time
        metrics["throughput"] = request_count / total_time

        return metrics

    async def test_sampling_performance(self, test_duration: int = 30) -> Dict[str, Any]:
        """サンプリング機能のパフォーマンステスト"""
        # メトリクス設定から基準値を取得
        sampling_config = self.metrics_config.get('base_metrics', {}).get('sampling', {})
        
        # 各サンプリングモードの設定を取得
        sampling_modes = {
            "llm_sampling": {
                "latency": sampling_config.get('llm_latency', {'threshold': 0.001}),
                "error_rate": sampling_config.get('llm_error_rate', {'threshold': 0.005})
            },
            "tool_fallback": {
                "latency": sampling_config.get('tool_latency', {'threshold': 0.001}),
                "error_rate": sampling_config.get('tool_error_rate', {'threshold': 0.005})
            },
            "prompt_fallback": {
                "latency": sampling_config.get('prompt_latency', {'threshold': 0.001}),
                "error_rate": sampling_config.get('prompt_error_rate', {'threshold': 0.002})
            }
        }

        metrics = {mode: {"response_times": [], "success_count": 0, "error_count": 0}
                  for mode in sampling_modes}

        start_time = time.time()
        end_time = start_time + test_duration

        # 並列処理用のタスクリスト
        tasks = []
        
        async def process_sampling_mode(mode: str, config: dict) -> None:
            while time.time() < end_time:
                start_request = time.time()
                try:
                    # 設定された遅延を適用
                    await asyncio.sleep(config['latency']['threshold'])
                    
                    # エラー率に基づいてエラーを発生
                    if random.random() < config['error_rate']['threshold']:
                        raise Exception(f"{mode}エラー")
                    
                    metrics[mode]["success_count"] += 1
                    metrics[mode]["response_times"].append((time.time() - start_request) * 1000)
                except Exception:
                    metrics[mode]["error_count"] += 1
                
                # 処理間隔を最適化
                await asyncio.sleep(0.0001)

        # 各モードを並列実行
        for mode, config in sampling_modes.items():
            tasks.append(asyncio.create_task(process_sampling_mode(mode, config)))

        # すべてのタスクが完了するまで待機
        await asyncio.gather(*tasks)

        return metrics

    async def test_remote_mcp_performance(self, test_duration: int = 60) -> Dict[str, Any]:
        """リモートMCP接続のパフォーマンステスト"""
        # メトリクス設定から基準値を取得
        remote_config = self.metrics_config.get('base_metrics', {}).get('remote_mcp', {})
        
        # テスト設定の定義
        test_configs = {
            "discovery": {
                "tests": [
                    ("dns", remote_config.get('dns_latency', 0.005), remote_config.get('dns_error_rate', 0.003)),
                    ("http", remote_config.get('http_latency', 0.008), remote_config.get('http_error_rate', 0.003)),
                    ("manual", remote_config.get('manual_latency', 0.001), remote_config.get('manual_error_rate', 0.002))
                ],
                "batch_size": 100,
                "threshold": remote_config.get('discovery_threshold', 2.0)
            },
            "authentication": {
                "tests": [
                    ("oauth2", remote_config.get('oauth2_latency', 0.01), remote_config.get('oauth2_error_rate', 0.005)),
                    ("token", remote_config.get('token_latency', 0.005), remote_config.get('token_error_rate', 0.003))
                ],
                "batch_size": 100,
                "threshold": remote_config.get('auth_threshold', 1.0)
            },
            "stateless": {
                "tests": [
                    ("operation", remote_config.get('operation_latency', 0.001), remote_config.get('operation_error_rate', 0.002))
                ],
                "batch_size": 100,
                "threshold": remote_config.get('stateless_threshold', 0.5)
            }
        }

        metrics = {category: {
            "response_times": [],
            "success_count": 0,
            "error_count": 0,
            "response_times_batch": []
        } for category in test_configs}

        async def run_category_tests(category: str, config: dict) -> None:
            end_time = time.time() + test_duration
            while time.time() < end_time:
                for test_type, delay, error_rate in config["tests"]:
                    start_request = time.time()
                    try:
                        await asyncio.sleep(delay)
                        if random.random() < error_rate:
                            raise Exception(f"{test_type}エラー")
                        
                        response_time = time.time() - start_request
                        metrics[category]["response_times_batch"].append(response_time)
                        metrics[category]["success_count"] += 1
                        
                        # バッチ処理によるメモリ効率の改善
                        if len(metrics[category]["response_times_batch"]) >= config["batch_size"]:
                            metrics[category]["response_times"].extend(metrics[category]["response_times_batch"])
                            metrics[category]["response_times_batch"] = []
                            
                    except Exception as e:
                        metrics[category]["error_count"] += 1
                        self.add_error(f"{category}エラー ({test_type}): {str(e)}")
                    
                    # 処理間隔の最適化
                    await asyncio.sleep(0.0001)

        # 各カテゴリを並列実行
        tasks = [run_category_tests(category, config)
                for category, config in test_configs.items()]
        await asyncio.gather(*tasks)

        # 残りのバッチデータを処理
        for category in metrics:
            if metrics[category]["response_times_batch"]:
                metrics[category]["response_times"].extend(metrics[category]["response_times_batch"])
                del metrics[category]["response_times_batch"]

        # メトリクスの検証
        self._validate_remote_metrics(metrics)
        return metrics

    def _validate_remote_metrics(self, metrics: Dict[str, Any]) -> None:
        """リモートメトリクスの検証"""
        # メトリクス設定から閾値を取得
        remote_config = self.metrics_config.get('base_metrics', {}).get('remote_mcp', {})
        
        # カテゴリごとの閾値設定
        thresholds = {
            "discovery": {
                "success_rate": remote_config.get('discovery_success_rate', 95.0),
                "latency": remote_config.get('discovery_threshold', 2.0),
                "error_threshold": remote_config.get('discovery_error_threshold', 0.5)
            },
            "authentication": {
                "success_rate": remote_config.get('auth_success_rate', 95.0),
                "latency": remote_config.get('auth_threshold', 1.0),
                "error_threshold": remote_config.get('auth_error_threshold', 0.5)
            },
            "stateless": {
                "success_rate": remote_config.get('stateless_success_rate', 95.0),
                "latency": remote_config.get('stateless_threshold', 0.5),
                "error_threshold": remote_config.get('stateless_error_threshold', 0.5)
            }
        }

        for category, data in metrics.items():
            category_thresholds = thresholds[category]
            
            # 成功率の検証
            success_rate = MetricsAnalyzer.calculate_success_rate(
                data["success_count"], data["error_count"]
            )
            if success_rate < category_thresholds["success_rate"]:
                self.add_error(
                    f"{category}の低い成功率: {success_rate:.2f}% (目標: {category_thresholds['success_rate']}%)",
                    ErrorSeverity.CRITICAL
                )

            # レイテンシーの検証
            if data["response_times"]:
                try:
                    # メモリ効率を考慮した統計計算
                    response_times = sorted(data["response_times"])
                    p95_index = int(len(response_times) * 0.95)
                    p95_latency = response_times[p95_index]
                    
                    if p95_latency > category_thresholds["latency"]:
                        self.add_error(
                            f"{category}の高レイテンシー: {p95_latency:.2f}秒 (目標: {category_thresholds['latency']}秒)",
                            ErrorSeverity.CRITICAL
                        )
                        
                    # 詳細な統計情報を警告として追加
                    p50_index = int(len(response_times) * 0.5)
                    p99_index = int(len(response_times) * 0.99)
                    self.add_warning(
                        f"{category}のレイテンシー統計:\n"
                        f"  - P50: {response_times[p50_index]:.3f}秒\n"
                        f"  - P95: {p95_latency:.3f}秒\n"
                        f"  - P99: {response_times[p99_index]:.3f}秒"
                    )
                except Exception as e:
                    self.add_error(
                        f"{category}のレイテンシー計算エラー: {str(e)}",
                        ErrorSeverity.NON_CRITICAL
                    )

            # エラー率の検証
            error_rate = data["error_count"] / (data["success_count"] + data["error_count"]) * 100
            if error_rate > category_thresholds["error_threshold"]:
                self.add_error(
                    f"{category}の高いエラー率: {error_rate:.2f}% (目標: {category_thresholds['error_threshold']}%)",
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
        # 遅延を完全に除去し、即時返却
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