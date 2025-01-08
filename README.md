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

### 自動更新チェック

このプロジェクトはGitHub Actionsを使用して、以下の自動チェックを実行します：

- 毎週月曜日に更新チェック
- 更新が見つかった場合、自動的にIssueを作成
- 手動でワークフローを実行可能

更新が見つかった場合、以下の情報を含むIssueが作成されます：
- 利用可能な更新の一覧
- 更新手順
- 潜在的な影響の説明

## プロジェクト構造

```
Cline/
├── package.json           # プロジェクトのルート設定
├── .gitignore            # Git除外設定
├── .gitmodules           # サブモジュール設定
└── extensions/           # 拡張機能ディレクトリ
    ├── core/             # コア拡張機能
    ├── mcp/              # MCPサーバー
    ├── configs/          # 設定ファイル
    └── prompts/          # カスタムプロンプト
```

## MCPサーバー

外部MCPサーバーは`MCP/`ディレクトリ配下でサブモジュールとして管理されています。
現在以下のサーバーが統合されています：

- github-server: GitHub操作用MCPサーバー（from modelcontextprotocol/servers）

### サーバーの設定

サーバーの設定は`extensions/configs/extensions.json`で管理されています。
各サーバーの有効/無効の切り替えや環境変数の設定が可能です。

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