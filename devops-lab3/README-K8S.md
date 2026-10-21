# Лабораторна №3 — Розгортання застосунку в Kubernetes (minikube)

Той самий проєкт «Менеджер задач»: `web` (інтерфейс) → `api` (REST) → `db` (PostgreSQL).
Усі маніфести — в каталозі `k8s/`, по одному файлу на об'єкт, namespace — `task-manager`.

| Файл | Об'єкт | Призначення |
|---|---|---|
| `00-namespace.yaml` | Namespace `task-manager` | окремий простір імен проєкту |
| `01-configmap.yaml` | ConfigMap `tasks-config` | несекретні параметри |
| `02-secret.yaml` | Secret `tasks-secret` | пароль БД та рядок підключення |
| `03-pvc-db.yaml` | PersistentVolumeClaim `db-data` | 1 ГБ для PostgreSQL |
| `04-deployment-db.yaml` | Deployment `db` | PostgreSQL, 1 репліка, Recreate |
| `05-service-db.yaml` | Service `db` (ClusterIP) | `db:5432` усередині кластера |
| `06-deployment-api.yaml` | Deployment `api` | 2 репліки, проби, requests/limits |
| `07-service-api.yaml` | Service `api` (ClusterIP) | `api:5000` усередині кластера |
| `08-deployment-web.yaml` | Deployment `web` | 2 репліки, RollingUpdate без простою |
| `09-service-web.yaml` | Service `web` (NodePort 30080) | доступ усередині кластера й з хоста |
| `10-ingress.yaml` | Ingress `web` | доступ через ingress-nginx |

## Параметри конфігурації

**ConfigMap `tasks-config`** (змінні оточення контейнерів):

