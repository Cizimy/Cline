export class ValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ValidationError';
    Object.setPrototypeOf(this, ValidationError.prototype);
  }
}

export function validateString(value: unknown, fieldName: string): string {
  if (typeof value !== 'string') {
    throw new ValidationError(
      `${fieldName} must be a string, got ${typeof value}`
    );
  }
  return value;
}

export function validateNumber(value: unknown, fieldName: string): number {
  if (typeof value !== 'number' || isNaN(value)) {
    throw new ValidationError(
      `${fieldName} must be a number, got ${typeof value}`
    );
  }
  return value;
}

export function validateBoolean(value: unknown, fieldName: string): boolean {
  if (typeof value !== 'boolean') {
    throw new ValidationError(
      `${fieldName} must be a boolean, got ${typeof value}`
    );
  }
  return value;
}

export function validateArray<T>(
  value: unknown,
  fieldName: string,
  elementValidator: (element: unknown, index: number) => T
): T[] {
  if (!Array.isArray(value)) {
    throw new ValidationError(
      `${fieldName} must be an array, got ${typeof value}`
    );
  }
  return value.map((element, index) => elementValidator(element, index));
}

export function validateObject<T extends object>(
  value: unknown,
  fieldName: string,
  validator: (obj: unknown) => T
): T {
  if (typeof value !== 'object' || value === null) {
    throw new ValidationError(
      `${fieldName} must be an object, got ${typeof value}`
    );
  }
  return validator(value);
}

export function validateEnumValue<T extends string>(
  value: unknown,
  fieldName: string,
  enumValues: readonly T[]
): T {
  const strValue = validateString(value, fieldName);
  if (!enumValues.includes(strValue as T)) {
    throw new ValidationError(
      `${fieldName} must be one of [${enumValues.join(', ')}], got ${strValue}`
    );
  }
  return strValue as T;
}

export interface ProcessEnv {
  [key: string]: string | undefined;
}

export function validateEnvironmentVariable(
  name: string,
  env: ProcessEnv = process.env
): string {
  const value = env[name];
  if (value === undefined) {
    throw new ValidationError(`Missing required environment variable: ${name}`);
  }
  return value;
}
