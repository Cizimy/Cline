import { checkEnvironment } from './index';
import * as fs from 'fs';
import * as path from 'path';

async function main(): Promise<void> {
  try {
    // MCPサーバー設定ファイルの読み込み
    const configPath = process.env['CLINE_CONFIG_PATH'];
    if (!configPath) {
      throw new Error('CLINE_CONFIG_PATH environment variable is not set');
    }

    const settingsPath = path.join(configPath, 'cline_mcp_settings.json');
    const settings = JSON.parse(fs.readFileSync(settingsPath, 'utf-8'));

    console.log('Checking environment compatibility...\n');

    // 環境チェックの実行
    const result = await checkEnvironment(settings.mcpServers);

    // 結果の表示
    console.log('Environment Check Results:');
    console.log('-------------------------\n');

    console.log('System Requirements:');
    result.details.systemRequirements.forEach(req => {
      console.log(`- ${req.name}: ${req.satisfied ? '✓' : '✗'} (${req.currentVersion || 'not found'}, required: ${req.requiredVersion})`);
      if (req.error) console.log(`  Error: ${req.error}`);
    });

    console.log('\nMCP Server Compatibility:');
    result.details.mcpServerCompatibility.forEach(server => {
      console.log(`- ${server.name}: ${server.compatible ? '✓' : '✗'}`);
      console.log(`  ${server.details}`);
    });

    console.log('\nEnvironment Variables:');
    result.details.environmentVariables.forEach(env => {
      console.log(`- ${env.name}: ${env.exists ? '✓' : '✗'}`);
      if (env.error) console.log(`  Error: ${env.error}`);
    });

    console.log('\nOverall Result:', result.success ? '✓ Compatible' : '✗ Incompatible');

    if (!result.success) {
      process.exit(1);
    }
  } catch (error) {
    console.error('Error during environment check:', error);
    process.exit(1);
  }
}

main().catch(console.error);