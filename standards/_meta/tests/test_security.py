#!/usr/bin/env python3
import os
import sys
import yaml
import json
import re
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class SecurityLevel:
    """セキュリティレベル定義クラス"""
    response_time: int
    description: str

class ErrorCodeRegistry:
    """エラーコード管理クラス（MCPフレームワーク標準v1.2.0準拠）"""
    def __init__(self):
        self.standard_error_codes = {
            'parse_error': -32700,
            'invalid_request': -32600,
            'method_not_found': -32601,
            'invalid_params': -32602,
            'internal_error': -32603
        }
        self.server_error_code_range = {'minimum': -32599, 'maximum': -32000}
        self.used_error_codes: Set[int] = set()
        self.error_code_mapping: Dict[int, str] = {}

    def is_valid_error_code(self, code: int) -> bool:
        """エラーコードの範囲検証"""
        return (code in self.standard_error_codes.values() or
                self.server_error_code_range['minimum'] <= code <= self.server_error_code_range['maximum'])

    def register_error_code(self, code: int, message: str) -> bool:
        """エラーコードの登録"""
        if not self.is_valid_error_code(code) or code in self.used_error_codes:
            return False
        self.used_error_codes.add(code)
        self.error_code_mapping[code] = message
        return True

    def get_next_available_code(self) -> int:
        """利用可能な次のエラーコードを取得"""
        for code in range(self.server_error_code_range['minimum'], 
                         self.server_error_code_range['maximum'] + 1):
            if code not in self.used_error_codes:
                return code
        raise ValueError("利用可能なエラーコードがありません")

class ConfigValidator(ABC):
    """設定検証の基底クラス"""
    @abstractmethod
    def validate(self, config: Dict[str, Any]) -> bool:
        pass

class AuthenticationConfigValidator(ConfigValidator):
    """認証設定の検証クラス"""
    def validate(self, config: Dict[str, Any]) -> bool:
        if not config:
            return False

        is_valid = True
        auth_type = config.get('auth_type')
        if not auth_type or auth_type not in {'oauth2', 'token'}:
            is_valid = False

        token_expiration = config.get('token_expiration', 0)
        if token_expiration < 5 or token_expiration > 24 * 60:
            is_valid = False

        return is_valid

class OAuth2ConfigValidator(ConfigValidator):
    """OAuth2設定の検証クラス"""
    def validate(self, config: Dict[str, Any]) -> bool:
        if not config:
            return False

        is_valid = True
        grant_types = config.get('grant_types', [])
        allowed_grants = {'authorization_code', 'client_credentials', 'refresh_token'}
        if not set(grant_types).issubset(allowed_grants):
            is_valid = False

        required_endpoints = ['token_endpoint', 'auth_endpoint', 'refresh_endpoint']
        for endpoint in required_endpoints:
            if not config.get(endpoint):
                is_valid = False

        return is_valid

