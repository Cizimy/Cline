# Cline Custom Extensions

Clineのカスタム拡張機能を管理するリポジトリです。

## セットアップ

```bash
# リポジトリのクローン
git clone https://github.com/Cizimy/Cline.git
cd Cline

# 依存関係のインストール
npm install
```

## 更新管理

### 依存関係の更新

```bash
# すべての更新をチェック
npm run check:updates

# すべての更新を実行
npm run update

# 依存関係のみ更新
npm run update:deps
```

## 開発環境

### コード品質管理

- ESLint: コード品質とスタイルの確認
- Prettier: コードフォーマット
- TypeScript: 静的型チェック

### テスト環境

このプロジェクトはJestとTypeScriptを使用したテスト環境を提供しています：

```bash
# テストの実行
npm test

# カバレッジレポートの生成
npm test -- --coverage
```

テストファイルは以下の規則に従って配置されています：

- `tests/unit/`: ユニットテスト
- `tests/integration/`: 統合テスト（予定）

カバレッジレポートは `coverage/lcov-report/index.html` で確認できます。

## CI/CD

このプロジェクトはGitHub Actionsを使用して、以下の自動化を実行します：

### 自動テストとカバレッジ

- プッシュおよびプルリクエスト時にテストを自動実行
- カバレッジレポートを自動生成（目標: 80%以上）
- 成果物としてカバレッジレポートを保存（14日間）

### 品質管理

- ESLintによるコード品質チェック
- Prettierによるコードフォーマットチェック
- TypeScriptの型チェック

## ドキュメント

### プロジェクトコンテキスト

`docs/PROJECT_CONTEXT.md`は、このプロジェクトの全体像と重要な文脈情報を提供します：

- プロジェクトの目的と方向性
- リポジトリ構造の基本概念
- 重要な運用ルール
- タスク実行時の考慮事項
- MCPサーバーとの連携方法
- トラブルシューティングガイド

このドキュメントは、特にClineがタスクを効率的に実行するために必要な基本情報を提供することを目的としています。

### MCPフレームワーク参照

プロジェクトはModel Context Protocol（MCP）フレームワークに基づいて実装されています：

- 公式ドキュメント: https://modelcontextprotocol.io/introduction
- LLM向け詳細仕様: docs/references/mcp_llm_reference.txt

これらのドキュメントは、MCPの基本概念、実装ガイドライン、ベストプラクティスを提供し、プロジェクトの開発において重要な参照資料となります。

### コンテキスト定義

`standards/_meta/contexts/`ディレクトリには、以下の重要なコンテキスト定義ファイルが含まれています：

- `global_context.yaml`: プロジェクト全体のグローバルコンテキスト（v1.2.0）
- `process_context.yaml`: プロセス実行に関するコンテキスト（v1.2.0）
- `mcp_context.yaml`: MCPサーバー固有のコンテキスト（v1.2.0）
- `unified_metrics.yaml`: 統一メトリクス定義（v1.2.0）

### Autonomous Agent機能

プロジェクトは以下の2つの基本的な柱に基づいてAIエージェントを実装しています：

1. Task Management
   - タスク分解と計画立案
   - ツールと協力エージェントの特定
   - 実行管理と進捗モニタリング
   - エラーハンドリングと回復

2. Intelligence
   - LLMベースの意思決定プロセス
   - 特化型学習モデル（SLM）との連携
   - RAGによる知識ベースアクセス
   - 適応的学習と改善

これらの機能は`standards/processes/_base/process_types.yaml`で定義され、以下の特徴を持ちます：

- マルチエージェント連携のサポート
- 階層的なタスク計画と実行
- 会話履歴による学習と適応
- プライバシーを考慮した情報管理

これらのファイルは、プロジェクトの動作を定義し、一貫性のある運用を可能にします。各コンテキストファイルは以下の特徴を持ちます：
1. グローバルコンテキスト（v1.2.0）
   - プロジェクト全体の設定
   - AIエージェントの基本動作
   - MCPフレームワーク標準準拠のエラー管理
   - 品質管理の指針

2. プロセスコンテキスト（v1.2.0）
   - プロセス実行環境の定義
   - 状態管理とトランジション
   - メトリクス収集と分析
   - エラーハンドリングポリシー（2段階重要度）

3. MCPコンテキスト（v1.2.0）
   - サーバー定義と設定
   - 非同期処理の管理
   - プロセス間通信の設定
   - エラーパターンと重要度（2段階評価）
   - サンプリング機能の強化

4. 統一メトリクス（v1.2.0）
   - システムメトリクスの標準定義
   - パフォーマンス指標の統一
   - アラートポリシーの一元管理
   - レポート形式の標準化
   - エラーパターンと重要度

### 引継ぎドキュメント

`docs/HANDOVER.md`は、開発タスクの引継ぎ情報を管理します。過去の引継ぎ文書は`docs/archive/`に保管されています。

## プロジェクト構造

