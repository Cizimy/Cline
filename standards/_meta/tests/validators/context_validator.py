#!/usr/bin/env python3
from typing import Dict, List, Any
import os
from .base_validator import BaseValidator, ErrorSeverity

class ContextValidator(BaseValidator):
    def __init__(self, meta_dir: str):
        super().__init__(meta_dir)
        self.contexts_dir = os.path.join(meta_dir, "contexts")

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
                    ErrorSeverity.CRITICAL
                )
                valid = False
                continue

            # 対応時間の検証
            max_times = {'critical': 15, 'non-critical': 60}
            if response_time is None:
                self.add_error(
                    f"対応時間が未定義 in {os.path.basename(file_path)} for {severity}",
                    ErrorSeverity.CRITICAL
                )
                valid = False
            elif response_time > max_times[severity]:
                self.add_error(
                    f"{severity}重要度の対応時間超過 in {os.path.basename(file_path)}: "
                    f"{response_time}分 > {max_times[severity]}分",
                    ErrorSeverity.CRITICAL
                )
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
                    self.add_error(
                        f"無効なコンテキスト参照 in {current_file}: {ref}",
                        ErrorSeverity.CRITICAL
                    )
                    valid = False
                    continue

                # 循環参照の検出
                if ref_file in visited:
                    self.add_error(
                        f"循環参照が検出されました: {' -> '.join(visited)} -> {ref_file}",
                        ErrorSeverity.CRITICAL
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
                    self.add_error(
                        f"参照先コンテキストの読み込みエラー {ref_file}: {str(e)}",
                        ErrorSeverity.CRITICAL
                    )
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
                        self.add_error(
                            f"依存コンテキストが見つかりません in {current_file}: {ctx}",
                            ErrorSeverity.CRITICAL
                        )
                        valid = False
                        continue

                    try:
                        with open(ctx_path, 'r', encoding='utf-8') as f:
                            ctx_data = yaml.safe_load(f)
                            ctx_version = ctx_data.get('version')
                            if not ctx_version:
                                self.add_error(
                                    f"依存コンテキストにバージョンが定義されていません: {ctx}",
                                    ErrorSeverity.CRITICAL
                                )
                                valid = False
                            elif not self.validate_version_compatibility(version, ctx_version):
                                self.add_error(
                                    f"バージョン互換性エラー in {current_file}: "
                                    f"{ctx} requires {version}, but found {ctx_version}",
                                    ErrorSeverity.CRITICAL
                                )
                                valid = False
                    except Exception as e:
                        self.add_error(
                            f"依存コンテキストの読み込みエラー {ctx}: {str(e)}",
                            ErrorSeverity.CRITICAL
                        )
                        valid = False

            # 機能依存関係の検証
            if 'required_features' in deps:
                for ctx, features in deps['required_features'].items():
                    ctx_path = os.path.join(self.contexts_dir, f"{ctx}.yaml")
                    if not os.path.exists(ctx_path):
                        self.add_error(
                            f"依存コンテキストが見つかりません in {current_file}: {ctx}",
                            ErrorSeverity.CRITICAL
                        )
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
                                        f"{ctx} does not provide {feature}",
                                        ErrorSeverity.CRITICAL
                                    )
                                    valid = False
                    except Exception as e:
                        self.add_error(
                            f"依存コンテキストの読み込みエラー {ctx}: {str(e)}",
                            ErrorSeverity.CRITICAL
                        )
                        valid = False

        return valid

    def validate_metrics(self, data: Dict[str, Any], file_path: str) -> bool:
        """メトリクスの検証"""
        if 'metrics' not in data:
            return True

        valid = True
        for metric in data['metrics']:
            if 'name' not in metric:
                self.add_error(
                    f"メトリクス名が欠落 in {os.path.basename(file_path)}",
                    ErrorSeverity.CRITICAL
                )
                valid = False
            if 'type' not in metric:
                self.add_error(
                    f"メトリクスタイプが欠落 in {os.path.basename(file_path)}",
                    ErrorSeverity.CRITICAL
                )
                valid = False
            if 'unit' not in metric:
                self.add_warning(
                    f"メトリクス単位が未定義 in {os.path.basename(file_path)}: {metric.get('name', 'unknown')}"
                )
            if 'threshold' not in metric:
                self.add_warning(
                    f"メトリクス閾値が未定義 in {os.path.basename(file_path)}: {metric.get('name', 'unknown')}"
                )

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
                self.add_error(
                    f"サンプリング設定の必須フィールド欠落 in {current_file}: {field}",
                    ErrorSeverity.CRITICAL
                )
                valid = False

        if not valid:
            return False

        # サンプリングモードの検証
        valid_modes = ['llm', 'tool', 'prompt']
        if sampling['mode'] not in valid_modes:
            self.add_error(
                f"無効なサンプリングモード in {current_file}: {sampling['mode']}",
                ErrorSeverity.CRITICAL
            )
            valid = False

        # LLMサンプリング設定の検証
        if sampling['mode'] == 'llm':
            if 'llm_config' not in sampling:
                self.add_error(
                    f"LLM設定が欠落 in {current_file}",
                    ErrorSeverity.CRITICAL
                )
                valid = False
            else:
                llm_config = sampling['llm_config']
                llm_required = ['model', 'temperature', 'max_tokens']
                for field in llm_required:
                    if field not in llm_config:
                        self.add_error(
                            f"LLM設定の必須フィールド欠落 in {current_file}: {field}",
                            ErrorSeverity.CRITICAL
                        )
                        valid = False

                # パラメータ範囲の検証
                if 'temperature' in llm_config:
                    temp = llm_config['temperature']
                    if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                        self.add_error(
                            f"無効なtemperature値 in {current_file}: {temp}",
                            ErrorSeverity.CRITICAL
                        )
                        valid = False

                if 'max_tokens' in llm_config:
                    tokens = llm_config['max_tokens']
                    if not isinstance(tokens, int) or tokens < 1:
                        self.add_error(
                            f"無効なmax_tokens値 in {current_file}: {tokens}",
                            ErrorSeverity.CRITICAL
                        )
                        valid = False

        # 代替機能の検証
        if 'fallback' in sampling:
            fallback = sampling['fallback']
            if 'type' not in fallback:
                self.add_error(
                    f"代替機能のタイプが未定義 in {current_file}",
                    ErrorSeverity.CRITICAL
                )
                valid = False
            else:
                valid_types = ['tool', 'prompt']
                if fallback['type'] not in valid_types:
                    self.add_error(
                        f"無効な代替機能タイプ in {current_file}: {fallback['type']}",
                        ErrorSeverity.CRITICAL
                    )
                    valid = False

                # ツールベースの代替機能の検証
                if fallback['type'] == 'tool':
                    if 'tool_config' not in fallback:
                        self.add_error(
                            f"ツール設定が欠落 in {current_file}",
                            ErrorSeverity.CRITICAL
                        )
                        valid = False
                    else:
                        tool_config = fallback['tool_config']
                        tool_required = ['name', 'parameters']
                        for field in tool_required:
                            if field not in tool_config:
                                self.add_error(
                                    f"ツール設定の必須フィールド欠落 in {current_file}: {field}",
                                    ErrorSeverity.CRITICAL
                                )
                                valid = False

                # プロンプトベースの代替機能の検証
                elif fallback['type'] == 'prompt':
                    if 'prompt_template' not in fallback:
                        self.add_error(
                            f"プロンプトテンプレートが欠落 in {current_file}",
                            ErrorSeverity.CRITICAL
                        )
                        valid = False

        return valid