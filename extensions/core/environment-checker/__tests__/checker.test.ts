import { EnvironmentChecker } from './checker';
import { MCPServerConfig } from './types';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

describe('EnvironmentChecker', () => {
  const mockMCPConfig: Record<string, MCPServerConfig> = {
    'test-server': {
      command: 'node',
      args: ['test.js'],
      env: {
        TEST_ENV: 'test'
      },
      disabled: false,
      alwaysAllow: []
    }
  };

  let checker: EnvironmentChecker;

  beforeEach(() => {
    checker = new EnvironmentChecker(mockMCPConfig);
    // 環境変数のモック
    process.env['CLINE_HOME'] = '/test/home';
    process.env['CLINE_CONFIG_PATH'] = '/test/config';
  });

  afterEach(() => {
    delete process.env['CLINE_HOME'];
    delete process.env['CLINE_CONFIG_PATH'];
  });

  it('should check system requirements correctly', async () => {
    const result = await checker.checkEnvironment();
    
    // Node.jsとnpmのバージョンチェック
    expect(result).toBeDefined();
    expect(result.details.systemRequirements).toBeDefined();
    expect(result.details.systemRequirements).toHaveLength(2);
    expect(result.details.systemRequirements[0]?.name).toBe('Node.js');
    expect(result.details.systemRequirements[1]?.name).toBe('npm');
  });

  it('should check environment variables', async () => {
    const result = await checker.checkEnvironment();
    
    expect(result.details.environmentVariables).toBeDefined();
    expect(result.details.environmentVariables).toHaveLength(2);
    const vars = result.details.environmentVariables;
    expect(vars[0]?.exists).toBe(true);
    expect(vars[1]?.exists).toBe(true);
  });

  it('should check MCP server compatibility', async () => {
    const result = await checker.checkEnvironment();
    
    expect(result.details.mcpServerCompatibility).toBeDefined();
    expect(result.details.mcpServerCompatibility).toHaveLength(1);
    const server = result.details.mcpServerCompatibility[0];
    expect(server?.name).toBe('test-server');
  });

  it('should fail when environment variables are missing', async () => {
    delete process.env['CLINE_HOME'];
    const result = await checker.checkEnvironment();
    
    expect(result.success).toBe(false);
    expect(result.details.environmentVariables).toBeDefined();
    expect(result.details.environmentVariables.some(v => !v.exists)).toBe(true);
  });
});