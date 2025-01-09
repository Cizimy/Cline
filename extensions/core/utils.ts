import { ValidationError } from './validation.js';

export interface ProcessEnv {
  [key: string]: string | undefined;
}

export interface PerformanceMetrics {
  startTime: number;
  endTime: number;
  duration: number;
  label?: string;
}

export type JsonPrimitive = string | number | boolean | null;
export type JsonArray = JsonValue[];
export type JsonObject = { [key: string]: JsonValue };
export type JsonValue = JsonPrimitive | JsonObject | JsonArray;

export function validateEnvironmentVariables(
  required: string[],
  env: ProcessEnv = process.env
): void {
  const missing = required.filter(name => !env[name]);
  if (missing.length > 0) {
    throw new ValidationError(
      `Missing required environment variables: ${missing.join(', ')}`
    );
  }
}

export function parseJson<T extends JsonValue>(input: string): T {
  try {
    return JSON.parse(input) as T;
  } catch (error) {
    throw new ValidationError(
      `Invalid JSON: ${error instanceof Error ? error.message : String(error)}`
    );
  }
}

export function stringifyJson(value: JsonValue): string {
  try {
    return JSON.stringify(value, null, 2);
  } catch (error) {
    throw new ValidationError(
      `Failed to stringify JSON: ${
        error instanceof Error ? error.message : String(error)
      }`
    );
  }
}

export function measurePerformance<T>(
  operation: () => T,
  label?: string
): [T, PerformanceMetrics] {
  const startTime = performance.now();
  const result = operation();
  const endTime = performance.now();
  const duration = endTime - startTime;

  return [
    result,
    {
      startTime,
      endTime,
      duration,
      label,
    },
  ];
}

export function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export function retryWithBackoff<T>(
  operation: () => Promise<T>,
  options: {
    maxAttempts?: number;
    initialDelay?: number;
    maxDelay?: number;
    backoffFactor?: number;
  } = {}
): Promise<T> {
  const {
    maxAttempts = 3,
    initialDelay = 1000,
    maxDelay = 10000,
    backoffFactor = 2,
  } = options;

  return new Promise((resolve, reject) => {
    let attempts = 0;
    let currentDelay = initialDelay;

    const attempt = async (): Promise<void> => {
      try {
        const result = await operation();
        resolve(result);
      } catch (error) {
        attempts++;
        if (attempts >= maxAttempts) {
          reject(error);
          return;
        }

        currentDelay = Math.min(currentDelay * backoffFactor, maxDelay);
        await delay(currentDelay);
        attempt();
      }
    };

    attempt();
  });
}
