# Noah Custom Extensions

Noahのカスタム拡張機能を管理するリポジトリです。

## セットアップ

```bash
# リポジトリのクローン
git clone https://github.com/Cizimy/Noah.git
cd Noah

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

このドキュメントは、特にNoahがタスクを効率的に実行するために必要な基本情報を提供することを目的としています。

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

### MCPサーバー管理

MCPサーバーは新しい設定管理システムを導入し、より効率的な管理を実現しています：

1. 設定管理システム
   ```
   MCP/
   ├── config/              # MCPサーバー設定管理
   │   ├── env.json        # 環境変数定義
   │   ├── base.json       # 基本設定テンプレート
   │   ├── development.json # 開発環境設定
   │   └── README.md       # 設定管理ドキュメント
   └── servers/            # 標準MCPサーバー
       ├── sqlite/         # SQLiteサーバー（Python実装）
       ├── postgres/       # PostgreSQLサーバー（TypeScript実装）
       ├── filesystem/     # ファイル操作サーバー（TypeScript実装）
       ├── memory/         # 知識グラフメモリサーバー（TypeScript実装）
       ├── git/           # Gitリポジトリ操作（Python実装）
       ├── github/        # GitHub API連携（TypeScript実装）
       ├── gitlab/        # GitLab API連携（TypeScript実装）
       └── puppeteer/     # ブラウザ自動化（TypeScript実装）
   ```

2. 実装状況
   - [x] SQLiteサーバー: Python実装による標準MCPサーバー
   - [x] PostgreSQLサーバー: TypeScript実装による読み取り専用アクセス
   - [x] Filesystemサーバー: TypeScript実装によるファイル操作基盤
   - [x] Memoryサーバー: TypeScript実装による知識グラフ管理
   - [x] Gitサーバー: Python実装によるリポジトリ操作
   - [x] GitHubサーバー: TypeScript実装によるGitHub API連携
   - [x] GitLabサーバー: TypeScript実装によるGitLab API連携
   - [x] Puppeteerサーバー: TypeScript実装によるブラウザ自動化
   - [ ] その他のサーバー: 段階的に実装予定

3. 運用ルール
   - 標準MCPサーバーを優先的に使用
   - サーバー実装前に必ずREADMEを確認
   - 設定変更時は必ずgenerate-config.ps1を実行
   - 環境変数は必ずenv.jsonで管理
   - パスの指定は環境変数を使用
   - 環境変数は命名規則（[SERVER]_[CATEGORY]_[NAME]）に従う
   - 実装言語に応じた適切な設定を使用
     * Python: PYTHONPATHとモジュール名の設定
     * TypeScript: NODE_PATHとdistディレクトリの設定

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

### 引継ぎドキュメント

`docs/HANDOVER.md`は、開発タスクの引継ぎ情報を管理します。過去の引継ぎ文書は`docs/archive/`に保管されています。

## プロジェクト構造

```
Noah/
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
├── MCP/                  # MCPサーバー関連
│   ├── config/           # 設定管理
│   └── servers/          # 標準サーバー
└── standards/            # 作業標準設計
    ├── _meta/            # メタ情報
    ├── processes/        # プロセス定義
    ├── validations/      # 検証フレームワーク
    └── templates/        # 各種テンプレート
```

## バージョン管理方針

- コア拡張機能：サブモジュールとして管理し、定期的に更新
- 依存パッケージ：セマンティックバージョニングに従って更新
- MCPサーバー：標準サーバーの活用と設定の標準化

## 貢献

1. このリポジトリをフォーク
2. 新しいブランチを作成（`git checkout -b feature/amazing-feature`）
3. 変更をコミット（`git commit -m 'Add some amazing feature'`）
4. ブランチにプッシュ（`git push origin feature/amazing-feature`）
5. プルリクエストを作成

詳細は[CONTRIBUTING.md](CONTRIBUTING.md)を参照してください。
