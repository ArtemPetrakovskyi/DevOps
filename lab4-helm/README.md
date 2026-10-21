# DVO-L4-3C8B52
# Лабораторна робота №4 — Пакування застосунку в Helm-чарт

Helm-чарт `task-manager` описує той самий застосунок, що й лабораторна №3 («Менеджер задач»:
`web` + `api` + PostgreSQL) і створює той самий набір об'єктів: ConfigMap, Secret, PVC, 3 Deployment,
3 Service та (за бажанням) Ingress. Додатково — pre-upgrade хук і тест релізу (`helm test`, завдання 9б).

## Структура репозиторію

```
lab4-helm/
├── chart/task-manager/
│   ├── Chart.yaml            # name, description, version, appVersion
│   ├── values.yaml           # значення за замовчуванням = середовище розробки
│   ├── values-dev.yaml       # dev: 1 репліка, мінімум ресурсів, tag 1.0.0, Ingress вимкнено
│   ├── values-prod.yaml      # prod: 3 репліки, більше ресурсів, tag 1.1.0, Ingress увімкнено
│   └── templates/
│       ├── _helpers.tpl      # іменовані шаблони: fullname, labels, selectorLabels, annotations
│       ├── NOTES.txt         # підказка після встановлення
│       ├── configmap.yaml  secret.yaml  pvc-db.yaml
│       ├── deployment-{db,api,web}.yaml   service-{db,api,web}.yaml
│       ├── ingress.yaml
│       ├── hook-pre-upgrade.yaml          # хук pre-upgrade (Job)
│       └── tests/test-connection.yaml     # helm test
├── scripts/lab4.py           # запуск усіх кроків з PyCharm
├── scripts/check_requirements.py   # самоперевірка вимог
└── README.md
```

## version і appVersion

- `version` (0.1.0) — версія **самого чарта**: змінюється, коли змінюються шаблони, структура значень
  чи логіка пакування. Саме за нею Helm розрізняє пакунки чарта (`task-manager-0.1.0.tgz`).
- `appVersion` (1.0.0) — версія **застосунку**, який чарт розгортає (теги образів `tasks-api` / `tasks-web`).
  Змінюється, коли виходить нова версія коду застосунку. Чарт можна оновлювати (0.1.0 → 0.1.1), не чіпаючи
  застосунок, і навпаки.

## Параметри values

| Параметр | Опис | За замовчуванням |
|---|---|---|
| `nameOverride`, `fullnameOverride` | Перевизначення імені чарта / повного імені об'єктів | `""` |
| `mascot.label` | Значення мітки `mascot` (маркування кафедри, ASCII) | `harbuz` |
| `config.appTitle` | Заголовок веб-інтерфейсу (`APP_TITLE`) | `Менеджер задач (Kubernetes)` |
| `config.logLevel` | Рівень логування (`LOG_LEVEL`) | `INFO` |
| `config.postgresDb` / `config.postgresUser` | Назва БД / користувач | `tasks` / `tasks` |
| `secret.postgresPassword` | Пароль БД. Порожньо = генерується автоматично й зберігається при оновленнях | `""` |
| `api.replicaCount` / `web.replicaCount` | Кількість реплік | `2` / `2` |
| `api.image.repository` / `.tag` / `.pullPolicy` | Образ API | `tasks-api` / `1.0.0` / `IfNotPresent` |
| `web.image.repository` / `.tag` / `.pullPolicy` | Образ web | `tasks-web` / `1.0.0` / `IfNotPresent` |
| `api.containerPort`, `web.containerPort` | Порт контейнера | `5000` |
| `api.service.type` / `.port` | Тип і порт Service api | `ClusterIP` / `5000` |
| `web.service.type` / `.port` / `.nodePort` | Тип, порт і nodePort Service web (`null` = автоматично) | `NodePort` / `80` / `null` |
| `api.resources`, `web.resources`, `db.resources` | requests/limits | див. `values.yaml` |
| `db.replicaCount` | Кількість реплік БД (лише 1) | `1` |
| `db.image.*` | Образ PostgreSQL | `postgres` / `16-alpine` |
| `db.persistence.enabled` | Створювати PVC (інакше `emptyDir`) | `true` |
| `db.persistence.size` / `.storageClass` | Розмір і клас сховища | `1Gi` / `""` |
| `ingress.enabled` | Створювати Ingress | `false` |
| `ingress.className` / `.host` / `.path` | Параметри Ingress | `nginx` / `""` / `/` |
| `hooks.preUpgrade.enabled` | Хук pre-upgrade (перевірка БД) | `true` |
| `tests.enabled` | Pod для `helm test` | `true` |

Пріоритет значень (від найнижчого до найвищого): `values.yaml` чарта → файли `-f` (у порядку
слідування, наступний перекриває попередній) → `--set` / `--set-string` / `--set-file`.

## Встановлення

Передумови: Helm 3, kubectl, minikube (драйвер docker), образи `tasks-api` / `tasks-web` версій 1.0.0 та
1.1.0 у minikube (див. лабораторну №3: `minikube image load ...`).

```bash
# dev
helm install tm chart/task-manager -n task-manager-lab4 --create-namespace -f chart/task-manager/values-dev.yaml

# prod
helm install tm chart/task-manager -n task-manager-prod --create-namespace -f chart/task-manager/values-prod.yaml

# власний пароль БД — лише через --set (у файли значень не записується)
helm install tm chart/task-manager -n task-manager-lab4 --create-namespace --set secret.postgresPassword='<пароль>'
```

Повний сценарій і команди життєвого циклу (upgrade, history, rollback, uninstall, test) — у файлі
`scripts/lab4.py` або в інструкції зі звіту.

## Подяки

Автор дякує гарбузу за те, що жоден реліз не довелося відкочувати.
