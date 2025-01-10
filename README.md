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
├── docs/                # ドキュメント
│   ├── PROJECT_CONTEXT.md  # プロジェクト全体の文脈情報
│   ├── HANDOVER.md     # 引継ぎ文書
│   └── archive/        # 引継ぎ文書アーカイブ
├── tests/              # テストディレクトリ
│   ├── unit/          # ユニットテスト
│   └── integration/   # 統合テスト（予定）
├── extensions/         # 拡張機能ディレクトリ
│   ├── core/          # コア拡張機能
│   │   └── environment-checker/  # 環境互換性チェッカー
│   ├── mcp/           # MCPサーバー
│   ├── configs/       # 設定ファイル
│   └── prompts/       # カスタムプロンプト
└── .github/           # GitHub設定
    └── workflows/     # GitHub Actions設定
```

## MCPサーバー

MCPサーバーは`MCP/`ディレクトリで管理されます。新しいMCPサーバーを追加する際は、以下の手順に従ってください：

### サーバー追加のガイドライン

1. 環境チェッカーによる互換性確認
   - システム要件の検証
   - 必要な環境変数の確認
   - ランタイムの互換性チェック

2. extensions.jsonでの設定
   - リポジトリ情報の明示的な指定
   - 更新戦略の設定
   - 必要な環境変数の定義

### サーバーの設定と管理

サーバーの設定は`extensions/configs/extensions.json`で管理されています：

- リポジトリ情報の明示的な指定
  - 外部リポジトリURLの設定（必須）
  - ブランチの指定
  - 更新戦略の設定
- サーバーの有効/無効の切り替え
- 環境変数の設定
- 自動同期の設定

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