```
Cline/
├── package.json           # プロジェクトのルート設定
├── .gitignore            # Git除外設定
├── .gitmodules           # サブモジュール設定
├── jest.config.js        # Jestテスト設定
├── tsconfig.json         # TypeScript設定
├── .eslintrc.json        # ESLint設定
├── .prettierrc           # Prettier設定
├── docs/                 # ドキュメント
│   ├── PROJECT_CONTEXT.md  # プロジェクト全体の文脈情報
│   ├── HANDOVER.md        # 引継ぎ文書
│   └── archive/           # 引継ぎ文書アーカイブ
├── standards/            # 作業標準設計
│   ├── _meta/            # メタ情報
│   │   ├── schemas/      # スキーマ定義
│   │   │   ├── process_schema.yaml    # プロセス定義スキーマ
│   │   │   ├── validation_schema.yaml # 検証定義スキーマ
│   │   │   ├── context_schema.yaml    # コンテキスト定義スキーマ
│   │   │   └── error_schema.yaml      # エラーパターン定義スキーマ
│   │   └── contexts/     # コンテキスト定義
│   ├── processes/        # プロセス定義
│   │   ├── _base/       # 基本プロセス
│   │   └── mcp/         # MCPサーバー関連
│   ├── validations/      # 検証フレームワーク
│   │   └── prerequisites/ # 前提条件チェック
│   └── templates/        # 各種テンプレート
│       ├── process/      # プロセス用
│       ├── validation/   # 検証用
│       └── documentation/ # ドキュメント用
├── tests/               # テストディレクトリ
│   ├── unit/           # ユニットテスト
│   └── integration/    # 統合テスト（予定）
├── extensions/          # 拡張機能ディレクトリ
│   ├── core/           # コア拡張機能
│   │   └── environment-checker/  # 環境互換性チェッカー
│   ├── mcp/            # MCPサーバー
│   ├── configs/        # 設定ファイル
│   └── prompts/        # カスタムプロンプト
└── .github/            # GitHub設定
    └── workflows/      # GitHub Actions設定
```

## MCPサーバー

MCPサーバーは`MCP/servers`ディレクトリでサブモジュールとして管理されています。Model Context Protocol Serversリポジトリの全サーバーが利用可能です。

### MCPフレームワーク標準準拠（v1.2.0）

1. エラー管理
   - Critical: システム停止、セキュリティ違反、データ損失リスクに対する15分以内の即時対応
   - Non-Critical: 一般的なエラー、パフォーマンス低下に対する60分以内の対応
   - 自動リカバリー機能：エラータイプに基づく判断とリソース状態の監視

2. リモートMCPサポート
   - 認証：OAuth2およびトークンベース認証
   - サービスディスカバリー：DNS、HTTP、手動設定
   - ステートレス操作のサポート

3. エージェントサポート
   - 階層的なエージェントシステム（Coordinator/Worker/Specialist）
   - インタラクティブなワークフローのサポート
   - ストリーミング結果の対応

4. サンプリング機能
   - LLMからの補完要求機能
   - 未対応クライアント向け代替機能
     - ツールベースの補完
     - プロンプトベースの補完

### サーバー管理の特徴

1. サブモジュール管理
   - GitHubの公式リポジトリを参照
   - 一貫性のあるバージョン管理
   - 簡単なアップデート管理

2. 環境チェッカーによる互換性確認
   - システム要件の検証
   - 必要な環境変数の確認
   - ランタイムの互換性チェック

### サーバーの設定と認証情報の管理

1. 設定ファイルの構造
   ```json
   {
     "mcpServers": {
       "サーバー名": {
         "command": "実行コマンド",
         "args": ["コマンド引数"],
         "disabled": false,
         "alwaysAllow": [],
         "env": {
           "認証変数": "値",
           "設定変数": "値"
         }
       }
     }
   }
   ```

2. 認証情報の管理
   - 基本ディレクトリ構造：
     ```
     MCP/
     ├── config/
     │   └── [サーバー名]/
     │       ├── oauth.keys.json    # OAuth認証キー
     │       └── token.json         # アクセストークン
     └── servers/
     ```
   - 環境変数による参照：
     ```json
     "env": {
       "SERVICE_API_KEY": "APIキー",
       "SERVICE_OAUTH_KEYS": "キーファイルパス",
       "SERVICE_TOKEN_PATH": "トークンファイルパス"
     }
     ```

3. サーバータイプ別の追加設定
   - Python系サーバー：
     ```json
     "env": {
       "PYTHONPATH": "ソースコードパス"
     }
     ```
   - Node.js系サーバー：
     - 依存パッケージの管理
     - ビルド設定の指定

### トラブルシューティングガイド

1. モジュール未検出エラー
   ```bash
   # Pythonモジュールの場合
   cd MCP/servers/src/.venv/Scripts
   .\activate
   cd ../../[サーバー名]
   pip install -e .
   ```

2. 認証エラー
   - 環境変数の確認
   - キーファイルの配置確認
   ```
   MCP/config/[サーバー名]/
   └── oauth.keys.json
   ```

3. 設定ファイルの検証
   - 必須パラメータの確認
   - パスの正確性の確認
   - 環境変数の設定確認

### 利用可能なサーバー

以下のMCPサーバーが利用可能です：

- aws-kb-retrieval: AWS Knowledge Base検索
- brave-search: Brave検索エンジン連携
- everart: アート生成・管理
- everything: ファイル検索
- fetch: Webコンテンツ取得
- filesystem: ファイルシステム操作
- gdrive: Google Drive連携
- git: Gitリポジトリ操作
- github: GitHub API連携
- gitlab: GitLab API連携
- google-maps: Google Maps連携
- memory: メモリ管理
- postgres: PostgreSQL操作
- puppeteer: ブラウザ自動化
- sentry: エラー追跡
- sequentialthinking: 思考プロセス管理
- slack: Slack連携
- sqlite: SQLite操作
- time: 時間管理

## バージョン管理方針

- コア拡張機能：サブモジュールとして管理し、定期的に更新
- 依存パッケージ：セマンティックバージョニングに従って更新

## 貢献

1. このリポジトリをフォーク
2. 新しいブランチを作成（`git checkout -b feature/amazing-feature`）
3. 変更をコミット（`git commit -m 'Add some amazing feature'`）
4. ブランチにプッシュ（`git push origin feature/amazing-feature`）
5. プルリクエストを作成

詳細は[CONTRIBUTING.md](CONTRIBUTING.md)を参照してください。
