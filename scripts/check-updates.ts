import { execSync } from 'child_process';

export type UpdateType = 'submodule' | 'npm';

export interface UpdateInfo {
  type: UpdateType;
  name: string;
  currentVersion: string;
  availableVersion: string;
}

export interface NpmPackageInfo {
  current: string;
  latest: string;
  [key: string]: unknown;
}

interface NpmOutdatedResult {
  [key: string]: NpmPackageInfo;
}

export class UpdateError extends Error {
  constructor(
    message: string,
    public readonly code: number
  ) {
    if (!Number.isInteger(code) || code < 0) {
      throw new Error('UpdateError code must be a non-negative integer');
    }
    super(message);
    this.name = 'UpdateError';
    // Ensure proper prototype chain for instanceof checks
    Object.setPrototypeOf(this, UpdateError.prototype);
  }

  override toString(): string {
    return `${this.name}: ${this.message} (code: ${this.code})`;
  }
}

export function checkGitStatus(): boolean {
  const status = execSync('git status --porcelain').toString();
  return status.length === 0;
}

export function checkSubmoduleUpdates(): UpdateInfo[] {
  try {
    const output = execSync(
      'git submodule foreach git log --oneline HEAD..origin/HEAD'
    ).toString();
    const updates: UpdateInfo[] = [];

    output.split('\n').forEach(line => {
      if (line.startsWith('Entering')) {
        const match = line.match(/["'](.+)["']$/);
        const submoduleName = match?.[1];
        if (submoduleName) {
          updates.push({
            type: 'submodule',
            name: submoduleName,
            currentVersion: 'current',
            availableVersion: 'latest',
          });
        }
      }
    });

    return updates;
  } catch (error) {
    console.error(
      'Submodule check failed:',
      error instanceof Error ? error.message : String(error)
    );
    return [];
  }
}

export function checkNpmUpdates(): UpdateInfo[] {
  try {
    const output = execSync('npm outdated --json').toString();
    const outdated = JSON.parse(output) as NpmOutdatedResult;

    return Object.entries(outdated)
      .filter(([_, info]) => info.current && info.latest) // バージョン情報が完全な場合のみ処理
      .map(([name, info]) => ({
        type: 'npm' as const,
        name,
        currentVersion: info.current,
        availableVersion: info.latest,
      }));
  } catch (error) {
    if (error instanceof Error) {
      if (error.message.includes('No outdated packages')) {
        return [];
      }
      // JSON.parseエラーを含む他のエラーをログ
      console.error('NPM update check failed:', error.message);
    } else {
      console.error('NPM update check failed:', String(error));
    }
    return [];
  }
}

export function generateReport(updates: UpdateInfo[]): string {
  if (updates.length === 0) {
    return 'No updates available.';
  }

  const sections = {
    submodule: [] as string[],
    npm: [] as string[],
  };

  updates.forEach(update => {
    sections[update.type].push(
      `- ${update.name}: ${update.currentVersion} -> ${update.availableVersion}`
    );
  });

  let report = '# Available Updates\n\n';

  if (sections['submodule'].length > 0) {
    report += '## Submodules\n' + sections['submodule'].join('\n') + '\n\n';
  }

  if (sections['npm'].length > 0) {
    report += '## NPM Packages\n' + sections['npm'].join('\n') + '\n\n';
  }

  return report;
}

export function main(): void {
  try {
    let isClean: boolean;
    try {
      isClean = checkGitStatus();
    } catch (error) {
      const message = `Unexpected error: ${error instanceof Error ? error.message : String(error)}`;
      console.error(message);
      throw new UpdateError(message, 99);
    }

    if (!isClean) {
      const message =
        'Working directory is not clean. Please commit or stash changes first.';
      console.error(message);
      throw new UpdateError(message, 1);
    }

    const updates = [...checkSubmoduleUpdates(), ...checkNpmUpdates()];

    const report = generateReport(updates);
    process.stdout.write(report);

    if (updates.length > 0) {
      const message = 'Updates available. Run `npm run update` to apply them.';
      console.error(message);
      throw new UpdateError(message, 2);
    }
  } catch (error) {
    if (error instanceof UpdateError) {
      throw error;
    }
    // 予期しないエラーの場合
    const message = `Unexpected error: ${error instanceof Error ? error.message : String(error)}`;
    console.error(message);
    throw new UpdateError(message, 99);
  }
}
