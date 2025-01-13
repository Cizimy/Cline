# MCPサーバー移行計画

## 1. 移行の目的と概要

- 標準MCPサーバーの活用による実装の簡素化
- 新しい設定管理システムへの統一
- 運用管理の効率化

## 2. 移行対象サーバー

### フェーズ1: 基本インフラストラクチャ（完了）
- [x] SQLite: データベース操作の基盤
  - 標準MCPサーバー（Python実装）を使用
  - 基本的なデータベース操作機能を提供
  - 主要なクエリツールを許可
- [x] PostgreSQL: データベース操作の基盤
  - 標準MCPサーバー（TypeScript実装）を使用
  - 読み取り専用アクセスとスキーマ検査機能を提供
  - queryツールを許可
- [x] Filesystem: ファイル操作の基盤
  - 標準MCPサーバー（TypeScript実装）を使用
  - NOAH_DATA_PATHに制限されたファイル操作機能を提供
  - 主要なファイル操作ツールを許可
- [x] Memory: 知識グラフベースの永続メモリシステム
  - 標準MCPサーバー（TypeScript実装）を使用
  - エンティティ、リレーション、オブザベーションの管理
  - 全ての知識グラフ操作ツールを許可

### フェーズ2: 開発支援ツール（実装中）
- [x] Git: リポジトリ操作
  - 標準MCPサーバー（Python実装）を使用
  - 基本的なGit操作機能を提供
  - リポジトリ操作ツールを許可
- [x] GitHub: GitHub API連携
  - 標準MCPサーバー（TypeScript実装）を使用
  - GitHub APIを介した操作機能を提供
  - リポジトリ管理ツールを許可
- [x] GitLab: GitLab API連携
  - 標準MCPサーバー（TypeScript実装）を使用
  - GitLab APIを介した操作機能を提供
  - リポジトリ管理ツールを許可
- [x] Puppeteer: ブラウザ自動化
  - 標準MCPサーバー（TypeScript実装）を使用
  - ブラウザ自動化機能を提供
  - 画面操作ツールを許可

### フェーズ3: 外部サービス連携（2週間）
- [ ] Google Drive: ファイルアクセス
  - 標準MCPサーバー（@modelcontextprotocol/server-gdrive）を使用予定
  - OAuth2認証による安全なアクセス
- [ ] Google Maps: 位置情報サービス
  - 標準MCPサーバー（@modelcontextprotocol/server-gmaps）を使用予定
  - 位置情報APIの活用
- [ ] Slack: チャネル管理
  - 標準MCPサーバー（@modelcontextprotocol/server-slack）を使用予定
  - Slack APIを介した操作
- [ ] Sentry: エラー追跡
  - 標準MCPサーバー（@modelcontextprotocol/server-sentry）を使用予定
  - エラー監視と通知

### フェーズ4: 特殊機能（2週間）
- [ ] EverArt: AI画像生成
  - 標準MCPサーバー（@modelcontextprotocol/server-everart）を使用予定
  - AI画像生成機能の統合
- [ ] Sequential Thinking: 思考プロセス
  - 標準MCPサーバー（@modelcontextprotocol/server-sequential）を使用予定
  - 思考プロセスの管理
- [ ] Time: 時間管理
  - 標準MCPサーバー（@modelcontextprotocol/server-time）を使用予定
  - 時間関連の操作機能
- [ ] Everything: リファレンス/テスト
  - 標準MCPサーバー（@modelcontextprotocol/server-everything）を使用予定
  - 統合テスト環境の提供

## 3. 移行手順の標準化

### 3.1 準備フェーズ
1. サーバー情報の確認
   - Model Context Protocol Serversリポジトリの確認
   - 実装言語の確認（Python/TypeScript）
   - 各サーバーのREADMEドキュメント精読

2. サーバー選択と設定
   - READMEから機能と設定要件を確認
   - 利用可能なツールとリソースの確認
   - 必要な環境変数の特定

3. 設定ファイルの準備
   - env.jsonの環境変数追加
   - development.jsonの設定追加
   - 各サーバーの許可ツール（alwaysAllow）の設定

### 3.2 環境変数の標準化
1. 命名規則の統一
   - サーバー固有の変数: [SERVER]_[CATEGORY]_[NAME]
   - 共通変数: NOAH_[CATEGORY]_[NAME]
   - パス変数: [SERVER]_PATH または NOAH_PATH_[NAME]

2. 変数カテゴリの整理
   - AUTH: 認証情報（トークン、キーなど）
   - PATH: ファイルパス
   - CONFIG: 設定情報
   - API: APIエンドポイント
   - ENV: 環境識別子

3. 変数の集中管理
   - すべての環境変数をenv.jsonで管理
   - 機密情報は.env.localで管理
   - パスは相対パスを使用

### 3.3 設定管理の効率化
1. 設定テンプレートの活用
   - base.jsonでの共通設定定義
   - 環境別の設定ファイル分離
   - 設定の継承関係の明確化

2. 実装言語別の設定
   - Python実装
     * PYTHONPATHの設定（src/ディレクトリ）
     * モジュール名に.__main__を追加
     * 仮想環境の使用
   - TypeScript実装
     * NODE_PATHの設定（dist/ディレクトリ）
     * ビルド後のJSファイルを使用
     * 依存関係の管理

3. 設定の検証
   - 必須項目の存在確認
   - 型チェック
   - 依存関係の検証

### 3.4 テストと検証
1. 基本機能テスト
2. 権限テスト
3. エラーハンドリングテスト

## 4. リスク管理

### 4.1 想定されるリスク
- 依存関係の競合
- パス解決の問題
- 権限設定の不整合
- データの整合性
- 実装言語の違いによる問題

### 4.2 対策
- 段階的な移行による影響範囲の制限
- バックアップと復元手順の整備
- ロールバック手順の準備
- 監視体制の強化
- 実装言語別のテスト強化

## 5. スケジュール

### 5.1 全体スケジュール
- 総期間: 8週間
- 各フェーズ: 2週間
- バッファ: 1週間

### 5.2 マイルストーン
1. フェーズ1完了: 基本インフラの移行（完了）
2. フェーズ2完了: 開発ツールの移行（完了）
3. フェーズ3完了: 外部サービスの移行
4. フェーズ4完了: 特殊機能の移行

## 6. 監視と報告

### 6.1 監視項目
- 移行進捗状況
- エラー発生率
- パフォーマンス指標
- ユーザー影響度

### 6.2 報告体制
- 週次進捗報告
- 問題発生時の即時報告
- 完了報告書の作成

## 7. 運用ガイドライン

### 7.1 新規追加された運用ルール
- 標準MCPサーバーを優先的に使用
- サーバー実装前に必ずREADMEを確認
- 設定変更時は必ずgenerate-config.ps1を実行
- 環境変数は必ずenv.jsonで管理
- パスの指定は環境変数を使用
- 実装言語に応じた適切な設定を使用

### 7.2 移行後の確認事項
- 設定ファイルの生成状況
- 環境変数の解決結果
- サーバーの動作状況
- 実装言語別の動作確認

## 8. 参考情報

### 8.1 重要なファイル
- MCP/config/env.json: 環境変数定義
- MCP/config/base.json: 基本設定テンプレート
- MCP/config/development.json: 開発環境設定
- MCP/config/generate-config.ps1: 設定生成スクリプト

### 8.2 関連ドキュメント
- MCPフレームワーク仕様書: docs/references/mcp_llm_reference.txt
- Model Context Protocol Servers: https://github.com/modelcontextprotocol/servers