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