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
        """スキーマ参照の検証"""
        valid = True
        if 'references' in data:
            for ref in data['references']:
                ref_path = os.path.join(self.schemas_dir, f"{ref}.yaml")
                if not os.path.exists(ref_path):
                    self.add_error(f"無効なスキーマ参照 in {os.path.basename(file_path)}: {ref}")
                    valid = False
        return valid

    def validate_context_references(self, data: Dict[str, Any], file_path: str, visited: set = None) -> bool:
        """コンテキスト間の相互参照を検証"""
        if visited is None:
            visited = set()

        valid = True
        current_file = os.path.basename(file_path)
        visited.add(current_file)

        if 'context_references' in data:
            for ref in data['context_references']:
                ref_file = f"{ref}.yaml"
                ref_path = os.path.join(self.contexts_dir, ref_file)

                # 参照先の存在確認
                if not os.path.exists(ref_path):
                    self.add_error(f"無効なコンテキスト参照 in {current_file}: {ref}")
                    valid = False
                    continue

                # 循環参照の検出
                if ref_file in visited:
                    self.add_error(
                        f"循環参照が検出されました: {' -> '.join(visited)} -> {ref_file}",
                        "critical"
                    )
                    valid = False
                    continue

                # 参照先のコンテキストを読み込んで再帰的に検証
                try:
                    with open(ref_path, 'r', encoding='utf-8') as f:
                        ref_data = yaml.safe_load(f)
                        if not self.validate_context_references(ref_data, ref_path, visited.copy()):
                            valid = False
                except Exception as e:
                    self.add_error(f"参照先コンテキストの読み込みエラー {ref_file}: {str(e)}")
                    valid = False

        return valid

    def validate_context_dependencies(self, data: Dict[str, Any], file_path: str) -> bool:
        """コンテキスト間の依存関係の整合性を検証"""
        valid = True
        current_file = os.path.basename(file_path)

        if 'dependencies' in data:
            deps = data['dependencies']
            
            # バージョン依存関係の検証
            if 'required_versions' in deps:
                for ctx, version in deps['required_versions'].items():
                    ctx_path = os.path.join(self.contexts_dir, f"{ctx}.yaml")
                    if not os.path.exists(ctx_path):
                        self.add_error(f"依存コンテキストが見つかりません in {current_file}: {ctx}")
                        valid = False
                        continue

                    try:
                        with open(ctx_path, 'r', encoding='utf-8') as f:
                            ctx_data = yaml.safe_load(f)
                            ctx_version = ctx_data.get('version')
                            if not ctx_version:
                                self.add_error(f"依存コンテキストにバージョンが定義されていません: {ctx}")
                                valid = False
                            elif not self.validate_version_compatibility(version, ctx_version):
                                self.add_error(
                                    f"バージョン互換性エラー in {current_file}: "
                                    f"{ctx} requires {version}, but found {ctx_version}"
                                )
                                valid = False
                    except Exception as e:
                        self.add_error(f"依存コンテキストの読み込みエラー {ctx}: {str(e)}")
                        valid = False

            # 機能依存関係の検証
            if 'required_features' in deps:
                for ctx, features in deps['required_features'].items():
                    ctx_path = os.path.join(self.contexts_dir, f"{ctx}.yaml")
                    if not os.path.exists(ctx_path):
                        self.add_error(f"依存コンテキストが見つかりません in {current_file}: {ctx}")
                        valid = False
                        continue

                    try:
                        with open(ctx_path, 'r', encoding='utf-8') as f:
                            ctx_data = yaml.safe_load(f)
                            available_features = ctx_data.get('features', {})
                            for feature in features:
                                if feature not in available_features:
                                    self.add_error(
                                        f"必要な機能が見つかりません in {current_file}: "
                                        f"{ctx} does not provide {feature}"
                                    )
                                    valid = False
                    except Exception as e:
                        self.add_error(f"依存コンテキストの読み込みエラー {ctx}: {str(e)}")
                        valid = False

        return valid

    def validate_version_compatibility(self, required: str, actual: str) -> bool:
        """バージョンの互換性を検証"""
        import re
        pattern = r'^(\d+)\.(\d+)\.(\d+)$'
        
        req_match = re.match(pattern, required)
        act_match = re.match(pattern, actual)
        
        if not req_match or not act_match:
            return False
            
        req_major, req_minor, req_patch = map(int, req_match.groups())
        act_major, act_minor, act_patch = map(int, act_match.groups())
        
        # メジャーバージョンは完全一致が必要
        if req_major != act_major:
            return False
            
        # マイナーバージョンは同じかそれ以上である必要がある
        if act_minor < req_minor:
            return False
            
        # 同じマイナーバージョンの場合、パッチバージョンは同じかそれ以上である必要がある
        if act_minor == req_minor and act_patch < req_patch:
            return False
            
        return True

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
        """トランスポート層の設定を検証（MCPフレームワーク標準v1.2.0準拠）"""
        if 'transport' not in data.get('mcp_protocol', {}):
            return True

        valid = True
        transport = data['mcp_protocol']['transport']
        current_file = os.path.basename(file_path)

        # トランスポートタイプの検証
        if 'type' in transport:
            transport_type = transport['type']
            if transport_type not in ['stdio', 'http_sse', 'remote']:
                self.add_error(f"無効なトランスポートタイプ in {current_file}: {transport_type}")
                valid = False

            # リモートトランスポートの追加検証
            if transport_type == 'remote':
                if not self._validate_remote_transport(transport, current_file):
                    valid = False

        # タイムアウト設定の検証
        if 'timeout' in transport:
            timeout = transport['timeout']
            if not isinstance(timeout, (int, float)):
                self.add_error(f"無効なタイムアウト値 in {current_file}")
                valid = False
            elif timeout <= 0 or timeout > 30:
                self.add_error(f"不適切なタイムアウト値 in {current_file}: {timeout}秒")
                valid = False

        return valid

    def _validate_remote_transport(self, transport: Dict[str, Any], file_path: str) -> bool:
        """リモートトランスポートの詳細検証"""
        valid = True

        # サービスディスカバリー設定の検証
        if 'discovery' not in transport:
            self.add_error(f"リモート設定エラー: サービスディスカバリー設定が欠落 in {file_path}", "critical")
            return False

        discovery = transport['discovery']
        required_discovery_fields = ['methods', 'timeout', 'retry_policy']
        for field in required_discovery_fields:
            if field not in discovery:
                self.add_error(f"サービスディスカバリー設定エラー: 必須フィールド {field} が欠落 in {file_path}", "critical")
                valid = False

        # サービスディスカバリー方式の検証
        if 'methods' in discovery:
            methods = discovery['methods']
            valid_methods = {'dns', 'http', 'manual'}
            configured_methods = set(methods)
            if not configured_methods.intersection(valid_methods):
                self.add_error(
                    f"無効なサービスディスカバリー方式 in {file_path}: {methods}",
                    "critical"
                )
                valid = False

            # 各方式の詳細設定を検証
            for method in configured_methods:
                if method == 'dns':
                    if not self._validate_dns_discovery(discovery.get('dns', {}), file_path):
                        valid = False
                elif method == 'http':
                    if not self._validate_http_discovery(discovery.get('http', {}), file_path):
                        valid = False

        # セキュリティ設定の検証
        if 'security' not in transport:
            self.add_error(f"リモート設定エラー: セキュリティ設定が欠落 in {file_path}", "critical")
            valid = False
        else:
            security = transport['security']
            if not security.get('tls_required', True):
                self.add_error(f"セキュリティリスク: TLSが無効 in {file_path}", "critical")
                valid = False
            if not security.get('certificate_validation', True):
                self.add_error(f"セキュリティリスク: 証明書検証が無効 in {file_path}", "critical")
                valid = False

        return valid

    def _validate_dns_discovery(self, config: Dict[str, Any], file_path: str) -> bool:
        """DNS方式のサービスディスカバリー設定を検証"""
        valid = True

        # セキュアDNSの検証
        if not config.get('secure_lookup', True):
            self.add_error(f"セキュリティリスク: 安全でないDNSルックアップ in {file_path}", "critical")
            valid = False

        # DNSSECの検証
        if not config.get('dnssec_validation', True):
            self.add_error(f"セキュリティリスク: DNSSEC検証が無効 in {file_path}", "critical")
            valid = False

        return valid

    def _validate_http_discovery(self, config: Dict[str, Any], file_path: str) -> bool:
        """HTTP方式のサービスディスカバリー設定を検証"""
        valid = True

        # HTTPS要件の検証
        if not config.get('use_https', True):
            self.add_error(f"セキュリティリスク: HTTPSが無効 in {file_path}", "critical")
            valid = False

        # SSL/TLS検証の確認
        if not config.get('verify_ssl', True):
            self.add_error(f"セキュリティリスク: SSL検証が無効 in {file_path}", "critical")
            valid = False

        # 証明書ピン留めの検証
        if not config.get('certificate_pinning', {}):
            self.add_warning(f"セキュリティ警告: 証明書ピン留めが未設定 in {file_path}")

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

    def validate_sampling(self, data: Dict[str, Any], file_path: str) -> bool:
        """サンプリング機能の検証（MCPフレームワーク標準v1.2.0準拠）"""
        if 'sampling' not in data:
            return True

        valid = True
        sampling = data['sampling']
        current_file = os.path.basename(file_path)

        # 基本設定の検証
        required_fields = ['enabled', 'mode', 'fallback']
        for field in required_fields:
            if field not in sampling:
                self.add_error(f"サンプリング設定の必須フィールド欠落 in {current_file}: {field}")
                valid = False

        if not valid:
            return False

        # サンプリングモードの検証
        valid_modes = ['llm', 'tool', 'prompt']
        if sampling['mode'] not in valid_modes:
            self.add_error(
                f"無効なサンプリングモード in {current_file}: {sampling['mode']}",
                "critical"
            )
            valid = False

        # LLMサンプリング設定の検証
        if sampling['mode'] == 'llm':
            if 'llm_config' not in sampling:
                self.add_error(f"LLM設定が欠落 in {current_file}")
                valid = False
            else:
                llm_config = sampling['llm_config']
                llm_required = ['model', 'temperature', 'max_tokens']
                for field in llm_required:
                    if field not in llm_config:
                        self.add_error(f"LLM設定の必須フィールド欠落 in {current_file}: {field}")
                        valid = False

                # パラメータ範囲の検証
                if 'temperature' in llm_config:
                    temp = llm_config['temperature']
                    if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                        self.add_error(f"無効なtemperature値 in {current_file}: {temp}")
                        valid = False

                if 'max_tokens' in llm_config:
                    tokens = llm_config['max_tokens']
                    if not isinstance(tokens, int) or tokens < 1:
                        self.add_error(f"無効なmax_tokens値 in {current_file}: {tokens}")
                        valid = False

        # 代替機能の検証
        if 'fallback' in sampling:
            fallback = sampling['fallback']
            if 'type' not in fallback:
                self.add_error(f"代替機能のタイプが未定義 in {current_file}")
                valid = False
            else:
                valid_types = ['tool', 'prompt']
                if fallback['type'] not in valid_types:
                    self.add_error(f"無効な代替機能タイプ in {current_file}: {fallback['type']}")
                    valid = False

                # ツールベースの代替機能の検証
                if fallback['type'] == 'tool':
                    if 'tool_config' not in fallback:
                        self.add_error(f"ツール設定が欠落 in {current_file}")
                        valid = False
                    else:
                        tool_config = fallback['tool_config']
                        tool_required = ['name', 'parameters']
                        for field in tool_required:
                            if field not in tool_config:
                                self.add_error(f"ツール設定の必須フィールド欠落 in {current_file}: {field}")
                                valid = False

                # プロンプトベースの代替機能の検証
                elif fallback['type'] == 'prompt':
                    if 'prompt_template' not in fallback:
                        self.add_error(f"プロンプトテンプレートが欠落 in {current_file}")
                        valid = False

        return valid

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

    def validate_directory_structure(self) -> bool:
        """必須ディレクトリ構造の検証"""
        valid = True
        
        # メタディレクトリの存在確認
        if not os.path.exists(self.meta_dir):
            self.add_error(f"メタディレクトリが見つかりません: {self.meta_dir}", "critical")
            return False

        # 必須ディレクトリの検証
        for dir_name, dir_info in self.required_directories.items():
            dir_path = os.path.join(self.meta_dir, dir_name)
            
            # ディレクトリの存在確認
            if not os.path.exists(dir_path):
                self.add_error(f"必須ディレクトリが見つかりません: {dir_name}", "critical")
                valid = False
                continue
            
            if not os.path.isdir(dir_path):
                self.add_error(f"{dir_name}はディレクトリではありません", "critical")
                valid = False
                continue

            # 必須ファイルの検証
            for required_file in dir_info['required_files']:
                file_path = os.path.join(dir_path, required_file)
                if not os.path.exists(file_path):
                    self.add_error(
                        f"必須ファイルが見つかりません: {dir_name}/{required_file}",
                        "critical"
                    )
                    valid = False
                elif not os.path.isfile(file_path):
                    self.add_error(
                        f"{dir_name}/{required_file}はファイルではありません",
                        "critical"
                    )
                    valid = False

        return valid

    def validate_file_naming(self, file_path: str) -> bool:
        """ファイル命名規則の検証"""
        import re
        filename = os.path.basename(file_path)
        
        # ファイルタイプに基づく命名規則の検証
        valid_rule_found = False
        for pattern, description in self.file_naming_rules.items():
            if re.match(pattern, filename):
                valid_rule_found = True
                break
        
        if not valid_rule_found:
            self.add_error(
                f"ファイル名が命名規則に違反しています: {filename}\n"
                f"適用可能な規則:\n" + "\n".join([
                    f"- {desc}: {pattern}"
                    for pattern, desc in self.file_naming_rules.items()
                ])
            )
            return False
        
        return True

    def validate_all(self) -> bool:
        # ディレクトリ構造の検証
        if not self.validate_directory_structure():
            return False

        # スキーマファイルの検証
        schema_files = [f for f in os.listdir(self.schemas_dir) if f.endswith('.yaml')]
        
        # 各スキーマファイルの命名規則を検証
        for schema_file in schema_files:
            file_path = os.path.join(self.schemas_dir, schema_file)
            if not self.validate_file_naming(file_path):
                continue
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
        
        # 各コンテキストファイルの命名規則を検証
        for context_file in context_files:
            file_path = os.path.join(self.contexts_dir, context_file)
            if not self.validate_file_naming(file_path):
                continue

        # 各コンテキストファイルの内容を検証
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

            # コンテキスト間の相互参照と依存関係の検証
            self.validate_context_references(data, file_path)
            self.validate_context_dependencies(data, file_path)

            # MCPプロトコル関連の検証
            if 'mcp_protocol' in data:
                self.validate_transport(data, file_path)
                self.validate_capabilities(data, file_path)
                self.validate_authentication(data, file_path)
                self.validate_ipc(data, file_path)
                self.validate_sampling(data, file_path)  # サンプリング機能の検証を追加

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