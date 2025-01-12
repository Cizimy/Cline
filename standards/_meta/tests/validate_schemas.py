#!/usr/bin/env python3
import os
import sys
import yaml
import json
import jsonschema
from typing import Dict, List, Any
from datetime import datetime

class SchemaValidator:
    def __init__(self, meta_dir: str):
        self.meta_dir = meta_dir
        self.schemas_dir = os.path.join(meta_dir, "schemas")
        self.contexts_dir = os.path.join(meta_dir, "contexts")
        self.results: List[Dict[str, Any]] = []
        self.error_count = 0
        self.warning_count = 0

        # 必須ディレクトリ構造の定義
        self.required_directories = {
            'schemas': {
                'required_files': [
                    'process_schema.yaml',
                    'validation_schema.yaml',
                    'context_schema.yaml',
                    'error_schema.yaml'
                ],
                'description': 'スキーマ定義ファイル'
            },
            'contexts': {
                'required_files': [
                    'global_context.yaml',
                    'mcp_context.yaml',
                    'process_context.yaml',
                    'async_storage_patterns.yaml',
                    'unified_metrics.yaml'
                ],
                'description': 'コンテキスト定義ファイル'
            },
            'tests': {
                'required_files': [
                    'README.md',
                    'run_tests.py',
                    'validate_schemas.py',
                    'test_async_performance.py',
                    'test_security.py'
                ],
                'description': 'テストスクリプト'
            }
        }

        # ファイル命名規則の定義
        self.file_naming_rules = {
            r'^[a-z][a-z0-9_]*\.yaml$': 'YAML設定ファイル',
            r'^[a-z][a-z0-9_]*\.py$': 'Pythonスクリプト',
            r'^[A-Z][A-Z0-9_]*\.md$': 'ドキュメントファイル',
            r'^test_[a-z][a-z0-9_]*\.py$': 'テストスクリプト'
        }

    def validate_yaml_syntax(self, file_path: str) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
            return True
        except yaml.YAMLError as e:
            self.add_error(f"YAML構文エラー in {os.path.basename(file_path)}: {str(e)}")
            return False

    def validate_file_encoding(self, file_path: str) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read()
            return True
        except UnicodeDecodeError:
            self.add_error(f"ファイルエンコーディングエラー in {os.path.basename(file_path)}: UTF-8である必要があります")
            return False

    def validate_version(self, data: Dict[str, Any], file_path: str) -> bool:
        """バージョン番号の検証（MCPフレームワーク標準v1.2.0準拠）"""
        if 'version' not in data:
            self.add_error(f"バージョン情報が欠落: {os.path.basename(file_path)}", "critical")
            return False

        version = data['version']
        
        # セマンティックバージョニングの形式チェック
        import re
        semver_pattern = r'^(\d+)\.(\d+)\.(\d+)$'
        match = re.match(semver_pattern, version)
        if not match:
            self.add_error(
                f"無効なバージョン形式 in {os.path.basename(file_path)}: {version} "
                "(形式: MAJOR.MINOR.PATCH)",
                "critical"
            )
            return False

        # バージョン番号の各部分を取得
        major, minor, patch = map(int, match.groups())
        required_version = (1, 2, 0)  # MCPフレームワーク標準v1.2.0

        # メジャーバージョンの検証
        if major != required_version[0]:
            self.add_error(
                f"互換性のないメジャーバージョン in {os.path.basename(file_path)}: "
                f"{version} (必要: {required_version[0]}.x.x)",
                "critical"
            )
            return False

        # マイナーバージョンの検証
        if minor != required_version[1]:
            self.add_error(
                f"互換性のないマイナーバージョン in {os.path.basename(file_path)}: "
                f"{version} (必要: {required_version[0]}.{required_version[1]}.x)",
                "critical"
            )
            return False

        # パッチバージョンの検証
        if patch != required_version[2]:
            self.add_error(
                f"互換性のないパッチバージョン in {os.path.basename(file_path)}: "
                f"{version} (必要: {required_version[0]}.{required_version[1]}.{required_version[2]})",
                "critical"
            )
            return False

        return True

    def validate_required_fields(self, data: Dict[str, Any], required_fields: List[str], file_path: str) -> bool:
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            self.add_error(f"必須フィールド欠落 in {os.path.basename(file_path)}: {', '.join(missing_fields)}")
            return False
        return True

    def validate_error_codes(self, data: Dict[str, Any], file_path: str) -> bool:
        if 'error_codes' not in data and 'message_format' not in data:
            return True

        valid = True
        
        # error_codesの検証
        if 'error_codes' in data:
            for error in data['error_codes']:
                code = error.get('code')
                if code is None:
                    continue

                # 標準エラーコードの範囲チェック
                if -32700 <= code <= -32603:
                    if code not in [-32700, -32600, -32601, -32602, -32603]:
                        self.add_error(f"無効な標準エラーコード in {os.path.basename(file_path)}: {code}")
                        valid = False
                # サーバー固有エラーコードの範囲チェック
                elif not (-32099 <= code <= -32000):
                    self.add_error(f"範囲外のエラーコード in {os.path.basename(file_path)}: {code}")
                    valid = False

        # message_formatのエラー定義の検証
        if 'message_format' in data:
            error_def = data['message_format'].get('error', {}).get('required_fields', [])
            for field in error_def:
                if field.get('name') == 'code':
                    code_def = field.get('oneOf', [])
                    # 標準エラーコードの検証
                    standard_codes = next((item.get('enum', []) for item in code_def if 'enum' in item), [])
                    if standard_codes != [-32700, -32600, -32601, -32602, -32603]:
                        self.add_error(f"標準エラーコードの定義が不正 in {os.path.basename(file_path)}")
                        valid = False
                    
                    # サーバー固有エラーコードの範囲検証
                    range_def = next((item for item in code_def if 'minimum' in item and 'maximum' in item), None)
                    if not range_def or range_def.get('minimum') != -32099 or range_def.get('maximum') != -32000:
                        self.add_error(f"サーバー固有エラーコードの範囲定義が不正 in {os.path.basename(file_path)}")
                        valid = False

        return valid

    def validate_error_severity(self, data: Dict[str, Any], file_path: str) -> bool:
        """エラー重要度の検証（MCPフレームワーク標準v1.2.0準拠）"""
        if 'error_severity' not in data:
            return True

        valid = True
        for error in data['error_severity']:
            severity = error.get('level')
            response_time = error.get('response_time')

            # 重要度の検証
            if severity not in ['critical', 'non-critical']:
                self.add_error(
                    f"無効なエラー重要度 in {os.path.basename(file_path)}: {severity}",
                    "critical"
                )
                valid = False
                continue

            # 対応時間の検証
            max_times = {'critical': 15, 'non-critical': 60}
            if response_time is None:
                self.add_error(
                    f"対応時間が未定義 in {os.path.basename(file_path)} for {severity}",
                    severity
                )
                valid = False
            elif response_time > max_times[severity]:
                self.add_error(
                    f"{severity}重要度の対応時間超過 in {os.path.basename(file_path)}: "
                    f"{response_time}分 > {max_times[severity]}分",
                    severity
                )
                valid = False

        return valid

    def validate_schema_references(self, data: Dict[str, Any], file_path: str) -> bool:
        valid = True
        if 'references' in data:
            for ref in data['references']:
                ref_path = os.path.join(self.schemas_dir, f"{ref}.yaml")
                if not os.path.exists(ref_path):
                    self.add_error(f"無効なスキーマ参照 in {os.path.basename(file_path)}: {ref}")
                    valid = False
        return valid

    def validate_metrics(self, data: Dict[str, Any], file_path: str) -> bool:
        if 'metrics' not in data:
            return True

        valid = True
        for metric in data['metrics']:
            if 'name' not in metric:
                self.add_error(f"メトリクス名が欠落 in {os.path.basename(file_path)}")
                valid = False
            if 'type' not in metric:
                self.add_error(f"メトリクスタイプが欠落 in {os.path.basename(file_path)}")
                valid = False
            if 'unit' not in metric:
                self.add_warning(f"メトリクス単位が未定義 in {os.path.basename(file_path)}: {metric.get('name', 'unknown')}")
            if 'threshold' not in metric:
                self.add_warning(f"メトリクス閾値が未定義 in {os.path.basename(file_path)}: {metric.get('name', 'unknown')}")

        return valid

    def validate_transport(self, data: Dict[str, Any], file_path: str) -> bool:
        """トランスポート層の設定を検証"""
        if 'transport' not in data.get('mcp_protocol', {}):
            return True

        valid = True
        transport = data['mcp_protocol']['transport']

        # トランスポートタイプの検証
        if 'type' in transport:
            transport_type = transport['type']
            if transport_type not in ['stdio', 'http_sse', 'remote']:
                self.add_error(f"無効なトランスポートタイプ in {os.path.basename(file_path)}: {transport_type}")
                valid = False

        # タイムアウト設定の検証
        if 'timeout' in transport and not isinstance(transport['timeout'], (int, float)):
            self.add_error(f"無効なタイムアウト値 in {os.path.basename(file_path)}")
            valid = False

        return valid

    def validate_capabilities(self, data: Dict[str, Any], file_path: str) -> bool:
        """サーバー機能（capabilities）の検証"""
        if 'capabilities' not in data:
            return True

        valid = True
        capabilities = data['capabilities']

        required_capabilities = ['resources', 'tools', 'prompts']
        for cap in required_capabilities:
            if cap not in capabilities:
                self.add_error(f"必須のcapability欠落 in {os.path.basename(file_path)}: {cap}")
                valid = False
            elif not isinstance(capabilities[cap], bool):
                self.add_error(f"無効なcapability値 in {os.path.basename(file_path)}: {cap}")
                valid = False

        return valid

    def validate_authentication(self, data: Dict[str, Any], file_path: str) -> bool:
        """認証設定の検証"""
        if 'authentication' not in data.get('mcp_protocol', {}):
            return True

        valid = True
        auth = data['mcp_protocol']['authentication']

        # 認証タイプの検証
        if 'type' in auth:
            auth_type = auth['type']
            if auth_type not in ['none', 'oauth2', 'token']:
                self.add_error(f"無効な認証タイプ in {os.path.basename(file_path)}: {auth_type}")
                valid = False

            # OAuth2設定の検証
            if auth_type == 'oauth2' and 'config' in auth:
                config = auth['config']
                required_oauth2_fields = ['client_id', 'client_secret', 'auth_url', 'token_url']
                for field in required_oauth2_fields:
                    if field not in config:
                        self.add_error(f"OAuth2設定の必須フィールド欠落 in {os.path.basename(file_path)}: {field}")
                        valid = False

        return valid

    def validate_ipc(self, data: Dict[str, Any], file_path: str) -> bool:
        """プロセス間通信（IPC）の検証"""
        if 'ipc_schema' not in data:
            return True

        valid = True
        ipc = data['ipc_schema']

        # 必須フィールドの検証
        required_fields = ['transport_type', 'jsonrpc_message', 'timeout', 'retry_policy']
        for field in required_fields:
            if field not in ipc.get('required_fields', []):
                self.add_error(f"IPC定義の必須フィールド欠落 in {os.path.basename(file_path)}: {field}")
                valid = False

        # 通信タイプの検証
        if 'communication_type' in ipc:
            comm_type = ipc['communication_type'].get('enum', [])
            expected_types = ['event', 'message', 'stream', 'shared_memory']
            if not all(t in expected_types for t in comm_type):
                self.add_error(f"無効な通信タイプ定義 in {os.path.basename(file_path)}")
                valid = False

        return valid

    def add_error(self, message: str, severity: str = "non-critical"):
        """エラーの追加（MCPフレームワーク標準v1.2.0準拠）"""
        if severity not in ["critical", "non-critical"]:
            severity = "non-critical"
        
        self.results.append({
            "level": "ERROR",
            "severity": severity,
            "message": message,
            "response_time": 15 if severity == "critical" else 60
        })
        self.error_count += 1

    def add_warning(self, message: str):
        """警告の追加"""
        self.results.append({"level": "WARNING", "message": message})
        self.warning_count += 1

    def generate_report(self) -> str:
        report = []
        report.append("# スキーマ検証レポート")
        report.append(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"\n検証結果サマリー:")
        report.append(f"- エラー数: {self.error_count}")
        report.append(f"- 警告数: {self.warning_count}")
        
        if self.results:
            report.append("\n## 詳細:")
            for result in self.results:
                report.append(f"- [{result['level']}] {result['message']}")
        else:
            report.append("\n問題は検出されませんでした。")

        return "\n".join(report)

    def validate_all(self) -> bool:
        # スキーマファイルの検証
        schema_files = [f for f in os.listdir(self.schemas_dir) if f.endswith('.yaml')]
        for schema_file in schema_files:
            file_path = os.path.join(self.schemas_dir, schema_file)
            
            # 基本的な検証
            if not self.validate_file_encoding(file_path):
                continue
            if not self.validate_yaml_syntax(file_path):
                continue

            # ファイル内容の検証
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
            # 基本的な検証
            self.validate_version(data, file_path)
            self.validate_required_fields(data, ['version', 'type'], file_path)
            self.validate_error_codes(data, file_path)
            self.validate_schema_references(data, file_path)

            # MCPプロトコル関連の検証
            if data.get('type') in ['context_schema', 'process_schema']:
                self.validate_transport(data, file_path)
                self.validate_capabilities(data, file_path)
                self.validate_authentication(data, file_path)
                self.validate_ipc(data, file_path)

        # コンテキストファイルの検証
        context_files = [f for f in os.listdir(self.contexts_dir) if f.endswith('.yaml')]
        for context_file in context_files:
            file_path = os.path.join(self.contexts_dir, context_file)
            
            # 基本的な検証
            if not self.validate_file_encoding(file_path):
                continue
            if not self.validate_yaml_syntax(file_path):
                continue

            # ファイル内容の検証
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
            # 基本的な検証
            self.validate_version(data, file_path)
            self.validate_required_fields(data, ['version', 'type', 'required_fields'], file_path)
            self.validate_metrics(data, file_path)
            self.validate_error_severity(data, file_path)

            # MCPプロトコル関連の検証
            if 'mcp_protocol' in data:
                self.validate_transport(data, file_path)
                self.validate_capabilities(data, file_path)
                self.validate_authentication(data, file_path)
                self.validate_ipc(data, file_path)

        return self.error_count == 0

def main():
    if len(sys.argv) != 2:
        print("使用方法: python validate_schemas.py <path_to_meta_dir>")
        sys.exit(1)

    meta_dir = sys.argv[1]
    validator = SchemaValidator(meta_dir)
    success = validator.validate_all()
    
    report = validator.generate_report()
    print(report)
    
    # レポートをファイルに保存
    report_path = os.path.join(meta_dir, "validation_report.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()