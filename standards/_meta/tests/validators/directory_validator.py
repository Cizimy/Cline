#!/usr/bin/env python3
from typing import Dict, List, Any
import os
import re
from .base_validator import BaseValidator, ErrorSeverity

class DirectoryValidator(BaseValidator):
    def __init__(self, meta_dir: str):
        super().__init__(meta_dir)
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

    def validate_directory_structure(self) -> bool:
        """必須ディレクトリ構造の検証"""
        valid = True
        
        # メタディレクトリの存在確認
        if not os.path.exists(self.meta_dir):
            self.add_error(
                f"メタディレクトリが見つかりません: {self.meta_dir}",
                ErrorSeverity.CRITICAL
            )
            return False

        # 必須ディレクトリの検証
        for dir_name, dir_info in self.required_directories.items():
            dir_path = os.path.join(self.meta_dir, dir_name)
            
            # ディレクトリの存在確認
            if not os.path.exists(dir_path):
                self.add_error(
                    f"必須ディレクトリが見つかりません: {dir_name}",
                    ErrorSeverity.CRITICAL
                )
                valid = False
                continue
            
            if not os.path.isdir(dir_path):
                self.add_error(
                    f"{dir_name}はディレクトリではありません",
                    ErrorSeverity.CRITICAL
                )
                valid = False
                continue

            # 必須ファイルの検証
            for required_file in dir_info['required_files']:
                file_path = os.path.join(dir_path, required_file)
                if not os.path.exists(file_path):
                    self.add_error(
                        f"必須ファイルが見つかりません: {dir_name}/{required_file}",
                        ErrorSeverity.CRITICAL
                    )
                    valid = False
                elif not os.path.isfile(file_path):
                    self.add_error(
                        f"{dir_name}/{required_file}はファイルではありません",
                        ErrorSeverity.CRITICAL
                    )
                    valid = False

        return valid

    def validate_file_naming(self, file_path: str) -> bool:
        """ファイル命名規則の検証"""
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
                ]),
                ErrorSeverity.CRITICAL
            )
            return False
        
        return True

    def validate_all_files(self) -> bool:
        """すべてのファイルの命名規則を検証"""
        valid = True
        
        for dir_name in self.required_directories.keys():
            dir_path = os.path.join(self.meta_dir, dir_name)
            if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
                continue
                
            for file_name in os.listdir(dir_path):
                file_path = os.path.join(dir_path, file_name)
                if os.path.isfile(file_path):
                    if not self.validate_file_naming(file_path):
                        valid = False
                        
        return valid