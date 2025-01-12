#!/usr/bin/env python3
import os
import sys
import subprocess
import asyncio
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, NamedTuple
from enum import Enum, auto

class ErrorSeverity(Enum):
    """エラーの重要度を定義"""
    CRITICAL = auto()
    NON_CRITICAL = auto()

class TestResult(NamedTuple):
    """テスト結果を表現する型"""
    name: str
    description: str
    success: bool
    output: str
    error: Optional[str]
    severity: Optional[ErrorSeverity]

class ReportGenerator:
    """レポート生成を管理するクラス"""
    def __init__(self, meta_dir: str):
        self.meta_dir = meta_dir
        self.report_config = {
            'title': 'テスト実行サマリー',
            'sections': {
                'summary': '実行結果',
                'details': '詳細結果',
                'reports': '詳細レポート'
            },
            'report_files': {
                'validation': 'validation_report.md',
                'performance': 'async_performance_report.md',
                'security': 'security_report.md'
            }
        }

    def get_header(self, timestamp: str) -> List[str]:
        """ヘッダーセクションを生成"""
        return [
            f"# {self.report_config['title']}",
            f"実行日時: {timestamp}",
            ""
        ]

    def get_summary(self, total: int, success: int) -> List[str]:
        """サマリーセクションを生成"""
        return [
            f"## {self.report_config['sections']['summary']}",
            f"- 総テスト数: {total}",
            f"- 成功: {success}",
            f"- 失敗: {total - success}",
            ""
        ]

    def get_detail_header(self) -> str:
        """詳細セクションのヘッダーを生成"""
        return f"## {self.report_config['sections']['details']}"

    def get_report_links(self) -> List[str]:
        """関連レポートへのリンクを生成"""
        files = self.report_config['report_files']
        return [
            f"## {self.report_config['sections']['reports']}",
            f"- [スキーマ検証レポート]({files['validation']})",
            f"- [非同期処理・パフォーマンステストレポート]({files['performance']})",
            f"- [セキュリティテストレポート]({files['security']})"
        ]

    def format_test_result(self, result: TestResult) -> List[str]:
        """テスト結果を整形"""
        status = "✓" if result.success else "✗"
        lines = [f"\n### {status} {result.description}"]
        
        if result.output.strip():
            lines.extend([
                "出力:",
                "```",
                result.output.strip(),
                "```"
            ])
        
        if not result.success and result.error:
            lines.extend([
                f"重要度: {result.severity.name if result.severity else 'Unknown'}",
                "エラー:",
                "```",
                result.error.strip(),
                "```"
            ])
        elif result.error and self._is_expected_error(result.name, result.output, result.error):
            lines.extend([
                "注: 検出されたエラーは想定内の動作です",
                "```",
                result.error.strip(),
                "```"
            ])
        
        return lines

    def generate_report(self, test_results: List[TestResult]) -> str:
        """完全なレポートを生成"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        sections = []
        sections.extend(self.get_header(timestamp))
        
        total_tests = len(test_results)
        successful_tests = sum(1 for r in test_results if r.success)
        sections.extend(self.get_summary(total_tests, successful_tests))
        
        sections.append(self.get_detail_header())
        for result in test_results:
            sections.extend(self.format_test_result(result))
        
        sections.extend(["\n"] + self.get_report_links())
        
        return "\n".join(sections)

class MetricsConfig:
    """メトリクス設定を管理するクラス"""
    def __init__(self, meta_dir: str):
        self.config_path = os.path.join(meta_dir, "contexts", "unified_metrics.yaml")
        self._load_config()

    def _load_config(self):
        """unified_metrics.yamlから設定を読み込む"""
        try:
            import yaml
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            # パフォーマンス基準値の設定
            perf = config['base_metrics']['performance']
            self.response_time = perf['response_time']['threshold']
            self.throughput = perf['throughput']['threshold']
            self.error_rate = perf['error_rate']['threshold']
            
            # サンプリング基準値の設定
            sampling = config['base_metrics']['sampling']
            self.sampling_latency = sampling['latency']['threshold']
            self.sampling_throughput = sampling['throughput']['threshold']
            self.fallback_rate = sampling['fallback_rate']['threshold']
        except Exception as e:
            print(f"設定ファイルの読み込みエラー: {str(e)}")
            # デフォルト値の設定
            self.response_time = {'critical': 1000, 'non_critical': 500}
            self.throughput = {'critical': 1000, 'non_critical': 800}
            self.error_rate = {'critical': 0.01, 'non_critical': 0.005}
            self.sampling_latency = {'critical': 2000, 'warning': 1000}
            self.sampling_throughput = {'critical': 10, 'warning': 20}
            self.fallback_rate = {'critical': 0.3, 'warning': 0.2}

class TestConfig:
    """テスト設定を管理するクラス"""
    def __init__(self, meta_dir: str):
        self.meta_dir = meta_dir
        self.tests = [
            ("validate_schemas.py", "スキーマ検証"),
            ("test_async_performance.py", "非同期処理・パフォーマンステスト"),
            ("test_security.py", "セキュリティテスト")
        ]
        self.expected_errors = {
            "test_async_performance.py": [
                "httpエラー", "manualエラー", "tokenエラー",
                "operationエラー", "dnsエラー", "oauth2エラー"
            ],
            "test_security.py": [
                "認証エラー", "権限エラー", "トークンエラー"
            ]
        }

class MetricsValidator:
    """メトリクス検証を担当するクラス"""
    def __init__(self, metrics_config: MetricsConfig):
        self.config = metrics_config
        self.patterns = {
            'throughput': (r"スループット: (\d+\.\d+) req/sec", 0),
            'latency': (r"P99: (\d+\.\d+) ms", float('inf')),
            'success_rate': (r"成功率: (\d+\.\d+)%", 0)
        }

    def extract_metrics(self, output: str) -> Dict[str, float]:
        """出力からメトリクスを抽出"""
        metrics = {}
        for name, (pattern, default) in self.patterns.items():
            match = re.search(pattern, output)
            metrics[name] = float(match.group(1)) if match else default

        if 'success_rate' in metrics:
            rates = [float(rate) for rate in re.findall(self.patterns['success_rate'][0], output)]
            metrics['success_rate'] = min(rates) if rates else 0

        return metrics

    def validate_metrics(self, metrics: Dict[str, float]) -> bool:
        """メトリクスが基準を満たしているか検証"""
        return (
            metrics['throughput'] >= self.config.throughput['non_critical'] and
            metrics['latency'] <= self.config.sampling_latency['warning'] and
            metrics['success_rate'] >= (100 - self.config.error_rate['non_critical'] * 100)
        )

class ErrorAnalyzer:
    """エラー分析を担当するクラス"""
    def __init__(self, test_config: TestConfig):
        self.test_config = test_config
        self.critical_patterns = [
            (r'CRITICAL|FATAL', 'システム停止やデータ損失のリスク'),
            (r'SECURITY', 'セキュリティ違反'),
            (r'DATA_LOSS', 'データ損失'),
            (r'AUTHENTICATION|AUTH_FAIL', '認証エラー'),
            (r'PERMISSION|ACCESS_DENIED', '権限エラー')
        ]

    def determine_severity(self, error_message: str) -> Tuple[ErrorSeverity, str]:
        """エラーの重要度と理由を判定"""
        for pattern, reason in self.critical_patterns:
            if re.search(pattern, error_message.upper()):
                return ErrorSeverity.CRITICAL, reason
        return ErrorSeverity.NON_CRITICAL, "一般的なエラー"

    def is_expected_error(self, script_name: str, error: str) -> bool:
        """想定内のエラーかどうかを判定"""
        if script_name not in self.test_config.expected_errors:
            return False

        expected_errors = self.test_config.expected_errors[script_name]
        actual_errors = re.findall(r'\[ERROR\] .*?: (.+?)$', error, re.MULTILINE)
        return all(any(expected in err for expected in expected_errors)
                  for err in actual_errors)

class TestRunner:
    def __init__(self, meta_dir: str):
        self.meta_dir = meta_dir
        self.test_results: List[TestResult] = []
        self.max_parallel_tests = 3
        metrics_config = MetricsConfig(meta_dir)
        test_config = TestConfig(meta_dir)
        self.metrics_validator = MetricsValidator(metrics_config)
        self.error_analyzer = ErrorAnalyzer(test_config)

    async def _execute_test_process(self, script_path: str, env: Dict[str, str]) -> Tuple[int, str, str]:
        """テストプロセスの実行を担当"""
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-X", "utf8",
                script_path,
                self.meta_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env
            )

            stdout, stderr = await process.communicate()
            return (
                process.returncode,
                stdout.decode('utf-8-sig', errors='replace'),
                stderr.decode('utf-8-sig', errors='replace')
            )
        except Exception as e:
            return (1, "", f"プロセス実行エラー: {str(e)}")

    def _validate_test_output(self, script_name: str, output: str, error: str) -> Tuple[bool, Optional[ErrorSeverity], Optional[str]]:
        """テスト出力を検証"""
        # パフォーマンステストの場合
        if script_name == "test_async_performance.py":
            # 基本パフォーマンス指標の抽出
            throughput_match = re.search(r"スループット: (\d+\.\d+) req/sec", output)
            latency_match = re.search(r"P99: (\d+\.\d+) ms", output)
            success_rate_matches = re.findall(r"成功率: (\d+\.\d+)%", output)

            if throughput_match and latency_match and success_rate_matches:
                throughput = float(throughput_match.group(1))
                latency = float(latency_match.group(1))
                min_success_rate = min(float(rate) for rate in success_rate_matches)

                # 基準値との比較（unified_metrics.yamlの基準に基づく）
                meets_criteria = (
                    throughput >= 800 and  # non_critical threshold from unified_metrics.yaml
                    latency <= 500 and     # non_critical threshold from unified_metrics.yaml
                    min_success_rate >= 95.0
                )

                if not meets_criteria:
                    return False, ErrorSeverity.NON_CRITICAL, "パフォーマンス基準未達: 一般的なエラー"

        # エラーメッセージの検証
        if error and not self.error_analyzer.is_expected_error(script_name, error):
            severity, reason = self.error_analyzer.determine_severity(error)
            return False, severity, reason

        return True, None, None

    async def run_test(self, script_name: str, description: str) -> bool:
        """個別のテストスクリプトを実行"""
        print(f"\n実行中: {description}...")
        
        try:
            script_path = os.path.join(os.path.dirname(__file__), script_name)
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            returncode, stdout, stderr = await self._execute_test_process(script_path, env)
            
            # テスト出力を検証
            success, severity, reason = self._validate_test_output(script_name, stdout, stderr)
            
            # 結果オブジェクトを作成
            result = TestResult(
                name=script_name,
                description=description,
                success=success,
                output=stdout,
                error=stderr if stderr else reason,
                severity=severity
            )
            
            self.test_results.append(result)

            # 結果を表示
            if success:
                print(f"✓ {description} - 成功")
                if stdout.strip():
                    print("出力:")
                    print(stdout)
            else:
                print(f"✗ {description} - 失敗")
                if stderr or reason:
                    print(f"エラー出力:")
                    print(stderr if stderr else reason)
                    if severity:
                        print(f"重要度: {severity.name}")

            return success

        except Exception as e:
            error_msg = str(e)
            severity, reason = self.error_analyzer.determine_severity(error_msg)
            print(f"✗ {description} - エラー: {error_msg}")
            print(f"重要度: {severity.name} - {reason}")
            
            self.test_results.append(TestResult(
                name=script_name,
                description=description,
                success=False,
                output="",
                error=error_msg,
                severity=severity
            ))
            return False

    async def generate_and_save_report(self) -> None:
        """レポートを生成して保存"""
        report_generator = ReportGenerator(self.meta_dir)
        report = report_generator.generate_report(self.test_results)
        report_path = os.path.join(self.meta_dir, "test_summary_report.md")
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\nテスト完了。詳細は {report_path} を参照してください。")
        except Exception as e:
            print(f"レポート保存中にエラーが発生: {str(e)}")
            raise

class TestExecutor:
    """テスト実行を管理するクラス"""
    def __init__(self, meta_dir: str):
        self.runner = TestRunner(meta_dir)
        self.test_config = TestConfig(meta_dir)

    async def execute_tests(self) -> bool:
        """テストを実行し、結果を返す"""
        async def run_test_wrapper(test: Tuple[str, str]) -> bool:
            script, desc = test
            return await self.runner.run_test(script, desc)

        # セマフォを使用して並列実行数を制限
        semaphore = asyncio.Semaphore(self.runner.max_parallel_tests)
        async def run_with_semaphore(test: Tuple[str, str]) -> bool:
            async with semaphore:
                return await run_test_wrapper(test)

        results = await asyncio.gather(
            *(run_with_semaphore(test) for test in self.test_config.tests)
        )

        await self.runner.generate_and_save_report()
        return all(results)

async def main():
    if len(sys.argv) != 2:
        print("使用方法: python run_tests.py <path_to_meta_dir>")
        sys.exit(1)

    try:
        meta_dir = sys.argv[1]
        executor = TestExecutor(meta_dir)
        success = await executor.execute_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"テスト実行中にエラーが発生: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())