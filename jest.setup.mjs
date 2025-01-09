import { jest } from '@jest/globals';

// Mock process.stdout.write
const mockStdout = jest.fn().mockReturnValue(true);
const originalStdoutWrite = process.stdout.write;
process.stdout.write = function (text) {
  mockStdout(text);
  return true;
};

// Mock process.stderr.write
const mockStderr = jest.fn().mockReturnValue(true);
const originalStderrWrite = process.stderr.write;
process.stderr.write = function (text) {
  mockStderr(text);
  return true;
};

// Mock console.error
const mockConsoleError = jest.fn();
const originalConsoleError = console.error;
console.error = (...args) => {
  mockConsoleError(...args);
};

// Reset all mocks before each test
beforeEach(() => {
  jest.clearAllMocks();
  mockStdout.mockClear();
  mockStderr.mockClear();
  mockConsoleError.mockClear();
});

// Restore original functions after all tests
afterAll(() => {
  console.error = originalConsoleError;
  process.stdout.write = originalStdoutWrite;
  process.stderr.write = originalStderrWrite;
});

// Make mocks available globally
global.__mocks__ = {
  stdout: mockStdout,
  stderr: mockStderr,
  consoleError: mockConsoleError,
};
