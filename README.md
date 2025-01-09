# Cline Custom Extensions

Clineのカスタム拡張機能を管理するリポジトリです。

## セットアップ

```bash
# リポジトリのクローン
git clone https://github.com/Cizimy/Cline.git
cd Cline

# 依存関係のインストール（サブモジュールも自動的に初期化されます）
npm install
```

## 更新管理

### サブモジュールの更新

```bash
# サブモジュールを最新バージョンに更新
npm run update:submodules

# 更新後、必要に応じてビルドを実行
npm run build
```

### 依存関係の更新

```bash
# すべての更新をチェック（サブモジュールとnpm）
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
│   ├── HANDOVER.md     # 引継ぎ文書
│   └── archive/        # 引継ぎ文書アーカイブ
├── tests/              # テストディレクトリ
│   ├── unit/          # ユニットテスト
│   └── integration/   # 統合テスト（予定）
├── extensions/         # 拡張機能ディレクトリ
│   ├── core/          # コア拡張機能
│   ├── mcp/           # MCPサーバー
│   ├── configs/       # 設定ファイル
│   └── prompts/       # カスタムプロンプト
└── .github/           # GitHub設定
    └── workflows/     # GitHub Actions設定
```

## MCPサーバー

外部MCPサーバーは`MCP/`ディレクトリ配下でサブモジュールとして管理されています。現在以下のサーバーが統合されています：

- github-server: GitHub操作用MCPサーバー（from modelcontextprotocol/servers）

### サーバーの設定

サーバーの設定は`extensions/configs/extensions.json`で管理されています。各サーバーの有効/無効の切り替えや環境変数の設定が可能です。

## バージョン管理方針

- コア拡張機能：サブモジュールとして管理し、定期的に更新
- 外部MCPサーバー：サブモジュールとして管理し、安定版にバージョンを固定
- 依存パッケージ：セマンティックバージョニングに従って更新

## 貢献

1. このリポジトリをフォーク
2. 新しいブランチを作成（`git checkout -b feature/amazing-feature`）
3. 変更をコミット（`git commit -m 'Add some amazing feature'`）
4. ブランチにプッシュ（`git push origin feature/amazing-feature`）
5. プルリクエストを作成

詳細は[CONTRIBUTING.md](CONTRIBUTING.md)を参照してください。
