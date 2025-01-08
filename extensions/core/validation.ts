import { ExtensionError } from './types';
import { z } from 'zod';

/**
 * 設定のバリデーション
 */
export function validateConfig<T>(
  config: unknown,
  schema: z.ZodType<T>
): T {
  try {
    return schema.parse(config);
  } catch (error) {
    if (error instanceof z.ZodError) {
      throw new ExtensionError(
        '設定ファイルが無効です',
        'INVALID_CONFIG',
        error.errors
      );
    }
    throw error;
  }
}

/**
 * 環境変数の存在チェック
 */
export function validateEnvironment(required: string[]): void {
  const missing = required.filter(key => !process.env[key]);
  if (missing.length > 0) {
    throw new ExtensionError(
      '必要な環境変数が設定されていません',
      'MISSING_ENV',
      missing
    );
  }
}

/**
 * パスの存在チェック
 */
export async function validatePaths(paths: string[]): Promise<void> {
  const fs = await import('fs/promises');
  
  for (const path of paths) {
    try {
      await fs.access(path);
    } catch {
      throw new ExtensionError(
        `パスが存在しません: ${path}`,
        'INVALID_PATH'
      );
    }
  }
}

// スキーマの型定義
export interface MCPServerSchema {
  enabled: boolean;
  command: string;
  args: string[];
  env: Record<string, string>;
}

export interface ExtensionConfigSchema {
  mcp: {
    servers: Record<string, MCPServerSchema>;
  };
  prompts: {
    customInstructions: {
      enabled: boolean;
      path: string;
    };
  };
  settings: {
    core: {
      updateStrategy: 'submodule' | 'manual';
      version: string;
    };
  };
}

// 共通のスキーマ定義
export const commonSchemas: {
  mcpServer: z.ZodType<MCPServerSchema>;
  extensionConfig: z.ZodType<ExtensionConfigSchema>;
} = {
  mcpServer: z.object({
    enabled: z.boolean(),
    command: z.string(),
    args: z.array(z.string()),
    env: z.record(z.string())
  }),

  extensionConfig: z.object({
    mcp: z.object({
      servers: z.record(z.lazy(() => commonSchemas.mcpServer))
    }),
    prompts: z.object({
      customInstructions: z.object({
        enabled: z.boolean(),
        path: z.string()
      })
    }),
    settings: z.object({
      core: z.object({
        updateStrategy: z.enum(['submodule', 'manual']),
        version: z.string()
      })
    })
  })
};