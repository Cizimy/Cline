# テスト実行サマリー
実行日時: 2025-01-12 22:56:45

## 実行結果
- 総テスト数: 3
- 成功: 3
- 失敗: 0

## 詳細結果

### ✓ セキュリティテスト
出力:
```
# セキュリティテストレポート
実行日時: 2025-01-12 22:54:53

## テスト結果サマリー:
- クリティカルエラー数: 0
- 非クリティカルエラー数: 0
- 警告数: 0

問題は検出されませんでした。

## セキュリティ推奨事項:
1. すべての設定ファイルで適切なファイルパーミッションを設定
2. 機密情報は環境変数または暗号化された設定ファイルで管理
3. すべてのユーザー入力に対して適切なバリデーションを実装
4. エラーメッセージから機密情報が漏洩しないよう注意
5. 適切なレート制限を実装してDDoS攻撃を防止
6. 最新のセキュリティパッチを適用
7. 定期的なセキュリティ監査を実施
8. トークンローテーションを有効化し、適切な間隔で実施
9. セキュアなトークン保存方式（encrypted/secure_keystore）を使用
10. HTTPSを使用し、安全でない通信プロトコルを避ける
```

### ✓ スキーマ検証
出力:
```
# スキーマ検証レポート
実行日時: 2025-01-12 22:54:54

検証結果サマリー:
- エラー数: 0
- 警告数: 0

問題は検出されませんでした。
```

### ✓ 非同期処理・パフォーマンステスト
出力:
```
非同期処理テストを実行中...
パフォーマンステストを実行中...
サンプリング機能のパフォーマンステストを実行中...
リモートMCP接続のパフォーマンステストを実行中...
# 非同期処理・パフォーマンステストレポート
実行日時: 2025-01-12 22:56:45

## 基本パフォーマンスメトリクス:
- スループット: 119237.64 req/sec
- エラー数: 0
- レイテンシー:
  - P50: 0.000 ms
  - P95: 0.000 ms
  - P99: 0.000 ms

## サンプリング機能メトリクス:

### llm_sampling:
- 成功率: 99.38%
- 成功数: 959
- エラー数: 6
- レイテンシー:
  - P50: 15.582 ms
  - P95: 16.387 ms
  - P99: 17.104 ms

### tool_fallback:
- 成功率: 99.07%
- 成功数: 956
- エラー数: 9
- レイテンシー:
  - P50: 15.584 ms
  - P95: 16.611 ms
  - P99: 17.187 ms

### prompt_fallback:
- 成功率: 99.79%
- 成功数: 963
- エラー数: 2
- レイテンシー:
  - P50: 15.582 ms
  - P95: 16.659 ms
  - P99: 17.177 ms

## テスト結果サマリー:
- エラー数: 10
- 警告数: 3

## 詳細:
- [ERROR] discoveryエラー (http): httpエラー
- [ERROR] authenticationエラー (token): tokenエラー
- [ERROR] authenticationエラー (oauth2): oauth2エラー
- [ERROR] discoveryエラー (manual): manualエラー
- [ERROR] authenticationエラー (token): tokenエラー
- [ERROR] authenticationエラー (token): tokenエラー
- [ERROR] discoveryエラー (manual): manualエラー
- [ERROR] authenticationエラー (oauth2): oauth2エラー
- [ERROR] statelessエラー (operation): operationエラー
- [ERROR] discoveryエラー (manual): manualエラー
- [WARNING] discoveryのレイテンシー統計:
  - P50: 0.016秒
  - P95: 0.017秒
  - P99: 0.018秒
- [WARNING] authenticationのレイテンシー統計:
  - P50: 0.016秒
  - P95: 0.017秒
  - P99: 0.018秒
- [WARNING] statelessのレイテンシー統計:
  - P50: 0.016秒
  - P95: 0.016秒
  - P99: 0.017秒
```


## 詳細レポート
- [スキーマ検証レポート](validation_report.md)
- [非同期処理・パフォーマンステストレポート](async_performance_report.md)
- [セキュリティテストレポート](security_report.md)