class SecurityTester:
    """セキュリティテストの実行クラス"""
    def __init__(self, meta_dir: str):
        self.meta_dir = meta_dir
        self.results: List[Dict[str, Any]] = []
        self.error_count = 0
        self.warning_count = 0
        self.error_registry = ErrorCodeRegistry()
        
        # セキュリティレベル定義
        self.severity_levels = {
            'critical': SecurityLevel(15, 'システム停止、セキュリティ違反、データ損失リスク'),
            'non-critical': SecurityLevel(60, '一般的なエラー、パフォーマンス低下')
        }
        
        # 脆弱性パターン定義
        self.vulnerability_patterns = {
            'sql_injection': r'(?i)(SELECT|INSERT|UPDATE|DELETE|DROP).*\$\{.*\}',
            'command_injection': r'(?i)(eval|exec|system|popen|subprocess\.call).*\$\{.*\}',
            'path_traversal': r'\.\./',
            'sensitive_data': r'(?i)(password|secret|key|token|credential).*:.*[^*]$',
            'insecure_protocols': r'(?i)(http://|ftp://)',
            'hardcoded_credentials': r'(?i)(password|secret|key|token|credential)["\']:\s*["\'][^*\n]{3,}["\']',
        }

        # 設定検証クラスの初期化
        self.validators = {
            'authentication': AuthenticationConfigValidator(),
            'oauth2': OAuth2ConfigValidator()
        }

    def validate_config(self, config: Dict[str, Any], validator_name: str) -> bool:
        """設定の検証を実行"""
        validator = self.validators.get(validator_name)
        if not validator:
            self.add_error(f"未定義の検証タイプ: {validator_name}")
            return False
        return validator.validate(config)

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

    def test_file_permissions(self, file_path: str) -> bool:
        """ファイルのパーミッションをチェック"""
        try:
            import win32security
            import ntsecuritycon as con

            sd = win32security.GetFileSecurity(file_path, win32security.DACL_SECURITY_INFORMATION)
            dacl = sd.GetSecurityDescriptorDacl()

            if dacl is None:
                self.add_error(f"セキュリティリスク: NULLのDACL {file_path}", "critical")
                return False

            everyone = win32security.ConvertStringSidToSid("S-1-1-0")
            users = win32security.ConvertStringSidToSid("S-1-5-32-545")

            for i in range(dacl.GetAceCount()):
                try:
                    ace = dacl.GetAce(i)
                    if ace[2] in (everyone, users):
                        if (ace[1] & con.FILE_GENERIC_WRITE) or (ace[1] & con.GENERIC_WRITE):
                            self.add_error(
                                f"セキュリティリスク: 一般ユーザーに書き込み権限があります {file_path}",
                                "non-critical"
                            )
                            return False
                except Exception as ace_error:
                    self.add_warning(f"ACEの解析エラー {file_path}: {str(ace_error)}")
                    continue

            return True

        except ImportError:
            self.add_warning("Windows セキュリティチェックには pywin32 が必要です")
            return True
        except Exception as e:
            self.add_warning(f"パーミッションチェックをスキップ {file_path}: {str(e)}")
            return True

    def add_error(self, message: str, severity: str = 'non-critical', error_code: Optional[int] = None):
        """エラーの追加"""
        try:
            if severity not in self.severity_levels:
                severity = 'non-critical'

            if error_code is None:
                error_code = self.error_registry.get_next_available_code()
            elif not self.error_registry.register_error_code(error_code, message):
                error_code = self.error_registry.get_next_available_code()

            self.results.append({
                "level": "ERROR",
                "severity": severity,
                "error_code": error_code,
                "message": message,
                "response_time": self.severity_levels[severity].response_time,
                "timestamp": datetime.now().isoformat()
            })
            self.error_count += 1

        except Exception as e:
            fallback_code = self.error_registry.standard_error_codes['internal_error']
            self.results.append({
                "level": "ERROR",
                "severity": "critical",
                "error_code": fallback_code,
                "message": f"エラーコード管理エラー: {str(e)}",
                "response_time": self.severity_levels['critical'].response_time,
                "timestamp": datetime.now().isoformat()
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
        """セキュリティテストレポートの生成"""
        report = []
        report.append("# セキュリティテストレポート")
        report.append(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # テスト結果サマリー
        report.append("\n## テスト結果サマリー:")
        critical_errors = sum(1 for r in self.results 
                            if r.get('level') == 'ERROR' and r.get('severity') == 'critical')
        non_critical_errors = sum(1 for r in self.results 
                                if r.get('level') == 'ERROR' and r.get('severity') == 'non-critical')
        
        report.append(f"- クリティカルエラー数: {critical_errors}")
        report.append(f"- 非クリティカルエラー数: {non_critical_errors}")
        report.append(f"- 警告数: {self.warning_count}")
        
        if self.results:
            report.append("\n## 詳細:")
            for result in sorted(self.results,
                               key=lambda x: (x.get('level') != 'ERROR',
                                            x.get('severity') != 'critical',
                                            x.get('timestamp', ''))):
                if result['level'] == 'ERROR':
                    severity = result.get('severity', 'non-critical')
                    error_code = result.get('error_code', '')
                    response_time = result.get('response_time', 
                                            self.severity_levels[severity].response_time)
                    report.append(
                        f"- [{result['level']} - {severity.upper()}] "
                        f"(コード: {error_code}, 対応時間: {response_time}分) "
                        f"{result['message']}"
                    )
                else:
                    report.append(f"- [{result['level']}] {result['message']}")
        else:
            report.append("\n問題は検出されませんでした。")

        # セキュリティ推奨事項
        report.append("\n## セキュリティ推奨事項:")
        recommendations = [
            "すべての設定ファイルで適切なファイルパーミッションを設定",
            "機密情報は環境変数または暗号化された設定ファイルで管理",
            "すべてのユーザー入力に対して適切なバリデーションを実装",
            "エラーメッセージから機密情報が漏洩しないよう注意",
            "適切なレート制限を実装してDDoS攻撃を防止",
            "最新のセキュリティパッチを適用",
            "定期的なセキュリティ監査を実施",
            "トークンローテーションを有効化し、適切な間隔で実施",
            "セキュアなトークン保存方式（encrypted/secure_keystore）を使用",
            "HTTPSを使用し、安全でない通信プロトコルを避ける"
        ]
        for i, rec in enumerate(recommendations, 1):
            report.append(f"{i}. {rec}")

        return "\n".join(report)

    def test_all(self) -> bool:
        """すべてのセキュリティテストを実行"""
        success = True

        # 設定ファイルの読み込みと検証
        try:
            config = self._load_config()
            if not config:
                return False

            # 各種設定の検証
            if not self._validate_all_configs(config):
                success = False

            # ファイルシステムの検証
            if not self._validate_filesystem():
                success = False

        except Exception as e:
            self.add_error(f"テスト実行エラー: {str(e)}", "critical")
            success = False

        return success

    def _load_config(self) -> Optional[Dict[str, Any]]:
        """設定ファイルの読み込み"""
        index_path = os.path.join(self.meta_dir, 'index.yaml')
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.add_error(f"設定ファイル読み込みエラー {index_path}: {str(e)}")
            return None

    def _validate_all_configs(self, config: Dict[str, Any]) -> bool:
        """すべての設定を検証"""
        success = True

        # グローバル設定の検証
        global_settings = config.get('global', {})
        if not global_settings:
            self.add_error("グローバル設定が見つかりません", "critical")
            return False

        # 認証設定の検証
        auth_config = global_settings.get('security', {}).get('authentication', {})
        if not self.validate_config(auth_config, 'authentication'):
            success = False

        # OAuth2設定の検証
        if auth_config.get('auth_type') == 'oauth2':
            oauth2_config = auth_config.get('oauth2', {})
            if not self.validate_config(oauth2_config, 'oauth2'):
                success = False

        return success

    def _validate_filesystem(self) -> bool:
        """ファイルシステムの検証"""
        success = True
        for root, _, files in os.walk(self.meta_dir):
            for file in files:
                if file.endswith(('.yaml', '.json')):
                    file_path = os.path.join(root, file)
                    if not self.test_file_permissions(file_path):
                        success = False
                    if not self.scan_for_vulnerabilities(file_path):
                        success = False
        return success

def main():
    """メイン実行関数"""
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