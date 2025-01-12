#!/usr/bin/env python3
from typing import Dict, List, Any
import os
from .base_validator import BaseValidator, ErrorSeverity

class SchemaValidator(BaseValidator):
    def __init__(self, meta_dir: str):
        super().__init__(meta_dir)
        self.schemas_dir = os.path.join(meta_dir, "schemas")

    def validate_error_codes(self, data: Dict[str, Any], file_path: str) -> bool:
        """エラーコードの検証"""
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
                        self.add_error(
                            f"無効な標準エラーコード in {os.path.basename(file_path)}: {code}",
                            ErrorSeverity.CRITICAL
                        )
                        valid = False
                # サーバー固有エラーコードの範囲チェック
                elif not (-32099 <= code <= -32000):
                    self.add_error(
                        f"範囲外のエラーコード in {os.path.basename(file_path)}: {code}",
                        ErrorSeverity.CRITICAL
                    )
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
                        self.add_error(
                            f"標準エラーコードの定義が不正 in {os.path.basename(file_path)}",
                            ErrorSeverity.CRITICAL
                        )
                        valid = False
                    
                    # サーバー固有エラーコードの範囲検証
                    range_def = next((item for item in code_def if 'minimum' in item and 'maximum' in item), None)
                    if not range_def or range_def.get('minimum') != -32099 or range_def.get('maximum') != -32000:
                        self.add_error(
                            f"サーバー固有エラーコードの範囲定義が不正 in {os.path.basename(file_path)}",
                            ErrorSeverity.CRITICAL
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
                    self.add_error(
                        f"無効なスキーマ参照 in {os.path.basename(file_path)}: {ref}",
                        ErrorSeverity.CRITICAL
                    )
                    valid = False
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
                self.add_error(
                    f"無効なトランスポートタイプ in {current_file}: {transport_type}",
                    ErrorSeverity.CRITICAL
                )
                valid = False

            # リモートトランスポートの追加検証
            if transport_type == 'remote':
                if not self._validate_remote_transport(transport, current_file):
                    valid = False

        # タイムアウト設定の検証
        if 'timeout' in transport:
            timeout = transport['timeout']
            if not isinstance(timeout, (int, float)):
                self.add_error(
                    f"無効なタイムアウト値 in {current_file}",
                    ErrorSeverity.CRITICAL
                )
                valid = False
            elif timeout <= 0 or timeout > 30:
                self.add_error(
                    f"不適切なタイムアウト値 in {current_file}: {timeout}秒",
                    ErrorSeverity.CRITICAL
                )
                valid = False

        return valid

    def _validate_remote_transport(self, transport: Dict[str, Any], file_path: str) -> bool:
        """リモートトランスポートの詳細検証"""
        valid = True

        # サービスディスカバリー設定の検証
        if 'discovery' not in transport:
            self.add_error(
                f"リモート設定エラー: サービスディスカバリー設定が欠落 in {file_path}",
                ErrorSeverity.CRITICAL
            )
            return False

        discovery = transport['discovery']
        required_discovery_fields = ['methods', 'timeout', 'retry_policy']
        for field in required_discovery_fields:
            if field not in discovery:
                self.add_error(
                    f"サービスディスカバリー設定エラー: 必須フィールド {field} が欠落 in {file_path}",
                    ErrorSeverity.CRITICAL
                )
                valid = False

        # サービスディスカバリー方式の検証
        if 'methods' in discovery:
            methods = discovery['methods']
            valid_methods = {'dns', 'http', 'manual'}
            configured_methods = set(methods)
            if not configured_methods.intersection(valid_methods):
                self.add_error(
                    f"無効なサービスディスカバリー方式 in {file_path}: {methods}",
                    ErrorSeverity.CRITICAL
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
            self.add_error(
                f"リモート設定エラー: セキュリティ設定が欠落 in {file_path}",
                ErrorSeverity.CRITICAL
            )
            valid = False
        else:
            security = transport['security']
            if not security.get('tls_required', True):
                self.add_error(
                    f"セキュリティリスク: TLSが無効 in {file_path}",
                    ErrorSeverity.CRITICAL
                )
                valid = False
            if not security.get('certificate_validation', True):
                self.add_error(
                    f"セキュリティリスク: 証明書検証が無効 in {file_path}",
                    ErrorSeverity.CRITICAL
                )
                valid = False

        return valid

    def _validate_dns_discovery(self, config: Dict[str, Any], file_path: str) -> bool:
        """DNS方式のサービスディスカバリー設定を検証"""
        valid = True

        # セキュアDNSの検証
        if not config.get('secure_lookup', True):
            self.add_error(
                f"セキュリティリスク: 安全でないDNSルックアップ in {file_path}",
                ErrorSeverity.CRITICAL
            )
            valid = False

        # DNSSECの検証
        if not config.get('dnssec_validation', True):
            self.add_error(
                f"セキュリティリスク: DNSSEC検証が無効 in {file_path}",
                ErrorSeverity.CRITICAL
            )
            valid = False

        return valid

    def _validate_http_discovery(self, config: Dict[str, Any], file_path: str) -> bool:
        """HTTP方式のサービスディスカバリー設定を検証"""
        valid = True

        # HTTPS要件の検証
        if not config.get('use_https', True):
            self.add_error(
                f"セキュリティリスク: HTTPSが無効 in {file_path}",
                ErrorSeverity.CRITICAL
            )
            valid = False

        # SSL/TLS検証の確認
        if not config.get('verify_ssl', True):
            self.add_error(
                f"セキュリティリスク: SSL検証が無効 in {file_path}",
                ErrorSeverity.CRITICAL
            )
            valid = False

        # 証明書ピン留めの検証
        if not config.get('certificate_pinning', {}):
            self.add_warning(f"セキュリティ警告: 証明書ピン留めが未設定 in {file_path}")

        return valid