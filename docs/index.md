# Cline ドキュメント

## 目次

- [開発ガイド](DEVELOPMENT.md)
- [APIリファレンス](API.md)
- [コントリビューションガイド](../CONTRIBUTING.md)
- [タスク引継ぎガイド](HANDOVER_GUIDELINES.md)
- [引継ぎテンプレート](HANDOVER_TEMPLATE.md)

## ドキュメントの更新

ドキュメントの更新は以下の手順で行います：

1. 変更が必要なドキュメントを編集
2. 変更内容をコミット

```bash
git add docs/
git commit -m "docs: [変更内容の概要]"
```

3. 変更をプッシュ

```bash
git push origin main
```

## ドキュメントの構造

```
docs/
├── index.md            # ドキュメントの目次
├── DEVELOPMENT.md      # 開発ガイド
├── API.md              # APIリファレンス
├── HANDOVER_GUIDELINES.md # 引継ぎガイド
├── HANDOVER_TEMPLATE.md  # 引継ぎテンプレート
└── archive/            # 過去の引継ぎ文書
```

## ドキュメント作成ガイド

1. 新しいドキュメントを作成する場合

- 適切なディレクトリにファイルを作成
- index.mdにリンクを追加
- 変更をコミット

2. 既存ドキュメントを更新する場合

- 変更内容を明確に記述
- バージョン情報を更新
- 関連する他のドキュメントも必要に応じて更新

3. ドキュメントの品質基準

- 明確で簡潔な記述
- 具体的な例を含める
- 最新の状態を保つ
