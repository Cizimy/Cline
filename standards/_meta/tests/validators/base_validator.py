#!/usr/bin/env python3
from typing import Dict, List, Any
from enum import Enum
import os
import yaml

class ErrorSeverity(Enum):
    CRITICAL = "critical"
    NON_CRITICAL = "non-critical"

class ValidationResult:
    def __init__(self, level: str, message: str, severity: ErrorSeverity = ErrorSeverity.NON_CRITICAL):
        self.level = level
        self.message = message
        self.severity = severity
        self.response_time = 15 if severity == ErrorSeverity.CRITICAL else 60

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level,
            "severity": self.severity.value,
            "message": self.message,
            "response_time": self.response_time
        }

class BaseValidator:
    def __init__(self, meta_dir: str):
        self.meta_dir = meta_dir
        self.results: List[ValidationResult] = []
        self.error_count = 0
        self.warning_count = 0

    def add_error(self, message: str, severity: ErrorSeverity = ErrorSeverity.NON_CRITICAL):
        """エラーの追加（MCPフレームワーク標準v1.2.0準拠）"""
        result = ValidationResult("ERROR", message, severity)
        self.results.append(result)
        self.error_count += 1

    def add_warning(self, message: str):
        """警告の追加"""
        result = ValidationResult("WARNING", message)
        self.results.append(result)
        self.warning_count += 1

    def validate_file_encoding(self, file_path: str) -> bool:
        """ファイルエンコーディングの検証"""
        try:
            # まずUTF-8で試す
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read()
            return True
        except UnicodeDecodeError:
            try:
                # UTF-8-SIGで試す
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    content = f.read()
                # UTF-8に変換して書き直す
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            except UnicodeDecodeError:
                self.add_error(
                    f"ファイルエンコーディングエラー in {os.path.basename(file_path)}: "
                    "UTF-8またはUTF-8-SIGである必要があります",
                    ErrorSeverity.CRITICAL
                )
                return False

    def validate_yaml_syntax(self, file_path: str) -> bool:
        """YAML構文の検証"""
        try:
            # まずUTF-8で試す
            with open(file_path, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
            return True
        except yaml.YAMLError as e:
            self.add_error(
                f"YAML構文エラー in {os.path.basename(file_path)}: {str(e)}",
                ErrorSeverity.CRITICAL
            )
            return False
        except UnicodeDecodeError:
            try:
                # UTF-8-SIGで試す
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    yaml.safe_load(f)
                return True
            except (yaml.YAMLError, UnicodeDecodeError) as e:
                self.add_error(
                    f"YAML構文またはエンコーディングエラー in {os.path.basename(file_path)}: {str(e)}",
                    ErrorSeverity.CRITICAL
                )
                return False

    def validate_required_fields(self, data: Dict[str, Any], required_fields: List[str], file_path: str) -> bool:
        """必須フィールドの検証"""
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            self.add_error(
                f"必須フィールド欠落 in {os.path.basename(file_path)}: {', '.join(missing_fields)}",
                ErrorSeverity.CRITICAL
            )
            return False
        return True

    def validate_version(self, data: Dict[str, Any], file_path: str) -> bool:
        """バージョン番号の検証（MCPフレームワーク標準v1.2.0準拠）"""
        if 'version' not in data:
            self.add_error(
                f"バージョン情報が欠落: {os.path.basename(file_path)}",
                ErrorSeverity.CRITICAL
            )
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
                ErrorSeverity.CRITICAL
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
                ErrorSeverity.CRITICAL
            )
            return False

        # マイナーバージョンの検証
        if minor != required_version[1]:
            self.add_error(
                f"互換性のないマイナーバージョン in {os.path.basename(file_path)}: "
                f"{version} (必要: {required_version[0]}.{required_version[1]}.x)",
                ErrorSeverity.CRITICAL
            )
            return False

        # パッチバージョンの検証
        if patch != required_version[2]:
            self.add_error(
                f"互換性のないパッチバージョン in {os.path.basename(file_path)}: "
                f"{version} (必要: {required_version[0]}.{required_version[1]}.{required_version[2]})",
                ErrorSeverity.CRITICAL
            )
            return False

        return True