/**
 * Cline拡張機能の共通型定義
 */

// MCPサーバーの設定型
export interface MCPServerConfig {
  enabled: boolean;
  command: string;
  args: string[];
  env: Record<string, string>;
}

// MCPサーバーのメタデータ
export interface MCPServerMeta {
  name: string;
  version: string;
  description?: string;
}

// MCPツールの共通インターフェース
export interface MCPTool {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
  handler: (args: unknown) => Promise<unknown>;
}

// 設定ファイルの型定義
export interface ExtensionConfig {
  mcp: {
    servers: Record<string, MCPServerConfig>;
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

// エラー型
export class ExtensionError extends Error {
  constructor(
    message: string,
    public code: string,
    public details?: unknown
  ) {
    super(message);
    this.name = 'ExtensionError';
  }
}
