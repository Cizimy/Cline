#!/usr/bin/env python3
import os
import sys
import yaml
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

class ErrorCodeManager:
    """エラーコード管理クラス（MCPフレームワーク標準v1.2.0準拠）"""
    def __init__(self):
        # MCPプロトコル標準エラーコード
        self.standard_error_codes = {
            'parse_error': -32700,
            'invalid_request': -32600,
            'method_not_found': -32601,
            'invalid_params': -32602,
            'internal_error': -32603
        }
        # サーバー固有エラーコード範囲
        self.server_error_code_range = {
            'minimum': -32099,
            'maximum': -32000
        }
        # 使用済みエラーコード
        self.used_error_codes: Set[int] = set()
        # エラーコードとメッセージのマッピング
        self.error_code_mapping: Dict[int, str] = {}

    def is_valid_error_code(self, code: int) -> bool:
        """エラーコードの範囲検証"""
        if code in self.standard_error_codes.values():
            return True
        return self.server_error_code_range['minimum'] <= code <= self.server_error_code_range['maximum']

    def is_duplicate_error_code(self, code: int) -> bool:
        """エラーコードの重複チェック"""
        return code in self.used_error_codes

    def register_error_code(self, code: int, message: str) -> bool:
        """エラーコードの登録"""
        if not self.is_valid_error_code(code):
            return False
        if self.is_duplicate_error_code(code):
            return False
        self.used_error_codes.add(code)
        self.error_code_mapping[code] = message
        return True

    def get_next_available_code(self) -> int:
        """利用可能な次のエラーコードを取得"""
        for code in range(self.server_error_code_range['minimum'], self.server_error_code_range['maximum'] + 1):
            if code not in self.used_error_codes:
                return code
        raise ValueError("利用可能なエラーコードがありません")