| Ключ | Значення | Хто використовує | Призначення |
|---|---|---|---|
| `APP_TITLE` | `Менеджер задач (Kubernetes)` | web | заголовок сторінки |
| `API_URL` | `http://api:5000` | web | адреса API (DNS-ім'я Service) |
| `LOG_LEVEL` | `INFO` | web, api | рівень логування (`DEBUG`, `INFO`, `WARNING`) |
| `POSTGRES_DB` | `tasks` | db | назва бази даних |
| `POSTGRES_USER` | `tasks` | db | користувач бази даних |

**Secret `tasks-secret`** (навчальні значення, не реальні паролі):

| Ключ | Значення | Хто використовує | Призначення |
|---|---|---|---|
| `POSTGRES_PASSWORD` | `lab-only-password` | db | пароль користувача БД |
| `DATABASE_URL` | `postgresql://tasks:lab-only-password@db:5432/tasks` | api | рядок підключення до БД |

> Змінили пароль — змініть його в обох ключах Secret. Після зміни ConfigMap/Secret перезапустіть поди:
> `kubectl rollout restart deployment/web deployment/api -n task-manager`.

---

## 0. Встановлення інструментів

Потрібні: **Docker** (Docker Desktop або Engine), **kubectl**, **minikube**. Перевірка:
```bash
docker --version
kubectl version --client
minikube version
```

**Windows (PowerShell від адміністратора):**
```powershell
winget install Kubernetes.kubectl
winget install Kubernetes.minikube
# або через Chocolatey:  choco install kubernetes-cli minikube
```
Після встановлення закрийте й знову відкрийте термінал (PyCharm теж перезапустіть).

**macOS:** `brew install kubectl minikube`

**Linux:**
```bash
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
sudo snap install kubectl --classic        # або інструкція на kubernetes.io/docs/tasks/tools
```

Усі команди нижче виконуються з кореня проєкту (папка, де лежать `k8s/`, `api/`, `web/`). У PyCharm: **View → Tool Windows → Terminal**.

## 1. Підготовка образів (дві версії, без тегу latest)

Версія зашивається в образ через `--build-arg APP_VERSION` і відображається на сторінці (бейдж `v1.0.0`) та в `/info`.
Образи завантажуємо безпосередньо в minikube (реєстр не потрібен).

**Спочатку запустіть кластер (крок 2), потім:**

Linux / macOS / Git Bash:
```bash
./scripts/build-images.sh 1.0.0
./scripts/build-images.sh 1.1.0
```
Windows PowerShell:
```powershell
.\scripts\build-images.ps1 1.0.0
.\scripts\build-images.ps1 1.1.0
```
(Якщо PowerShell забороняє скрипти: `Set-ExecutionPolicy -Scope Process Bypass`.)

Скрипти виконують те саме, що й ці команди:
```bash
docker build --build-arg APP_VERSION=1.0.0 -t tasks-api:1.0.0 ./api
docker build --build-arg APP_VERSION=1.0.0 -t tasks-web:1.0.0 ./web
minikube image load tasks-api:1.0.0
minikube image load tasks-web:1.0.0
# те саме для 1.1.0
```
Перевірка: `minikube image ls | grep tasks` (PowerShell: `minikube image ls | Select-String tasks`) — мають бути чотири образи.

> Для більшої наочності перед збіркою 1.1.0 можна внести будь-яку видиму зміну в код web (наприклад, колір кнопки в `web/templates/index.html`). Це необов'язково: версія все одно відрізняється.

**Варіант із реєстром (GHCR/Docker Hub) замість `minikube image load`:**
```bash
docker login ghcr.io -u <логін>
docker tag tasks-web:1.0.0 ghcr.io/<owner>/<repo>-web:1.0.0 && docker push ghcr.io/<owner>/<repo>-web:1.0.0
# аналогічно для api та версії 1.1.0, потім замініть image: у k8s/06-*.yaml і k8s/08-*.yaml
```

## 2. Кластер minikube

```bash
minikube start --driver=docker
kubectl get nodes                      # вузол minikube має бути Ready
kubectl get pods -n kube-system        # системні поди мають бути Running
minikube addons enable metrics-server
minikube addons enable ingress
kubectl get pods -n ingress-nginx      # ingress-nginx-controller має стати Running (1–2 хв)
kubectl top nodes                      # метрики з'являються приблизно через хвилину
```

## 3. Namespace

Namespace створюється першим файлом `k8s/00-namespace.yaml` разом з усім іншим (див. крок 4). Окремо:
```bash
kubectl apply -f k8s/00-namespace.yaml
kubectl get namespace task-manager
```
Усі подальші команди містять `-n task-manager`.

## 4. Розгортання однією командою

```bash
kubectl apply -f k8s/
```
Перелік об'єктів:
```bash
kubectl get pods,deployments,replicasets,services -n task-manager
kubectl get all,pvc,configmap,secret,ingress -n task-manager
kubectl rollout status deployment/web -n task-manager
```
Відкрити в браузері (відкриється сам):
```bash
minikube service web -n task-manager
```
> На Windows/macOS із драйвером docker ця команда **не завершується** — вона тримає тунель; не закривайте цей термінал. Для всіх наступних команд відкривайте новий термінал. Лише URL: `minikube service web -n task-manager --url`.

Через Ingress (необов'язково): Linux — `http://$(minikube ip)`; Windows/macOS — в окремому терміналі `minikube tunnel` (лишити відкритим), потім `http://127.0.0.1`.

Додайте кілька задач, щоб у БД були дані.

### Перевірка, що ConfigMap і Secret потрапили в контейнер
```bash
kubectl exec -n task-manager deploy/web -- env | grep -E "APP_TITLE|API_URL|LOG_LEVEL"
kubectl exec -n task-manager deploy/api -- printenv DATABASE_URL
kubectl exec -n task-manager deploy/db  -- printenv POSTGRES_PASSWORD
```
PowerShell: замість `grep -E "A|B"` — `| Select-String "A|B"`.

Додатково:
```bash
kubectl describe configmap tasks-config -n task-manager
kubectl get secret tasks-secret -n task-manager -o yaml          # значення у base64
# декодування (Linux/macOS/Git Bash):
kubectl get secret tasks-secret -n task-manager -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d
# PowerShell:
[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String((kubectl get secret tasks-secret -n task-manager -o jsonpath='{.data.POSTGRES_PASSWORD}')))
kubectl exec -n task-manager deploy/db -- psql -U tasks -d tasks -c "SELECT * FROM task;"
```
Заголовок на сторінці має збігатися з `APP_TITLE`.

Метрики (metrics-server): `kubectl top pods -n task-manager`.

## 5. Керування життєвим циклом

### 5.1 Самовідновлення
```bash
kubectl get pods -n task-manager -l app=web
kubectl delete pod <ім'я-одного-пода-web> -n task-manager
kubectl get pods -n task-manager -l app=web -w      # з'являється новий под, Ctrl+C для виходу
```

### 5.2 Масштабування та розподіл трафіку
```bash
kubectl scale deployment/web --replicas=4 -n task-manager
kubectl get pods -n task-manager -l app=web -o wide
```
Розподіл запитів між подами (поле `pod` у відповіді змінюється). Незалежний від ОС спосіб — запити зсередини кластера через ClusterIP Service:
```bash
kubectl run curl-test -n task-manager --rm -it --restart=Never --image=curlimages/curl --command -- sh -c "for i in 1 2 3 4 5 6 7 8 9 10; do curl -s http://web/info; echo; done"
```
Або із хоста через NodePort-URL (`URL` — з `minikube service web -n task-manager --url`):
```bash
for i in $(seq 1 12); do curl -s $URL/info; echo; done
```
PowerShell: `1..12 | ForEach-Object { (Invoke-WebRequest "$URL/info" -UseBasicParsing).Content }`

Повернути 2 репліки: `kubectl scale deployment/web --replicas=2 -n task-manager`.

### 5.3 Rolling update 1.0.0 → 1.1.0 (із перевіркою доступності)
Потрібно 3 термінали.

**Термінал A** — спостереження за подами:
```bash
kubectl get pods -n task-manager -l app=web -w
```
**Термінал B** — постійне опитування застосунку (URL з `minikube service ... --url`):
```bash
./scripts/watch-availability.sh <URL>            # PowerShell: .\scripts\watch-availability.ps1 <URL>
```
**Термінал C** — оновлення:
```bash
kubectl annotate deployment/web -n task-manager kubernetes.io/change-cause="Initial deploy 1.0.0" --overwrite
kubectl set image deployment/web web=tasks-web:1.1.0 -n task-manager
kubectl annotate deployment/web -n task-manager kubernetes.io/change-cause="Update web to 1.1.0" --overwrite
kubectl rollout status deployment/web -n task-manager
```
Результат: у терміналі A старі поди замінюються новими по одному, у B увесь час `[HTTP 200]`, а версія змінюється з `1.0.0` на `1.1.0`. Оновіть сторінку в браузері — бейдж `v1.1.0`. Таким самим способом можна оновити `api`:
`kubectl set image deployment/api api=tasks-api:1.1.0 -n task-manager`.

> Чому без простою: `maxUnavailable: 0`, `maxSurge: 1`, readiness-проба та `preStop sleep 5`.

### 5.4 Історія та відкат
```bash
kubectl rollout history deployment/web -n task-manager
kubectl rollout history deployment/web -n task-manager --revision=2
kubectl rollout undo deployment/web -n task-manager            # або --to-revision=1
kubectl rollout status deployment/web -n task-manager
kubectl describe deployment web -n task-manager | grep Image   # PowerShell: | Select-String Image
```
Після відкату на сторінці знову `v1.0.0`.

## 6. Діагностика

**а) Неіснуючий тег:**
```bash
kubectl set image deployment/web web=tasks-web:9.9.9 -n task-manager
kubectl get pods -n task-manager -l app=web
```
Новий под отримає статус `ErrImagePull`, потім `ImagePullBackOff`, а старі поди залишаються `Running` (застосунок доступний — rolling update не завершується).

**б) Причина — опис пода та події:**
```bash
kubectl describe pod <ім'я-пода-з-ImagePullBackOff> -n task-manager     # розділ Events внизу
kubectl get events -n task-manager --sort-by=.lastTimestamp
```
У Events: `Failed to pull image "tasks-web:9.9.9": ... pull access denied, repository does not exist`.

