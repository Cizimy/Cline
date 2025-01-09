import { exec } from 'child_process';
import { promisify } from 'util';
import {
  SystemRequirement,
  MCPServerRequirement,
  EnvironmentCheckResult,
  MCPServerConfig
} from './types';

const execAsync = promisify(exec);

export class EnvironmentChecker {
  private systemRequirements: SystemRequirement[] = [
    {
      name: 'Node.js',
      minVersion: '20.0.0',
      command: 'node',
      versionFlag: '--version'
    },
    {
      name: 'npm',
      minVersion: '10.0.0',
      command: 'npm',
      versionFlag: '--version'
    }
  ];

  constructor(private mcpServersConfig: Record<string, MCPServerConfig>) {}

  private async checkVersion(requirement: SystemRequirement): Promise<{
    satisfied: boolean;
    currentVersion?: string;
    error?: string;
  }> {
    try {
      const { stdout } = await execAsync(`${requirement.command} ${requirement.versionFlag}`);
      const version = stdout.trim().replace(/^v/, '');
      const satisfied = this.compareVersions(version, requirement.minVersion) >= 0;
      return { satisfied, currentVersion: version };
    } catch (error) {
      return {
        satisfied: false,
        error: `Failed to check ${requirement.name} version: ${(error as Error).message}`
      };
    }
  }

  private compareVersions(version1: string, version2: string): number {
    const v1Parts = version1.split('.').map(Number);
    const v2Parts = version2.split('.').map(Number);
    
    for (let i = 0; i < Math.max(v1Parts.length, v2Parts.length); i++) {
      const v1 = v1Parts[i] || 0;
      const v2 = v2Parts[i] || 0;
      if (v1 !== v2) return v1 - v2;
    }
    return 0;
  }

  private async checkMCPServerCompatibility(
    serverName: string,
    config: MCPServerConfig
  ): Promise<{
    compatible: boolean;
    details: string;
  }> {
    // コマンドの存在確認
    try {
      const command = config.command.split(' ')[0];
      await execAsync(`where ${command}`);
    } catch {
      return {
        compatible: false,
        details: `Command '${config.command}' not found in system PATH`
      };
    }

    // 必要な環境変数の確認
    const missingEnvVars = Object.keys(config.env).filter(key => !process.env[key]);
    if (missingEnvVars.length > 0) {
      return {
        compatible: false,
        details: `Missing required environment variables: ${missingEnvVars.join(', ')}`
      };
    }

    return {
      compatible: true,
      details: 'All compatibility checks passed'
    };
  }

  private checkEnvironmentVariables(): {
    name: string;
    exists: boolean;
    error?: string;
  }[] {
    const requiredVars = ['CLINE_HOME', 'CLINE_CONFIG_PATH'];
    return requiredVars.map(varName => ({
      name: varName,
      exists: !!process.env[varName],
      error: !process.env[varName] ? `Environment variable ${varName} is not set` : undefined
    }));
  }

  public async checkEnvironment(): Promise<EnvironmentCheckResult> {
    // システム要件のチェック
    const systemRequirementsResults = await Promise.all(
      this.systemRequirements.map(async req => ({
        name: req.name,
        requiredVersion: req.minVersion,
        ...(await this.checkVersion(req))
      }))
    );

    // MCPサーバーの互換性チェック
    const mcpServerResults = await Promise.all(
      Object.entries(this.mcpServersConfig).map(async ([name, config]) => ({
        name,
        ...(await this.checkMCPServerCompatibility(name, config))
      }))
    );

    // 環境変数のチェック
    const envVarResults = this.checkEnvironmentVariables();

    // 全体の結果を集約
    const success = systemRequirementsResults.every(r => r.satisfied) &&
      mcpServerResults.every(r => r.compatible) &&
      envVarResults.every(r => r.exists);

    return {
      success,
      details: {
        systemRequirements: systemRequirementsResults,
        mcpServerCompatibility: mcpServerResults,
        environmentVariables: envVarResults
      }
    };
  }
}