class SecurityTester:
    def __init__(self, meta_dir: str):
        self.meta_dir = meta_dir
        self.results: List[Dict[str, Any]] = []
        self.error_count = 0
        self.warning_count = 0
        self.error_manager = ErrorCodeManager()
        # セキュリティレベル定義（MCPフレームワーク標準準拠）
        self.severity_levels = {
            'critical': {
                'response_time': 15,  # 分
                'description': 'システム停止、セキュリティ違反、データ損失リスク'
            },
            'non-critical': {
                'response_time': 60,  # 分
                'description': '一般的なエラー、パフォーマンス低下'
            }
        }
        # 脆弱性パターン
        self.vulnerability_patterns = {
            'sql_injection': r'(?i)(SELECT|INSERT|UPDATE|DELETE|DROP).*\$\{.*\}',
            'command_injection': r'(?i)(eval|exec|system|popen|subprocess\.call).*\$\{.*\}',
            'path_traversal': r'\.\./',
            'sensitive_data': r'(?i)(password|secret|key|token|credential).*:.*[^*]$',
            'insecure_protocols': r'(?i)(http://|ftp://)',
            'hardcoded_credentials': r'(?i)(password|secret|key|token|credential)["\']:\s*["\'][^*\n]{3,}["\']',
        }

    def test_file_permissions(self, file_path: str) -> bool:
        """ファイルのパーミッションをチェック"""
        try:
            stat = os.stat(file_path)
            mode = stat.st_mode

            # 世界書き込み可能なファイルをチェック
            if mode & 0o002:
                self.add_error(f"セキュリティリスク: 世界書き込み可能なファイル {file_path}")
                return False

            # グループ書き込み権限の警告
            if mode & 0o020:
                self.add_warning(f"潜在的リスク: グループ書き込み可能なファイル {file_path}")

            return True
        except Exception as e:
            self.add_error(f"パーミッションチェックエラー {file_path}: {str(e)}")
            return False

    def scan_for_vulnerabilities(self, file_path: str) -> bool:
        """ファイル内の潜在的な脆弱性をスキャン"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            is_secure = True
            for vuln_type, pattern in self.vulnerability_patterns.items():
                matches = re.finditer(pattern, content)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    self.add_error(
                        f"潜在的な{vuln_type}脆弱性: {file_path}:{line_num} - {match.group()}"
                    )
                    is_secure = False

            return is_secure
        except Exception as e:
            self.add_error(f"脆弱性スキャンエラー {file_path}: {str(e)}")
            return False

    def validate_sampling_config(self, config: Dict[str, Any]) -> bool:
        """サンプリング機能の設定検証（MCPフレームワーク標準v1.2.0準拠）"""
        is_valid = True

        if 'sampling' not in config:
            return True  # サンプリング機能は必須ではない

        sampling_config = config['sampling']

        # 基本設定の検証
        required_fields = ['enabled', 'mode', 'fallback']
        for field in required_fields:
            if field not in sampling_config:
                self.add_error(f"サンプリング設定エラー: 必須フィールド {field} が欠落", "critical")
                is_valid = False

        if not is_valid:
            return False

        # サンプリングモードの検証
        valid_modes = ['llm', 'tool', 'prompt']
        mode = sampling_config.get('mode')
        if mode not in valid_modes:
            self.add_error(f"無効なサンプリングモード: {mode}", "critical")
            is_valid = False

        # LLMサンプリング設定の検証
        if mode == 'llm':
            llm_config = sampling_config.get('llm_config', {})
            if not llm_config:
                self.add_error("LLM設定が欠落", "critical")
                is_valid = False
            else:
                # LLM設定の詳細検証
                if not self._validate_llm_sampling_config(llm_config):
                    is_valid = False

        # 代替機能の検証
        fallback = sampling_config.get('fallback', {})
        if not fallback:
            self.add_error("代替機能設定が欠落", "critical")
            is_valid = False
        else:
            # 代替機能の詳細検証
            if not self._validate_sampling_fallback_config(fallback):
                is_valid = False

        return is_valid

    def _validate_llm_sampling_config(self, config: Dict[str, Any]) -> bool:
        """LLMサンプリング設定の詳細検証"""
        is_valid = True

        # 必須パラメータの検証
        required_fields = ['model', 'temperature', 'max_tokens']
        for field in required_fields:
            if field not in config:
                self.add_error(f"LLM設定エラー: 必須フィールド {field} が欠落", "critical")
                is_valid = False

        # パラメータ範囲の検証
        if 'temperature' in config:
            temp = config['temperature']
            if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                self.add_error(f"無効なtemperature値: {temp}", "critical")
                is_valid = False

        if 'max_tokens' in config:
            tokens = config['max_tokens']
            if not isinstance(tokens, int) or tokens < 1:
                self.add_error(f"無効なmax_tokens値: {tokens}", "critical")
                is_valid = False

        # セキュリティ設定の検証
        security = config.get('security', {})
        if not security.get('input_validation', True):
            self.add_error("セキュリティリスク: LLM入力検証が無効", "critical")
            is_valid = False
        if not security.get('output_sanitization', True):
            self.add_error("セキュリティリスク: LLM出力サニタイズが無効", "critical")
            is_valid = False

        return is_valid

    def _validate_sampling_fallback_config(self, config: Dict[str, Any]) -> bool:
        """サンプリング代替機能の設定検証"""
        is_valid = True

        fallback_type = config.get('type')
        if fallback_type not in ['tool', 'prompt']:
            self.add_error(f"無効な代替機能タイプ: {fallback_type}", "critical")
            return False

        # ツールベースの代替機能の検証
        if fallback_type == 'tool':
            tool_config = config.get('tool_config', {})
            if not tool_config:
                self.add_error("ツール設定が欠落", "critical")
                is_valid = False
            else:
                # ツール設定の詳細検証
                required_tool_fields = ['name', 'parameters']
                for field in required_tool_fields:
                    if field not in tool_config:
                        self.add_error(f"ツール設定エラー: 必須フィールド {field} が欠落", "critical")
                        is_valid = False

                # ツールのセキュリティ設定
                security = tool_config.get('security', {})
                if not security.get('parameter_validation', True):
                    self.add_error("セキュリティリスク: ツールパラメータ検証が無効", "critical")
                    is_valid = False

        # プロンプトベースの代替機能の検証
        elif fallback_type == 'prompt':
            if 'prompt_template' not in config:
                self.add_error("プロンプトテンプレートが欠落", "critical")
                is_valid = False
            else:
                # プロンプトのセキュリティ設定
                security = config.get('security', {})
                if not security.get('template_validation', True):
                    self.add_error("セキュリティリスク: プロンプトテンプレート検証が無効", "critical")
                    is_valid = False

        return is_valid

    def validate_authentication_config(self, config: Dict[str, Any]) -> bool:
        """認証設定の検証（MCPフレームワーク標準v1.2.0準拠）"""
        is_valid = True
        auth_config = config.get('authentication', {})

        # 必須の認証設定をチェック
        required_auth_fields = [
            'auth_type', 'token_expiration', 'state_management',
            'session_handling', 'error_handling'
        ]
        for field in required_auth_fields:
            if field not in auth_config:
                self.add_error(f"認証設定エラー: 必須フィールド {field} が欠落", "critical")
                is_valid = False

        # 状態管理の検証
        state_config = auth_config.get('state_management', {})
        if not self._validate_state_management(state_config):
            is_valid = False

        # セッション管理の検証
        session_config = auth_config.get('session_handling', {})
        if not self._validate_session_handling(session_config):
            is_valid = False

        # トークン有効期限の検証
        token_expiration = auth_config.get('token_expiration', 0)
        if token_expiration > 24 * 60:  # 24時間以上
            self.add_error(
                f"セキュリティリスク: トークン有効期限が長すぎます ({token_expiration}分)",
                "critical"
            )
            is_valid = False
        elif token_expiration < 5:  # 5分未満
            self.add_error(
                f"セキュリティリスク: トークン有効期限が短すぎます ({token_expiration}分)",
                "critical"
            )
            is_valid = False

        # 認証方式の検証
        auth_type = auth_config.get('auth_type', '').lower()
        if auth_type not in ['none', 'oauth2', 'token']:
            self.add_error(f"セキュリティエラー: 未対応の認証方式 {auth_type}", "critical")
            is_valid = False

        # OAuth2設定の詳細検証
        if auth_type == 'oauth2':
            oauth2_config = auth_config.get('oauth2', {})
            if not self._validate_oauth2_config(oauth2_config, token_expiration):
                is_valid = False

        # トークン認証の詳細検証
        elif auth_type == 'token':
            token_config = auth_config.get('token', {})
            if not self._validate_token_config(token_config):
                is_valid = False

        return is_valid

    def _validate_state_management(self, config: Dict[str, Any]) -> bool:
        """状態管理の検証"""
        is_valid = True
        required_fields = ['storage_type', 'expiration', 'cleanup_interval']
        
        for field in required_fields:
            if field not in config:
                self.add_error(f"状態管理設定エラー: 必須フィールド {field} が欠落", "critical")
                is_valid = False

        # ストレージタイプの検証
        storage_type = config.get('storage_type', '')
        if storage_type not in ['memory', 'redis', 'database']:
            self.add_error(f"無効な状態管理ストレージタイプ: {storage_type}", "critical")
            is_valid = False

        # 有効期限の検証
        expiration = config.get('expiration', 0)
        if expiration < 1 or expiration > 60:
            self.add_error(f"無効な状態管理有効期限: {expiration}分", "critical")
            is_valid = False

        return is_valid

    def _validate_session_handling(self, config: Dict[str, Any]) -> bool:
        """セッション管理の検証"""
        is_valid = True
        required_fields = ['cookie_config', 'storage_config', 'security_config']
        
        for field in required_fields:
            if field not in config:
                self.add_error(f"セッション管理設定エラー: 必須フィールド {field} が欠落", "critical")
                is_valid = False

        # Cookieセキュリティ設定の検証
        cookie_config = config.get('cookie_config', {})
        if not cookie_config.get('secure', True):
            self.add_error("セキュリティリスク: セキュアCookieが無効", "critical")
            is_valid = False
        if not cookie_config.get('http_only', True):
            self.add_error("セキュリティリスク: HttpOnlyが無効", "critical")
            is_valid = False
        if cookie_config.get('same_site', '') not in ['Strict', 'Lax']:
            self.add_error("セキュリティリスク: 不適切なSameSite設定", "critical")
            is_valid = False

        return is_valid

    def _validate_oauth2_config(self, config: Dict[str, Any], token_expiration: int) -> bool:
        """OAuth2設定の詳細検証"""
        is_valid = True
        
        # 基本設定の検証
        required_oauth2_fields = [
            'client_id', 'client_secret', 'auth_url', 'token_url',
            'scope', 'redirect_uri', 'response_type', 'grant_types',
            'token_validation', 'pkce_config'
        ]
        for field in required_oauth2_fields:
            if field not in config:
                self.add_error(f"OAuth2設定エラー: 必須フィールド {field} が欠落", "critical")
                is_valid = False

        # リダイレクトURIの検証
        redirect_uri = config.get('redirect_uri', '')
        if not redirect_uri.startswith('https://'):
            self.add_error("セキュリティリスク: OAuth2リダイレクトURIが非HTTPS", "critical")
            is_valid = False

        # スコープの検証
        scopes = config.get('scope', '').split()
        if not scopes:
            self.add_error("セキュリティリスク: OAuth2スコープが未定義", "critical")
            is_valid = False
        elif 'offline_access' in scopes:
            if token_expiration > 12 * 60:
                self.add_error(
                    "セキュリティリスク: offline_accessスコープで長期トークン",
                    "critical"
                )
                is_valid = False

        # PKCE設定の検証
        pkce_config = config.get('pkce_config', {})
        if not pkce_config.get('enabled', False):
            self.add_error("セキュリティリスク: PKCEが無効", "critical")
            is_valid = False
        elif pkce_config.get('method', '') != 'S256':
            self.add_error("セキュリティリスク: 非推奨のPKCEメソッド", "critical")
            is_valid = False

        # トークン検証設定の確認
        token_validation = config.get('token_validation', {})
        if not token_validation.get('verify_exp', True):
            self.add_error("セキュリティリスク: トークン有効期限検証が無効", "critical")
            is_valid = False
        if not token_validation.get('verify_iss', True):
            self.add_error("セキュリティリスク: トークン発行者検証が無効", "critical")
            is_valid = False

        return is_valid

    def _validate_token_config(self, config: Dict[str, Any]) -> bool:
        """トークン認証の詳細検証"""
        is_valid = True

        if not config:
            self.add_error("セキュリティエラー: トークン設定が未定義", "critical")
            return False

        # トークン管理設定の検証
        token_management = config.get('management', {})
        if not token_management:
            self.add_error("セキュリティエラー: トークン管理設定が未定義", "critical")
            return False

        # トークンローテーションの検証
        if not token_management.get('rotation_enabled', False):
            self.add_error("セキュリティリスク: トークンローテーションが無効", "critical")
            is_valid = False

        rotation_interval = token_management.get('rotation_interval', 0)
        if rotation_interval > 24 * 60:
            self.add_error(
                f"セキュリティリスク: トークンローテーション間隔が長すぎます ({rotation_interval}分)",
                "critical"
            )
            is_valid = False
        elif rotation_interval < 5:
            self.add_error(
                f"セキュリティリスク: トークンローテーション間隔が短すぎます ({rotation_interval}分)",
                "critical"
            )
            is_valid = False

        # トークンの保存方法の検証
        storage_config = token_management.get('storage', {})
        if storage_config.get('type', '') not in ['encrypted', 'secure_keystore']:
            self.add_error("セキュリティリスク: 非推奨のトークン保存方式", "critical")
            is_valid = False

        # トークンの暗号化方式の検証
        encryption_config = token_management.get('encryption', {})
        if not encryption_config:
            self.add_error("セキュリティエラー: トークン暗号化設定が未定義", "critical")
            is_valid = False
        elif encryption_config.get('algorithm', '') not in ['AES-256-GCM', 'ChaCha20-Poly1305']:
            self.add_error("セキュリティリスク: 非推奨の暗号化アルゴリズム", "critical")
            is_valid = False

        # トークン検証設定の確認
        validation_config = config.get('validation', {})
        if not validation_config:
            self.add_error("セキュリティエラー: トークン検証設定が未定義", "critical")
            is_valid = False
        else:
            required_validations = ['signature', 'expiration', 'issuer', 'audience']
            for validation in required_validations:
                if not validation_config.get(f'verify_{validation}', False):
                    self.add_error(f"セキュリティリスク: {validation}検証が無効", "critical")
                    is_valid = False

        return is_valid

    def validate_error_handling(self, config: Dict[str, Any]) -> bool:
        """エラーハンドリング設定の検証"""
        is_valid = True

        if 'error_handling' not in config:
            self.add_error("セキュリティエラー: エラーハンドリング設定が欠落")
            return False

        error_config = config['error_handling']

        # 機密情報の漏洩防止設定
        if not error_config.get('sanitize_errors', True):
            self.add_error("セキュリティリスク: エラーメッセージのサニタイズが無効")
            is_valid = False

        # エラーログレベルの検証
        if 'log_level' not in error_config:
            self.add_warning("セキュリティ警告: エラーログレベルが未設定")
        elif error_config['log_level'].lower() not in ['error', 'warn', 'info']:
            self.add_warning(f"セキュリティ警告: 不適切なログレベル {error_config['log_level']}")

        return is_valid

    def validate_rate_limiting(self, config: Dict[str, Any]) -> bool:
        """レート制限設定の検証"""
        is_valid = True

        if 'rate_limiting' not in config:
            self.add_warning("セキュリティ警告: レート制限が未設定")
            return False

        rate_config = config['rate_limiting']

        # 基本的なレート制限設定
        if 'max_requests' not in rate_config or 'window_size' not in rate_config:
            self.add_error("セキュリティエラー: レート制限の基本設定が欠落")
            is_valid = False
        else:
            # レート制限値の妥当性チェック
            max_requests = rate_config['max_requests']
            window_size = rate_config['window_size']
            
            if max_requests > 1000:  # 1000リクエスト/ウィンドウ以上は警告
                self.add_warning(f"セキュリティ警告: 高すぎるレート制限 ({max_requests} req/{window_size}s)")

        return is_valid

    def check_secure_defaults(self, config: Dict[str, Any]) -> bool:
        """セキュアなデフォルト設定の検証"""
        is_valid = True

        # TLS設定の検証
        if not config.get('use_tls', False):
            self.add_error("セキュリティリスク: TLSが無効")
            is_valid = False

        # CORS設定の検証
        cors_config = config.get('cors', {})
        if cors_config.get('allow_all_origins', False):
            self.add_error("セキュリティリスク: すべてのオリジンを許可するCORS設定")
            is_valid = False

        # セッション設定の検証
        session_config = config.get('session', {})
        if not session_config.get('secure_only', True):
            self.add_error("セキュリティリスク: セキュアでないセッション設定")
            is_valid = False

        return is_valid

    def add_error(self, message: str, severity: str = 'non-critical', error_code: Optional[int] = None):
        """エラーの追加（MCPフレームワーク標準v1.2.0準拠）"""
        try:
            if severity not in self.severity_levels:
                severity = 'non-critical'  # デフォルトは非クリティカル

            # エラーコードの生成と検証
            if error_code is None:
                error_code = self.error_manager.get_next_available_code()
            elif not self.error_manager.is_valid_error_code(error_code):
                self.add_warning(
                    f"無効なエラーコード {error_code} が指定されました。"
                    f"範囲 {self.error_manager.server_error_code_range['minimum']} "
                    f"～ {self.error_manager.server_error_code_range['maximum']} "
                    "内のコードを使用してください。"
                )
                error_code = self.error_manager.get_next_available_code()
            elif self.error_manager.is_duplicate_error_code(error_code):
                self.add_warning(
                    f"重複するエラーコード {error_code} が検出されました。"
                    "新しいコードを生成します。"
                )
                error_code = self.error_manager.get_next_available_code()

            # エラーコードの登録
            if not self.error_manager.register_error_code(error_code, message):
                raise ValueError(f"エラーコード {error_code} の登録に失敗しました")

            # エラー情報の記録
            self.results.append({
                "level": "ERROR",
                "severity": severity,
                "error_code": error_code,
                "message": message,
                "response_time": self.severity_levels[severity]['response_time'],
                "timestamp": datetime.now().isoformat(),
                "error_details": {
                    "code_type": "server_specific" if error_code in range(
                        self.error_manager.server_error_code_range['minimum'],
                        self.error_manager.server_error_code_range['maximum'] + 1
                    ) else "standard",
                    "registered_at": datetime.now().isoformat()
                }
            })
            self.error_count += 1

        except ValueError as e:
            # エラーコード管理に問題が発生した場合のフォールバック
            fallback_code = self.error_manager.standard_error_codes['internal_error']
            self.results.append({
                "level": "ERROR",
                "severity": "critical",
                "error_code": fallback_code,
                "message": f"エラーコード管理エラー: {str(e)}",
                "response_time": self.severity_levels['critical']['response_time'],
                "timestamp": datetime.now().isoformat(),
                "error_details": {
                    "code_type": "standard",
                    "original_message": message,
                    "registered_at": datetime.now().isoformat()
                }
            })
            self.error_count += 1

    def add_warning(self, message: str):
        """警告の追加"""
        self.results.append({
            "level": "WARNING",
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        self.warning_count += 1

    def generate_report(self) -> str:
        """セキュリティテストレポートの生成（MCPフレームワーク標準準拠）"""
        report = []
        report.append("# セキュリティテストレポート")
        report.append(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # テスト結果サマリー
        report.append(f"\n## テスト結果サマリー:")
        critical_errors = sum(1 for r in self.results if r.get('level') == 'ERROR' and r.get('severity') == 'critical')
        non_critical_errors = sum(1 for r in self.results if r.get('level') == 'ERROR' and r.get('severity') == 'non-critical')
        
        report.append(f"- クリティカルエラー数: {critical_errors}")
        report.append(f"- 非クリティカルエラー数: {non_critical_errors}")
        report.append(f"- 警告数: {self.warning_count}")
        
        if self.results:
            report.append("\n## 詳細:")
            # クリティカルエラーを先に表示
            for result in sorted(self.results,
                               key=lambda x: (x.get('level') != 'ERROR',
                                            x.get('severity') != 'critical',
                                            x.get('timestamp', ''))):
                if result['level'] == 'ERROR':
                    severity = result.get('severity', 'non-critical')
                    error_code = result.get('error_code', '')
                    response_time = result.get('response_time', self.severity_levels[severity]['response_time'])
                    report.append(
                        f"- [{result['level']} - {severity.upper()}] "
                        f"(コード: {error_code}, 対応時間: {response_time}分) "
                        f"{result['message']}"
                    )
                else:
                    report.append(f"- [{result['level']}] {result['message']}")
        else:
            report.append("\n問題は検出されませんでした。")

        # MCPフレームワーク標準のセキュリティ推奨事項
        report.append("\n## セキュリティ推奨事項:")
        report.append("1. すべての設定ファイルで適切なファイルパーミッションを設定")
        report.append("2. 機密情報は環境変数または暗号化された設定ファイルで管理")
        report.append("3. すべてのユーザー入力に対して適切なバリデーションを実装")
        report.append("4. エラーメッセージから機密情報が漏洩しないよう注意")
        report.append("5. 適切なレート制限を実装してDDoS攻撃を防止")
        report.append("6. 最新のセキュリティパッチを適用")
        report.append("7. 定期的なセキュリティ監査を実施")
        report.append("8. トークンローテーションを有効化し、適切な間隔で実施")
        report.append("9. セキュアなトークン保存方式（encrypted/secure_keystore）を使用")
        report.append("10. HTTPSを使用し、安全でない通信プロトコルを避ける")

        return "\n".join(report)

    def test_all(self) -> bool:
        success = True

        # ファイルパーミッションとコンテンツの検証
        for root, _, files in os.walk(self.meta_dir):
            for file in files:
                if file.endswith('.yaml') or file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    
                    # ファイルパーミッションの検証
                    if not self.test_file_permissions(file_path):
                        success = False
                    
                    # 脆弱性スキャン
                    if not self.scan_for_vulnerabilities(file_path):
                        success = False

                    # 設定ファイルの検証
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            if file.endswith('.yaml'):
                                config = yaml.safe_load(f)
                            else:
                                config = json.load(f)

                            if not self.validate_authentication_config(config):
                                success = False
                            if not self.validate_error_handling(config):
                                success = False
                            if not self.validate_rate_limiting(config):
                                success = False
                            if not self.check_secure_defaults(config):
                                success = False
                            if not self.validate_sampling_config(config):
                                success = False

                    except Exception as e:
                        self.add_error(f"設定ファイル検証エラー {file_path}: {str(e)}")
                        success = False

        return success

def main():
    if len(sys.argv) != 2:
        print("使用方法: python test_security.py <path_to_meta_dir>")
        sys.exit(1)

    meta_dir = sys.argv[1]
    tester = SecurityTester(meta_dir)
    success = tester.test_all()
    
    report = tester.generate_report()
    print(report)
    
    # レポートをファイルに保存
    report_path = os.path.join(meta_dir, "security_report.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()