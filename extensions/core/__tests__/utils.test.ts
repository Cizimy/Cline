import { safeAsync, deepMerge, getEnvVar, retry } from '../utils';
import { ExtensionError } from '../types';

describe('Utils', () => {
  describe('safeAsync', () => {
    it('正常な Promise を処理できること', async () => {
      const result = await safeAsync(Promise.resolve('test'), 'TEST_ERROR');
      expect(result).toBe('test');
    });

    it('エラーを ExtensionError として wrap すること', async () => {
      await expect(
        safeAsync(Promise.reject(new Error('test error')), 'TEST_ERROR')
      ).rejects.toThrow(ExtensionError);
    });
  });

  describe('deepMerge', () => {
    it('シンプルなオブジェクトをマージできること', () => {
      const base = {
        name: 'test',
        value: 1,
        enabled: true,
      };

      const override = {
        value: 2,
      };

      const result = deepMerge(base, override);
      expect(result).toEqual({
        name: 'test',
        value: 2,
        enabled: true,
      });
    });

    it('ネストされたオブジェクトをマージできること', () => {
      const base = {
        settings: {
          name: 'test',
          options: {
            enabled: false,
            debug: true,
            values: {
              timeout: 1000,
            },
          },
        },
      };

      const override = {
        settings: {
          options: {
            enabled: true,
            values: {
              timeout: 2000,
            },
          },
        },
      };

      const result = deepMerge(base, override);
      expect(result.settings.options.enabled).toBe(true);
      expect(result.settings.name).toBe('test');
      expect(result.settings.options.debug).toBe(true);
      expect(result.settings.options.values.timeout).toBe(2000);
    });

    it('配列を置き換えできること', () => {
      const base = {
        items: [1, 2, 3],
        config: {
          tags: ['a', 'b'],
        },
      };

      const override = {
        items: [4, 5],
        config: {
          tags: ['c'],
        },
      };

      const result = deepMerge(base, override);
      expect(result.items).toEqual([4, 5]);
      expect(result.config.tags).toEqual(['c']);
    });
  });

  describe('getEnvVar', () => {
    const originalEnv = process.env;

    beforeEach(() => {
      process.env = { ...originalEnv };
    });

    afterEach(() => {
      process.env = originalEnv;
    });

    it('環境変数が存在する場合、その値を返すこと', () => {
      process.env.TEST_VAR = 'test-value';
      expect(getEnvVar('TEST_VAR')).toBe('test-value');
    });

    it('必須の環境変数が存在しない場合、エラーを投げること', () => {
      expect(() => getEnvVar('NON_EXISTENT_VAR')).toThrow(ExtensionError);
    });

    it('オプションの環境変数が存在しない場合、空文字を返すこと', () => {
      expect(getEnvVar('NON_EXISTENT_VAR', false)).toBe('');
    });
  });

  describe('retry', () => {
    beforeAll(() => {
      jest.useFakeTimers();
    });

    afterAll(() => {
      jest.useRealTimers();
    });

    afterEach(() => {
      jest.clearAllTimers();
    });

    it('成功する関数は1回で完了すること', async () => {
      const fn = jest.fn().mockResolvedValue('success');
      const promise = retry(fn, { maxAttempts: 3 });

      jest.runAllTimers();
      const result = await promise;

      expect(result).toBe('success');
      expect(fn).toHaveBeenCalledTimes(1);
    });

    it('失敗後に成功する関数は再試行されること', async () => {
      const fn = jest
        .fn()
        .mockRejectedValueOnce(new Error('fail'))
        .mockResolvedValue('success');

      const promise = retry(fn, {
        maxAttempts: 2,
        delay: 100,
        backoff: 1,
      });

      // 最初の試行（失敗）
      await Promise.resolve();
      // 遅延時間を進める
      jest.advanceTimersByTime(100);
      // 2回目の試行（成功）
      await Promise.resolve();

      const result = await promise;
      expect(result).toBe('success');
      expect(fn).toHaveBeenCalledTimes(2);
    });

    it('すべての試行が失敗した場合、エラーを投げること', async () => {
      const fn = jest.fn().mockRejectedValue(new Error('always fail'));

      const promise = retry(fn, {
        maxAttempts: 2,
        delay: 100,
        backoff: 1,
      });

      // 最初の試行
      await Promise.resolve();
      // 遅延時間を進める
      jest.advanceTimersByTime(100);
      // 2回目の試行
      await Promise.resolve();

      await expect(promise).rejects.toThrow(ExtensionError);
      expect(fn).toHaveBeenCalledTimes(2);
    });
  });
});
