export default {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      [
        'feat', // 新機能
        'fix', // バグ修正
        'docs', // ドキュメントのみの変更
        'style', // コードの意味に影響を与えない変更（空白、フォーマット、セミコロンなど）
        'refactor', // バグ修正や機能追加のないコードの変更
        'perf', // パフォーマンスを向上させるコードの変更
        'test', // テストの追加・修正
        'chore', // ビルドプロセスやドキュメント生成などの補助ツールやライブラリの変更
        'ci', // CI設定ファイルやスクリプトの変更
        'revert', // コミットの取り消し
      ],
    ],
    'type-case': [2, 'always', 'lower'],
    'type-empty': [2, 'never'],
    'scope-case': [2, 'always', 'lower'],
    'subject-empty': [2, 'never'],
    'subject-full-stop': [2, 'never', '.'],
    'header-max-length': [2, 'always', 72],
  },
};
