#!/usr/bin/env node

import { execSync } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.join(__dirname, '..');

export function checkGitStatus() {
  try {
    const status = execSync('git status --porcelain', { cwd: ROOT_DIR }).toString();
    return status.length === 0;
  } catch (error) {
    console.error('Git status check failed:', error.message);
    return false;
  }
}

export function checkSubmoduleUpdates() {
  try {
    const result = execSync('git submodule status', { cwd: ROOT_DIR }).toString();
    const updates = [];
    
    result.split('\n').forEach(line => {
      if (line.startsWith('+')) {
        const [, hash, path] = line.match(/^\+([a-f0-9]+)\s+(\S+)/) || [];
        if (hash && path) {
          updates.push(path);
        }
      }
    });
    
    return updates;
  } catch (error) {
    console.error('Submodule check failed:', error.message);
    return [];
  }
}

export function checkNpmUpdates() {
  try {
    const output = execSync('npm outdated --json', { cwd: ROOT_DIR }).toString();
    const outdated = JSON.parse(output);
    return Object.keys(outdated);
  } catch (error) {
    // npmがoutdatedを見つけた場合は終了コード1を返すため、エラーをパースする
    try {
      const outdated = JSON.parse(error.stdout.toString());
      return Object.keys(outdated);
    } catch {
      console.error('NPM outdated check failed:', error.message);
      return [];
    }
  }
}

export function generateReport(submoduleUpdates, npmUpdates) {
  const report = [];
  
  if (submoduleUpdates.length > 0) {
    report.push('## サブモジュールの更新が利用可能');
    report.push('以下のサブモジュールに更新があります：');
    submoduleUpdates.forEach(module => {
      report.push(`- ${module}`);
    });
    report.push('\n更新するには以下のコマンドを実行：\n```\nnpm run update:submodules\n```\n');
  }
  
  if (npmUpdates.length > 0) {
    report.push('## NPMパッケージの更新が利用可能');
    report.push('以下のパッケージに更新があります：');
    npmUpdates.forEach(pkg => {
      report.push(`- ${pkg}`);
    });
    report.push('\n更新するには以下のコマンドを実行：\n```\nnpm run update:deps\n```\n');
  }
  
  if (report.length === 0) {
    report.push('すべてのコンポーネントが最新です。更新は必要ありません。');
  }
  
  return report.join('\n');
}

// スクリプトが直接実行された場合のみメイン処理を実行
if (import.meta.url === `file://${process.argv[1]}`) {
  console.log('更新チェックを開始...\n');

  if (!checkGitStatus()) {
    console.error('警告: コミットされていない変更があります。先に変更を処理してください。');
    process.exit(1);
  }

  const submoduleUpdates = checkSubmoduleUpdates();
  const npmUpdates = checkNpmUpdates();

  const report = generateReport(submoduleUpdates, npmUpdates);
  console.log(report);

  // 更新が必要な場合は終了コード1を返す
  if (submoduleUpdates.length > 0 || npmUpdates.length > 0) {
    process.exit(1);
  }
}