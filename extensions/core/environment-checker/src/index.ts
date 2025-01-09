import { EnvironmentChecker } from './checker';
import { EnvironmentCheckResult, MCPServerConfig } from './types';

export async function checkEnvironment(
  mcpServersConfig: Record<string, MCPServerConfig>
): Promise<EnvironmentCheckResult> {
  const checker = new EnvironmentChecker(mcpServersConfig);
  return checker.checkEnvironment();
}

export * from './types';