#!/usr/bin/env bash
# Збирає образи обох сервісів із заданою версією та завантажує їх у minikube.
# Використання:  ./scripts/build-images.sh 1.0.0
set -euo pipefail

VERSION="${1:?Вкажіть версію, наприклад 1.0.0}"

docker build --build-arg APP_VERSION="${VERSION}" -t "tasks-api:${VERSION}" ./api
docker build --build-arg APP_VERSION="${VERSION}" -t "tasks-web:${VERSION}" ./web

minikube image load "tasks-api:${VERSION}"
minikube image load "tasks-web:${VERSION}"

echo "Готово: tasks-api:${VERSION} та tasks-web:${VERSION} завантажені в minikube."
