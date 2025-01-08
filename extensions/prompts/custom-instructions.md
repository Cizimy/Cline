# Custom Instructions

## Language Settings
You should always speak and think in the Japanese language.

## Project-Specific Instructions
- プロジェクトのディレクトリ構造を常に意識して作業を行う
- コア機能との互換性を維持しながら拡張機能を開発
- 設定ファイルの変更は慎重に行う

## Development Guidelines
1. 拡張機能の開発
   - 独立したモジュールとして開発
   - 明確なバージョニング
   - テストの作成

2. MCPサーバーの開発
   - extensions/mcp/配下に配置
   - 個別のパッケージとして管理
   - 環境変数による設定

3. プロンプトのカスタマイズ
   - extensions/prompts/配下で管理
   - 目的別に分割
   - バージョン管理対象として追跡