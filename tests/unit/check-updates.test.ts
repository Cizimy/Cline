import { jest, describe, beforeEach, it, expect } from '@jest/globals';

// モックの設定
const mockExecSync = jest.fn();
const mockReadFileSync = jest.fn();
const mockJoin = jest.fn();
const mockDirname = jest.fn();
const mockFileURLToPath = jest.fn();

// モジュールのモックを設定
jest.unstable_mockModule('child_process', () => ({
  execSync: mockExecSync
}));

jest.unstable_mockModule('fs', () => ({
  readFileSync: mockReadFileSync,
  default: {
    readFileSync: mockReadFileSync
  }
}));

jest.unstable_mockModule('path', () => ({
  join: mockJoin,
  dirname: mockDirname,
  default: {
    join: mockJoin,
    dirname: mockDirname
  }
}));

jest.unstable_mockModule('url', () => ({
  fileURLToPath: mockFileURLToPath,
  default: {
    fileURLToPath: mockFileURLToPath
  }
}));

describe('check-updates script', () => {
  beforeEach(() => {
    // モックをリセット
    jest.clearAllMocks();
    jest.resetModules();

    // 基本的なモックの実装
    mockJoin.mockImplementation((...args) => args.join('/'));
    mockDirname.mockReturnValue('/mock/dir');
    mockFileURLToPath.mockReturnValue('/mock/path');
  });

  describe('checkGitStatus', () => {
    it('should return true when working directory is clean', async () => {
      // モックの設定
      mockExecSync.mockReturnValueOnce(Buffer.from(''));

      // テスト対象の関数をインポート
      const { checkGitStatus } = await import('../../scripts/check-updates.js');
      const result = checkGitStatus();

      // 検証
      expect(result).toBe(true);
      expect(mockExecSync).toHaveBeenCalledWith(
        'git status --porcelain',
        expect.objectContaining({ cwd: expect.any(String) })
      );
    });

    it('should return false when there are uncommitted changes', async () => {
      // モックの設定
      mockExecSync.mockReturnValueOnce(Buffer.from(' M file.txt'));

      // テスト対象の関数をインポート
      const { checkGitStatus } = await import('../../scripts/check-updates.js');
      const result = checkGitStatus();

      // 検証
      expect(result).toBe(false);
      expect(mockExecSync).toHaveBeenCalledWith(
        'git status --porcelain',
        expect.objectContaining({ cwd: expect.any(String) })
      );
    });

    it('should handle git command errors', async () => {
      // モックの設定
      mockExecSync.mockImplementationOnce(() => {
        throw new Error('git error');
      });

      // テスト対象の関数をインポート
      const { checkGitStatus } = await import('../../scripts/check-updates.js');
      const result = checkGitStatus();

      // 検証
      expect(result).toBe(false);
      expect(mockExecSync).toHaveBeenCalledWith(
        'git status --porcelain',
        expect.objectContaining({ cwd: expect.any(String) })
      );
    });
  });

  describe('checkSubmoduleUpdates', () => {
    it('should detect submodule updates', async () => {
      // モックの設定
      mockExecSync.mockReturnValueOnce(
        Buffer.from('+abcdef1234 submodule1\n+fedcba4321 submodule2')
      );

      // テスト対象の関数をインポート
      const { checkSubmoduleUpdates } = await import('../../scripts/check-updates.js');
      const updates = checkSubmoduleUpdates();

      // 検証
      expect(updates).toHaveLength(2);
      expect(updates).toContain('submodule1');
      expect(updates).toContain('submodule2');
      expect(mockExecSync).toHaveBeenCalledWith(
        'git submodule status',
        expect.objectContaining({ cwd: expect.any(String) })
      );
    });

    it('should handle no submodule updates', async () => {
      // モックの設定
      mockExecSync.mockReturnValueOnce(
        Buffer.from(' abcdef1234 submodule1\n abcdef1234 submodule2')
      );

      // テスト対象の関数をインポート
      const { checkSubmoduleUpdates } = await import('../../scripts/check-updates.js');
      const updates = checkSubmoduleUpdates();

      // 検証
      expect(updates).toHaveLength(0);
      expect(mockExecSync).toHaveBeenCalledWith(
        'git submodule status',
        expect.objectContaining({ cwd: expect.any(String) })
      );
    });
  });

  describe('checkNpmUpdates', () => {
    it('should detect npm updates', async () => {
      // モックの設定
      mockExecSync.mockReturnValueOnce(
        Buffer.from(JSON.stringify({
          'package1': {
            current: '1.0.0',
            wanted: '1.1.0',
            latest: '2.0.0'
          }
        }))
      );

      // テスト対象の関数をインポート
      const { checkNpmUpdates } = await import('../../scripts/check-updates.js');
      const updates = checkNpmUpdates();

      // 検証
      expect(updates).toHaveLength(1);
      expect(updates).toContain('package1');
      expect(mockExecSync).toHaveBeenCalledWith(
        'npm outdated --json',
        expect.objectContaining({ cwd: expect.any(String) })
      );
    });

    it('should handle no npm updates', async () => {
      // モックの設定
      mockExecSync.mockReturnValueOnce(Buffer.from('{}'));

      // テスト対象の関数をインポート
      const { checkNpmUpdates } = await import('../../scripts/check-updates.js');
      const updates = checkNpmUpdates();

      // 検証
      expect(updates).toHaveLength(0);
      expect(mockExecSync).toHaveBeenCalledWith(
        'npm outdated --json',
        expect.objectContaining({ cwd: expect.any(String) })
      );
    });

    it('should handle npm command errors', async () => {
      // モックの設定
      mockExecSync.mockImplementationOnce(() => {
        const error: any = new Error('npm error');
        error.stdout = Buffer.from('{}');
        throw error;
      });

      // テスト対象の関数をインポート
      const { checkNpmUpdates } = await import('../../scripts/check-updates.js');
      const updates = checkNpmUpdates();

      // 検証
      expect(updates).toHaveLength(0);
      expect(mockExecSync).toHaveBeenCalledWith(
        'npm outdated --json',
        expect.objectContaining({ cwd: expect.any(String) })
      );
    });
  });

  describe('generateReport', () => {
    it('should generate report with updates', async () => {
      const submoduleUpdates = ['submodule1', 'submodule2'];
      const npmUpdates = ['package1', 'package2'];

      // テスト対象の関数をインポート
      const { generateReport } = await import('../../scripts/check-updates.js');
      const report = generateReport(submoduleUpdates, npmUpdates);

      // 検証
      expect(report).toContain('サブモジュールの更新が利用可能');
      expect(report).toContain('submodule1');
      expect(report).toContain('submodule2');
      expect(report).toContain('NPMパッケージの更新が利用可能');
      expect(report).toContain('package1');
      expect(report).toContain('package2');
    });

    it('should generate report with no updates', async () => {
      const submoduleUpdates: string[] = [];
      const npmUpdates: string[] = [];

      // テスト対象の関数をインポート
      const { generateReport } = await import('../../scripts/check-updates.js');
      const report = generateReport(submoduleUpdates, npmUpdates);

      // 検証
      expect(report).toContain('すべてのコンポーネントが最新です');
    });
  });
});