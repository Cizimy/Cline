export interface SystemRequirement {
  name: string;
  minVersion: string;
  command: string;
  versionFlag: string;
}

export interface MCPServerRequirement {
  name: string;
  runtime: string;
  minVersion: string;
  requiredEnvVars: string[];
}

export interface EnvironmentCheckResult {
  success: boolean;
  details: {
    systemRequirements: {
      name: string;
      satisfied: boolean;
      currentVersion?: string;
      requiredVersion: string;
      error?: string;
    }[];
    mcpServerCompatibility: {
      name: string;
      compatible: boolean;
      details: string;
    }[];
    environmentVariables: {
      name: string;
      exists: boolean;
      error?: string;
    }[];
  };
}

export interface MCPServerConfig {
  command: string;
  args: string[];
  env: Record<string, string>;
  disabled: boolean;
  alwaysAllow: string[];
}