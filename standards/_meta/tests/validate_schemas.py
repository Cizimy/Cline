#!/usr/bin/env python3
import os
import sys
import yaml
from datetime import datetime
from typing import Dict, List, Any
from validators.base_validator import BaseValidator, ErrorSeverity
from validators.schema_validator import SchemaValidator
from validators.context_validator import ContextValidator
from validators.directory_validator import DirectoryValidator

class ValidationManager:
    def __init__(self, meta_dir: str):
        self.meta_dir = meta_dir
        self.schemas_dir = os.path.join(meta_dir, "schemas")
        self.contexts_dir = os.path.join(meta_dir, "contexts")
        self.results: List[Dict[str, Any]] = []
        self.error_count = 0
        self.warning_count = 0

        # 各バリデーターのインスタンス化
        self.directory_validator = DirectoryValidator(meta_dir)
        self.schema_validator = SchemaValidator(meta_dir)
        self.context_validator = ContextValidator(meta_dir)

    def validate_all(self) -> bool:
        """すべての検証を実行"""
        # ディレクトリ構造の検証
        if not self.directory_validator.validate_directory_structure():
            self._merge_results(self.directory_validator)
            return False

        # ファイル命名規則の検証
        self.directory_validator.validate_all_files()
        self._merge_results(self.directory_validator)

        # スキーマファイルの検証
        schema_files = [f for f in os.listdir(self.schemas_dir) if f.endswith('.yaml')]
        for schema_file in schema_files:
            file_path = os.path.join(self.schemas_dir, schema_file)
            
            # 基本的な検証
            if not self.schema_validator.validate_file_encoding(file_path):
                continue
            if not self.schema_validator.validate_yaml_syntax(file_path):
                continue

            # ファイル内容の検証
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
            # 基本的な検証
            self.schema_validator.validate_version(data, file_path)
            self.schema_validator.validate_required_fields(data, ['version', 'type'], file_path)
            self.schema_validator.validate_error_codes(data, file_path)
            self.schema_validator.validate_schema_references(data, file_path)

            # MCPプロトコル関連の検証
            if data.get('type') in ['context_schema', 'process_schema']:
                self.schema_validator.validate_transport(data, file_path)

        self._merge_results(self.schema_validator)

        # コンテキストファイルの検証
        context_files = [f for f in os.listdir(self.contexts_dir) if f.endswith('.yaml')]
        for context_file in context_files:
            file_path = os.path.join(self.contexts_dir, context_file)
            
            # 基本的な検証
            if not self.context_validator.validate_file_encoding(file_path):
                continue
            if not self.context_validator.validate_yaml_syntax(file_path):
                continue

            # ファイル内容の検証
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
            # 基本的な検証
            self.context_validator.validate_version(data, file_path)
            self.context_validator.validate_required_fields(
                data,
                ['version', 'type', 'required_fields'],
                file_path
            )
            self.context_validator.validate_metrics(data, file_path)
            self.context_validator.validate_error_severity(data, file_path)

            # コンテキスト間の相互参照と依存関係の検証
            self.context_validator.validate_context_references(data, file_path)
            self.context_validator.validate_context_dependencies(data, file_path)

            # MCPプロトコル関連の検証
            if 'mcp_protocol' in data:
                self.schema_validator.validate_transport(data, file_path)
                self.context_validator.validate_sampling(data, file_path)

        self._merge_results(self.context_validator)

        return self.error_count == 0

    def _merge_results(self, validator: BaseValidator):
        """バリデーターの結果をマージ"""
        for result in validator.results:
            self.results.append(result.to_dict())
        self.error_count += validator.error_count
        self.warning_count += validator.warning_count

    def generate_report(self) -> str:
        """検証レポートの生成"""
        report = []
        report.append("# スキーマ検証レポート")
        report.append(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"\n検証結果サマリー:")
        report.append(f"- エラー数: {self.error_count}")
        report.append(f"- 警告数: {self.warning_count}")
        
        if self.results:
            report.append("\n## 詳細:")
            # 重要度でソート（criticalを先に）
            sorted_results = sorted(
                self.results,
                key=lambda x: (
                    0 if x.get('severity') == 'critical' else 1,
                    x.get('level', ''),
                    x.get('message', '')
                )
            )
            for result in sorted_results:
                severity = f"[{result['severity']}]" if 'severity' in result else ""
                report.append(f"- [{result['level']}]{severity} {result['message']}")
        else:
            report.append("\n問題は検出されませんでした。")

        return "\n".join(report)

def main():
    if len(sys.argv) != 2:
        print("使用方法: python validate_schemas.py <path_to_meta_dir>")
        sys.exit(1)

    meta_dir = sys.argv[1]
    validator = ValidationManager(meta_dir)
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