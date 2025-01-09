import { jest, expect } from '@jest/globals';
import type { UpdateInfo } from '../../scripts/check-updates';

// Mock child_process module
const mockExecSync = jest.fn();
jest.unstable_mockModule('child_process', () => ({
  execSync: mockExecSync,
}));

// Import after mocking
const {
  checkGitStatus,
  checkSubmoduleUpdates,
  checkNpmUpdates,
  generateReport,
  main,
  UpdateError,
} = await import('../../scripts/check-updates.js');

describe('check-updates script', () => {
  describe('UpdateError', () => {
    it('should create error with valid code', () => {
      const error = new UpdateError('test error', 1);
      expect(error).toBeInstanceOf(Error);
      expect(error).toBeInstanceOf(UpdateError);
      expect(error.name).toBe('UpdateError');
      expect(error.message).toBe('test error');
      expect(error.code).toBe(1);
    });

    it('should throw on invalid code', () => {
      expect(() => new UpdateError('test error', -1)).toThrow(
        'UpdateError code must be a non-negative integer'
      );
      expect(() => new UpdateError('test error', 1.5)).toThrow(
        'UpdateError code must be a non-negative integer'
      );
    });

    it('should format error message correctly', () => {
      const error = new UpdateError('test error', 1);
      expect(error.toString()).toBe('UpdateError: test error (code: 1)');
    });
  });

  beforeEach(() => {
    jest.clearAllMocks();
    mockExecSync.mockReset();
  });

  describe('checkGitStatus', () => {
    it('should return true when working directory is clean', () => {
      mockExecSync.mockReturnValue(Buffer.from(''));
      const result = checkGitStatus();
      expect(result).toBe(true);
      expect(mockExecSync).toHaveBeenCalledWith('git status --porcelain');
    });

    it('should return false when there are uncommitted changes', () => {
      mockExecSync.mockReturnValue(Buffer.from(' M file.txt'));
      const result = checkGitStatus();
      expect(result).toBe(false);
      expect(mockExecSync).toHaveBeenCalledWith('git status --porcelain');
    });

    it('should throw error on git command failure', () => {
      mockExecSync.mockImplementation(() => {
        throw new Error('git error');
      });
      expect(() => checkGitStatus()).toThrow('git error');
      expect(mockExecSync).toHaveBeenCalledWith('git status --porcelain');
    });
  });

  describe('checkSubmoduleUpdates', () => {
    it('should detect submodule updates', () => {
      mockExecSync.mockReturnValue(
        Buffer.from(
          "Entering 'submodule1'\n123abc Some commit message\nEntering 'submodule2'\n456def Another commit"
        )
      );
      const updates = checkSubmoduleUpdates();
      expect(updates).toEqual([
        {
          type: 'submodule',
          name: 'submodule1',
          currentVersion: 'current',
          availableVersion: 'latest',
        },
        {
          type: 'submodule',
          name: 'submodule2',
          currentVersion: 'current',
          availableVersion: 'latest',
        },
      ]);
      expect(mockExecSync).toHaveBeenCalledWith(
        'git submodule foreach git log --oneline HEAD..origin/HEAD'
      );
    });

    it('should handle no submodule updates', () => {
      mockExecSync.mockReturnValue(Buffer.from(''));
      const updates = checkSubmoduleUpdates();
      expect(updates).toEqual([]);
      expect(mockExecSync).toHaveBeenCalledWith(
        'git submodule foreach git log --oneline HEAD..origin/HEAD'
      );
    });

    it('should handle submodule command errors', () => {
      mockExecSync.mockImplementation(() => {
        throw new Error('submodule error');
      });
      const updates = checkSubmoduleUpdates();
      expect(updates).toEqual([]);
      expect(mockExecSync).toHaveBeenCalledWith(
        'git submodule foreach git log --oneline HEAD..origin/HEAD'
      );
      expect(global.__mocks__.consoleError).toHaveBeenCalledWith(
        'Submodule check failed:',
        'submodule error'
      );
    });
  });

  describe('checkNpmUpdates', () => {
    it('should detect npm updates', () => {
      mockExecSync.mockReturnValue(
        Buffer.from(
          JSON.stringify({
            package1: {
              current: '1.0.0',
              latest: '2.0.0',
            },
            package2: {
              current: '3.0.0',
              latest: '3.1.0',
            },
          })
        )
      );
      const updates = checkNpmUpdates();
      expect(updates).toEqual([
        {
          type: 'npm',
          name: 'package1',
          currentVersion: '1.0.0',
          availableVersion: '2.0.0',
        },
        {
          type: 'npm',
          name: 'package2',
          currentVersion: '3.0.0',
          availableVersion: '3.1.0',
        },
      ]);
      expect(mockExecSync).toHaveBeenCalledWith('npm outdated --json');
    });

    it('should handle no npm updates', () => {
      mockExecSync.mockImplementation(() => {
        const error = new Error('No outdated packages');
        error.message = 'No outdated packages';
        throw error;
      });
      const updates = checkNpmUpdates();
      expect(updates).toEqual([]);
      expect(mockExecSync).toHaveBeenCalledWith('npm outdated --json');
    });

    it('should handle npm command errors with Error instance', () => {
      mockExecSync.mockImplementation(() => {
        throw new Error('npm error');
      });
      const updates = checkNpmUpdates();
      expect(updates).toEqual([]);
      expect(mockExecSync).toHaveBeenCalledWith('npm outdated --json');
      expect(global.__mocks__.consoleError).toHaveBeenCalledWith(
        'NPM update check failed:',
        'npm error'
      );
    });

    it('should handle npm command errors with non-Error object', () => {
      mockExecSync.mockImplementation(() => {
        throw 'npm error string'; // 文字列として投げる
      });
      const updates = checkNpmUpdates();
      expect(updates).toEqual([]);
      expect(mockExecSync).toHaveBeenCalledWith('npm outdated --json');
      expect(global.__mocks__.consoleError).toHaveBeenCalledWith(
        'NPM update check failed:',
        'npm error string'
      );
    });

    it('should handle invalid JSON output', () => {
      mockExecSync.mockReturnValue(Buffer.from('invalid json'));
      const updates = checkNpmUpdates();
      expect(updates).toEqual([]);
      expect(mockExecSync).toHaveBeenCalledWith('npm outdated --json');
      expect(global.__mocks__.consoleError).toHaveBeenCalledWith(
        'NPM update check failed:',
        expect.stringContaining('Unexpected token')
      );
    });

    it('should handle missing version information', () => {
      mockExecSync.mockReturnValue(
        Buffer.from(
          JSON.stringify({
            package1: {
              // missing current version
              latest: '2.0.0',
            },
            package2: {
              current: '1.0.0',
              // missing latest version
            },
          })
        )
      );
      const updates = checkNpmUpdates();
      expect(updates).toEqual([]);
      expect(mockExecSync).toHaveBeenCalledWith('npm outdated --json');
    });
  });

  describe('generateReport', () => {
    it('should generate report with updates', () => {
      const updates: UpdateInfo[] = [
        {
          type: 'submodule',
          name: 'sub1',
          currentVersion: 'current',
          availableVersion: 'latest',
        },
        {
          type: 'npm',
          name: 'pkg1',
          currentVersion: '1.0.0',
          availableVersion: '2.0.0',
        },
      ];
      const report = generateReport(updates);
      expect(report).toContain('# Available Updates');
      expect(report).toContain('## Submodules');
      expect(report).toContain('## NPM Packages');
      expect(report).toContain('sub1: current -> latest');
      expect(report).toContain('pkg1: 1.0.0 -> 2.0.0');
    });

    it('should generate report with no updates', () => {
      const report = generateReport([]);
      expect(report).toBe('No updates available.');
    });
  });

  describe('main', () => {
    it('should throw UpdateError when working directory is not clean', () => {
      mockExecSync.mockReturnValueOnce(Buffer.from(' M file.txt')); // git status

      expect(() => main()).toThrow(UpdateError);
      expect(global.__mocks__.consoleError).toHaveBeenCalledWith(
        'Working directory is not clean. Please commit or stash changes first.'
      );
    });

    it('should throw UpdateError when updates are available', () => {
      // Mock clean git status
      mockExecSync.mockReturnValueOnce(Buffer.from(''));
      // Mock submodule updates
      mockExecSync.mockReturnValueOnce(Buffer.from("Entering 'sub1'\ncommit"));
      // Mock npm updates
      mockExecSync.mockReturnValueOnce(
        Buffer.from(
          JSON.stringify({
            package1: {
              current: '1.0.0',
              latest: '2.0.0',
            },
          })
        )
      );

      expect(() => main()).toThrow(UpdateError);

      const report = generateReport([
        {
          type: 'submodule',
          name: 'sub1',
          currentVersion: 'current',
          availableVersion: 'latest',
        },
        {
          type: 'npm',
          name: 'package1',
          currentVersion: '1.0.0',
          availableVersion: '2.0.0',
        },
      ]);
      expect(global.__mocks__.stdout).toHaveBeenCalledWith(report);
      expect(global.__mocks__.consoleError).toHaveBeenCalledWith(
        'Updates available. Run `npm run update` to apply them.'
      );
    });

    it('should handle unexpected errors', () => {
      mockExecSync.mockImplementationOnce(() => {
        throw new Error('Unexpected git error');
      });

      expect(() => main()).toThrow(UpdateError);
      expect(global.__mocks__.consoleError).toHaveBeenCalledWith(
        'Unexpected error: Unexpected git error'
      );
    });

    it('should complete successfully when no updates are available', () => {
      // Mock clean git status
      mockExecSync.mockReturnValueOnce(Buffer.from(''));
      // Mock no submodule updates
      mockExecSync.mockReturnValueOnce(Buffer.from(''));
      // Mock no npm updates
      mockExecSync.mockImplementationOnce(() => {
        throw new Error('No outdated packages');
      });

      main();
      expect(global.__mocks__.stdout).toHaveBeenCalledWith(
        'No updates available.'
      );
    });

    it('should handle non-UpdateError exceptions in outer catch block', () => {
      // Mock git status to throw a non-Error object
      mockExecSync.mockImplementationOnce(() => {
        const customError = {
          toString() {
            return 'Custom error object';
          },
        };
        throw customError;
      });

      expect(() => main()).toThrow(UpdateError);
      expect(global.__mocks__.consoleError).toHaveBeenCalledWith(
        'Unexpected error: Custom error object'
      );
    });
  });
});
