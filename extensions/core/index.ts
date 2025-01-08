/**
 * Cline拡張機能開発用コアモジュール
 */

// 型定義のエクスポート
export * from './types';

// バリデーション機能のエクスポート
export * from './validation';

// ユーティリティ関数のエクスポート
export * from './utils';

// 定数定義
export const CORE_VERSION = '1.0.0';

// 基本設定
export const DEFAULT_CONFIG = {
  mcp: {
    servers: {}
  },
  prompts: {
    customInstructions: {
      enabled: true,
      path: '../prompts/custom-instructions.md'
    }
  },
  settings: {
    core: {
      updateStrategy: 'manual' as const,
      version: CORE_VERSION
    }
  }
};

// 初期化関数
export async function initializeExtension(): Promise<void> {
  try {
    // 環境変数の検証と取得
    const { getEnvVar } = await import('./utils');
    const clineHome = getEnvVar('CLINE_HOME');
    const configPath = getEnvVar('CLINE_CONFIG_PATH');

    // 基本ディレクトリの存在確認
    const { validatePaths } = await import('./validation');
    await validatePaths([clineHome, configPath]);

    console.warn('[Cline Extension] Initialization completed');
  } catch (error) {
    console.error('[Cline Extension] Initialization failed:', error);
    throw error;
  }
}

// MCPサーバー基本クラス
export abstract class BaseMCPServer {
  protected constructor(
    protected readonly name: string,
    protected readonly version: string
  ) {}

  abstract initialize(): Promise<void>;
  abstract shutdown(): Promise<void>;
  
  protected logInfo(message: string): void {
    console.warn(`[${this.name}] ${message}`);
  }
  
  protected logError(message: string, error?: unknown): void {
    console.error(`[${this.name}] ${message}`, error);
  }
}