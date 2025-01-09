import { SpyInstance } from 'jest-mock';

declare global {
  namespace NodeJS {
    interface Global {
      __mocks__: Mocks;
    }
  }

  interface Mocks {
    processExit: SpyInstance;
    stdout: SpyInstance;
    stderr: SpyInstance;
    consoleError: SpyInstance;
  }

  var __mocks__: Mocks;
}

export {};