**в) Логи та вхід у контейнер** (по справному поду):
```bash
kubectl logs <ім'я-пода-web> -n task-manager
kubectl logs deploy/api -n task-manager
kubectl logs -f deploy/api -n task-manager          # Ctrl+C для виходу
kubectl exec -it <ім'я-пода-web> -n task-manager -- sh
# усередині контейнера:
env | grep APP_
whoami
python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:5000/info').read().decode())"
exit
```
(у slim-образі немає `curl`, тому використано Python.)

**г) Виправлення:**
```bash
kubectl set image deployment/web web=tasks-web:1.1.0 -n task-manager
# або повернутись до попередньої ревізії:  kubectl rollout undo deployment/web -n task-manager
kubectl rollout status deployment/web -n task-manager
kubectl get pods -n task-manager
```

## 7. Очищення
```bash
kubectl delete -f k8s/          # видаляє все (PVC теж — дані БД зникнуть)
minikube stop                   # зупинити кластер
minikube delete                 # видалити кластер повністю
```
Перевірка «з нуля на чистому кластері»: `minikube delete` → `minikube start --driver=docker` → увімкнути addons → завантажити образи (крок 1) → `kubectl apply -f k8s/`.

## 8. Git
```bash
git checkout -b lab3-kubernetes
git add .
git commit -m "Lab 3: Kubernetes manifests (k8s/)"
git push -u origin lab3-kubernetes
```
(Якщо в репозиторії увімкнено захист `main` з лаб. №2 — створіть Pull Request і дочекайтесь зелених перевірок.)

## Часті проблеми

| Симптом | Причина / рішення |
|---|---|
| `ErrImagePull` / `ImagePullBackOff` для 1.0.0 | образи не завантажені в minikube → `./scripts/build-images.sh 1.0.0`, перевірка `minikube image ls` |
| Под `db` у стані `Pending` | PVC не створився → `kubectl describe pvc db-data -n task-manager`; перевірте, що minikube запущений |
| Под `api` перезапускається першою хвилиною | БД ще стартує; `api` повторює підключення — зачекайте 30–60 с |
| `minikube start` падає | Docker не запущений → запустіть Docker Desktop |
| Сторінка недоступна на Windows/macOS | використовуйте `minikube service web -n task-manager`, термінал із тунелем не закривайте |
| `kubectl top` порожній | metrics-server потребує ~1 хв: `kubectl get pods -n kube-system` |
