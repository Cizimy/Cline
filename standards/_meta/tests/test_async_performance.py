#!/usr/bin/env python3
import os
import sys
import yaml
import time
import random
import asyncio
import aiohttp
import statistics
from typing import Dict, List, Any
from datetime import datetime

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
                    self.add_error("統一メトリクス定義のバージョンが不一致", "critical")
                return config
        except Exception as e:
            self.add_error(f"統一メトリクス定義の読み込みエラー: {str(e)}", "critical")
            return {}

    async def test_async_operations(self, concurrency: int = 5, iterations: int = 100) -> bool:
        """非同期処理の信頼性テスト"""
        operations = []
        for i in range(iterations):
            operations.append(self.simulate_async_operation(i))

        # 同時実行数を制限してタスクを実行
        semaphore = asyncio.Semaphore(concurrency)
        async with semaphore:
            results = await asyncio.gather(*operations, return_exceptions=True)

        # エラー分析
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        error_count = len(results) - success_count
        error_rate = (error_count / len(results)) * 100

        if error_rate > 5:  # エラー率5%以上は警告
            self.add_warning(f"高いエラー率: {error_rate:.2f}% ({error_count}/{len(results)})")
            return False

        return True

    async def simulate_async_operation(self, iteration: int) -> Dict[str, Any]:
        """非同期処理のシミュレーション"""
        try:
            # ランダムな遅延を追加してリアルな状況をシミュレート
            delay = (iteration % 3) * 0.1
            await asyncio.sleep(delay)

            # 処理時間の計測
            start_time = time.time()
            
            # 実際の処理をシミュレート
            result = await self.process_async_task()
            
            end_time = time.time()
            processing_time = end_time - start_time

            return {
                "iteration": iteration,
                "success": True,
                "processing_time": processing_time
            }

        except Exception as e:
            self.add_error(f"非同期処理エラー (iteration {iteration}): {str(e)}")
            return {
                "iteration": iteration,
                "success": False,
                "error": str(e)
            }

    async def process_async_task(self) -> Dict[str, Any]:
        """実際の非同期タスク処理とリカバリーポイントの検証"""
        state = {
            "current_state": "pending",
            "checkpoints": [],
            "recovery_point": None,
            "error_state": None
        }

        try:
            # チェックポイント1: 初期化
            state["current_state"] = "running"
            state["checkpoints"].append({
                "name": "initialization",
                "timestamp": time.time(),
                "status": "completed"
            })
            # リカバリーポイントの設定
            state["recovery_point"] = {
                "checkpoint": "initialization",
                "timestamp": time.time(),
                "data": {"initialized": True}
            }
            await asyncio.sleep(0.1)

            # チェックポイント2: メイン処理
            state["checkpoints"].append({
                "name": "main_processing",
                "timestamp": time.time(),
                "status": "completed"
            })
            # リカバリーポイントの更新
            state["recovery_point"] = {
                "checkpoint": "main_processing",
                "timestamp": time.time(),
                "data": {"processing_completed": True}
            }
            await asyncio.sleep(0.1)

            # エラー発生のシミュレーション（10%の確率）
            if random.random() < 0.1:
                raise Exception("Simulated error during processing")

            # チェックポイント3: 完了処理
            state["checkpoints"].append({
                "name": "finalization",
                "timestamp": time.time(),
                "status": "completed"
            })
            state["current_state"] = "completed"

            return {
                "status": state["current_state"],
                "checkpoints": state["checkpoints"],
                "recovery_point": state["recovery_point"]
            }

        except Exception as e:
            state["current_state"] = "failed"
            state["error_state"] = {
                "error": str(e),
                "timestamp": time.time(),
                "severity": "high" if "critical" in str(e).lower() else "low"
            }

            # リカバリー処理の実行
            try:
                if state["recovery_point"]:
                    # 最後のリカバリーポイントから処理を再開
                    state["current_state"] = "running"
                    await self.recover_from_checkpoint(state["recovery_point"])
                    state["current_state"] = "completed"
            except Exception as recovery_error:
                state["error_state"] = {
                    "error": f"Recovery failed: {str(recovery_error)}",
                    "timestamp": time.time(),
                    "severity": "critical"
                }

            return {
                "status": state["current_state"],
                "checkpoints": state["checkpoints"],
                "recovery_point": state["recovery_point"],
                "error_state": state["error_state"]
            }

    async def recover_from_checkpoint(self, recovery_point: Dict[str, Any]) -> None:
        """リカバリーポイントからの復帰処理"""
        # リカバリー処理のシミュレーション
        await asyncio.sleep(0.2)
        
        # リカバリー成功の確率（80%）
        if random.random() > 0.2:
            return
        
        raise Exception("Recovery failed")

    async def test_ipc_patterns(self, iterations: int = 50) -> bool:
        """プロセス間通信パターンのテスト"""
        ipc_patterns = ['event', 'message', 'stream', 'shared_memory']
        results = {pattern: {'success': 0, 'failure': 0} for pattern in ipc_patterns}

        for pattern in ipc_patterns:
            for _ in range(iterations):
                try:
                    await self.simulate_ipc_communication(pattern)
                    results[pattern]['success'] += 1
                except Exception as e:
                    results[pattern]['failure'] += 1
                    self.add_error(f"IPC通信エラー ({pattern}): {str(e)}")

        # 結果の分析
        for pattern, counts in results.items():
            success_rate = (counts['success'] / iterations) * 100
            if success_rate < 95:  # 95%未満の成功率は警告
                self.add_warning(f"低いIPC成功率 ({pattern}): {success_rate:.2f}%")

        return all(counts['success'] / iterations >= 0.95 for counts in results.values())

    async def simulate_ipc_communication(self, pattern: str) -> None:
        """IPCパターンのシミュレーション"""
        await asyncio.sleep(0.1)  # 通信遅延のシミュレーション
        
        if pattern == 'event':
            # イベントベースの通信シミュレーション
            await self.simulate_event_communication()
        elif pattern == 'message':
            # メッセージベースの通信シミュレーション
            await self.simulate_message_communication()
        elif pattern == 'stream':
            # ストリームベースの通信シミュレーション
            await self.simulate_stream_communication()
        elif pattern == 'shared_memory':
            # 共有メモリベースの通信シミュレーション
            await self.simulate_shared_memory_communication()

    async def simulate_event_communication(self) -> None:
        """イベントベース通信のシミュレーション"""
        await asyncio.sleep(0.05)
        if random.random() < 0.02:  # 2%の確率でエラー
            raise Exception("イベント通信エラー")

    async def simulate_message_communication(self) -> None:
        """メッセージベース通信のシミュレーション"""
        await asyncio.sleep(0.05)
        if random.random() < 0.02:  # 2%の確率でエラー
            raise Exception("メッセージ通信エラー")

    async def simulate_stream_communication(self) -> None:
        """ストリームベース通信のシミュレーション"""
        await asyncio.sleep(0.05)
        if random.random() < 0.02:  # 2%の確率でエラー
            raise Exception("ストリーム通信エラー")

    async def simulate_shared_memory_communication(self) -> None:
        """共有メモリベース通信のシミュレーション"""
        await asyncio.sleep(0.05)
        if random.random() < 0.02:  # 2%の確率でエラー
            raise Exception("共有メモリ通信エラー")

    async def test_state_transitions(self, iterations: int = 50) -> bool:
        """状態遷移の検証（MCPフレームワーク標準v1.2.0準拠）"""
        # 状態定義
        states = {
            'pending': {
                'description': '処理待機中',
                'valid_transitions': ['running', 'cancelled'],
                'requires_checkpoint': False
            },
            'running': {
                'description': '実行中',
                'valid_transitions': ['completed', 'failed', 'cancelled', 'recovering'],
                'requires_checkpoint': True
            },
            'completed': {
                'description': '正常完了',
                'valid_transitions': [],
                'requires_checkpoint': False
            },
            'failed': {
                'description': '失敗',
                'valid_transitions': ['pending', 'recovering'],
                'requires_checkpoint': False
            },
            'cancelled': {
                'description': 'キャンセル済み',
                'valid_transitions': ['pending'],
                'requires_checkpoint': False
            },
            'recovering': {
                'description': 'リカバリー中',
                'valid_transitions': ['running', 'failed'],
                'requires_checkpoint': True
            }
        }

        transition_results = []
        for _ in range(iterations):
            current_state = 'pending'
            state_history = []
            checkpoints = []
            recovery_points = []

            # 状態遷移の実行
            while current_state not in ['completed', 'failed', 'cancelled']:
                state_info = states[current_state]
                state_record = {
                    'state': current_state,
                    'timestamp': time.time(),
                    'checkpoint': None,
                    'recovery_point': None
                }

                # チェックポイントの作成
                if state_info['requires_checkpoint']:
                    checkpoint = await self.create_checkpoint(current_state)
                    state_record['checkpoint'] = checkpoint
                    checkpoints.append(checkpoint)

                # 状態の記録
                state_history.append(state_record)

                # 次の状態の選択と遷移
                valid_next_states = state_info['valid_transitions']
                if not valid_next_states:
                    break

                next_state = random.choice(valid_next_states)

                try:
                    # リカバリーが必要な状態への遷移の場合
                    if next_state == 'recovering':
                        if not checkpoints:
                            self.add_error("リカバリーポイントが存在しない状態でのリカバリー試行", "critical")
                            break
                        
                        recovery_point = await self.create_recovery_point(
                            current_state,
                            checkpoints[-1]
                        )
                        state_record['recovery_point'] = recovery_point
                        recovery_points.append(recovery_point)

                    # 状態遷移の検証
                    await self.validate_state_transition(
                        current_state,
                        next_state,
                        state_record
                    )
                    current_state = next_state

                except Exception as e:
                    self.add_error(
                        f"状態遷移エラー {current_state} -> {next_state}: {str(e)}",
                        "critical"
                    )
                    break

            transition_results.append({
                'history': state_history,
                'checkpoints': checkpoints,
                'recovery_points': recovery_points
            })

        # 遷移結果の分析
        return await self.analyze_transition_results(transition_results, states)

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

    async def analyze_transition_results(
        self,
        results: List[Dict[str, Any]],
        states: Dict[str, Dict[str, Any]]
    ) -> bool:
        """遷移結果の詳細分析"""
        valid = True

        for result in results:
            history = result['history']
            checkpoints = result['checkpoints']
            recovery_points = result['recovery_points']

            # チェックポイントの検証
            for state_record in history:
                if states[state_record['state']]['requires_checkpoint']:
                    if not state_record['checkpoint']:
                        self.add_error(
                            f"必要なチェックポイントが欠落: {state_record['state']}",
                            "critical"
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
                            "critical"
                        )
                        valid = False

            # 遷移シーケンスの検証
            if not self.validate_transition_sequence([s['state'] for s in history]):
                self.add_error(
                    f"無効な状態遷移シーケンス: {' -> '.join(s['state'] for s in history)}",
                    "non-critical"
                )
                valid = False

        return valid

    def validate_transition_sequence(self, history: List[str]) -> bool:
        """状態遷移シーケンスの検証"""
        valid_transitions = {
            'pending': ['running', 'cancelled'],
            'running': ['completed', 'failed', 'cancelled', 'recovering'],
            'completed': [],
            'failed': ['pending', 'recovering'],
            'cancelled': ['pending'],
            'recovering': ['running', 'failed']
        }

        for i in range(len(history) - 1):
            current_state = history[i]
            next_state = history[i + 1]
            if next_state not in valid_transitions[current_state]:
                return False

        return True

    async def validate_state_transition(self, current_state: str, next_state: str) -> None:
        """状態遷移の妥当性検証"""
        await asyncio.sleep(0.05)  # 遷移処理のシミュレーション
        
        # 遷移の妥当性チェック
        valid_transitions = {
            'pending': ['running', 'cancelled'],
            'running': ['completed', 'failed', 'cancelled', 'recovering'],
            'completed': [],
            'failed': ['pending', 'recovering'],
            'cancelled': ['pending'],
            'recovering': ['running', 'failed']
        }

        if next_state not in valid_transitions[current_state]:
            raise Exception(f"無効な状態遷移: {current_state} -> {next_state}")

    async def test_performance(self, test_duration: int = 60) -> bool:
        """パフォーマンステスト（MCPフレームワーク標準v1.2.0準拠）"""
        # メトリクス閾値の取得
        perf_metrics = self.metrics_config.get('base_metrics', {}).get('performance', {})
        if not perf_metrics:
            self.add_error("パフォーマンスメトリクス定義が見つかりません", "critical")
            return False

        # 閾値の取得
        throughput_thresholds = perf_metrics.get('throughput', {}).get('threshold', {})
        error_rate_thresholds = perf_metrics.get('error_rate', {}).get('threshold', {})
        response_time_thresholds = perf_metrics.get('response_time', {}).get('threshold', {})

        start_time = time.time()
        end_time = start_time + test_duration
        
        metrics = {
            "response_times": [],
            "error_counts": 0,
            "throughput": 0
        }

        request_count = 0
        
        while time.time() < end_time:
            try:
                start_request = time.time()
                await self.simulate_async_operation(request_count)
                response_time = time.time() - start_request
                
                metrics["response_times"].append(response_time * 1000)  # msに変換
                request_count += 1
                
            except Exception as e:
                metrics["error_counts"] += 1
                self.add_error(f"パフォーマンステストエラー: {str(e)}", "non-critical")

        # メトリクスの計算
        total_time = time.time() - start_time
        metrics["throughput"] = request_count / total_time
        error_rate = metrics["error_counts"] / request_count if request_count > 0 else 1.0

        # スループットの検証
        if metrics["throughput"] < throughput_thresholds.get('critical', 1000):
            self.add_error(
                f"クリティカルなスループット低下: {metrics['throughput']:.2f} req/sec",
                "critical"
            )
        elif metrics["throughput"] < throughput_thresholds.get('non_critical', 800):
            self.add_error(
                f"スループット低下: {metrics['throughput']:.2f} req/sec",
                "non-critical"
            )

        # エラー率の検証
        if error_rate > error_rate_thresholds.get('critical', 0.01):
            self.add_error(
                f"クリティカルなエラー率: {error_rate*100:.2f}%",
                "critical"
            )
        elif error_rate > error_rate_thresholds.get('non_critical', 0.005):
            self.add_error(
                f"高いエラー率: {error_rate*100:.2f}%",
                "non-critical"
            )

        # レイテンシーの分析
        if metrics["response_times"]:
            p95_latency = statistics.quantiles(metrics["response_times"], n=20)[18]  # 95パーセンタイル
            if p95_latency > response_time_thresholds.get('critical', 1000):
                self.add_error(
                    f"クリティカルな高レイテンシー (P95): {p95_latency:.2f} ms",
                    "critical"
                )
            elif p95_latency > response_time_thresholds.get('non_critical', 500):
                self.add_error(
                    f"高レイテンシー (P95): {p95_latency:.2f} ms",
                    "non-critical"
                )

        return metrics

    def add_error(self, message: str, severity: str = "non-critical"):
        """エラーの追加（MCPフレームワーク標準準拠）
        
        Args:
            message: エラーメッセージ
            severity: エラーの重要度（"critical" or "non-critical"）
        """
        self.results.append({
            "level": "ERROR",
            "message": message,
            "severity": severity,
            "timestamp": time.time(),
            "response_time": {
                "critical": 15,  # 15分以内
                "non-critical": 60  # 60分以内
            }[severity]
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
        report = []
        report.append("# 非同期処理・パフォーマンステストレポート")
        report.append(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 基本パフォーマンスメトリクス
        report.append("\n## 基本パフォーマンスメトリクス:")
        report.append(f"- スループット: {metrics['throughput']:.2f} req/sec")
        report.append(f"- エラー数: {metrics['error_counts']}")
        
        if metrics['response_times']:
            p50, p95, p99 = statistics.quantiles(metrics['response_times'], n=100)[49:100:2]
            report.append(f"- レイテンシー:")
            report.append(f"  - P50: {p50:.3f} sec")
            report.append(f"  - P95: {p95:.3f} sec")
            report.append(f"  - P99: {p99:.3f} sec")

        # サンプリング機能のメトリクス
        if 'sampling' in metrics:
            report.append("\n## サンプリング機能メトリクス:")
            for mode, data in metrics['sampling'].items():
                total_requests = data['success_count'] + data['error_count']
                if total_requests > 0:
                    success_rate = (data['success_count'] / total_requests) * 100
                    report.append(f"\n### {mode}:")
                    report.append(f"- 成功率: {success_rate:.2f}%")
                    report.append(f"- 成功数: {data['success_count']}")
                    report.append(f"- エラー数: {data['error_count']}")
                    
                    if data['response_times']:
                        p50, p95, p99 = statistics.quantiles(data['response_times'], n=100)[49:100:2]
                        report.append(f"- レイテンシー:")
                        report.append(f"  - P50: {p50:.3f} sec")
                        report.append(f"  - P95: {p95:.3f} sec")
                        report.append(f"  - P99: {p99:.3f} sec")

        report.append(f"\n## テスト結果サマリー:")
        report.append(f"- エラー数: {self.error_count}")
        report.append(f"- 警告数: {self.warning_count}")
        
        if self.results:
            report.append("\n## 詳細:")
            for result in self.results:
                report.append(f"- [{result['level']}] {result['message']}")
        else:
            report.append("\n問題は検出されませんでした。")

        return "\n".join(report)

async def test_sampling_performance(self, test_duration: int = 60) -> Dict[str, Any]:
    """サンプリング機能のパフォーマンステスト（MCPフレームワーク標準v1.2.0準拠）"""
    # メトリクス閾値の取得
    sampling_metrics = self.metrics_config.get('base_metrics', {}).get('sampling', {})
    if not sampling_metrics:
        self.add_error("サンプリングメトリクス定義が見つかりません", "critical")
        return {}

    # 閾値の取得
    throughput_thresholds = sampling_metrics.get('throughput', {}).get('threshold', {})
    latency_thresholds = sampling_metrics.get('latency', {}).get('threshold', {})
    fallback_rate_thresholds = sampling_metrics.get('fallback_rate', {}).get('threshold', {})

    metrics = {
        "llm_sampling": {
            "response_times": [],
            "success_count": 0,
            "error_count": 0
        },
        "tool_fallback": {
            "response_times": [],
            "success_count": 0,
            "error_count": 0
        },
        "prompt_fallback": {
            "response_times": [],
            "success_count": 0,
            "error_count": 0
        }
    }

    start_time = time.time()
    end_time = start_time + test_duration

    while time.time() < end_time:
        # LLMサンプリングのテスト
        start_request = time.time()
        try:
            await self.simulate_llm_sampling()
            metrics["llm_sampling"]["success_count"] += 1
            metrics["llm_sampling"]["response_times"].append(time.time() - start_request)
        except Exception as e:
            metrics["llm_sampling"]["error_count"] += 1
            # 代替機能のテスト
            try:
                # ツールベースの代替機能
                start_fallback = time.time()
                await self.simulate_tool_fallback()
                metrics["tool_fallback"]["success_count"] += 1
                metrics["tool_fallback"]["response_times"].append(time.time() - start_fallback)
            except Exception:
                metrics["tool_fallback"]["error_count"] += 1
                # プロンプトベースの代替機能
                try:
                    start_prompt = time.time()
                    await self.simulate_prompt_fallback()
                    metrics["prompt_fallback"]["success_count"] += 1
                    metrics["prompt_fallback"]["response_times"].append(time.time() - start_prompt)
                except Exception:
                    metrics["prompt_fallback"]["error_count"] += 1

    # メトリクスの計算と検証
    total_time = time.time() - start_time
    for mode, data in metrics.items():
        total_requests = data["success_count"] + data["error_count"]
        if total_requests > 0:
            # スループットの計算と検証
            throughput = data["success_count"] / total_time
            if throughput < throughput_thresholds.get('critical', 10):
                self.add_error(
                    f"{mode}のクリティカルなスループット低下: {throughput:.2f} req/sec",
                    "critical"
                )
            elif throughput < throughput_thresholds.get('warning', 20):
                self.add_warning(f"{mode}のスループット低下: {throughput:.2f} req/sec")

            # レイテンシーの分析
            if data["response_times"]:
                p95_latency = statistics.quantiles(data["response_times"], n=20)[18]
                if p95_latency > latency_thresholds.get('critical', 2000):
                    self.add_error(
                        f"{mode}のクリティカルな高レイテンシー (P95): {p95_latency:.2f} ms",
                        "critical"
                    )
                elif p95_latency > latency_thresholds.get('warning', 1000):
                    self.add_warning(f"{mode}の高レイテンシー (P95): {p95_latency:.2f} ms")

            # 代替機能使用率の検証
            if mode != "llm_sampling":
                fallback_rate = data["success_count"] / total_requests
                if fallback_rate > fallback_rate_thresholds.get('critical', 0.3):
                    self.add_error(
                        f"{mode}の高い代替機能使用率: {fallback_rate*100:.2f}%",
                        "critical"
                    )
                elif fallback_rate > fallback_rate_thresholds.get('warning', 0.2):
                    self.add_warning(f"{mode}の高い代替機能使用率: {fallback_rate*100:.2f}%")

    return metrics

async def simulate_llm_sampling(self) -> None:
    """LLMサンプリングのシミュレーション"""
    await asyncio.sleep(0.1)  # LLM呼び出しの遅延をシミュレート
    if random.random() < 0.1:  # 10%の確率で失敗
        raise Exception("LLMサンプリングエラー")

async def simulate_tool_fallback(self) -> None:
    """ツールベースの代替機能のシミュレーション"""
    await asyncio.sleep(0.05)  # ツール実行の遅延をシミュレート
    if random.random() < 0.05:  # 5%の確率で失敗
        raise Exception("ツール代替機能エラー")

async def simulate_prompt_fallback(self) -> None:
    """プロンプトベースの代替機能のシミュレーション"""
    await asyncio.sleep(0.03)  # プロンプト処理の遅延をシミュレート
    if random.random() < 0.03:  # 3%の確率で失敗
        raise Exception("プロンプト代替機能エラー")

async def test_remote_mcp_performance(self, test_duration: int = 60) -> Dict[str, Any]:
    """リモートMCP接続のパフォーマンステスト（MCPフレームワーク標準v1.2.0準拠）"""
    metrics = {
        "discovery": {
            "response_times": [],
            "success_count": 0,
            "error_count": 0
        },
        "authentication": {
            "response_times": [],
            "success_count": 0,
            "error_count": 0
        },
        "stateless": {
            "response_times": [],
            "success_count": 0,
            "error_count": 0
        }
    }

    start_time = time.time()
    end_time = start_time + test_duration

    while time.time() < end_time:
        # サービスディスカバリーのテスト
        for method in ['dns', 'http', 'manual']:
            start_request = time.time()
            try:
                await self.simulate_service_discovery(method)
                metrics["discovery"]["success_count"] += 1
                metrics["discovery"]["response_times"].append(time.time() - start_request)
            except Exception as e:
                metrics["discovery"]["error_count"] += 1
                self.add_error(f"サービスディスカバリーエラー ({method}): {str(e)}")

        # 認証処理のテスト
        for auth_type in ['oauth2', 'token']:
            start_request = time.time()
            try:
                await self.simulate_authentication(auth_type)
                metrics["authentication"]["success_count"] += 1
                metrics["authentication"]["response_times"].append(time.time() - start_request)
            except Exception as e:
                metrics["authentication"]["error_count"] += 1
                self.add_error(f"認証エラー ({auth_type}): {str(e)}")

        # ステートレス操作のテスト
        start_request = time.time()
        try:
            await self.simulate_stateless_operation()
            metrics["stateless"]["success_count"] += 1
            metrics["stateless"]["response_times"].append(time.time() - start_request)
        except Exception as e:
            metrics["stateless"]["error_count"] += 1
            self.add_error(f"ステートレス操作エラー: {str(e)}")

    # メトリクスの検証
    for category, data in metrics.items():
        total_requests = data["success_count"] + data["error_count"]
        if total_requests > 0:
            success_rate = (data["success_count"] / total_requests) * 100
            if success_rate < 95:
                self.add_error(
                    f"{category}の低い成功率: {success_rate:.2f}%",
                    "critical"
                )

            if data["response_times"]:
                p95_latency = statistics.quantiles(data["response_times"], n=20)[18]
                if category == "discovery" and p95_latency > 2.0:
                    self.add_error(
                        f"サービスディスカバリーの高レイテンシー: {p95_latency:.2f}秒",
                        "critical"
                    )
                elif category == "authentication" and p95_latency > 1.0:
                    self.add_error(
                        f"認証処理の高レイテンシー: {p95_latency:.2f}秒",
                        "critical"
                    )
                elif category == "stateless" and p95_latency > 0.5:
                    self.add_error(
                        f"ステートレス操作の高レイテンシー: {p95_latency:.2f}秒",
                        "critical"
                    )

    return metrics

async def simulate_service_discovery(self, method: str) -> None:
    """サービスディスカバリーのシミュレーション"""
    await asyncio.sleep(0.1)  # 基本的な遅延

    # 方式別の追加遅延とエラー率
    if method == 'dns':
        await asyncio.sleep(0.2)  # DNS解決の追加遅延
        if random.random() < 0.05:  # 5%のエラー率
            raise Exception("DNS解決エラー")
    elif method == 'http':
        await asyncio.sleep(0.3)  # HTTP通信の追加遅延
        if random.random() < 0.08:  # 8%のエラー率
            raise Exception("HTTP通信エラー")
    elif method == 'manual':
        if random.random() < 0.02:  # 2%のエラー率
            raise Exception("手動設定エラー")

async def simulate_authentication(self, auth_type: str) -> None:
    """認証処理のシミュレーション"""
    await asyncio.sleep(0.1)  # 基本的な遅延

    if auth_type == 'oauth2':
        await asyncio.sleep(0.3)  # OAuth2の追加遅延
        if random.random() < 0.05:  # 5%のエラー率
            raise Exception("OAuth2認証エラー")
    elif auth_type == 'token':
        await asyncio.sleep(0.1)  # トークン認証の追加遅延
        if random.random() < 0.03:  # 3%のエラー率
            raise Exception("トークン認証エラー")

async def simulate_stateless_operation(self) -> None:
    """ステートレス操作のシミュレーション"""
    await asyncio.sleep(0.05)  # 基本的な遅延
    if random.random() < 0.02:  # 2%のエラー率
        raise Exception("ステートレス操作エラー")

async def main():
    if len(sys.argv) != 2:
        print("使用方法: python test_async_performance.py <path_to_meta_dir>")
        sys.exit(1)

    meta_dir = sys.argv[1]
    tester = AsyncPerformanceTester(meta_dir)

    # 非同期処理テスト
    print("非同期処理テストを実行中...")
    async_success = await tester.test_async_operations()

    # パフォーマンステスト
    print("パフォーマンステストを実行中...")
    performance_metrics = await tester.test_performance()

    # サンプリング機能のパフォーマンステスト
    print("サンプリング機能のパフォーマンステストを実行中...")
    sampling_metrics = await tester.test_sampling_performance()

    # リモートMCP接続のパフォーマンステスト
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