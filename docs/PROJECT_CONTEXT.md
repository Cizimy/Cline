# Clineプロジェクトコンテキスト

このドキュメントは、Clineがタスクを効率的に実行するために必要な、プロジェクトの基本的な文脈情報を提供します。

## プロジェクトの目的

Clineは安全かつ柔軟なパーソナルアシスタント的AIエージェントとして機能することを目指しています。主な目標は：

1. 安全性と制御可能性の確保
2. 柔軟な機能拡張の実現
3. 効率的なタスク実行の支援

## リポジトリ構造の基本概念

### コアコンポーネント（/extensions/core）

- プロジェクトの中核機能を提供
- 拡張機能の基盤となるインターフェースと型定義を管理
- MCPサーバーとの通信プロトコルを標準化

### 外部連携（/MCP）

- gitサブモジュールとして外部MCPサーバーを参照
- 本体との疎結合を維持しながら機能を拡張
- バージョン管理とアップデートを独立して制御

### 設定管理（/extensions/configs）

- MCPサーバーの設定
- プロンプトのカスタマイズ
- コア機能の動作設定

## 重要な運用ルール

1. バージョン管理
   - semantic-releaseによるバージョニング
   - gitサブモジュールによる外部依存の管理
   - 更新戦略は設定ファイルで明示的に制御

2. 品質管理
   - TypeScriptによる型安全性の確保
   - ESLint/Prettierによるコード品質の維持
   - Jestによるテスト自動化
   - テストカバレッジ80%以上の維持

3. ドキュメント管理
   - 引継ぎ文書の履歴管理（/docs/archive）
   - APIドキュメントの整備
   - 変更履歴の明確な記録

## タスク実行時の重要な考慮事項

1. 環境変数
   - CLINE_HOME: Clineのホームディレクトリ
   - CLINE_CONFIG_PATH: 設定ファイルのパス

2. 依存関係
   - Node.js >= 20.0.0
   - npm >= 10.0.0
   - 外部MCPサーバーの互換性確認

3. セキュリティ考慮事項
   - 環境変数経由の認証情報管理
   - MCPサーバーの権限制御
   - 外部APIアクセスの制限

## MCPサーバーとの連携

1. サーバー管理
   - 外部リポジトリとしての参照
   - サブモジュールによるバージョン管理
   - 設定ファイルでの有効化/無効化

2. 通信プロトコル
   - 標準化されたインターフェース
   - エラーハンドリングの統一
   - 型安全な通信

3. 拡張のベストプラクティス
   - 責務の明確な分離
   - 疎結合な設計
   - 適切なエラー処理

## プロジェクトの将来的な方向性

1. 短期目標
   - テスト実行の最適化
   - テストケースの整理
   - エラーハンドリングの強化

2. 中長期目標
   - MCPサーバー連携の強化
   - 自動化プロセスの拡充
   - ドキュメント体系の整備

## トラブルシューティング

1. 一般的な問題
   - サブモジュール同期の問題
   - 環境変数の設定ミス
   - 依存関係の競合

2. デバッグ手順
   - ログの確認方法
   - 設定の検証手順
   - テストの実行方法

## 参考情報

1. 重要なファイル
   - package.json: プロジェクトの依存関係と設定
   - .gitmodules: サブモジュールの定義
   - extensions/configs/extensions.json: MCPサーバーの設定

2. 外部リソース
   - MCPサーバーのリポジトリ
   - 関連ドキュメント
   - 開発ガイドライン

このコンテキスト情報は、Clineがタスクを実行する際の基本的な理解と判断の基準として機能します。プロジェクトの発展に伴い、適宜更新されるべきです。