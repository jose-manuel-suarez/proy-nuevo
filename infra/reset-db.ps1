# Reset only the local PostgreSQL volume and bring the development stack back.
$ErrorActionPreference = "Stop"

Set-Location (Split-Path $PSScriptRoot -Parent)

$compose = @("compose", "-f", "compose.yaml", "-f", "compose.dev.yaml")

docker @compose down
if (docker volume inspect proy-nuevo_postgres_data 2>$null) {
    docker volume rm proy-nuevo_postgres_data
}
docker @compose up -d --wait
