# SQLite MCPサーバーのDockerイメージをビルド

$ErrorActionPreference = "Stop"

# イメージ名とタグの設定
$IMAGE_NAME = "noah/sqlite-mcp"
$TAG = "latest"

# カレントディレクトリの取得と確認
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $SCRIPT_DIR

Write-Host "Building Docker image: $IMAGE_NAME`:$TAG"

# Dockerイメージのビルド
docker build -t "${IMAGE_NAME}:${TAG}" .

if ($LASTEXITCODE -eq 0) {
    Write-Host "Successfully built Docker image: $IMAGE_NAME`:$TAG"
} else {
    Write-Host "Failed to build Docker image"
    exit 1
}