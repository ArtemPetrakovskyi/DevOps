param([Parameter(Mandatory = $true)][string]$Version)
# Збирає образи обох сервісів із заданою версією та завантажує їх у minikube.
# Використання:  .\scripts\build-images.ps1 1.0.0
$ErrorActionPreference = "Stop"

docker build --build-arg APP_VERSION=$Version -t "tasks-api:$Version" ./api
docker build --build-arg APP_VERSION=$Version -t "tasks-web:$Version" ./web

minikube image load "tasks-api:$Version"
minikube image load "tasks-web:$Version"

Write-Host "Готово: tasks-api:$Version та tasks-web:$Version завантажені в minikube."
