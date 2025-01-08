import { jest } from '@jest/globals';

// グローバルなモックの設定
const mockExecSync = jest.fn();
const mockReadFileSync = jest.fn();
const mockJoin = jest.fn((...args) => args.join('/'));
const mockDirname = jest.fn(() => '/mock/dir');
const mockFileURLToPath = jest.fn(() => '/mock/path');

jest.mock('child_process', () => ({
  execSync: mockExecSync
}));

jest.mock('fs', () => ({
  readFileSync: mockReadFileSync
}));

jest.mock('path', () => ({
  join: mockJoin,
  dirname: mockDirname
}));

jest.mock('url', () => ({
  fileURLToPath: mockFileURLToPath
}));

// モックをエクスポート
export {
  mockExecSync,
  mockReadFileSync,
  mockJoin,
  mockDirname,
  mockFileURLToPath
};