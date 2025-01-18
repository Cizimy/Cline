# 引継ぎ文書

## タスク概要

MCPサーバーの実装と設定の改善を行いました。

## 実施内容

1. MCPサーバーの実装言語の整理と対応
   - Python実装（sqlite, git）
   - TypeScript実装（postgres, filesystem, memory, github, gitlab, puppeteer）

2. 設定ファイルの更新
   - development.jsonの更新
     * 実装言語に応じた設定の修正
     * 実行コマンドとパスの適切な設定
     * 環境変数の標準化
   - cline_mcp_settings.jsonの更新
     * 各サーバーの設定を最新化
     * 許可ツールの整理

3. ドキュメントの更新
   - README.mdの更新
     * MCPサーバー管理セクションの更新
     * 実装状況の反映
   - MCP_MIGRATION_PLAN.mdの更新
     * フェーズ1,2の完了マーク
     * 実装手順の詳細化
   - PROJECT_CONTEXT.mdの更新
     * サーバー実装方針の更新
     * 設定管理の詳細化

## 技術的な詳細

### 実装言語別の設定

1. Python実装（sqlite, git）
   - PYTHONPATHを`src`ディレクトリに設定
   - モジュール名に`.__main__`を追加
   - 仮想環境（.venv）を使用

2. TypeScript実装（その他のサーバー）
   - NODE_PATHを`dist`ディレクトリに設定
   - ビルド済みJSファイルを使用
   - 依存関係の管理を実施

### 設定管理の標準化

1. 環境変数の命名規則
   - サーバー固有: [SERVER]_[CATEGORY]_[NAME]
   - 共通変数: NOAH_[CATEGORY]_[NAME]
   - パス変数: [SERVER]_PATH または NOAH_PATH_[NAME]

2. 設定ファイルの構造
   - base.json: 共通設定テンプレート
   - development.json: 環境別設定
   - env.json: 環境変数定義

## 残課題

1. フェーズ3の実装準備
   - Google Drive連携
   - Google Maps連携
   - Slack連携
   - Sentry連携

2. フェーズ4の実装準備
   - EverArt
   - Sequential Thinking
   - Time
   - Everything

## 参考情報

1. 関連ドキュメント
   - docs/MCP_MIGRATION_PLAN.md
   - docs/PROJECT_CONTEXT.md
   - MCP/config/README.md

2. 重要なコマンド
   ```powershell
   # 設定の生成
   cd MCP/config
   ./generate-config.ps1
   ```

## 注意事項

1. 設定変更時は必ずgenerate-config.ps1を実行
2. 実装言語に応じた適切な設定を使用
3. 環境変数は必ずenv.jsonで管理
