import { ExtensionError } from './types';

/**
 * 非同期処理のエラーハンドリングユーティリティ
 */
export async function safeAsync<T>(
  promise: Promise<T>,
  errorCode: string
): Promise<T> {
  try {
    return await promise;
  } catch (error) {
    if (error instanceof ExtensionError) {
      throw error;
    }
    throw new ExtensionError(
      error instanceof Error ? error.message : '不明なエラーが発生しました',
      errorCode,
      error
    );
  }
}

type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends (infer U)[]
    ? U[]
    : T[P] extends object
    ? DeepPartial<T[P]>
    : T[P];
};

/**
 * オブジェクトの型ガード
 */
function isPlainObject(value: unknown): value is object {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

/**
 * ディープマージユーティリティ
 */
export function deepMerge<T>(target: T, source: DeepPartial<T>): T {
  if (!isPlainObject(target) || !isPlainObject(source)) {
    return source as T;
  }

  const output = { ...target };

  Object.keys(source).forEach(key => {
    if (key in target) {
      const targetValue = target[key as keyof T];
      const sourceValue = source[key as keyof T];

      if (sourceValue === undefined) {
        return;
      }

      if (Array.isArray(targetValue)) {
        if (Array.isArray(sourceValue)) {
          (output as any)[key] = [...sourceValue];
        }
      } else if (isPlainObject(targetValue) && isPlainObject(sourceValue)) {
        (output as any)[key] = deepMerge(targetValue, sourceValue);
      } else {
        (output as any)[key] = sourceValue;
      }
    }
  });

  return output;
}

/**
 * 環境変数の取得ユーティリティ
 */
export function getEnvVar(key: string, required = true): string {
  const value = process.env[key];
  if (required && !value) {
    throw new ExtensionError(
      `環境変数 ${key} が設定されていません`,
      'MISSING_ENV_VAR'
    );
  }
  return value ?? '';
}

/**
 * パフォーマンス計測ユーティリティ
 */
export async function measurePerformance<T>(
  name: string,
  fn: () => Promise<T>
): Promise<T> {
  const start = performance.now();
  try {
    return await fn();
  } finally {
    const duration = performance.now() - start;
    console.warn(`[Performance] ${name}: ${duration.toFixed(2)}ms`);
  }
}

/**
 * 再試行ユーティリティ
 */
export async function retry<T>(
  fn: () => Promise<T>,
  options: {
    maxAttempts?: number;
    delay?: number;
    backoff?: number;
  } = {}
): Promise<T> {
  const {
    maxAttempts = 3,
    delay = 1000,
    backoff = 2
  } = options;

  let lastError: unknown;
  
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      if (attempt === maxAttempts) break;
      
      await new Promise(resolve => 
        setTimeout(resolve, delay * Math.pow(backoff, attempt - 1))
      );
    }
  }

  throw new ExtensionError(
    '操作が失敗しました',
    'RETRY_FAILED',
    lastError
  );
}