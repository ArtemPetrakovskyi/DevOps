#!/usr/bin/env bash
# Двічі на секунду опитує застосунок і друкує код відповіді, версію та ім'я пода.
# Запускайте в окремому терміналі під час rolling update.
# Використання:  ./scripts/watch-availability.sh http://127.0.0.1:PORT
URL="${1:?Вкажіть URL, наприклад: ./scripts/watch-availability.sh \$(minikube service web -n task-manager --url)}"

while true; do
  out="$(curl -s -m 2 -w ' [HTTP %{http_code}]' "${URL}/info" || true)"
  [ -z "$out" ] && out="[FAILED] немає відповіді"
  echo "$(date +%H:%M:%S) ${out}"
  sleep 0.5
done
