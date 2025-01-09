import {
  validateConfig,
  validateEnvironment,
  validatePaths,
  commonSchemas,
} from '../validation';
import { ExtensionError } from '../types';
import { z } from 'zod';

describe('Validation', () => {
  describe('validateConfig', () => {
    it('MCPサーバー設定を検証できること', () => {
      const config = {
        enabled: true,
        command: 'node',
        args: ['server.js'],
        env: {
          PORT: '3000',
        },
      };

      expect(() =>
        validateConfig(config, commonSchemas.mcpServer)
      ).not.toThrow();
    });

    it('拡張機能の設定を検証できること', () => {
      const config = {
        mcp: {
          servers: {
            test: {
              enabled: true,
              command: 'node',
              args: ['server.js'],
              env: {},
            },
          },
        },
        prompts: {
          customInstructions: {
            enabled: true,
            path: './prompts/custom.md',
          },
        },
        settings: {
          core: {
            updateStrategy: 'manual' as const,
            version: '1.0.0',
          },
        },
      };

      expect(() =>
        validateConfig(config, commonSchemas.extensionConfig)
      ).not.toThrow();
    });

    it('カスタムスキーマでの検証をサポートすること', () => {
      const customSchema = z.object({
        name: z.string(),
        settings: z.object({
          enabled: z.boolean(),
          value: z.number().optional(),
        }),
      });

      const validConfig = {
        name: 'test',
        settings: {
          enabled: true,
          value: 42,
        },
      };

      const invalidConfig = {
        settings: {
          enabled: 'true',
        },
      };

      expect(() => validateConfig(validConfig, customSchema)).not.toThrow();
      expect(() => validateConfig(invalidConfig, customSchema)).toThrow(
        ExtensionError
      );
    });
  });

  describe('validateEnvironment', () => {
    const originalEnv = process.env;

    beforeEach(() => {
      process.env = { ...originalEnv };
    });

    afterEach(() => {
      process.env = originalEnv;
    });

    it('必要な環境変数が存在する場合、エラーを投げないこと', () => {
      process.env.CLINE_HOME = '/path/to/home';
      process.env.CLINE_CONFIG = '/path/to/config';

      expect(() =>
        validateEnvironment(['CLINE_HOME', 'CLINE_CONFIG'])
      ).not.toThrow();
    });

    it('必要な環境変数が欠けている場合、エラーを投げること', () => {
      process.env.CLINE_HOME = '/path/to/home';
      // CLINE_CONFIGは設定しない

      expect(() => validateEnvironment(['CLINE_HOME', 'CLINE_CONFIG'])).toThrow(
        ExtensionError
      );
    });
  });

  describe('validatePaths', () => {
    const fs = jest.requireActual(
      'fs/promises'
    ) as typeof import('fs/promises');

    beforeEach(() => {
      jest.spyOn(fs, 'access').mockImplementation(path => {
        return new Promise<void>((resolve, reject) => {
          if (path.toString() === '/valid/path') {
            resolve();
          } else {
            reject(new Error('ENOENT'));
          }
        });
      });
    });

    afterEach(() => {
      jest.restoreAllMocks();
    });

    it('有効なパスの場合、エラーを投げないこと', async () => {
      await expect(validatePaths(['/valid/path'])).resolves.not.toThrow();
    });

    it('無効なパスの場合、エラーを投げること', async () => {
      await expect(validatePaths(['/invalid/path'])).rejects.toThrow(
        ExtensionError
      );
    });

    it('複数のパスを検証できること', async () => {
      await expect(
        validatePaths(['/valid/path', '/invalid/path'])
      ).rejects.toThrow(ExtensionError);
    });
  });
});
