# MCP設定ファイルを生成するスクリプト

$ErrorActionPreference = "Stop"

# 設定ファイルのパス
$ENV_FILE = "env.json"
$BASE_FILE = "base.json"
$DEV_FILE = "development.json"
$OUTPUT_FILE = "C:/Users/Kenichi/AppData/Roaming/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/cline_mcp_settings.json"

# カレントディレクトリの取得と確認
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $SCRIPT_DIR

# 環境変数の読み込みと解決
$envConfig = Get-Content $ENV_FILE | ConvertFrom-Json
$envVars = @{}
$envConfig.PSObject.Properties | ForEach-Object {
    $value = $_.Value
    # 環境変数の参照を解決
    if ($value -match '\${([^}]+)}') {
        $matches[1] | ForEach-Object {
            $value = $value.Replace("`${$_}", $envVars[$_])
        }
    }
    $envVars[$_.Name] = $value
}

# 基本設定の読み込み
$baseConfig = Get-Content $BASE_FILE | ConvertFrom-Json

# 開発環境設定の読み込み
$devConfig = Get-Content $DEV_FILE | ConvertFrom-Json

# 設定のマージと環境変数の解決
function Resolve-EnvVars {
    param (
        [Parameter(ValueFromPipeline=$true)]
        $object
    )
    
    $json = $object | ConvertTo-Json -Depth 100
    $envVars.Keys | ForEach-Object {
        $key = $_
        $value = $envVars[$key]
        $json = $json.Replace("`${$key}", $value)
    }
    return $json | ConvertFrom-Json
}

# 最終的な設定の生成
$finalConfig = $devConfig | Resolve-EnvVars

# 出力ディレクトリの作成（存在しない場合）
$outputDir = Split-Path -Parent $OUTPUT_FILE
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force
}

# 設定ファイルの出力
$finalConfig | ConvertTo-Json -Depth 100 | Set-Content $OUTPUT_FILE

Write-Host "Generated MCP settings file at: $OUTPUT_FILE"